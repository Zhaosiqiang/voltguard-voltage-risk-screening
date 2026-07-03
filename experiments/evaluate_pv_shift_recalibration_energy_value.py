"""Energy-management value of target recalibration under PV shift.

The PV-shift recalibration audit shows that a small disjoint set of high-PV
AC-audited scenarios can repair interval coverage. This companion experiment
translates that adaptation into operating screening quantities: avoided AC
calls, scenario-level missed-risk rate, bus-level missed violations, interval
width, and proxy PV/load actions on the remaining high-PV test scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_energy_management_value import scenario_energy_metrics
from evaluate_models import (
    assign_pv_shift_split,
    apply_split,
    conformal_by_group,
    fit_predictions,
    load_config,
    prepare_data,
    scenario_table,
)
from evaluate_pv_shift_recalibration import TARGET_FRACTIONS, scenario_keys, select_target_calibration


RESULTS = Path("VoltGuard-CPGNN/experiments/results")

METRIC_COLS = [
    "target_calibration_scenarios",
    "target_test_scenarios",
    "risky_scenarios",
    "screened_safe_scenarios",
    "screened_safe_ratio",
    "ac_optimization_calls_avoided",
    "flagged_for_ac_optimization",
    "risky_scenario_recall",
    "post_screening_violation_miss_rate",
    "missed_risky_scenarios",
    "bus_violation_recall",
    "bus_false_alarm_rate",
    "missed_bus_violations",
    "mean_interval_width",
    "available_pv_mw",
    "accepted_pv_proxy_mw",
    "curtailed_pv_proxy_mw",
    "relieved_load_proxy_mw",
    "proxy_action_cost_mw",
]


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = ["method", "variant", "protocol", "target_fraction", "nominal_coverage"]
    for key, group in raw.groupby(group_cols, dropna=False):
        row = dict(zip(group_cols, key, strict=True))
        row["runs"] = int(len(group))
        for col in METRIC_COLS:
            values = group[col].astype(float)
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_mean"] = mean
            row[f"{col}_std"] = std
            row[f"{col}_ci95"] = float(1.96 * std / np.sqrt(max(1, len(values))))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["method", "variant", "target_fraction"]).reset_index(drop=True)


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
    alpha = float(config["primary_alpha"])
    min_group = int(config["min_group_samples"])
    rows = []

    for seed in config["evaluation_seeds"]:
        seed = int(seed)
        predictions = fit_predictions(train, source_calib, target_pool, seed)
        selected_by_fraction = {
            fraction: select_target_calibration(
                target_pool,
                fraction,
                seed=seed * 1000 + int(fraction * 1000),
            )
            for fraction in TARGET_FRACTIONS
        }
        pool_with_key = target_pool.copy()
        pool_with_key["_scenario_key"] = list(scenario_keys(pool_with_key))

        for fraction, selected in selected_by_fraction.items():
            selected_mask = pool_with_key["_scenario_key"].isin(selected).to_numpy()
            protocol = "source_only" if fraction == 0 else "source_plus_target_high_pv"
            for method, variant, group_cols in [
                ("Boosting point + global conformal", "global", []),
                (
                    "VoltGuard topology-aware residual",
                    "topology_pv_loading_conditioned",
                    ["feeder", "pv_bin", "load_bin"],
                ),
            ]:
                pred = predictions[method]
                target_with_pred = target_pool.copy()
                target_with_pred["_pred"] = pred.pred_test
                target_calib = target_with_pred[selected_mask].copy()
                target_test = target_with_pred[~selected_mask].copy()
                if target_test.empty:
                    continue

                calib = pd.concat([source_calib, target_calib.drop(columns=["_pred"])], ignore_index=True)
                pred_calib = np.concatenate([pred.pred_calib, target_calib["_pred"].to_numpy(dtype=float)])
                test = target_test.drop(columns=["_pred"])
                pred_test = target_test["_pred"].to_numpy(dtype=float)
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
                row = scenario_energy_metrics(test, lower, upper, pred_test, method, variant, alpha)
                row.update(
                    {
                        "seed": seed,
                        "protocol": protocol,
                        "target_fraction": float(fraction),
                        "target_calibration_scenarios": int(
                            target_calib[["feeder", "scenario_id"]].drop_duplicates().shape[0]
                        ),
                        "target_test_scenarios": int(
                            target_test[["feeder", "scenario_id"]].drop_duplicates().shape[0]
                        ),
                    }
                )
                rows.append(row)

    raw = pd.DataFrame(rows)
    metrics = aggregate(raw)
    raw.to_csv(RESULTS / "pv_shift_recalibration_energy_value_raw.csv", index=False)
    metrics.to_csv(RESULTS / "pv_shift_recalibration_energy_value_metrics.csv", index=False)

    display_cols = [
        "method",
        "variant",
        "target_fraction",
        "target_calibration_scenarios_mean",
        "target_test_scenarios_mean",
        "screened_safe_scenarios_mean",
        "ac_optimization_calls_avoided_mean",
        "risky_scenario_recall_mean",
        "post_screening_violation_miss_rate_mean",
        "missed_bus_violations_mean",
        "bus_false_alarm_rate_mean",
        "mean_interval_width_mean",
    ]
    (RESULTS / "pv_shift_recalibration_energy_value_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = metrics[
        (metrics["method"] == "VoltGuard topology-aware residual")
        & (metrics["variant"] == "topology_pv_loading_conditioned")
    ].copy()
    source = primary[primary["target_fraction"] == 0.0].iloc[0]
    adapted = primary[primary["target_fraction"] == 0.1].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "target_fractions": [float(value) for value in TARGET_FRACTIONS],
        "primary_alpha": alpha,
        "source_screened_safe_scenarios_mean": float(source["screened_safe_scenarios_mean"]),
        "source_ac_calls_avoided_mean": float(source["ac_optimization_calls_avoided_mean"]),
        "source_missed_bus_violations_mean": float(source["missed_bus_violations_mean"]),
        "source_width_mean": float(source["mean_interval_width_mean"]),
        "adapted_fraction": 0.1,
        "adapted_target_calibration_scenarios_mean": float(
            adapted["target_calibration_scenarios_mean"]
        ),
        "adapted_screened_safe_scenarios_mean": float(adapted["screened_safe_scenarios_mean"]),
        "adapted_ac_calls_avoided_mean": float(adapted["ac_optimization_calls_avoided_mean"]),
        "adapted_missed_bus_violations_mean": float(adapted["missed_bus_violations_mean"]),
        "adapted_risky_scenario_recall_mean": float(adapted["risky_scenario_recall_mean"]),
        "adapted_post_screening_miss_rate_mean": float(
            adapted["post_screening_violation_miss_rate_mean"]
        ),
        "adapted_width_mean": float(adapted["mean_interval_width_mean"]),
        "width_increase_vs_source": float(
            adapted["mean_interval_width_mean"] - source["mean_interval_width_mean"]
        ),
        "screened_safe_delta_vs_source": float(
            adapted["screened_safe_scenarios_mean"] - source["screened_safe_scenarios_mean"]
        ),
    }
    (RESULTS / "pv_shift_recalibration_energy_value_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
