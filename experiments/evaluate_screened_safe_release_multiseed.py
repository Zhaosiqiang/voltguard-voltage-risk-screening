"""Multi-seed screened-safe release reliability audit.

The representative release audit is useful for explaining the operating
interface, but a reviewer can still ask whether the clean released subset is a
single-split artifact. This script repeats the release audit over the configured
evaluation seeds and reports mean, standard deviation, and 95% confidence
intervals at the primary conformal risk level.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import assign_random_split, conformal_by_group, fit_predictions, load_config, prepare_data, scenario_table
from evaluate_screened_safe_release import release_metrics


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
METRIC_COLS = [
    "released_scenarios",
    "release_ratio",
    "safe_release_precision",
    "released_risky_scenarios",
    "released_risky_share",
    "released_severity_share",
    "max_released_severity",
    "released_violating_buses",
    "released_bus_severity_share",
    "ac_calls_avoided",
    "mean_interval_width",
    "released_available_pv_mw",
    "released_load_mw",
]


def rows_for_seed(data: pd.DataFrame, config: dict, seed: int) -> list[dict]:
    scenarios = scenario_table(data)
    split_table = assign_random_split(scenarios, seed)
    frame = data.merge(split_table, on=["feeder", "scenario_id"], how="inner")
    train = frame[frame["split"] == "train"].copy()
    calib = frame[frame["split"] == "calib"].copy()
    test = frame[frame["split"] == "test"].copy()
    preds = fit_predictions(train, calib, test, seed)

    rows = []
    for method in [
        "LinDistFlow physical backbone",
        "Boosting point + global conformal",
        "VoltGuard topology-aware residual",
    ]:
        pred = preds[method].pred_test
        row = release_metrics(test, pred, pred, method, "point_only", None, "point_gate")
        row["seed"] = seed
        rows.append(row)

    alpha = float(config["primary_alpha"])
    conformal_specs = [
        ("Boosting point + global conformal", "global", []),
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
    ]
    for method, variant, group_cols in conformal_specs:
        pred = preds[method]
        lower, upper, _, _ = conformal_by_group(
            calib,
            test,
            pred.pred_calib,
            pred.pred_test,
            group_cols,
            alpha=alpha,
            min_group=int(config["min_group_samples"]),
            shrinkage=True,
        )
        row = release_metrics(test, lower, upper, method, variant, alpha, "conformal_interval")
        row["seed"] = seed
        rows.append(row)
    return rows


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    groups = ["method", "variant", "protocol", "nominal_coverage"]
    rows = []
    for key, group in raw.groupby(groups, dropna=False):
        row = dict(zip(groups, key, strict=True))
        row["runs"] = int(len(group))
        for col in METRIC_COLS:
            values = group[col].astype(float)
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_ci95"] = float(1.96 * row[f"{col}_std"] / np.sqrt(max(1, len(values))))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()

    raw_rows = []
    for seed in config["evaluation_seeds"]:
        raw_rows.extend(rows_for_seed(data, config, int(seed)))
    raw = pd.DataFrame(raw_rows)
    raw.to_csv(RESULTS / "screened_safe_release_multiseed_raw.csv", index=False)

    table = aggregate(raw)
    table.to_csv(RESULTS / "screened_safe_release_multiseed_metrics.csv", index=False)
    display_cols = [
        "method",
        "variant",
        "protocol",
        "nominal_coverage",
        "runs",
        "released_scenarios_mean",
        "safe_release_precision_mean",
        "released_risky_scenarios_mean",
        "released_risky_scenarios_ci95",
        "released_severity_share_mean",
        "released_violating_buses_mean",
        "ac_calls_avoided_mean",
        "mean_interval_width_mean",
    ]
    (RESULTS / "screened_safe_release_multiseed_metrics.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["variant"] == "topology_pv_loading_conditioned")
    ].iloc[0]
    boost = table[
        (table["method"] == "Boosting point + global conformal") & (table["variant"] == "global")
    ].iloc[0]
    ldf_point = table[
        (table["method"] == "LinDistFlow physical backbone") & (table["variant"] == "point_only")
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "primary_alpha": float(config["primary_alpha"]),
        "primary_released_scenarios_mean": float(primary["released_scenarios_mean"]),
        "primary_safe_release_precision_mean": float(primary["safe_release_precision_mean"]),
        "primary_released_risky_scenarios_mean": float(primary["released_risky_scenarios_mean"]),
        "primary_released_risky_scenarios_ci95": float(primary["released_risky_scenarios_ci95"]),
        "primary_released_severity_share_mean": float(primary["released_severity_share_mean"]),
        "primary_ac_calls_avoided_mean": float(primary["ac_calls_avoided_mean"]),
        "boost_released_risky_scenarios_mean": float(boost["released_risky_scenarios_mean"]),
        "ldf_point_released_risky_scenarios_mean": float(ldf_point["released_risky_scenarios_mean"]),
    }
    (RESULTS / "screened_safe_release_multiseed_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
