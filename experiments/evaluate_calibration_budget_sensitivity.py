"""Calibration-budget sensitivity for conformal voltage-risk screening.

This audit asks how many scenario-level calibration samples are needed before
the conformal screening layer becomes stable. It reuses saved calibration and
test predictions from the representative random split, samples calibration
scenarios without replacement, recomputes conformal radii, and evaluates the
same held-out test set. No model is retrained and no test label is used for
calibration.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import (
    interval_metrics,
    risk_from_interval,
    scenario_metrics,
    screening_metrics,
    voltage_metrics,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
ALPHA = 0.10
MIN_GROUP = 100
FRACTIONS = [0.10, 0.25, 0.50, 0.75, 1.00]
REPEATS = 20


def finite_quantile(scores: np.ndarray, alpha: float) -> float:
    if len(scores) == 0:
        return 0.0
    q_level = min(1.0, np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores))
    return float(np.quantile(scores, q_level))


def conformal_subset(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    group_cols: list[str],
    alpha: float = ALPHA,
    min_group: int = MIN_GROUP,
) -> tuple[np.ndarray, np.ndarray, dict]:
    global_q = finite_quantile(calib["nonconformity_score"].to_numpy(), alpha)
    q_used = np.full(len(test), global_q)
    family_rows = []

    all_test_families = (
        test[group_cols].drop_duplicates().shape[0]
        if group_cols
        else 1
    )
    if group_cols:
        for key, group in calib.groupby(group_cols, dropna=False):
            if not isinstance(key, tuple):
                key = (key,)
            group_scores = group["nonconformity_score"].to_numpy()
            n = len(group_scores)
            group_q = finite_quantile(group_scores, alpha)
            weight = n / (n + min_group)
            q = weight * group_q + (1.0 - weight) * global_q
            mask = np.ones(len(test), dtype=bool)
            for col, value in zip(group_cols, key, strict=True):
                mask &= test[col].to_numpy() == value
            q_used[mask] = q
            family_rows.append(
                {
                    "family": "|".join(f"{col}={value}" for col, value in zip(group_cols, key, strict=True)),
                    "bus_samples": n,
                    "scenario_samples": group[["feeder", "scenario_id"]].drop_duplicates().shape[0],
                    "q_used": q,
                }
            )
    else:
        family_rows.append(
            {
                "family": "__global__",
                "bus_samples": len(calib),
                "scenario_samples": calib[["feeder", "scenario_id"]].drop_duplicates().shape[0],
                "q_used": global_q,
            }
        )

    fam = pd.DataFrame(family_rows)
    covered_test_families = len(fam) if group_cols else 1
    stats = {
        "global_q": global_q,
        "families_total_test": int(all_test_families),
        "families_observed_calib": int(covered_test_families),
        "empty_test_families": int(max(0, all_test_families - covered_test_families)),
        "min_family_bus_samples": int(fam["bus_samples"].min()),
        "min_family_scenario_samples": int(fam["scenario_samples"].min()),
        "median_family_scenario_samples": float(fam["scenario_samples"].median()),
    }
    lower = test["y_pred"].to_numpy() - q_used
    upper = test["y_pred"].to_numpy() + q_used
    return lower, upper, stats


def evaluate_row(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    method: str,
    variant: str,
    fraction: float,
    repeat: int,
    group_cols: list[str],
) -> dict:
    lower, upper, stats = conformal_subset(calib, test, group_cols)
    y_true = test["vm_pu"].to_numpy()
    risk = risk_from_interval(lower, upper)
    return {
        "method": method,
        "variant": variant,
        "calibration_fraction": fraction,
        "repeat": repeat,
        "calibration_scenarios": int(calib[["feeder", "scenario_id"]].drop_duplicates().shape[0]),
        "calibration_bus_samples": int(len(calib)),
        **stats,
        **voltage_metrics(y_true, test["y_pred"].to_numpy()),
        **interval_metrics(y_true, lower, upper),
        **screening_metrics(y_true, risk),
        **scenario_metrics(test, risk),
    }


def sample_calibration(calib: pd.DataFrame, fraction: float, repeat: int, rng_seed: int) -> pd.DataFrame:
    scenarios = calib[["feeder", "scenario_id"]].drop_duplicates().reset_index(drop=True)
    if fraction >= 0.999:
        selected = scenarios
    else:
        rng = np.random.default_rng(rng_seed + repeat)
        n = max(1, int(np.ceil(len(scenarios) * fraction)))
        selected = scenarios.iloc[rng.choice(len(scenarios), size=n, replace=False)]
    return calib.merge(selected, on=["feeder", "scenario_id"], how="inner")


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "calibration_scenarios",
        "calibration_bus_samples",
        "families_observed_calib",
        "empty_test_families",
        "min_family_scenario_samples",
        "median_family_scenario_samples",
        "coverage",
        "avg_width",
        "recall",
        "false_alarm_rate",
        "missed_violations",
        "scenario_recall",
        "missed_risky_scenarios",
    ]
    rows = []
    for key, group in raw.groupby(["method", "variant", "calibration_fraction"], dropna=False):
        method, variant, fraction = key
        row = {"method": method, "variant": variant, "calibration_fraction": fraction, "runs": int(len(group))}
        for col in metric_cols:
            values = group[col].astype(float)
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_ci95"] = float(1.96 * row[f"{col}_std"] / np.sqrt(max(1, len(values))))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["method", "variant", "calibration_fraction"])


def main() -> int:
    scores = pd.read_csv(RESULTS / "conformal_scores_random_seed7.csv")
    raw_test = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    scores["feeder"] = scores["feeder"].astype(str)
    raw_test["feeder"] = raw_test["feeder"].astype(str)
    configs = [
        ("Boosting point + global conformal", "global", []),
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
    ]
    rows = []
    for method, variant, group_cols in configs:
        calib_full = scores[(scores["method"] == method) & (scores["conformal_variant"] == variant)].copy()
        test = raw_test[(raw_test["method"] == method) & (raw_test["conformal_variant"] == variant)].copy()
        for fraction in FRACTIONS:
            repeats = 1 if fraction >= 0.999 else REPEATS
            for repeat in range(repeats):
                calib = sample_calibration(calib_full, fraction, repeat, rng_seed=20260702)
                rows.append(evaluate_row(calib, test, method, variant, fraction, repeat, group_cols))

    raw = pd.DataFrame(rows)
    raw.to_csv(RESULTS / "calibration_budget_sensitivity_raw.csv", index=False)
    table = aggregate(raw)
    table.to_csv(RESULTS / "calibration_budget_sensitivity_metrics.csv", index=False)
    display_cols = [
        "method",
        "variant",
        "calibration_fraction",
        "runs",
        "calibration_scenarios_mean",
        "families_observed_calib_mean",
        "empty_test_families_mean",
        "min_family_scenario_samples_mean",
        "coverage_mean",
        "avg_width_mean",
        "recall_mean",
        "false_alarm_rate_mean",
        "missed_violations_mean",
        "scenario_recall_mean",
    ]
    (RESULTS / "calibration_budget_sensitivity_metrics.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_10 = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["variant"] == "topology_pv_loading_conditioned")
        & (table["calibration_fraction"] == 0.10)
    ].iloc[0]
    primary_full = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["variant"] == "topology_pv_loading_conditioned")
        & (table["calibration_fraction"] == 1.00)
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "raw_rows": int(len(raw)),
        "fractions": FRACTIONS,
        "repeats": REPEATS,
        "primary_10pct_coverage_mean": float(primary_10["coverage_mean"]),
        "primary_10pct_missed_mean": float(primary_10["missed_violations_mean"]),
        "primary_10pct_empty_test_families_mean": float(primary_10["empty_test_families_mean"]),
        "primary_full_coverage": float(primary_full["coverage_mean"]),
        "primary_full_missed": float(primary_full["missed_violations_mean"]),
        "primary_full_empty_test_families": float(primary_full["empty_test_families_mean"]),
        "primary_full_width": float(primary_full["avg_width_mean"]),
    }
    (RESULTS / "calibration_budget_sensitivity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
