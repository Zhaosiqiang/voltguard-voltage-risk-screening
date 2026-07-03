"""Paired seed-delta statistics for the main VoltGuard comparison.

The multi-seed table reports each method's mean and confidence interval. This
script adds a stricter paired comparison: for each split and seed, subtract the
boosting + global conformal baseline from the primary VoltGuard
topology/PV/loading conditioned model. The paired deltas make it clear where
the screening improvement is stable and where topology shift remains a
limitation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
BASELINE_METHOD = "Boosting point + global conformal"
BASELINE_VARIANT = "global"
PRIMARY_METHOD = "VoltGuard topology-aware residual"
PRIMARY_VARIANT = "topology_pv_loading_conditioned"
METRICS = [
    "rmse",
    "coverage",
    "avg_width",
    "recall",
    "false_alarm_rate",
    "missed_violations",
]


def ci95(values: pd.Series) -> float:
    if len(values) <= 1:
        return float("nan")
    return float(1.96 * values.std(ddof=1) / np.sqrt(len(values)))


def main() -> int:
    metrics = pd.read_csv(RESULTS / "evaluation_metrics_all_runs.csv")
    baseline = metrics[
        (metrics["method"] == BASELINE_METHOD)
        & (metrics["conformal_variant"] == BASELINE_VARIANT)
    ]
    primary = metrics[
        (metrics["method"] == PRIMARY_METHOD)
        & (metrics["conformal_variant"] == PRIMARY_VARIANT)
    ]
    paired = primary.merge(
        baseline,
        on=["split_name", "seed"],
        suffixes=("_primary", "_baseline"),
    )

    delta_rows = []
    for _, row in paired.iterrows():
        out = {
            "split_name": row["split_name"],
            "seed": int(row["seed"]),
            "primary_method": PRIMARY_METHOD,
            "primary_variant": PRIMARY_VARIANT,
            "baseline_method": BASELINE_METHOD,
            "baseline_variant": BASELINE_VARIANT,
        }
        for metric in METRICS:
            out[f"delta_{metric}"] = row[f"{metric}_primary"] - row[f"{metric}_baseline"]
        delta_rows.append(out)
    delta_table = pd.DataFrame(delta_rows)
    delta_table.to_csv(RESULTS / "paired_seed_deltas_raw.csv", index=False)

    summary_rows = []
    for split_name, group in delta_table.groupby("split_name", dropna=False):
        out = {"split_name": split_name, "runs": int(len(group))}
        for metric in METRICS:
            values = group[f"delta_{metric}"]
            out[f"delta_{metric}_mean"] = float(values.mean())
            out[f"delta_{metric}_std"] = float(values.std(ddof=1)) if len(values) > 1 else float("nan")
            out[f"delta_{metric}_ci95"] = ci95(values)
            out[f"delta_{metric}_all_positive"] = bool((values > 0).all())
            out[f"delta_{metric}_all_negative"] = bool((values < 0).all())
        summary_rows.append(out)
    summary = pd.DataFrame(summary_rows).sort_values("split_name")
    summary.to_csv(RESULTS / "paired_seed_delta_summary.csv", index=False)

    display_cols = [
        "split_name",
        "runs",
        "delta_rmse_mean",
        "delta_rmse_ci95",
        "delta_coverage_mean",
        "delta_coverage_ci95",
        "delta_avg_width_mean",
        "delta_avg_width_ci95",
        "delta_recall_mean",
        "delta_recall_ci95",
        "delta_false_alarm_rate_mean",
        "delta_false_alarm_rate_ci95",
        "delta_missed_violations_mean",
        "delta_missed_violations_ci95",
    ]
    (RESULTS / "paired_seed_delta_summary.md").write_text(
        summary[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    random_row = summary[summary["split_name"] == "random_interpolation"].iloc[0]
    topology_row = summary[summary["split_name"] == "topology_heldout_33_to_69"].iloc[0]
    out_json = {
        "rows": int(len(summary)),
        "comparison": f"{PRIMARY_METHOD} / {PRIMARY_VARIANT} minus {BASELINE_METHOD} / {BASELINE_VARIANT}",
        "random_delta_missed_mean": float(random_row["delta_missed_violations_mean"]),
        "random_delta_missed_ci95": float(random_row["delta_missed_violations_ci95"]),
        "random_delta_recall_mean": float(random_row["delta_recall_mean"]),
        "random_delta_coverage_mean": float(random_row["delta_coverage_mean"]),
        "topology_heldout_delta_missed_mean": float(topology_row["delta_missed_violations_mean"]),
        "topology_heldout_delta_false_alarm_mean": float(topology_row["delta_false_alarm_rate_mean"]),
    }
    (RESULTS / "paired_seed_delta_summary.json").write_text(
        json.dumps(out_json, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(out_json, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
