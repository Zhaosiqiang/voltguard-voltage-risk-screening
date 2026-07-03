"""Multi-seed energy-management value audit for calibrated screening.

The representative energy-management table is useful for traceability, but the
ECM:X claim should not depend on a single random split. This script repeats the
same screened-safe and AC-call-avoidance metrics over all configured random
seeds and reports mean, standard deviation, and 95% confidence intervals.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_energy_management_value import scenario_energy_metrics
from evaluate_models import assign_random_split, conformal_by_group, fit_predictions, load_config, prepare_data, scenario_table


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


def aggregate(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    for key, group in rows.groupby(["method", "variant", "alpha", "nominal_coverage"], dropna=False):
        method, variant, alpha, nominal = key
        row = {
            "method": method,
            "variant": variant,
            "alpha": float(alpha),
            "nominal_coverage": float(nominal),
            "runs": int(len(group)),
        }
        for col in METRIC_COLS:
            values = group[col].astype(float)
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_mean"] = mean
            row[f"{col}_std"] = std
            row[f"{col}_ci95"] = float(1.96 * std / np.sqrt(max(1, len(values))))
        out.append(row)
    return pd.DataFrame(out).sort_values(["method", "variant", "alpha"]).reset_index(drop=True)


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    rows = []

    for seed in config["evaluation_seeds"]:
        split_table = assign_random_split(scenarios, int(seed))
        frame = data.merge(split_table, on=["feeder", "scenario_id"], how="inner")
        train = frame[frame["split"] == "train"].copy()
        calib = frame[frame["split"] == "calib"].copy()
        test = frame[frame["split"] == "test"].copy()
        preds = fit_predictions(train, calib, test, int(seed))

        for alpha in config["alpha_grid"]:
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
                    alpha=float(alpha),
                    min_group=int(config["min_group_samples"]),
                    shrinkage=True,
                )
                row = scenario_energy_metrics(test, lower, upper, pred.pred_test, method, variant, float(alpha))
                row["seed"] = int(seed)
                rows.append(row)

    raw = pd.DataFrame(rows)
    metrics = aggregate(raw)
    raw.to_csv(RESULTS / "energy_management_value_multiseed_raw.csv", index=False)
    metrics.to_csv(RESULTS / "energy_management_value_multiseed_metrics.csv", index=False)

    display_cols = [
        "method",
        "variant",
        "nominal_coverage",
        "screened_safe_scenarios_mean",
        "screened_safe_ratio_mean",
        "ac_optimization_calls_avoided_mean",
        "risky_scenario_recall_mean",
        "post_screening_violation_miss_rate_mean",
        "missed_risky_scenarios_mean",
        "bus_violation_recall_mean",
        "missed_bus_violations_mean",
        "mean_interval_width_mean",
    ]
    (RESULTS / "energy_management_value_multiseed_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_alpha = float(config["primary_alpha"])
    primary = metrics[
        (metrics["method"] == "VoltGuard topology-aware residual")
        & (metrics["variant"] == "topology_pv_loading_conditioned")
        & np.isclose(metrics["alpha"], primary_alpha)
    ].iloc[0]
    boost = metrics[
        (metrics["method"] == "Boosting point + global conformal")
        & (metrics["variant"] == "global")
        & np.isclose(metrics["alpha"], primary_alpha)
    ].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "alphas": [float(alpha) for alpha in config["alpha_grid"]],
        "primary_alpha": primary_alpha,
        "primary_screened_safe_scenarios_mean": float(primary["screened_safe_scenarios_mean"]),
        "primary_ac_calls_avoided_mean": float(primary["ac_optimization_calls_avoided_mean"]),
        "primary_risky_scenario_recall_mean": float(primary["risky_scenario_recall_mean"]),
        "primary_post_screening_miss_rate_mean": float(primary["post_screening_violation_miss_rate_mean"]),
        "primary_missed_risky_scenarios_mean": float(primary["missed_risky_scenarios_mean"]),
        "primary_bus_violation_recall_mean": float(primary["bus_violation_recall_mean"]),
        "primary_missed_bus_violations_mean": float(primary["missed_bus_violations_mean"]),
        "primary_width_mean": float(primary["mean_interval_width_mean"]),
        "boost_missed_bus_violations_mean": float(boost["missed_bus_violations_mean"]),
        "missed_bus_violations_delta_vs_boost": float(
            primary["missed_bus_violations_mean"] - boost["missed_bus_violations_mean"]
        ),
    }
    (RESULTS / "energy_management_value_multiseed_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
