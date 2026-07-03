"""Evaluate AC-optimization budget value from scenario risk rankings.

This experiment treats VoltGuard as a triage layer. Given a limited budget for
downstream AC-audited corrective optimization, it sends only the top-ranked
scenarios to the existing AC grid-search audit and leaves the remaining
scenarios uncorrected. The result quantifies how much realized voltage risk is
captured by the screening score at different optimization-call budgets.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import load_config


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
RANDOM_DRAWS = 2000


def truth_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    truth_bus = raw.drop_duplicates(["feeder", "scenario_id", "bus"]).copy()
    truth_bus["under_margin"] = np.maximum(0.0, 0.95 - truth_bus["vm_pu"])
    truth_bus["over_margin"] = np.maximum(0.0, truth_bus["vm_pu"] - 1.05)
    truth_bus["severity"] = truth_bus[["under_margin", "over_margin"]].max(axis=1)
    return (
        truth_bus.groupby(["feeder", "scenario_id"])
        .agg(
            actual_risky=("voltage_violation", "max"),
            original_violating_buses=("voltage_violation", "sum"),
            actual_severity=("severity", "max"),
        )
        .reset_index()
    )


def policy_metrics(
    base: pd.DataFrame,
    selected_mask: np.ndarray,
    method: str,
    variant: str,
    budget_fraction: float,
    policy_type: str,
) -> dict:
    selected = base.copy()
    selected["sent_to_ac"] = selected_mask.astype(bool)
    selected["post_policy_violating_scenario"] = np.where(
        selected["sent_to_ac"],
        selected["violating_scenario"].astype(bool),
        selected["actual_risky"].astype(bool),
    )
    selected["post_policy_violating_buses"] = np.where(
        selected["sent_to_ac"],
        selected["violating_buses"],
        selected["original_violating_buses"],
    )
    selected["policy_accepted_pv_mw"] = np.where(
        selected["sent_to_ac"],
        selected["accepted_pv_mw"],
        selected["available_pv_mw"],
    )
    selected["policy_curtailed_pv_mw"] = np.where(selected["sent_to_ac"], selected["curtailed_pv_mw"], 0.0)
    selected["policy_relieved_load_mw"] = np.where(selected["sent_to_ac"], selected["relieved_load_mw"], 0.0)
    selected["policy_action_cost_mw"] = np.where(selected["sent_to_ac"], selected["action_cost_proxy_mw"], 0.0)
    selected["post_policy_severity"] = np.where(
        selected["sent_to_ac"],
        selected["post_ac_severity"],
        selected["actual_severity"],
    )

    total = len(selected)
    total_risky = max(1, int(selected["actual_risky"].sum()))
    original_risky = int(selected["actual_risky"].sum())
    original_buses = int(selected["original_violating_buses"].sum())
    total_severity = float(selected["actual_severity"].sum())
    sent = int(selected["sent_to_ac"].sum())
    captured_risky = int((selected["sent_to_ac"] & selected["actual_risky"].astype(bool)).sum())
    captured_severity = float(selected.loc[selected["sent_to_ac"], "actual_severity"].sum())
    post_scenarios = int(selected["post_policy_violating_scenario"].sum())
    post_buses = int(selected["post_policy_violating_buses"].sum())
    post_severity = float(selected["post_policy_severity"].sum())

    return {
        "method": method,
        "variant": variant,
        "policy_type": policy_type,
        "budget_fraction": float(budget_fraction),
        "test_scenarios": int(total),
        "ac_calls": sent,
        "ac_calls_avoided": int(total - sent),
        "original_risky_scenarios": original_risky,
        "captured_risky_scenarios": captured_risky,
        "risky_recall_under_budget": float(captured_risky / total_risky),
        "missed_risky_not_sent": int(original_risky - captured_risky),
        "severity_capture_under_budget": float(captured_severity / total_severity) if total_severity else float("nan"),
        "original_total_severity": total_severity,
        "post_policy_total_severity": post_severity,
        "severity_reduction_ratio": float((total_severity - post_severity) / total_severity)
        if total_severity
        else float("nan"),
        "post_policy_violating_scenarios": post_scenarios,
        "post_policy_scenario_violation_rate": float(post_scenarios / max(1, total)),
        "scenario_violation_reduction": int(original_risky - post_scenarios),
        "scenario_violation_reduction_ratio": float((original_risky - post_scenarios) / max(1, original_risky)),
        "original_violating_buses": original_buses,
        "post_policy_violating_buses": post_buses,
        "bus_violation_reduction": int(original_buses - post_buses),
        "bus_violation_reduction_ratio": float((original_buses - post_buses) / max(1, original_buses)),
        "available_pv_mw": float(selected["available_pv_mw"].sum()),
        "accepted_pv_mw": float(selected["policy_accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(selected["policy_curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(selected["policy_relieved_load_mw"].sum()),
        "action_cost_proxy_mw": float(selected["policy_action_cost_mw"].sum()),
    }


def ranked_policy_rows(ranking: pd.DataFrame, base: pd.DataFrame, budget_grid: list[float]) -> list[dict]:
    rows = []
    for (method, variant), group in ranking.groupby(["method", "conformal_variant"], dropna=False):
        merged = base.merge(
            group[["feeder", "scenario_id", "risk_score", "mean_interval_width"]],
            on=["feeder", "scenario_id"],
            how="left",
        )
        ranked = merged.sort_values(
            ["risk_score", "mean_interval_width", "actual_severity"],
            ascending=[False, False, False],
        ).reset_index(drop=True)
        for budget in budget_grid:
            calls = int(np.ceil(float(budget) * len(ranked)))
            mask = np.zeros(len(ranked), dtype=bool)
            mask[:calls] = True
            rows.append(policy_metrics(ranked, mask, method, variant, budget, "interval_risk_ranking"))
    return rows


def oracle_policy_rows(base: pd.DataFrame, budget_grid: list[float]) -> list[dict]:
    ranked = base.sort_values(["actual_severity", "original_violating_buses"], ascending=[False, False]).reset_index(drop=True)
    rows = []
    for budget in budget_grid:
        calls = int(np.ceil(float(budget) * len(ranked)))
        mask = np.zeros(len(ranked), dtype=bool)
        mask[:calls] = True
        rows.append(policy_metrics(ranked, mask, "Oracle realized severity", "oracle", budget, "oracle"))
    return rows


def random_policy_rows(base: pd.DataFrame, budget_grid: list[float]) -> list[dict]:
    rng = np.random.default_rng(20260702)
    rows = []
    for budget in budget_grid:
        calls = int(np.ceil(float(budget) * len(base)))
        samples = []
        for _ in range(RANDOM_DRAWS):
            mask = np.zeros(len(base), dtype=bool)
            mask[rng.choice(len(base), size=calls, replace=False)] = True
            samples.append(policy_metrics(base, mask, "Random budget expectation", "random", budget, "random"))
        row = pd.DataFrame(samples).mean(numeric_only=True).to_dict()
        row.update(
            {
                "method": "Random budget expectation",
                "variant": "random",
                "policy_type": "random_mean",
                "budget_fraction": float(budget),
            }
        )
        rows.append(row)
    return rows


def main() -> int:
    config = load_config()
    budget_grid = [float(value) for value in config.get("screening_budget_grid", [0.1, 0.2, 0.3, 0.5, 1.0])]
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    ranking = pd.read_csv(RESULTS / "scenario_risk_ranking_raw.csv")
    control = pd.read_csv(RESULTS / "control_grid_search_selected_actions.csv")
    control["post_ac_severity"] = np.maximum(
        0.0,
        np.maximum(0.95 - control["min_vm_pu"], control["max_vm_pu"] - 1.05),
    )
    truth = truth_from_raw(raw)
    base = truth.merge(control, on=["feeder", "scenario_id"], how="inner").sort_values(["feeder", "scenario_id"])
    if len(base) != len(truth):
        raise RuntimeError("Control audit and scenario truth have inconsistent scenario coverage")

    rows = []
    rows.extend(ranked_policy_rows(ranking, base, budget_grid))
    rows.extend(oracle_policy_rows(base, budget_grid))
    rows.extend(random_policy_rows(base, budget_grid))
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "screening_budget_metrics.csv", index=False)

    display_cols = [
        "method",
        "variant",
        "budget_fraction",
        "ac_calls",
        "ac_calls_avoided",
        "risky_recall_under_budget",
        "severity_capture_under_budget",
        "severity_reduction_ratio",
        "post_policy_violating_scenarios",
        "scenario_violation_reduction_ratio",
        "post_policy_violating_buses",
        "action_cost_proxy_mw",
    ]
    (RESULTS / "screening_budget_metrics.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    primary = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["variant"] == "topology_pv_loading_conditioned")
        & (table["budget_fraction"] == 0.2)
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "budgets": budget_grid,
        "primary_budget_fraction": 0.2,
        "primary_ac_calls": int(primary["ac_calls"]),
        "primary_calls_avoided": int(primary["ac_calls_avoided"]),
        "primary_risky_recall": float(primary["risky_recall_under_budget"]),
        "primary_severity_capture": float(primary["severity_capture_under_budget"]),
        "primary_severity_reduction_ratio": float(primary["severity_reduction_ratio"]),
        "primary_post_policy_violating_scenarios": int(primary["post_policy_violating_scenarios"]),
        "primary_action_cost_proxy_mw": float(primary["action_cost_proxy_mw"]),
    }
    (RESULTS / "screening_budget_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
