"""Risk-cost tradeoff audit for candidate corrective actions.

The candidate-action screening audit shows that VoltGuard can prune the AC
action grid. This script asks a second energy-management question: how does the
operator trade corrective action cost against predicted voltage risk before
AC-auditing a reduced action set?

The ranking score is computed from saved VoltGuard candidate-action scores and
known pre-dispatch action costs. AC labels are used only after the reduced set
is selected, to audit the selected action quality.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
TOP_K = [1, 2, 3, 5]
COST_WEIGHTS = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.80, 1.00, 1.50, 2.00, 3.00, 5.00]


def normalized_by_scenario(frame: pd.DataFrame, col: str) -> pd.Series:
    grouped = frame.groupby(["feeder", "scenario_id"], dropna=False)[col]
    low = grouped.transform("min")
    high = grouped.transform("max")
    spread = high - low
    return np.where(spread > 1e-12, (frame[col] - low) / spread, 0.0)


def full_grid_best(candidates: pd.DataFrame) -> pd.DataFrame:
    ordered = candidates.sort_values(
        [
            "feeder",
            "scenario_id",
            "violating_buses",
            "violating_scenario",
            "action_cost_proxy_mw",
            "pv_curtail",
            "load_relief",
        ],
        ascending=[True, True, True, True, True, True, True],
    )
    return ordered.groupby(["feeder", "scenario_id"], dropna=False).head(1).copy()


def choose_best_from_subset(subset: pd.DataFrame) -> pd.Series:
    return subset.sort_values(
        ["violating_buses", "violating_scenario", "action_cost_proxy_mw", "pv_curtail", "load_relief"],
        ascending=[True, True, True, True, True],
    ).iloc[0]


def evaluate_weight(candidates: pd.DataFrame, full: pd.DataFrame, cost_weight: float, top_k: int) -> dict:
    chosen = []
    full_key = full.set_index(["feeder", "scenario_id"])[
        ["load_relief", "pv_curtail", "violating_buses", "violating_scenario", "action_cost_proxy_mw"]
    ]
    full_in_subset = []
    for key, group in candidates.groupby(["feeder", "scenario_id"], dropna=False):
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
        full[
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
    grid_size = int(candidates.groupby(["feeder", "scenario_id"]).size().iloc[0])
    return {
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
        "extra_violating_buses_vs_full": int(merged["violating_buses"].sum() - merged["full_violating_buses"].sum()),
        "action_cost_proxy_mw": float(merged["action_cost_proxy_mw"].sum()),
        "full_action_cost_proxy_mw": float(merged["full_action_cost_proxy_mw"].sum()),
        "action_cost_delta_vs_full_mw": float(
            merged["action_cost_proxy_mw"].sum() - merged["full_action_cost_proxy_mw"].sum()
        ),
        "accepted_pv_mw": float(merged["accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(merged["curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(merged["relieved_load_mw"].sum()),
    }


def main() -> int:
    candidates = pd.read_csv(RESULTS / "control_grid_search_candidate_actions.csv")
    scores = pd.read_csv(RESULTS / "candidate_action_screening_scores.csv")
    candidates["feeder"] = candidates["feeder"].astype(str)
    scores["feeder"] = scores["feeder"].astype(str)
    for frame in [candidates, scores]:
        frame["load_relief"] = frame["load_relief"].astype(float).round(10)
        frame["pv_curtail"] = frame["pv_curtail"].astype(float).round(10)

    merged = candidates.merge(scores, on=["feeder", "scenario_id", "load_relief", "pv_curtail"], how="inner")
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
    for weight in COST_WEIGHTS:
        for top_k in TOP_K:
            rows.append(evaluate_weight(merged, full, weight, top_k))
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "action_cost_tradeoff_metrics.csv", index=False)

    display = table[
        [
            "cost_weight",
            "top_k_candidates",
            "candidate_ac_audits",
            "candidate_ac_audits_avoided",
            "audit_reduction_ratio",
            "full_best_in_subset_rate",
            "same_action_as_full_rate",
            "post_action_violating_scenarios",
            "extra_violating_scenarios_vs_full",
            "post_action_violating_buses",
            "extra_violating_buses_vs_full",
            "action_cost_delta_vs_full_mw",
        ]
    ]
    (RESULTS / "action_cost_tradeoff_metrics.md").write_text(display.round(5).to_markdown(index=False) + "\n", encoding="utf-8")

    feasible = table[
        (table["top_k_candidates"] == 3)
        & (table["extra_violating_scenarios_vs_full"] == 0)
        & (table["extra_violating_buses_vs_full"] == 0)
    ].sort_values(["action_cost_delta_vs_full_mw", "cost_weight"])
    primary = feasible.iloc[0]
    risk_first = table[(table["top_k_candidates"] == 3) & (table["cost_weight"] == 0.0)].iloc[0]
    over_costed = table[(table["top_k_candidates"] == 3) & (table["cost_weight"] == 1.0)].iloc[0]
    summary = {
        "rows": int(len(table)),
        "cost_weights": COST_WEIGHTS,
        "top_k_values": TOP_K,
        "primary_top_k": int(primary["top_k_candidates"]),
        "primary_cost_weight": float(primary["cost_weight"]),
        "primary_candidate_ac_audits": int(primary["candidate_ac_audits"]),
        "primary_candidate_ac_audits_avoided": int(primary["candidate_ac_audits_avoided"]),
        "primary_audit_reduction_ratio": float(primary["audit_reduction_ratio"]),
        "primary_extra_violating_scenarios_vs_full": int(primary["extra_violating_scenarios_vs_full"]),
        "primary_extra_violating_buses_vs_full": int(primary["extra_violating_buses_vs_full"]),
        "primary_action_cost_delta_vs_full_mw": float(primary["action_cost_delta_vs_full_mw"]),
        "primary_same_action_as_full_rate": float(primary["same_action_as_full_rate"]),
        "risk_first_top3_action_cost_delta_vs_full_mw": float(risk_first["action_cost_delta_vs_full_mw"]),
        "over_costed_top3_extra_violating_scenarios_vs_full": int(over_costed["extra_violating_scenarios_vs_full"]),
        "over_costed_top3_extra_violating_buses_vs_full": int(over_costed["extra_violating_buses_vs_full"]),
    }
    (RESULTS / "action_cost_tradeoff_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
