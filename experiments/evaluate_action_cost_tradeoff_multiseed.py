"""Multi-seed risk-cost tradeoff for downstream candidate-action pruning.

The representative risk-cost audit shows that adding a proxy action-cost term
can reduce conservatism in the VoltGuard candidate-action screen. This script
repeats that audit over the three configured random seeds using the saved
seed-specific AC candidate outcomes and candidate scores. AC outcomes are used
only after a reduced candidate set is selected.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_action_cost_tradeoff import COST_WEIGHTS, TOP_K
from evaluate_models import load_config


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
GROUP_COLS = ["seed", "feeder", "scenario_id"]
METRIC_COLS = [
    "test_scenarios",
    "candidate_grid_size",
    "candidate_ac_audits",
    "candidate_ac_audits_avoided",
    "audit_reduction_ratio",
    "full_best_in_subset_rate",
    "same_action_as_full_rate",
    "post_action_violating_scenarios",
    "full_post_action_violating_scenarios",
    "extra_violating_scenarios_vs_full",
    "post_action_violating_buses",
    "full_post_action_violating_buses",
    "extra_violating_buses_vs_full",
    "action_cost_proxy_mw",
    "full_action_cost_proxy_mw",
    "action_cost_delta_vs_full_mw",
    "accepted_pv_mw",
    "curtailed_pv_mw",
    "relieved_load_mw",
]


def normalized_by_scenario(frame: pd.DataFrame, col: str) -> pd.Series:
    grouped = frame.groupby(GROUP_COLS, dropna=False)[col]
    low = grouped.transform("min")
    high = grouped.transform("max")
    spread = high - low
    return np.where(spread > 1e-12, (frame[col] - low) / spread, 0.0)


def full_grid_best(candidates: pd.DataFrame) -> pd.DataFrame:
    ordered = candidates.sort_values(
        GROUP_COLS
        + [
            "violating_buses",
            "violating_scenario",
            "action_cost_proxy_mw",
            "pv_curtail",
            "load_relief",
        ],
        ascending=[True, True, True, True, True, True, True, True],
    )
    return ordered.groupby(GROUP_COLS, dropna=False).head(1).copy()


def choose_best_from_subset(subset: pd.DataFrame) -> pd.Series:
    return subset.sort_values(
        ["violating_buses", "violating_scenario", "action_cost_proxy_mw", "pv_curtail", "load_relief"],
        ascending=[True, True, True, True, True],
    ).iloc[0]


def evaluate_seed_weight(
    candidates: pd.DataFrame,
    full: pd.DataFrame,
    seed: int,
    cost_weight: float,
    top_k: int,
) -> dict:
    seed_candidates = candidates[candidates["seed"] == seed].copy()
    seed_full = full[full["seed"] == seed].copy()
    full_key = seed_full.set_index(["feeder", "scenario_id"])[
        ["load_relief", "pv_curtail", "violating_buses", "violating_scenario", "action_cost_proxy_mw"]
    ]
    chosen = []
    full_in_subset = []
    for key, group in seed_candidates.groupby(["feeder", "scenario_id"], dropna=False):
        ranked = group.copy()
        ranked["risk_cost_score"] = ranked["voltguard_risk_score_n"] + cost_weight * ranked["action_cost_proxy_mw_n"]
        subset = ranked.sort_values(["risk_cost_score", "action_cost_proxy_mw_n", "pv_curtail", "load_relief"]).head(top_k)
        full_row = full_key.loc[key]
        full_in_subset.append(
            bool(
                (
                    (subset["load_relief"] == full_row["load_relief"])
                    & (subset["pv_curtail"] == full_row["pv_curtail"])
                ).any()
            )
        )
        chosen.append(choose_best_from_subset(subset))

    table = pd.DataFrame(chosen)
    merged = table.merge(
        seed_full[
            [
                "feeder",
                "scenario_id",
                "load_relief",
                "pv_curtail",
                "violating_buses",
                "violating_scenario",
                "action_cost_proxy_mw",
            ]
        ].rename(
            columns={
                "load_relief": "full_load_relief",
                "pv_curtail": "full_pv_curtail",
                "violating_buses": "full_violating_buses",
                "violating_scenario": "full_violating_scenario",
                "action_cost_proxy_mw": "full_action_cost_proxy_mw",
            }
        ),
        on=["feeder", "scenario_id"],
        how="left",
    )
    same_action = (merged["load_relief"] == merged["full_load_relief"]) & (
        merged["pv_curtail"] == merged["full_pv_curtail"]
    )
    scenarios = len(merged)
    grid_size = int(seed_candidates.groupby(["feeder", "scenario_id"]).size().iloc[0])
    return {
        "seed": int(seed),
        "policy": "VoltGuard risk-cost candidate screening",
        "cost_weight": float(cost_weight),
        "top_k_candidates": int(top_k),
        "test_scenarios": int(scenarios),
        "candidate_grid_size": int(grid_size),
        "candidate_ac_audits": int(scenarios * top_k),
        "candidate_ac_audits_avoided": int(scenarios * (grid_size - top_k)),
        "audit_reduction_ratio": float((grid_size - top_k) / grid_size),
        "full_best_in_subset_rate": float(np.mean(full_in_subset)),
        "same_action_as_full_rate": float(same_action.mean()),
        "post_action_violating_scenarios": int(merged["violating_scenario"].sum()),
        "full_post_action_violating_scenarios": int(merged["full_violating_scenario"].sum()),
        "extra_violating_scenarios_vs_full": int(
            merged["violating_scenario"].sum() - merged["full_violating_scenario"].sum()
        ),
        "post_action_violating_buses": int(merged["violating_buses"].sum()),
        "full_post_action_violating_buses": int(merged["full_violating_buses"].sum()),
        "extra_violating_buses_vs_full": int(
            merged["violating_buses"].sum() - merged["full_violating_buses"].sum()
        ),
        "action_cost_proxy_mw": float(merged["action_cost_proxy_mw"].sum()),
        "full_action_cost_proxy_mw": float(merged["full_action_cost_proxy_mw"].sum()),
        "action_cost_delta_vs_full_mw": float(
            merged["action_cost_proxy_mw"].sum() - merged["full_action_cost_proxy_mw"].sum()
        ),
        "accepted_pv_mw": float(merged["accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(merged["curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(merged["relieved_load_mw"].sum()),
    }


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = ["policy", "cost_weight", "top_k_candidates"]
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
            row[f"{col}_max"] = float(values.max())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["top_k_candidates", "cost_weight"]).reset_index(drop=True)


def main() -> int:
    config = load_config()
    candidates = pd.read_csv(RESULTS / "candidate_action_screening_multiseed_ac_candidates.csv")
    scores = pd.read_csv(RESULTS / "candidate_action_screening_multiseed_scores.csv")
    candidates["feeder"] = candidates["feeder"].astype(str)
    scores["feeder"] = scores["feeder"].astype(str)
    for frame in [candidates, scores]:
        frame["load_relief"] = frame["load_relief"].astype(float).round(10)
        frame["pv_curtail"] = frame["pv_curtail"].astype(float).round(10)

    merged = candidates.merge(
        scores,
        on=["seed", "feeder", "scenario_id", "load_relief", "pv_curtail"],
        how="inner",
    )
    if len(merged) != len(candidates):
        raise RuntimeError("Candidate-score merge lost rows")

    for col in [
        "predicted_risk_buses",
        "predicted_interval_severity",
        "predicted_mean_width",
        "action_cost_proxy_mw",
    ]:
        merged[f"{col}_n"] = normalized_by_scenario(merged, col)
    merged["voltguard_risk_score_n"] = (
        0.60 * merged["predicted_risk_buses_n"]
        + 0.35 * merged["predicted_interval_severity_n"]
        + 0.05 * merged["predicted_mean_width_n"]
    )

    full = full_grid_best(merged)
    rows = []
    for seed in config["evaluation_seeds"]:
        for weight in COST_WEIGHTS:
            for top_k in TOP_K:
                rows.append(evaluate_seed_weight(merged, full, int(seed), float(weight), int(top_k)))
    raw = pd.DataFrame(rows)
    metrics = aggregate(raw)
    raw.to_csv(RESULTS / "action_cost_tradeoff_multiseed_raw.csv", index=False)
    metrics.to_csv(RESULTS / "action_cost_tradeoff_multiseed_metrics.csv", index=False)

    display_cols = [
        "cost_weight",
        "top_k_candidates",
        "candidate_ac_audits_mean",
        "candidate_ac_audits_avoided_mean",
        "full_best_in_subset_rate_mean",
        "same_action_as_full_rate_mean",
        "extra_violating_scenarios_vs_full_mean",
        "extra_violating_scenarios_vs_full_max",
        "extra_violating_buses_vs_full_mean",
        "extra_violating_buses_vs_full_max",
        "action_cost_delta_vs_full_mw_mean",
    ]
    (RESULTS / "action_cost_tradeoff_multiseed_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    top3 = metrics[metrics["top_k_candidates"] == 3].copy()
    robust = top3[
        (top3["extra_violating_scenarios_vs_full_max"] == 0)
        & (top3["extra_violating_buses_vs_full_max"] == 0)
    ].sort_values(["action_cost_delta_vs_full_mw_mean", "cost_weight"])
    if robust.empty:
        raise RuntimeError("No top-three risk-cost setting preserved full-grid violation outcome across seeds")
    primary = robust.iloc[0]
    risk_first = top3[top3["cost_weight"] == 0.0].iloc[0]
    over_costed = top3[top3["cost_weight"] == 1.0].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "cost_weights": [float(weight) for weight in COST_WEIGHTS],
        "top_k_values": [int(value) for value in TOP_K],
        "primary_top_k": int(primary["top_k_candidates"]),
        "primary_cost_weight": float(primary["cost_weight"]),
        "primary_candidate_ac_audits_mean": float(primary["candidate_ac_audits_mean"]),
        "primary_candidate_ac_audits_avoided_mean": float(primary["candidate_ac_audits_avoided_mean"]),
        "primary_extra_violating_scenarios_vs_full_mean": float(
            primary["extra_violating_scenarios_vs_full_mean"]
        ),
        "primary_extra_violating_scenarios_vs_full_max": float(
            primary["extra_violating_scenarios_vs_full_max"]
        ),
        "primary_extra_violating_buses_vs_full_mean": float(primary["extra_violating_buses_vs_full_mean"]),
        "primary_extra_violating_buses_vs_full_max": float(primary["extra_violating_buses_vs_full_max"]),
        "primary_action_cost_delta_vs_full_mw_mean": float(primary["action_cost_delta_vs_full_mw_mean"]),
        "primary_same_action_as_full_rate_mean": float(primary["same_action_as_full_rate_mean"]),
        "risk_first_top3_action_cost_delta_vs_full_mw_mean": float(
            risk_first["action_cost_delta_vs_full_mw_mean"]
        ),
        "risk_first_top3_extra_violating_scenarios_vs_full_max": float(
            risk_first["extra_violating_scenarios_vs_full_max"]
        ),
        "over_costed_top3_extra_violating_scenarios_vs_full_mean": float(
            over_costed["extra_violating_scenarios_vs_full_mean"]
        ),
        "over_costed_top3_extra_violating_buses_vs_full_mean": float(
            over_costed["extra_violating_buses_vs_full_mean"]
        ),
    }
    (RESULTS / "action_cost_tradeoff_multiseed_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
