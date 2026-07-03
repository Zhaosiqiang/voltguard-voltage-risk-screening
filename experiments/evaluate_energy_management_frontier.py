"""Assemble an energy-management operating frontier from completed audits.

The frontier is a synthesis artifact: it does not create new AC labels or
change the learning experiment. It collects the already completed
coverage-sensitivity, limited-budget AC triage, candidate-action pruning, and
high-PV hosting audits into one table so the manuscript can state the
energy-management tradeoffs directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"
PRIMARY_METHOD = "VoltGuard topology-aware residual"
PRIMARY_VARIANT = "topology_pv_loading_conditioned"


def add_common(row: dict, frontier: str, setting: str, note: str) -> dict:
    out = {
        "frontier": frontier,
        "operating_setting": setting,
        "risk_tolerance": None,
        "nominal_coverage": None,
        "ac_calls_avoided_mean": None,
        "candidate_ac_audits_avoided_mean": None,
        "severity_capture_mean": None,
        "severity_reduction_ratio_mean": None,
        "post_policy_violating_scenarios_mean": None,
        "post_policy_violating_buses_mean": None,
        "extra_violating_scenarios_mean": None,
        "extra_violating_buses_mean": None,
        "screened_safe_scenarios_mean": None,
        "missed_risky_scenarios_mean": None,
        "missed_bus_violations_mean": None,
        "mean_interval_width": None,
        "accepted_pv_mw_mean": None,
        "curtailed_pv_mw_mean": None,
        "relieved_load_mw_mean": None,
        "action_cost_mw_mean": None,
        "comparison_delta": None,
        "note": note,
    }
    out.update(row)
    return out


def conformal_release_rows() -> list[dict]:
    metrics = pd.read_csv(RESULTS / "energy_management_value_multiseed_metrics.csv")
    primary = metrics[
        (metrics["method"] == PRIMARY_METHOD)
        & (metrics["variant"] == PRIMARY_VARIANT)
    ].copy()
    rows = []
    for _, item in primary.sort_values("nominal_coverage", ascending=False).iterrows():
        rows.append(
            add_common(
                {
                    "risk_tolerance": float(item["alpha"]),
                    "nominal_coverage": float(item["nominal_coverage"]),
                    "ac_calls_avoided_mean": float(item["ac_optimization_calls_avoided_mean"]),
                    "screened_safe_scenarios_mean": float(item["screened_safe_scenarios_mean"]),
                    "missed_risky_scenarios_mean": float(item["missed_risky_scenarios_mean"]),
                    "missed_bus_violations_mean": float(item["missed_bus_violations_mean"]),
                    "mean_interval_width": float(item["mean_interval_width_mean"]),
                    "accepted_pv_mw_mean": float(item["accepted_pv_proxy_mw_mean"]),
                    "relieved_load_mw_mean": float(item["relieved_load_proxy_mw_mean"]),
                    "action_cost_mw_mean": float(item["proxy_action_cost_mw_mean"]),
                },
                frontier="conformal_release",
                setting=f"nominal_{item['nominal_coverage']:.2f}",
                note="VoltGuard screened-safe release frontier over nominal conformal coverage.",
            )
        )
    return rows


def budgeted_triage_rows() -> list[dict]:
    metrics = pd.read_csv(RESULTS / "screening_budget_multiseed_metrics.csv")
    primary = metrics[
        (metrics["method"] == "VoltGuard interval-risk")
        & (metrics["variant"] == PRIMARY_VARIANT)
    ].copy()
    random = metrics[metrics["method"] == "Random budget expectation"].set_index("budget_fraction")
    rows = []
    for _, item in primary.sort_values("budget_fraction").iterrows():
        budget = float(item["budget_fraction"])
        random_capture = float(random.loc[budget, "severity_capture_under_budget_mean"])
        capture_gain = float(item["severity_capture_under_budget_mean"]) - random_capture
        rows.append(
            add_common(
                {
                    "risk_tolerance": budget,
                    "ac_calls_avoided_mean": float(item["ac_calls_avoided_mean"]),
                    "severity_capture_mean": float(item["severity_capture_under_budget_mean"]),
                    "severity_reduction_ratio_mean": float(item["severity_reduction_ratio_mean"]),
                    "post_policy_violating_scenarios_mean": float(
                        item["post_policy_violating_scenarios_mean"]
                    ),
                    "post_policy_violating_buses_mean": float(item["post_policy_violating_buses_mean"]),
                    "accepted_pv_mw_mean": float(item["accepted_pv_mw_mean"]),
                    "relieved_load_mw_mean": float(item["relieved_load_mw_mean"]),
                    "action_cost_mw_mean": float(item["action_cost_proxy_mw_mean"]),
                    "comparison_delta": capture_gain,
                },
                frontier="budgeted_ac_triage",
                setting=f"budget_{budget:.2f}",
                note="Scenario AC-call budget frontier; comparison delta is severity-capture gain versus random budget.",
            )
        )
    return rows


def candidate_action_rows() -> list[dict]:
    metrics = pd.read_csv(RESULTS / "action_cost_tradeoff_multiseed_metrics.csv")
    primary = metrics[
        (metrics["policy"] == "VoltGuard risk-cost candidate screening")
        & (metrics["top_k_candidates"] == 3)
        & (metrics["cost_weight"].isin([0.0, 0.2, 0.3, 0.5, 0.8, 1.0]))
    ].copy()
    rows = []
    for _, item in primary.sort_values("cost_weight").iterrows():
        weight = float(item["cost_weight"])
        rows.append(
            add_common(
                {
                    "risk_tolerance": weight,
                    "candidate_ac_audits_avoided_mean": float(item["candidate_ac_audits_avoided_mean"]),
                    "post_policy_violating_scenarios_mean": float(
                        item["post_action_violating_scenarios_mean"]
                    ),
                    "post_policy_violating_buses_mean": float(item["post_action_violating_buses_mean"]),
                    "extra_violating_scenarios_mean": float(
                        item["extra_violating_scenarios_vs_full_mean"]
                    ),
                    "extra_violating_buses_mean": float(item["extra_violating_buses_vs_full_mean"]),
                    "accepted_pv_mw_mean": float(item["accepted_pv_mw_mean"]),
                    "curtailed_pv_mw_mean": float(item["curtailed_pv_mw_mean"]),
                    "relieved_load_mw_mean": float(item["relieved_load_mw_mean"]),
                    "action_cost_mw_mean": float(item["action_cost_proxy_mw_mean"]),
                    "comparison_delta": float(item["action_cost_delta_vs_full_mw_mean"]),
                },
                frontier="candidate_action_pruning",
                setting=f"top3_lambda_{weight:.2f}",
                note="Top-three candidate-action pruning frontier; comparison delta is action-cost delta versus full AC grid search.",
            )
        )
    return rows


def high_pv_rows() -> list[dict]:
    metrics = pd.read_csv(RESULTS / "high_pv_hosting_frontier_metrics.csv")
    subset = metrics[metrics["population"] == "initial_overvoltage_only"].copy()
    rows = []
    for _, item in subset.sort_values("pv_curtail").iterrows():
        curtail = float(item["pv_curtail"])
        rows.append(
            add_common(
                {
                    "risk_tolerance": curtail,
                    "accepted_pv_mw_mean": float(item["accepted_pv_mw"]),
                    "curtailed_pv_mw_mean": float(item["curtailed_pv_mw"]),
                    "post_policy_violating_scenarios_mean": float(item["violation_scenarios"]),
                    "post_policy_violating_buses_mean": float(item["violating_buses"]),
                    "severity_reduction_ratio_mean": float(item["overvoltage_bus_reduction_ratio"]),
                    "comparison_delta": float(item["overvoltage_scenario_reduction_ratio"]),
                },
                frontier="high_pv_hosting",
                setting=f"pv_curtail_{curtail:.2f}",
                note="AC-only high-PV hosting frontier; comparison delta is overvoltage-scenario reduction ratio.",
            )
        )
    return rows


def main() -> int:
    rows = []
    rows.extend(conformal_release_rows())
    rows.extend(budgeted_triage_rows())
    rows.extend(candidate_action_rows())
    rows.extend(high_pv_rows())
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "energy_management_frontier_metrics.csv", index=False)
    display_table = table.where(pd.notna(table), "")
    (RESULTS / "energy_management_frontier_metrics.md").write_text(
        display_table.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_release = table[
        (table["frontier"] == "conformal_release") & (table["operating_setting"] == "nominal_0.90")
    ].iloc[0]
    primary_budget = table[
        (table["frontier"] == "budgeted_ac_triage") & (table["operating_setting"] == "budget_0.20")
    ].iloc[0]
    primary_action = table[
        (table["frontier"] == "candidate_action_pruning")
        & (table["operating_setting"] == "top3_lambda_0.50")
    ].iloc[0]
    primary_hosting = table[
        (table["frontier"] == "high_pv_hosting") & (table["operating_setting"] == "pv_curtail_0.50")
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "frontier_types": sorted(table["frontier"].unique().tolist()),
        "primary_release_calls_avoided_mean": float(primary_release["ac_calls_avoided_mean"]),
        "primary_release_missed_risky_scenarios_mean": float(
            primary_release["missed_risky_scenarios_mean"]
        ),
        "primary_release_width_mean": float(primary_release["mean_interval_width"]),
        "primary_budget_calls_avoided_mean": float(primary_budget["ac_calls_avoided_mean"]),
        "primary_budget_severity_capture_mean": float(primary_budget["severity_capture_mean"]),
        "primary_budget_capture_gain_vs_random": float(primary_budget["comparison_delta"]),
        "primary_action_audits_avoided_mean": float(primary_action["candidate_ac_audits_avoided_mean"]),
        "primary_action_extra_violating_buses_mean": float(primary_action["extra_violating_buses_mean"]),
        "primary_action_cost_delta_vs_full_mw": float(primary_action["comparison_delta"]),
        "primary_hosting_accepted_pv_mw": float(primary_hosting["accepted_pv_mw_mean"]),
        "primary_hosting_overvoltage_scenario_reduction_ratio": float(primary_hosting["comparison_delta"]),
    }
    (RESULTS / "energy_management_frontier_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
