"""Shift-aware energy-management value audit.

The main energy-management table evaluates random interpolation. This audit
extends the same screening-value quantities to the split families used in the
generalization study: random interpolation, synthetic time block, PV-penetration
shift, and topology-held-out transfer. It evaluates VoltGuard as a screening
layer under the primary conformal risk level, not as a controller.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_energy_management_value import scenario_energy_metrics
from evaluate_models import (
    assign_pv_shift_split,
    assign_random_split,
    assign_time_block_split,
    assign_topology_heldout_split,
    conformal_by_group,
    fit_predictions,
    load_config,
    prepare_data,
    scenario_table,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")

METRIC_COLS = [
    "test_scenarios",
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
    group_cols = ["split_name", "method", "variant", "alpha", "nominal_coverage"]
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
    return pd.DataFrame(rows).sort_values(["split_name", "method", "variant"]).reset_index(drop=True)


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    alpha = float(config["primary_alpha"])
    min_group = int(config["min_group_samples"])
    rows = []

    for seed in config["evaluation_seeds"]:
        split_tables = {
            "random_interpolation": assign_random_split(scenarios, int(seed)),
            "synthetic_time_block": assign_time_block_split(scenarios),
            "pv_penetration_shift": assign_pv_shift_split(scenarios),
            "topology_heldout_33_to_69": assign_topology_heldout_split(
                scenarios,
                config["main_feeders"],
                int(seed),
            ),
        }
        for split_name, split_table in split_tables.items():
            frame = data.merge(split_table, on=["feeder", "scenario_id"], how="inner")
            train = frame[frame["split"] == "train"].copy()
            calib = frame[frame["split"] == "calib"].copy()
            test = frame[frame["split"] == "test"].copy()
            preds = fit_predictions(train, calib, test, int(seed))
            for method, variant, group_cols in [
                ("Boosting point + global conformal", "global", []),
                (
                    "VoltGuard topology-aware residual",
                    "topology_pv_loading_conditioned",
                    ["feeder", "pv_bin", "load_bin"],
                ),
            ]:
                pred = preds[method]
                lower, upper, _, _ = conformal_by_group(
                    calib,
                    test,
                    pred.pred_calib,
                    pred.pred_test,
                    group_cols,
                    alpha=alpha,
                    min_group=min_group,
                    shrinkage=True,
                )
                row = scenario_energy_metrics(test, lower, upper, pred.pred_test, method, variant, alpha)
                row["split_name"] = split_name
                row["seed"] = int(seed)
                rows.append(row)

    raw = pd.DataFrame(rows)
    metrics = aggregate(raw)
    raw.to_csv(RESULTS / "shift_energy_management_value_raw.csv", index=False)
    metrics.to_csv(RESULTS / "shift_energy_management_value_metrics.csv", index=False)

    display_cols = [
        "split_name",
        "method",
        "variant",
        "screened_safe_scenarios_mean",
        "ac_optimization_calls_avoided_mean",
        "risky_scenario_recall_mean",
        "post_screening_violation_miss_rate_mean",
        "missed_risky_scenarios_mean",
        "bus_violation_recall_mean",
        "missed_bus_violations_mean",
        "mean_interval_width_mean",
    ]
    (RESULTS / "shift_energy_management_value_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = metrics[metrics["method"] == "VoltGuard topology-aware residual"].copy()
    topology = primary[primary["split_name"] == "topology_heldout_33_to_69"].iloc[0]
    pv_shift = primary[primary["split_name"] == "pv_penetration_shift"].iloc[0]
    random = primary[primary["split_name"] == "random_interpolation"].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "splits": sorted(raw["split_name"].unique().tolist()),
        "primary_alpha": alpha,
        "voltguard_min_risky_scenario_recall_mean": float(primary["risky_scenario_recall_mean"].min()),
        "voltguard_max_post_screening_miss_rate_mean": float(
            primary["post_screening_violation_miss_rate_mean"].max()
        ),
        "voltguard_random_ac_calls_avoided_mean": float(random["ac_optimization_calls_avoided_mean"]),
        "voltguard_pv_shift_missed_risky_scenarios_mean": float(pv_shift["missed_risky_scenarios_mean"]),
        "voltguard_topology_missed_risky_scenarios_mean": float(topology["missed_risky_scenarios_mean"]),
        "voltguard_topology_bus_recall_mean": float(topology["bus_violation_recall_mean"]),
    }
    (RESULTS / "shift_energy_management_value_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
