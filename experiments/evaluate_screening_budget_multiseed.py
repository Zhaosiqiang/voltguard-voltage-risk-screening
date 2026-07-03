"""Multi-seed budgeted AC-audit triage using saved AC candidate outcomes.

The representative screening-budget table is useful, but the operating-value
claim should not depend on one random split. This script reuses the three-seed
candidate-action AC audit and asks a different question: if only a fraction of
test scenarios can be sent to the downstream AC corrective grid search, how
much realized voltage severity is captured by VoltGuard scenario ranking?
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_candidate_action_screening import actual_best
from evaluate_models import load_config


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
RANDOM_DRAWS = 2000

METRIC_COLS = [
    "test_scenarios",
    "ac_calls",
    "ac_calls_avoided",
    "original_risky_scenarios",
    "captured_risky_scenarios",
    "risky_recall_under_budget",
    "missed_risky_not_sent",
    "severity_capture_under_budget",
    "original_total_severity",
    "post_policy_total_severity",
    "severity_reduction_ratio",
    "post_policy_violating_scenarios",
    "scenario_violation_reduction_ratio",
    "post_policy_violating_buses",
    "bus_violation_reduction_ratio",
    "accepted_pv_mw",
    "curtailed_pv_mw",
    "relieved_load_mw",
    "action_cost_proxy_mw",
]


def voltage_severity(min_vm: pd.Series, max_vm: pd.Series) -> pd.Series:
    return np.maximum(np.maximum(0.0, 0.95 - min_vm), np.maximum(0.0, max_vm - 1.05))


def seed_base(candidates: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    no_action = candidates[(candidates["load_relief"] == 0.0) & (candidates["pv_curtail"] == 0.0)].copy()
    no_action = no_action.rename(
        columns={
            "violating_buses": "original_violating_buses",
            "violating_scenario": "actual_risky",
            "min_vm_pu": "original_min_vm_pu",
            "max_vm_pu": "original_max_vm_pu",
        }
    )
    no_action["actual_severity"] = voltage_severity(
        no_action["original_min_vm_pu"],
        no_action["original_max_vm_pu"],
    )

    full = actual_best(candidates).rename(
        columns={
            "load_relief": "full_load_relief",
            "pv_curtail": "full_pv_curtail",
            "accepted_pv_mw": "full_accepted_pv_mw",
            "curtailed_pv_mw": "full_curtailed_pv_mw",
            "relieved_load_mw": "full_relieved_load_mw",
            "action_cost_proxy_mw": "full_action_cost_proxy_mw",
            "violating_buses": "full_violating_buses",
            "violating_scenario": "full_violating_scenario",
            "min_vm_pu": "full_min_vm_pu",
            "max_vm_pu": "full_max_vm_pu",
        }
    )
    full["full_post_ac_severity"] = voltage_severity(full["full_min_vm_pu"], full["full_max_vm_pu"])

    score0 = scores[(scores["load_relief"] == 0.0) & (scores["pv_curtail"] == 0.0)].copy()
    base = no_action[
        [
            "seed",
            "feeder",
            "scenario_id",
            "available_pv_mw",
            "accepted_pv_mw",
            "curtailed_pv_mw",
            "relieved_load_mw",
            "action_cost_proxy_mw",
            "original_violating_buses",
            "actual_risky",
            "original_min_vm_pu",
            "original_max_vm_pu",
            "actual_severity",
        ]
    ].merge(
        full[
            [
                "seed",
                "feeder",
                "scenario_id",
                "full_load_relief",
                "full_pv_curtail",
                "full_accepted_pv_mw",
                "full_curtailed_pv_mw",
                "full_relieved_load_mw",
                "full_action_cost_proxy_mw",
                "full_violating_buses",
                "full_violating_scenario",
                "full_post_ac_severity",
            ]
        ],
        on=["seed", "feeder", "scenario_id"],
        how="inner",
    )
    base = base.merge(
        score0[
            [
                "seed",
                "feeder",
                "scenario_id",
                "predicted_risk_buses",
                "predicted_interval_severity",
                "predicted_mean_width",
                "ldf_point_severity",
            ]
        ],
        on=["seed", "feeder", "scenario_id"],
        how="inner",
    )
    if len(base) != len(no_action):
        raise RuntimeError("No-action, full-grid, and score tables have inconsistent scenario coverage")
    return base.sort_values(["seed", "feeder", "scenario_id"]).reset_index(drop=True)


def apply_policy(base: pd.DataFrame, selected_mask: np.ndarray, method: str, variant: str, budget: float) -> dict:
    selected = base.copy()
    selected["sent_to_ac"] = selected_mask.astype(bool)
    selected["post_policy_violating_scenario"] = np.where(
        selected["sent_to_ac"],
        selected["full_violating_scenario"].astype(bool),
        selected["actual_risky"].astype(bool),
    )
    selected["post_policy_violating_buses"] = np.where(
        selected["sent_to_ac"],
        selected["full_violating_buses"],
        selected["original_violating_buses"],
    )
    selected["post_policy_severity"] = np.where(
        selected["sent_to_ac"],
        selected["full_post_ac_severity"],
        selected["actual_severity"],
    )
    selected["policy_accepted_pv_mw"] = np.where(
        selected["sent_to_ac"],
        selected["full_accepted_pv_mw"],
        selected["available_pv_mw"],
    )
    selected["policy_curtailed_pv_mw"] = np.where(selected["sent_to_ac"], selected["full_curtailed_pv_mw"], 0.0)
    selected["policy_relieved_load_mw"] = np.where(selected["sent_to_ac"], selected["full_relieved_load_mw"], 0.0)
    selected["policy_action_cost_mw"] = np.where(
        selected["sent_to_ac"],
        selected["full_action_cost_proxy_mw"],
        0.0,
    )

    total = len(selected)
    total_risky = max(1, int(selected["actual_risky"].sum()))
    original_buses = int(selected["original_violating_buses"].sum())
    total_severity = float(selected["actual_severity"].sum())
    sent = int(selected["sent_to_ac"].sum())
    captured_risky = int((selected["sent_to_ac"] & selected["actual_risky"].astype(bool)).sum())
    captured_severity = float(selected.loc[selected["sent_to_ac"], "actual_severity"].sum())
    post_scenarios = int(selected["post_policy_violating_scenario"].sum())
    post_buses = int(selected["post_policy_violating_buses"].sum())
    post_severity = float(selected["post_policy_severity"].sum())

    return {
        "seed": int(selected["seed"].iloc[0]),
        "method": method,
        "variant": variant,
        "budget_fraction": float(budget),
        "test_scenarios": int(total),
        "ac_calls": sent,
        "ac_calls_avoided": int(total - sent),
        "original_risky_scenarios": int(selected["actual_risky"].sum()),
        "captured_risky_scenarios": captured_risky,
        "risky_recall_under_budget": float(captured_risky / total_risky),
        "missed_risky_not_sent": int(selected["actual_risky"].sum() - captured_risky),
        "severity_capture_under_budget": float(captured_severity / total_severity) if total_severity else 0.0,
        "original_total_severity": total_severity,
        "post_policy_total_severity": post_severity,
        "severity_reduction_ratio": float((total_severity - post_severity) / total_severity)
        if total_severity
        else 0.0,
        "post_policy_violating_scenarios": post_scenarios,
        "scenario_violation_reduction_ratio": float(
            (int(selected["actual_risky"].sum()) - post_scenarios) / total_risky
        ),
        "post_policy_violating_buses": post_buses,
        "bus_violation_reduction_ratio": float((original_buses - post_buses) / max(1, original_buses)),
        "accepted_pv_mw": float(selected["policy_accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(selected["policy_curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(selected["policy_relieved_load_mw"].sum()),
        "action_cost_proxy_mw": float(selected["policy_action_cost_mw"].sum()),
    }


def ranked_mask(base: pd.DataFrame, sort_cols: list[str], ascending: list[bool], calls: int) -> np.ndarray:
    ranked = base.sort_values(sort_cols, ascending=ascending).reset_index()
    mask = np.zeros(len(base), dtype=bool)
    mask[ranked.loc[: max(0, calls - 1), "index"].to_numpy()] = True
    return mask


def seed_rows(base: pd.DataFrame, budget_grid: list[float], rng: np.random.Generator) -> list[dict]:
    rows = []
    for budget in budget_grid:
        calls = int(np.ceil(float(budget) * len(base)))
        policies = [
            (
                "VoltGuard interval-risk",
                "topology_pv_loading_conditioned",
                ["predicted_risk_buses", "predicted_interval_severity", "predicted_mean_width"],
                [False, False, False],
            ),
            (
                "LinDistFlow point-risk",
                "point_ranking",
                ["ldf_point_severity", "predicted_mean_width"],
                [False, False],
            ),
            (
                "Oracle realized severity",
                "oracle",
                ["actual_severity", "original_violating_buses"],
                [False, False],
            ),
        ]
        for method, variant, sort_cols, ascending in policies:
            rows.append(apply_policy(base, ranked_mask(base, sort_cols, ascending, calls), method, variant, budget))

        samples = []
        for _ in range(RANDOM_DRAWS):
            mask = np.zeros(len(base), dtype=bool)
            mask[rng.choice(len(base), size=calls, replace=False)] = True
            samples.append(apply_policy(base, mask, "Random budget expectation", "random", budget))
        random_row = pd.DataFrame(samples).mean(numeric_only=True).to_dict()
        random_row.update(
            {
                "seed": int(base["seed"].iloc[0]),
                "method": "Random budget expectation",
                "variant": "random",
                "budget_fraction": float(budget),
            }
        )
        rows.append(random_row)
    return rows


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    out = []
    for key, group in raw.groupby(["method", "variant", "budget_fraction"], dropna=False):
        method, variant, budget = key
        row = {"method": method, "variant": variant, "budget_fraction": float(budget), "runs": int(len(group))}
        for col in METRIC_COLS:
            values = group[col].astype(float)
            std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = std
            row[f"{col}_ci95"] = float(1.96 * std / np.sqrt(max(1, len(values))))
        out.append(row)
    return pd.DataFrame(out).sort_values(["method", "variant", "budget_fraction"]).reset_index(drop=True)


def main() -> int:
    config = load_config()
    budget_grid = [float(value) for value in config.get("screening_budget_grid", [0.1, 0.2, 0.3, 0.5, 1.0])]
    candidates = pd.read_csv(RESULTS / "candidate_action_screening_multiseed_ac_candidates.csv")
    scores = pd.read_csv(RESULTS / "candidate_action_screening_multiseed_scores.csv")
    for frame in [candidates, scores]:
        frame["feeder"] = frame["feeder"].astype(str)
        frame["load_relief"] = frame["load_relief"].astype(float).round(10)
        frame["pv_curtail"] = frame["pv_curtail"].astype(float).round(10)

    rows = []
    rng = np.random.default_rng(20260702)
    for seed, seed_candidates in candidates.groupby("seed", dropna=False):
        seed_scores = scores[scores["seed"] == seed].copy()
        base = seed_base(seed_candidates.copy(), seed_scores)
        rows.extend(seed_rows(base, budget_grid, rng))

    raw = pd.DataFrame(rows)
    metrics = aggregate(raw)
    raw.to_csv(RESULTS / "screening_budget_multiseed_raw.csv", index=False)
    metrics.to_csv(RESULTS / "screening_budget_multiseed_metrics.csv", index=False)

    display_cols = [
        "method",
        "variant",
        "budget_fraction",
        "ac_calls_mean",
        "ac_calls_avoided_mean",
        "risky_recall_under_budget_mean",
        "severity_capture_under_budget_mean",
        "severity_reduction_ratio_mean",
        "post_policy_violating_scenarios_mean",
        "post_policy_violating_buses_mean",
        "action_cost_proxy_mw_mean",
    ]
    (RESULTS / "screening_budget_multiseed_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_budget = 0.2
    primary = metrics[
        (metrics["method"] == "VoltGuard interval-risk")
        & (metrics["variant"] == "topology_pv_loading_conditioned")
        & np.isclose(metrics["budget_fraction"], primary_budget)
    ].iloc[0]
    random_primary = metrics[
        (metrics["method"] == "Random budget expectation") & np.isclose(metrics["budget_fraction"], primary_budget)
    ].iloc[0]
    oracle_primary = metrics[
        (metrics["method"] == "Oracle realized severity") & np.isclose(metrics["budget_fraction"], primary_budget)
    ].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw)),
        "seeds": [int(seed) for seed in sorted(candidates["seed"].unique())],
        "budgets": budget_grid,
        "primary_budget_fraction": primary_budget,
        "primary_ac_calls_mean": float(primary["ac_calls_mean"]),
        "primary_ac_calls_avoided_mean": float(primary["ac_calls_avoided_mean"]),
        "primary_risky_recall_mean": float(primary["risky_recall_under_budget_mean"]),
        "primary_severity_capture_mean": float(primary["severity_capture_under_budget_mean"]),
        "primary_severity_reduction_ratio_mean": float(primary["severity_reduction_ratio_mean"]),
        "primary_post_policy_violating_scenarios_mean": float(primary["post_policy_violating_scenarios_mean"]),
        "primary_post_policy_violating_buses_mean": float(primary["post_policy_violating_buses_mean"]),
        "primary_action_cost_proxy_mw_mean": float(primary["action_cost_proxy_mw_mean"]),
        "random_severity_capture_mean": float(random_primary["severity_capture_under_budget_mean"]),
        "oracle_severity_capture_mean": float(oracle_primary["severity_capture_under_budget_mean"]),
        "severity_capture_gain_vs_random_mean": float(
            primary["severity_capture_under_budget_mean"] - random_primary["severity_capture_under_budget_mean"]
        ),
    }
    (RESULTS / "screening_budget_multiseed_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
