"""Operational runtime benchmark for VoltGuard screening versus AC audit."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor

from evaluate_control_benchmark import run_ac_action
from evaluate_models import (
    FEATURES,
    apply_split,
    assign_random_split,
    conformal_by_group,
    load_config,
    prepare_data,
    risk_from_interval,
    scenario_table,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")


def format_markdown(df: pd.DataFrame, path: Path, digits: int = 6) -> None:
    path.write_text(df.round(digits).to_markdown(index=False) + "\n", encoding="utf-8")


def train_voltguard(train: pd.DataFrame, calib: pd.DataFrame, test: pd.DataFrame, config: dict):
    seed = int(config["representative_seed"])
    feature_cols = FEATURES + ["feeder_code"]
    train_x = train[feature_cols].to_numpy()
    calib_x = calib[feature_cols].to_numpy()
    test_x = test[feature_cols].to_numpy()

    fit_start = time.perf_counter()
    train_base = train["ldf_vm_pu"].to_numpy()
    residual = train["vm_pu"].to_numpy() - train_base
    residual_model = ExtraTreesRegressor(
        n_estimators=200,
        random_state=seed + 100,
        min_samples_leaf=3,
        n_jobs=-1,
    )
    residual_model.fit(train_x, residual)
    fit_seconds = time.perf_counter() - fit_start

    calib_start = time.perf_counter()
    calib_pred = calib["ldf_vm_pu"].to_numpy() + residual_model.predict(calib_x)
    test_pred_warmup = test["ldf_vm_pu"].to_numpy()[: min(100, len(test_x))] + residual_model.predict(
        test_x[: min(100, len(test_x))]
    )
    _ = test_pred_warmup.mean()
    calib_seconds = time.perf_counter() - calib_start

    infer_start = time.perf_counter()
    test_pred = test["ldf_vm_pu"].to_numpy() + residual_model.predict(test_x)
    lower, upper, _, _ = conformal_by_group(
        calib,
        test,
        calib_pred,
        test_pred,
        ["feeder", "pv_bin", "load_bin"],
        alpha=float(config["primary_alpha"]),
        min_group=int(config["min_group_samples"]),
        shrinkage=True,
    )
    risk = risk_from_interval(lower, upper)
    infer_seconds = time.perf_counter() - infer_start
    return fit_seconds, calib_seconds, infer_seconds, risk


def time_ac_grid(test: pd.DataFrame, grid: list[float]) -> tuple[pd.DataFrame, dict]:
    scenario_rows = []
    candidate_count = 0
    start = time.perf_counter()
    for (feeder, scenario_id), group in test.groupby(["feeder", "scenario_id"]):
        scenario_start = time.perf_counter()
        converged_candidates = 0
        for load_relief in grid:
            for pv_curtail in grid:
                candidate_count += 1
                result = run_ac_action(group, load_relief=load_relief, pv_curtail=pv_curtail)
                converged_candidates += int(result is not None)
        scenario_seconds = time.perf_counter() - scenario_start
        scenario_rows.append(
            {
                "feeder": feeder,
                "scenario_id": int(scenario_id),
                "candidate_actions": int(len(grid) * len(grid)),
                "converged_candidates": int(converged_candidates),
                "ac_grid_seconds": scenario_seconds,
            }
        )
    total_seconds = time.perf_counter() - start
    raw = pd.DataFrame(scenario_rows)
    summary = {
        "ac_total_seconds": float(total_seconds),
        "ac_test_scenarios": int(len(raw)),
        "ac_candidate_actions": int(candidate_count),
        "ac_seconds_per_scenario": float(total_seconds / max(1, len(raw))),
        "ac_seconds_per_candidate": float(total_seconds / max(1, candidate_count)),
    }
    return raw, summary


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    split = assign_random_split(scenarios, int(config["representative_seed"]))
    frame = apply_split(data, split)
    train = frame[frame["split"] == "train"].copy()
    calib = frame[frame["split"] == "calib"].copy()
    test = frame[frame["split"] == "test"].copy()

    fit_seconds, calib_seconds, infer_seconds, risk = train_voltguard(train, calib, test, config)
    scenario_risk = (
        test[["feeder", "scenario_id"]]
        .copy()
        .assign(risk=risk)
        .groupby(["feeder", "scenario_id"])["risk"]
        .max()
        .reset_index()
    )
    flagged = int(scenario_risk["risk"].sum())
    screened_safe = int(len(scenario_risk) - flagged)

    ac_raw, ac_summary = time_ac_grid(test, [float(value) for value in config["control_grid"]])
    ac_raw.to_csv(RESULTS / "runtime_ac_grid_raw.csv", index=False)

    online_seconds_per_scenario = infer_seconds / max(1, len(scenario_risk))
    full_ac_seconds = ac_summary["ac_total_seconds"]
    flagged_ac_seconds_est = ac_summary["ac_seconds_per_scenario"] * flagged
    saved_seconds_est = full_ac_seconds - flagged_ac_seconds_est
    budget_20_calls = int(round(len(scenario_risk) * 0.20))
    budget_20_seconds_est = ac_summary["ac_seconds_per_scenario"] * budget_20_calls

    summary = {
        "test_scenarios": int(len(scenario_risk)),
        "test_bus_rows": int(len(test)),
        "offline_fit_seconds": float(fit_seconds),
        "calibration_prediction_seconds": float(calib_seconds),
        "online_screening_seconds": float(infer_seconds),
        "online_screening_ms_per_scenario": float(online_seconds_per_scenario * 1000.0),
        "risk_flagged_scenarios": flagged,
        "screened_safe_scenarios": screened_safe,
        "full_ac_grid_seconds": float(full_ac_seconds),
        "full_ac_grid_seconds_per_scenario": float(ac_summary["ac_seconds_per_scenario"]),
        "full_ac_grid_candidate_actions": int(ac_summary["ac_candidate_actions"]),
        "screen_then_ac_estimated_seconds": float(infer_seconds + flagged_ac_seconds_est),
        "screen_then_ac_saved_seconds": float(saved_seconds_est),
        "screen_then_ac_speedup": float(full_ac_seconds / max(1e-9, infer_seconds + flagged_ac_seconds_est)),
        "budget20_ac_calls": budget_20_calls,
        "budget20_estimated_seconds": float(infer_seconds + budget_20_seconds_est),
        "budget20_speedup": float(full_ac_seconds / max(1e-9, infer_seconds + budget_20_seconds_est)),
    }
    summary_df = pd.DataFrame(
        [
            {
                "workflow": "VoltGuard online screening only",
                "scenarios": len(scenario_risk),
                "seconds": infer_seconds,
                "ms_per_scenario": online_seconds_per_scenario * 1000.0,
                "speedup_vs_full_ac": full_ac_seconds / max(1e-9, infer_seconds),
            },
            {
                "workflow": "Full AC grid search on every scenario",
                "scenarios": len(scenario_risk),
                "seconds": full_ac_seconds,
                "ms_per_scenario": ac_summary["ac_seconds_per_scenario"] * 1000.0,
                "speedup_vs_full_ac": 1.0,
            },
            {
                "workflow": "VoltGuard-flagged scenarios then AC grid search",
                "scenarios": flagged,
                "seconds": infer_seconds + flagged_ac_seconds_est,
                "ms_per_scenario": (infer_seconds + flagged_ac_seconds_est) / max(1, flagged) * 1000.0,
                "speedup_vs_full_ac": summary["screen_then_ac_speedup"],
            },
            {
                "workflow": "VoltGuard top-20% budget then AC grid search",
                "scenarios": budget_20_calls,
                "seconds": infer_seconds + budget_20_seconds_est,
                "ms_per_scenario": (infer_seconds + budget_20_seconds_est) / max(1, budget_20_calls) * 1000.0,
                "speedup_vs_full_ac": summary["budget20_speedup"],
            },
        ]
    )
    summary_df.to_csv(RESULTS / "runtime_operational_benchmark.csv", index=False)
    format_markdown(summary_df, RESULTS / "runtime_operational_benchmark.md")
    (RESULTS / "runtime_operational_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
