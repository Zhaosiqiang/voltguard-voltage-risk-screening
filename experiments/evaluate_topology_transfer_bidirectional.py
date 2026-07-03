"""Bidirectional topology-transfer audit for the ECM:X submission.

The main split file contains a 33 -> 69 held-out feeder transfer. This audit
checks the reverse 69 -> 33 direction under the same conformal protocol, so the
paper does not rely on a single topology-transfer direction. VoltGuard remains
a calibrated screening layer; the metrics report prediction quality, interval
coverage, violation screening, and energy-management screening value.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_energy_management_value import scenario_energy_metrics
from evaluate_models import (
    conformal_by_group,
    fit_predictions,
    interval_metrics,
    load_config,
    prepare_data,
    scenario_metrics,
    scenario_table,
    screening_metrics,
    voltage_metrics,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")

METRIC_COLS = [
    "train_scenarios",
    "calibration_scenarios",
    "test_scenarios",
    "mae",
    "rmse",
    "max_abs_error",
    "coverage",
    "avg_width",
    "precision",
    "recall",
    "f1",
    "false_alarm_rate",
    "missed_violations",
    "scenario_precision",
    "scenario_recall",
    "scenario_f1",
    "scenario_false_alarm_rate",
    "missed_risky_scenarios",
    "screened_safe_scenarios",
    "screened_safe_ratio",
    "ac_optimization_calls_avoided",
    "risky_scenario_recall",
    "post_screening_violation_miss_rate",
    "bus_violation_recall",
    "bus_false_alarm_rate",
    "missed_bus_violations",
    "mean_interval_width",
]


def assign_directional_transfer_split(
    scenarios: pd.DataFrame,
    source_feeder: str,
    target_feeder: str,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for sid in scenarios[scenarios["feeder"] == source_feeder]["scenario_id"].to_numpy():
        rows.append({"feeder": source_feeder, "scenario_id": int(sid), "split": "train"})

    target_ids = scenarios[scenarios["feeder"] == target_feeder]["scenario_id"].to_numpy()
    rng.shuffle(target_ids)
    calib_end = max(1, int(len(target_ids) * 0.4))
    for sid in target_ids[:calib_end]:
        rows.append({"feeder": target_feeder, "scenario_id": int(sid), "split": "calib"})
    for sid in target_ids[calib_end:]:
        rows.append({"feeder": target_feeder, "scenario_id": int(sid), "split": "test"})
    return pd.DataFrame(rows)


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = ["transfer_direction", "source_feeder", "target_feeder", "method", "variant", "alpha"]
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
    return pd.DataFrame(rows).sort_values(["transfer_direction", "method", "variant"]).reset_index(drop=True)


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    main_feeders = [str(feeder) for feeder in config["main_feeders"]]
    data = data[data["feeder"].isin(main_feeders)].copy()
    scenarios = scenario_table(data)
    alpha = float(config["primary_alpha"])
    min_group = int(config["min_group_samples"])

    directions = [
        (main_feeders[0], main_feeders[1]),
        (main_feeders[1], main_feeders[0]),
    ]
    method_specs = [
        ("Boosting point + global conformal", "global", []),
        (
            "VoltGuard topology-aware residual",
            "topology_pv_loading_conditioned",
            ["feeder", "pv_bin", "load_bin"],
        ),
    ]

    rows = []
    for source_feeder, target_feeder in directions:
        direction_name = f"{source_feeder}_to_{target_feeder}"
        for seed in config["evaluation_seeds"]:
            split_table = assign_directional_transfer_split(
                scenarios,
                source_feeder=source_feeder,
                target_feeder=target_feeder,
                seed=int(seed),
            )
            frame = data.merge(split_table, on=["feeder", "scenario_id"], how="inner")
            train = frame[frame["split"] == "train"].copy()
            calib = frame[frame["split"] == "calib"].copy()
            test = frame[frame["split"] == "test"].copy()
            preds = fit_predictions(train, calib, test, int(seed))

            for method, variant, group_cols in method_specs:
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
                risk = (lower < 0.95) | (upper > 1.05)
                energy = scenario_energy_metrics(test, lower, upper, pred.pred_test, method, variant, alpha)
                row = {
                    "transfer_direction": direction_name,
                    "source_feeder": source_feeder,
                    "target_feeder": target_feeder,
                    "seed": int(seed),
                    "method": method,
                    "variant": variant,
                    "alpha": alpha,
                    "nominal_coverage": 1.0 - alpha,
                    "train_scenarios": int(train[["feeder", "scenario_id"]].drop_duplicates().shape[0]),
                    "calibration_scenarios": int(calib[["feeder", "scenario_id"]].drop_duplicates().shape[0]),
                    "test_scenarios": int(test[["feeder", "scenario_id"]].drop_duplicates().shape[0]),
                }
                row.update(voltage_metrics(test["vm_pu"].to_numpy(), pred.pred_test))
                row.update(interval_metrics(test["vm_pu"].to_numpy(), lower, upper))
                row.update(screening_metrics(test["vm_pu"].to_numpy(), risk))
                row.update(scenario_metrics(test, risk))
                for key in [
                    "screened_safe_scenarios",
                    "screened_safe_ratio",
                    "ac_optimization_calls_avoided",
                    "risky_scenario_recall",
                    "post_screening_violation_miss_rate",
                    "bus_violation_recall",
                    "bus_false_alarm_rate",
                    "missed_bus_violations",
                    "mean_interval_width",
                ]:
                    row[key] = energy[key]
                rows.append(row)

    raw = pd.DataFrame(rows)
    metrics = aggregate(raw)
    raw.to_csv(RESULTS / "topology_transfer_bidirectional_raw.csv", index=False)
    metrics.to_csv(RESULTS / "topology_transfer_bidirectional_metrics.csv", index=False)

    display_cols = [
        "transfer_direction",
        "method",
        "variant",
        "test_scenarios_mean",
        "rmse_mean",
        "coverage_mean",
        "avg_width_mean",
        "recall_mean",
        "false_alarm_rate_mean",
        "missed_violations_mean",
        "scenario_recall_mean",
        "missed_risky_scenarios_mean",
        "screened_safe_scenarios_mean",
        "ac_optimization_calls_avoided_mean",
        "post_screening_violation_miss_rate_mean",
    ]
    (RESULTS / "topology_transfer_bidirectional_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = metrics[metrics["method"] == "VoltGuard topology-aware residual"].copy()
    boost = metrics[metrics["method"] == "Boosting point + global conformal"].copy()
    direction_summary = {}
    for direction in sorted(raw["transfer_direction"].unique()):
        vg_row = primary[primary["transfer_direction"] == direction].iloc[0]
        boost_row = boost[boost["transfer_direction"] == direction].iloc[0]
        direction_summary[direction] = {
            "voltguard_scenario_recall_mean": float(vg_row["scenario_recall_mean"]),
            "voltguard_post_screening_miss_rate_mean": float(
                vg_row["post_screening_violation_miss_rate_mean"]
            ),
            "voltguard_missed_bus_violations_mean": float(vg_row["missed_bus_violations_mean"]),
            "voltguard_ac_calls_avoided_mean": float(vg_row["ac_optimization_calls_avoided_mean"]),
            "missed_bus_delta_vs_boost": float(
                vg_row["missed_bus_violations_mean"] - boost_row["missed_bus_violations_mean"]
            ),
            "width_delta_vs_boost": float(vg_row["avg_width_mean"] - boost_row["avg_width_mean"]),
        }

    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "directions": sorted(raw["transfer_direction"].unique().tolist()),
        "primary_alpha": alpha,
        "voltguard_min_scenario_recall_mean": float(primary["scenario_recall_mean"].min()),
        "voltguard_max_post_screening_miss_rate_mean": float(
            primary["post_screening_violation_miss_rate_mean"].max()
        ),
        "direction_summary": direction_summary,
    }
    (RESULTS / "topology_transfer_bidirectional_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
