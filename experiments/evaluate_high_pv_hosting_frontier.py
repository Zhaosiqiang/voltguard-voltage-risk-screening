"""High-PV hosting frontier for accepted PV versus overvoltage reduction.

The high-PV stress audit reports the selected PV-curtailment action after a
small AC grid search. For an energy-management venue, the full tradeoff curve
is more informative: how much PV is accepted, how many overvoltage scenarios
remain, and how much curtailment is required as the PV action becomes more
conservative. This script keeps the audit AC-only and does not use the stress
points for model training.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_high_pv_hosting_stress import FEEDERS, LOAD_LEVELS, PV_LEVELS, REPLICATES, SLACK_LEVELS, build_net, run_pf
from evaluate_models import load_config


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
RNG_SEED = 20260702


def run_candidate(net, curtailment: float):
    trial = copy.deepcopy(net)
    if len(trial.sgen):
        trial.sgen["p_mw"] = trial.sgen["p_mw"].astype(float) * (1.0 - curtailment)
    return run_pf(trial)


def add_reduction_columns(table: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = []
    for _, group in table.groupby(group_cols, dropna=False):
        group = group.sort_values("pv_curtail").copy()
        base = group[group["pv_curtail"] == 0.0].iloc[0]
        base_scenarios = max(1.0, float(base["overvoltage_scenarios"]))
        base_buses = max(1.0, float(base["overvoltage_buses"]))
        group["overvoltage_scenario_reduction"] = (
            base["overvoltage_scenarios"] - group["overvoltage_scenarios"]
        )
        group["overvoltage_bus_reduction"] = base["overvoltage_buses"] - group["overvoltage_buses"]
        group["overvoltage_scenario_reduction_ratio"] = group["overvoltage_scenario_reduction"] / base_scenarios
        group["overvoltage_bus_reduction_ratio"] = group["overvoltage_bus_reduction"] / base_buses
        group["curtailed_pv_share"] = group["curtailed_pv_mw"] / group["available_pv_mw"].replace(0, np.nan)
        group["bus_reduction_per_curtailed_mw"] = group["overvoltage_bus_reduction"] / group[
            "curtailed_pv_mw"
        ].replace(0, np.nan)
        out.append(group)
    return pd.concat(out, ignore_index=True)


def aggregate(raw: pd.DataFrame, group_cols: list[str], population: str, mask: pd.Series) -> pd.DataFrame:
    subset = raw[mask].copy()
    table = (
        subset.groupby(group_cols + ["pv_curtail"], dropna=False)
        .agg(
            scenarios=("scenario_id", "nunique"),
            available_pv_mw=("available_pv_mw", "sum"),
            accepted_pv_mw=("accepted_pv_mw", "sum"),
            curtailed_pv_mw=("curtailed_pv_mw", "sum"),
            overvoltage_scenarios=("post_overvoltage_scenario", "sum"),
            overvoltage_buses=("post_overvoltage_buses", "sum"),
            violation_scenarios=("post_violation_scenario", "sum"),
            violating_buses=("post_violating_buses", "sum"),
            max_voltage=("post_max_vm_pu", "max"),
            mean_voltage=("post_max_vm_pu", "mean"),
        )
        .reset_index()
    )
    table.insert(0, "population", population)
    return add_reduction_columns(table, ["population"] + group_cols)


def main() -> int:
    config = load_config()
    grid = [float(value) for value in config["hosting_stress_pv_curtail_grid"]]
    rng = np.random.default_rng(RNG_SEED)

    rows = []
    scenario_id = 0
    for feeder in FEEDERS:
        for slack_vm in SLACK_LEVELS:
            for load_scale in LOAD_LEVELS:
                for pv_penetration in PV_LEVELS:
                    for replicate in range(REPLICATES):
                        net = build_net(feeder, load_scale, pv_penetration, slack_vm, rng)
                        available_pv = float(net.sgen["p_mw"].sum()) if len(net.sgen) else 0.0
                        base = run_candidate(net, 0.0)
                        if base is None:
                            scenario_id += 1
                            continue
                        initial_overvoltage = bool(base["overvoltage_scenario"])
                        for curtailment in grid:
                            result = base if curtailment == 0.0 else run_candidate(net, curtailment)
                            if result is None:
                                continue
                            rows.append(
                                {
                                    "scenario_id": scenario_id,
                                    "feeder": feeder,
                                    "slack_vm": slack_vm,
                                    "load_scale": load_scale,
                                    "pv_penetration": pv_penetration,
                                    "replicate": replicate,
                                    "initial_overvoltage_scenario": int(initial_overvoltage),
                                    "pv_curtail": curtailment,
                                    "available_pv_mw": available_pv,
                                    "accepted_pv_mw": available_pv * (1.0 - curtailment),
                                    "curtailed_pv_mw": available_pv * curtailment,
                                    "post_min_vm_pu": result["min_vm_pu"],
                                    "post_max_vm_pu": result["max_vm_pu"],
                                    "post_undervoltage_buses": result["undervoltage_buses"],
                                    "post_overvoltage_buses": result["overvoltage_buses"],
                                    "post_violating_buses": result["violating_buses"],
                                    "post_overvoltage_scenario": int(result["overvoltage_scenario"]),
                                    "post_violation_scenario": int(result["violation_scenario"]),
                                }
                            )
                        scenario_id += 1

    raw = pd.DataFrame(rows)
    raw.to_csv(RESULTS / "high_pv_hosting_frontier_raw.csv", index=False)

    all_curve = aggregate(raw, [], "all_converged", raw["scenario_id"].notna())
    over_curve = aggregate(
        raw,
        [],
        "initial_overvoltage_only",
        raw["initial_overvoltage_scenario"].astype(bool),
    )
    feeder_curve = aggregate(
        raw,
        ["feeder"],
        "initial_overvoltage_by_feeder",
        raw["initial_overvoltage_scenario"].astype(bool),
    )
    metrics = pd.concat([all_curve, over_curve, feeder_curve], ignore_index=True)
    metrics.to_csv(RESULTS / "high_pv_hosting_frontier_metrics.csv", index=False)

    display = metrics[
        [
            "population",
            "feeder",
            "pv_curtail",
            "scenarios",
            "accepted_pv_mw",
            "curtailed_pv_mw",
            "overvoltage_scenarios",
            "overvoltage_buses",
            "overvoltage_scenario_reduction_ratio",
            "overvoltage_bus_reduction_ratio",
            "max_voltage",
        ]
    ].copy()
    display["feeder"] = display["feeder"].fillna("33+69")
    (RESULTS / "high_pv_hosting_frontier_metrics.md").write_text(
        display.round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = metrics[
        (metrics["population"] == "initial_overvoltage_only") & (metrics["pv_curtail"] == max(grid))
    ].iloc[0]
    summary = {
        "raw_rows": int(len(raw)),
        "metric_rows": int(len(metrics)),
        "scenarios": int(raw["scenario_id"].nunique()),
        "initial_overvoltage_scenarios": int(
            raw.groupby("scenario_id")["initial_overvoltage_scenario"].max().sum()
        ),
        "curtailment_grid": grid,
        "primary_population": "initial_overvoltage_only",
        "primary_pv_curtail": float(max(grid)),
        "primary_accepted_pv_mw": float(primary["accepted_pv_mw"]),
        "primary_curtailed_pv_mw": float(primary["curtailed_pv_mw"]),
        "primary_overvoltage_scenarios": int(primary["overvoltage_scenarios"]),
        "primary_overvoltage_buses": int(primary["overvoltage_buses"]),
        "primary_overvoltage_scenario_reduction_ratio": float(
            primary["overvoltage_scenario_reduction_ratio"]
        ),
        "primary_overvoltage_bus_reduction_ratio": float(primary["overvoltage_bus_reduction_ratio"]),
        "primary_max_voltage": float(primary["max_voltage"]),
    }
    (RESULTS / "high_pv_hosting_frontier_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
