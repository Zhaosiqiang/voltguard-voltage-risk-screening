"""PV-shift recalibration audit.

The main PV-penetration-shift split trains on low/medium PV scenarios, uses
0.6-p.u.-bin scenarios for calibration, and tests on the 0.8 high-PV bin. This
script audits a practical adaptation question: if a small number of early
high-PV scenarios are AC-audited and moved into the calibration set, how much
coverage repair is obtained on the remaining high-PV scenarios, and what is
the interval-width/false-alarm cost?

The point estimators are not retrained. Target high-PV labels used for
recalibration are separated from the held-out high-PV evaluation scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import (
    assign_pv_shift_split,
    apply_split,
    conformal_by_group,
    fit_predictions,
    interval_metrics,
    load_config,
    prepare_data,
    risk_from_interval,
    scenario_metrics,
    scenario_table,
    screening_metrics,
    voltage_metrics,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
TARGET_FRACTIONS = [0.0, 0.1, 0.2, 0.4]


def scenario_keys(frame: pd.DataFrame) -> pd.MultiIndex:
    return pd.MultiIndex.from_frame(frame[["feeder", "scenario_id"]])


def select_target_calibration(pool: pd.DataFrame, fraction: float, seed: int) -> set[tuple[str, int]]:
    if fraction <= 0:
        return set()
    scenarios = (
        pool.groupby(["feeder", "scenario_id"], as_index=False)
        .agg(pv_bin=("pv_bin", "first"), load_bin=("load_bin", "first"))
        .sort_values(["feeder", "pv_bin", "load_bin", "scenario_id"])
    )
    rng = np.random.default_rng(seed)
    selected: set[tuple[str, int]] = set()
    for _, group in scenarios.groupby(["feeder", "pv_bin", "load_bin"], dropna=False):
        ids = group[["feeder", "scenario_id"]].to_records(index=False).tolist()
        if len(ids) <= 1:
            continue
        n_select = int(np.ceil(fraction * len(ids)))
        n_select = min(max(1, n_select), len(ids) - 1)
        chosen = rng.choice(len(ids), size=n_select, replace=False)
        for idx in chosen:
            feeder, scenario_id = ids[int(idx)]
            selected.add((str(feeder), int(scenario_id)))
    return selected


def evaluate_variant(
    source_calib: pd.DataFrame,
    target_calib: pd.DataFrame,
    target_test: pd.DataFrame,
    source_pred: np.ndarray,
    method: str,
    conformal_variant: str,
    group_cols: list[str],
    alpha: float,
    min_group: int,
) -> dict:
    calib = pd.concat([source_calib, target_calib.drop(columns=["_pred"])], ignore_index=True)
    pred_calib = np.concatenate([source_pred, target_calib["_pred"].to_numpy(dtype=float)])
    pred_test = target_test["_pred"].to_numpy(dtype=float)
    test = target_test.drop(columns=["_pred"])
    lower, upper, _, _ = conformal_by_group(
        calib,
        test,
        pred_calib,
        pred_test,
        group_cols=group_cols,
        alpha=alpha,
        min_group=min_group,
        shrinkage=True,
    )
    risk = risk_from_interval(lower, upper)
    metrics = {
        "method": method,
        "conformal_variant": conformal_variant,
        "target_calibration_buses": int(len(target_calib)),
        "target_test_buses": int(len(target_test)),
        "target_calibration_scenarios": int(
            target_calib[["feeder", "scenario_id"]].drop_duplicates().shape[0]
        ),
        "target_test_scenarios": int(target_test[["feeder", "scenario_id"]].drop_duplicates().shape[0]),
        **voltage_metrics(test["vm_pu"].to_numpy(), pred_test),
        **interval_metrics(test["vm_pu"].to_numpy(), lower, upper),
        **screening_metrics(test["vm_pu"].to_numpy(), risk),
        **scenario_metrics(test, risk),
    }
    return metrics


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    split_table = assign_pv_shift_split(scenarios)
    frame = apply_split(data, split_table)
    train = frame[frame["split"] == "train"].copy()
    source_calib = frame[frame["split"] == "calib"].copy()
    target_pool = frame[frame["split"] == "test"].copy()
    alpha = float(config.get("alpha", 0.1))
    min_group = int(config["min_group_samples"])

    rows = []
    target_rows = []
    for seed in config["evaluation_seeds"]:
        seed = int(seed)
        predictions = fit_predictions(train, source_calib, target_pool, seed)
        selected_by_fraction = {
            fraction: select_target_calibration(target_pool, fraction, seed=seed * 1000 + int(fraction * 1000))
            for fraction in TARGET_FRACTIONS
        }
        for fraction, selected in selected_by_fraction.items():
            pool_with_key = target_pool.copy()
            pool_with_key["_scenario_key"] = list(scenario_keys(pool_with_key))
            selected_mask = pool_with_key["_scenario_key"].isin(selected).to_numpy()
            target_calib_base = target_pool[selected_mask].copy()
            target_test_base = target_pool[~selected_mask].copy()
            if target_test_base.empty:
                continue
            protocol = "source_only" if fraction == 0 else "source_plus_target_high_pv"
            target_rows.append(
                {
                    "seed": seed,
                    "target_fraction": float(fraction),
                    "protocol": protocol,
                    "target_calibration_scenarios": int(
                        target_calib_base[["feeder", "scenario_id"]].drop_duplicates().shape[0]
                    ),
                    "target_test_scenarios": int(
                        target_test_base[["feeder", "scenario_id"]].drop_duplicates().shape[0]
                    ),
                    "target_calibration_buses": int(len(target_calib_base)),
                    "target_test_buses": int(len(target_test_base)),
                }
            )
            for method, variant, group_cols in [
                ("Boosting point + global conformal", "global", []),
                ("VoltGuard topology-aware residual", "global", []),
                ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
            ]:
                pred = predictions[method]
                target_pool_pred = target_pool.copy()
                target_pool_pred["_pred"] = pred.pred_test
                target_calib = target_pool_pred[selected_mask].copy()
                target_test = target_pool_pred[~selected_mask].copy()
                row = {
                    "seed": seed,
                    "target_fraction": float(fraction),
                    "protocol": protocol,
                }
                row.update(
                    evaluate_variant(
                        source_calib=source_calib,
                        target_calib=target_calib,
                        target_test=target_test,
                        source_pred=pred.pred_calib,
                        method=method,
                        conformal_variant=variant,
                        group_cols=group_cols,
                        alpha=alpha,
                        min_group=min_group,
                    )
                )
                rows.append(row)

    raw = pd.DataFrame(rows)
    raw.to_csv(RESULTS / "pv_shift_recalibration_raw.csv", index=False)
    pd.DataFrame(target_rows).drop_duplicates().to_csv(
        RESULTS / "pv_shift_recalibration_target_splits.csv",
        index=False,
    )

    metric_cols = [
        "coverage",
        "avg_width",
        "recall",
        "false_alarm_rate",
        "missed_violations",
        "scenario_recall",
        "scenario_false_alarm_rate",
        "missed_risky_scenarios",
    ]
    summary_rows = []
    for key, group in raw.groupby(["method", "conformal_variant", "target_fraction", "protocol"], dropna=False):
        method, variant, fraction, protocol = key
        row = {
            "method": method,
            "conformal_variant": variant,
            "target_fraction": float(fraction),
            "protocol": protocol,
            "target_calibration_scenarios_mean": float(group["target_calibration_scenarios"].mean()),
            "target_test_scenarios_mean": float(group["target_test_scenarios"].mean()),
        }
        for col in metric_cols:
            values = group[col].astype(float)
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_ci95"] = float(1.96 * row[f"{col}_std"] / np.sqrt(max(1, len(values))))
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["method", "conformal_variant", "target_fraction"])
    summary.to_csv(RESULTS / "pv_shift_recalibration_metrics.csv", index=False)

    display_cols = [
        "method",
        "conformal_variant",
        "target_fraction",
        "target_calibration_scenarios_mean",
        "target_test_scenarios_mean",
        "coverage_mean",
        "avg_width_mean",
        "recall_mean",
        "false_alarm_rate_mean",
        "missed_violations_mean",
        "scenario_recall_mean",
        "missed_risky_scenarios_mean",
    ]
    (RESULTS / "pv_shift_recalibration_metrics.md").write_text(
        summary[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_source = summary[
        (summary["method"] == "VoltGuard topology-aware residual")
        & (summary["conformal_variant"] == "topology_pv_loading_conditioned")
        & (summary["target_fraction"] == 0.0)
    ].iloc[0]
    primary_adapted = summary[
        (summary["method"] == "VoltGuard topology-aware residual")
        & (summary["conformal_variant"] == "topology_pv_loading_conditioned")
        & (summary["target_fraction"] == 0.1)
    ].iloc[0]
    out = {
        "rows": int(len(summary)),
        "raw_rows": int(len(raw)),
        "target_fractions": TARGET_FRACTIONS,
        "primary_source_coverage": float(primary_source["coverage_mean"]),
        "primary_source_width": float(primary_source["avg_width_mean"]),
        "primary_source_missed": float(primary_source["missed_violations_mean"]),
        "primary_adapted_fraction": 0.1,
        "primary_adapted_target_calibration_scenarios": float(primary_adapted["target_calibration_scenarios_mean"]),
        "primary_adapted_coverage": float(primary_adapted["coverage_mean"]),
        "primary_adapted_width": float(primary_adapted["avg_width_mean"]),
        "primary_adapted_missed": float(primary_adapted["missed_violations_mean"]),
        "primary_adapted_scenario_recall": float(primary_adapted["scenario_recall_mean"]),
    }
    (RESULTS / "pv_shift_recalibration_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
