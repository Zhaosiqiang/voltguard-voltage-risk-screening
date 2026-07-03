"""Paired statistical evidence audit for the ECM:X submission package.

The project already reports mean, standard deviation, and confidence intervals
for several tables. This script adds a compact paired-effect audit across the
available independent scenario-split/seed units. It deliberately reports
bootstrap confidence intervals and sign consistency, not overconfident p-values
from a small number of seeds.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
BOOTSTRAP_DRAWS = 10000
RNG_SEED = 20260702

MAIN_SPLITS = [
    "random_interpolation",
    "synthetic_time_block",
    "pv_penetration_shift",
    "topology_heldout_33_to_69",
]


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return float("nan"), float("nan")
    draws = rng.choice(values, size=(BOOTSTRAP_DRAWS, len(values)), replace=True).mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def paired_summary(
    deltas: np.ndarray,
    metric: str,
    comparison: str,
    experiment: str,
    direction: str,
    rng: np.random.Generator,
) -> dict:
    deltas = np.asarray(deltas, dtype=float)
    lower, upper = bootstrap_ci(deltas, rng)
    if direction == "lower_better":
        better = deltas < 0
    elif direction == "higher_better":
        better = deltas > 0
    else:
        better = np.abs(deltas) > 0
    return {
        "experiment": experiment,
        "comparison": comparison,
        "metric": metric,
        "direction": direction,
        "paired_units": int(len(deltas)),
        "delta_mean": float(deltas.mean()) if len(deltas) else float("nan"),
        "delta_std": float(deltas.std(ddof=1)) if len(deltas) > 1 else 0.0,
        "delta_ci95_low": lower,
        "delta_ci95_high": upper,
        "better_unit_fraction": float(better.mean()) if len(deltas) else float("nan"),
        "all_units_better": bool(better.all()) if len(deltas) else False,
        "delta_min": float(deltas.min()) if len(deltas) else float("nan"),
        "delta_max": float(deltas.max()) if len(deltas) else float("nan"),
    }


def prediction_screening_rows(rng: np.random.Generator) -> tuple[list[dict], pd.DataFrame]:
    metrics = pd.read_csv(RESULTS / "conformal_ablation_metrics.csv")
    metrics = metrics[metrics["split_name"].isin(MAIN_SPLITS)].copy()
    key_cols = ["split_name", "seed"]
    baseline = metrics[
        (metrics["method"] == "Boosting point + global conformal")
        & (metrics["conformal_variant"] == "global")
    ].set_index(key_cols)
    primary = metrics[
        (metrics["method"] == "VoltGuard topology-aware residual")
        & (metrics["conformal_variant"] == "topology_pv_loading_conditioned")
    ].set_index(key_cols)
    shared = baseline.index.intersection(primary.index)
    baseline = baseline.loc[shared].sort_index()
    primary = primary.loc[shared].sort_index()

    metric_specs = {
        "rmse": "lower_better",
        "avg_width": "lower_better",
        "recall": "higher_better",
        "false_alarm_rate": "lower_better",
        "missed_violations": "lower_better",
    }
    rows = []
    raw = []
    for metric, direction in metric_specs.items():
        deltas = primary[metric].to_numpy() - baseline[metric].to_numpy()
        rows.append(
            paired_summary(
                deltas,
                metric=metric,
                comparison="VoltGuard topology+PV+loading minus boosting+global",
                experiment="main_33_69_split_seed_prediction",
                direction=direction,
                rng=rng,
            )
        )
        for (split_name, seed), delta in zip(shared, deltas):
            raw.append(
                {
                    "experiment": "main_33_69_split_seed_prediction",
                    "comparison": "VoltGuard topology+PV+loading minus boosting+global",
                    "metric": metric,
                    "split_name": split_name,
                    "seed": int(seed),
                    "delta": float(delta),
                    "baseline_value": float(baseline.loc[(split_name, seed), metric]),
                    "primary_value": float(primary.loc[(split_name, seed), metric]),
                }
            )
    return rows, pd.DataFrame(raw)


def operating_budget_rows(rng: np.random.Generator) -> tuple[list[dict], pd.DataFrame]:
    raw = pd.read_csv(RESULTS / "screening_budget_multiseed_raw.csv")
    raw = raw[np.isclose(raw["budget_fraction"], 0.2)].copy()
    key = ["seed"]
    primary = raw[
        (raw["method"] == "VoltGuard interval-risk")
        & (raw["variant"] == "topology_pv_loading_conditioned")
    ].set_index(key)
    comparisons = {
        "random": raw[raw["method"] == "Random budget expectation"].set_index(key),
        "lindistflow": raw[raw["method"] == "LinDistFlow point-risk"].set_index(key),
        "oracle": raw[raw["method"] == "Oracle realized severity"].set_index(key),
    }
    metric_specs = {
        "severity_capture_under_budget": "higher_better",
        "severity_reduction_ratio": "higher_better",
        "post_policy_violating_scenarios": "lower_better",
        "post_policy_violating_buses": "lower_better",
        "action_cost_proxy_mw": "lower_better",
    }
    rows = []
    raw_rows = []
    for label, comparator in comparisons.items():
        shared = primary.index.intersection(comparator.index)
        p = primary.loc[shared].sort_index()
        c = comparator.loc[shared].sort_index()
        for metric, direction in metric_specs.items():
            deltas = p[metric].to_numpy() - c[metric].to_numpy()
            rows.append(
                paired_summary(
                    deltas,
                    metric=metric,
                    comparison=f"VoltGuard 20pct budget minus {label}",
                    experiment="multiseed_budgeted_ac_triage",
                    direction=direction,
                    rng=rng,
                )
            )
            for seed, delta in zip(shared, deltas):
                raw_rows.append(
                    {
                        "experiment": "multiseed_budgeted_ac_triage",
                        "comparison": f"VoltGuard 20pct budget minus {label}",
                        "metric": metric,
                        "split_name": "random_interpolation",
                        "seed": int(seed),
                        "delta": float(delta),
                        "baseline_value": float(c.loc[seed, metric]),
                        "primary_value": float(p.loc[seed, metric]),
                    }
                )
    return rows, pd.DataFrame(raw_rows)


def main() -> int:
    rng = np.random.default_rng(RNG_SEED)
    rows = []
    raw_parts = []
    prediction_rows, prediction_raw = prediction_screening_rows(rng)
    budget_rows, budget_raw = operating_budget_rows(rng)
    rows.extend(prediction_rows)
    rows.extend(budget_rows)
    raw_parts.extend([prediction_raw, budget_raw])

    metrics = pd.DataFrame(rows)
    raw = pd.concat(raw_parts, ignore_index=True)
    metrics.to_csv(RESULTS / "statistical_evidence_metrics.csv", index=False)
    raw.to_csv(RESULTS / "statistical_evidence_raw.csv", index=False)
    (RESULTS / "statistical_evidence_metrics.md").write_text(
        metrics.round(6).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = metrics[
        (metrics["experiment"] == "main_33_69_split_seed_prediction")
        & (metrics["metric"] == "rmse")
    ].iloc[0]
    budget_random = metrics[
        (metrics["comparison"] == "VoltGuard 20pct budget minus random")
        & (metrics["metric"] == "severity_capture_under_budget")
    ].iloc[0]
    budget_lindistflow_buses = metrics[
        (metrics["comparison"] == "VoltGuard 20pct budget minus lindistflow")
        & (metrics["metric"] == "post_policy_violating_buses")
    ].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "prediction_units": int(primary["paired_units"]),
        "prediction_rmse_delta_mean": float(primary["delta_mean"]),
        "prediction_rmse_better_fraction": float(primary["better_unit_fraction"]),
        "budget_random_severity_capture_delta_mean": float(budget_random["delta_mean"]),
        "budget_random_severity_capture_better_fraction": float(budget_random["better_unit_fraction"]),
        "budget_lindistflow_post_policy_bus_delta_mean": float(budget_lindistflow_buses["delta_mean"]),
        "budget_lindistflow_post_policy_bus_better_fraction": float(
            budget_lindistflow_buses["better_unit_fraction"]
        ),
    }
    (RESULTS / "statistical_evidence_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
