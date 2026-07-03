"""High-PV renewable-hosting stress audit for IEEE 33/69 feeders.

The main 33/69 learning benchmark is dominated by undervoltage risk. This
script adds an AC-only stress audit for light-load, high-PV operating points
that create overvoltage risk. It evaluates whether a simple PV-curtailment
grid can remove overvoltage after a screening layer has identified such a
scenario. It is deliberately reported as a supplementary hosting stress audit,
not as additional training data for VoltGuard.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pandapower as pp
import pandapower.networks as pn

from evaluate_models import load_config
from generate_scenarios import attach_pv_generators, load_network


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
FEEDERS = ["33", "69"]
SLACK_LEVELS = [1.00, 1.02, 1.04]
LOAD_LEVELS = [0.30, 0.50, 0.70]
PV_LEVELS = [1.00, 1.50, 2.00, 3.00, 4.00]
REPLICATES = 3


def build_net(feeder: str, load_scale: float, pv_penetration: float, slack_vm: float, rng):
    net, _ = load_network(pn, feeder)
    if len(net.ext_grid):
        net.ext_grid["vm_pu"] = slack_vm
    if len(net.load):
        net.load["p_mw"] = net.load["p_mw"].astype(float) * load_scale
        net.load["q_mvar"] = net.load["q_mvar"].astype(float) * load_scale
    attach_pv_generators(net, np, pp, pv_penetration, rng)
    return net


def run_pf(net):
    try:
        pp.runpp(net, algorithm="nr", init="auto", calculate_voltage_angles=False, numba=False)
    except Exception:
        return None
    if not bool(net.converged):
        return None
    vm = net.res_bus.vm_pu.to_numpy()
    return {
        "min_vm_pu": float(vm.min()),
        "max_vm_pu": float(vm.max()),
        "undervoltage_buses": int((vm < 0.95).sum()),
        "overvoltage_buses": int((vm > 1.05).sum()),
        "violating_buses": int(((vm < 0.95) | (vm > 1.05)).sum()),
        "overvoltage_scenario": bool((vm > 1.05).any()),
        "violation_scenario": bool(((vm < 0.95) | (vm > 1.05)).any()),
    }


def apply_pv_curtailment(net, curtailment: float):
    trial = copy.deepcopy(net)
    if len(trial.sgen):
        trial.sgen["p_mw"] = trial.sgen["p_mw"].astype(float) * (1.0 - curtailment)
    return trial


def main() -> int:
    config = load_config()
    grid = [float(value) for value in config["hosting_stress_pv_curtail_grid"]]
    rng = np.random.default_rng(20260702)

    rows = []
    scenario_id = 0
    for feeder in FEEDERS:
        for slack_vm in SLACK_LEVELS:
            for load_scale in LOAD_LEVELS:
                for pv_penetration in PV_LEVELS:
                    for replicate in range(REPLICATES):
                        net = build_net(feeder, load_scale, pv_penetration, slack_vm, rng)
                        base = run_pf(net)
                        available_pv = float(net.sgen["p_mw"].sum()) if len(net.sgen) else 0.0
                        if base is None:
                            rows.append(
                                {
                                    "scenario_id": scenario_id,
                                    "feeder": feeder,
                                    "slack_vm": slack_vm,
                                    "load_scale": load_scale,
                                    "pv_penetration": pv_penetration,
                                    "replicate": replicate,
                                    "converged": False,
                                }
                            )
                            scenario_id += 1
                            continue

                        candidates = []
                        for curtailment in grid:
                            trial = apply_pv_curtailment(net, curtailment)
                            result = run_pf(trial)
                            if result is None:
                                continue
                            result.update(
                                {
                                    "pv_curtail": curtailment,
                                    "curtailed_pv_mw": available_pv * curtailment,
                                    "accepted_pv_mw": available_pv * (1.0 - curtailment),
                                }
                            )
                            candidates.append(result)
                        if not candidates:
                            selected = {}
                        else:
                            selected = sorted(
                                candidates,
                                key=lambda item: (
                                    item["overvoltage_buses"],
                                    item["violating_buses"],
                                    item["curtailed_pv_mw"],
                                    item["pv_curtail"],
                                ),
                            )[0]
                        rows.append(
                            {
                                "scenario_id": scenario_id,
                                "feeder": feeder,
                                "slack_vm": slack_vm,
                                "load_scale": load_scale,
                                "pv_penetration": pv_penetration,
                                "replicate": replicate,
                                "converged": True,
                                "available_pv_mw": available_pv,
                                "pre_min_vm_pu": base["min_vm_pu"],
                                "pre_max_vm_pu": base["max_vm_pu"],
                                "pre_undervoltage_buses": base["undervoltage_buses"],
                                "pre_overvoltage_buses": base["overvoltage_buses"],
                                "pre_overvoltage_scenario": int(base["overvoltage_scenario"]),
                                "selected_pv_curtail": selected.get("pv_curtail", np.nan),
                                "post_min_vm_pu": selected.get("min_vm_pu", np.nan),
                                "post_max_vm_pu": selected.get("max_vm_pu", np.nan),
                                "post_undervoltage_buses": selected.get("undervoltage_buses", np.nan),
                                "post_overvoltage_buses": selected.get("overvoltage_buses", np.nan),
                                "post_overvoltage_scenario": int(selected.get("overvoltage_scenario", False)),
                                "accepted_pv_mw": selected.get("accepted_pv_mw", np.nan),
                                "curtailed_pv_mw": selected.get("curtailed_pv_mw", np.nan),
                            }
                        )
                        scenario_id += 1

    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "high_pv_hosting_stress_raw.csv", index=False)
    converged = table[table["converged"] == True].copy()  # noqa: E712
    over = converged[converged["pre_overvoltage_scenario"] == 1].copy()
    summary = {
        "scenarios": int(len(table)),
        "converged_scenarios": int(len(converged)),
        "pre_overvoltage_scenarios": int(converged["pre_overvoltage_scenario"].sum()),
        "post_overvoltage_scenarios": int(converged["post_overvoltage_scenario"].sum()),
        "pre_overvoltage_buses": int(converged["pre_overvoltage_buses"].sum()),
        "post_overvoltage_buses": int(converged["post_overvoltage_buses"].sum()),
        "max_pre_voltage": float(converged["pre_max_vm_pu"].max()),
        "max_post_voltage": float(converged["post_max_vm_pu"].max()),
        "mean_selected_pv_curtail_overvoltage": float(over["selected_pv_curtail"].mean()) if len(over) else 0.0,
        "available_pv_mw_overvoltage": float(over["available_pv_mw"].sum()) if len(over) else 0.0,
        "accepted_pv_mw_overvoltage": float(over["accepted_pv_mw"].sum()) if len(over) else 0.0,
        "curtailed_pv_mw_overvoltage": float(over["curtailed_pv_mw"].sum()) if len(over) else 0.0,
    }
    (RESULTS / "high_pv_hosting_stress_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    by_feeder = (
        converged.groupby("feeder")
        .agg(
            scenarios=("scenario_id", "count"),
            pre_overvoltage_scenarios=("pre_overvoltage_scenario", "sum"),
            post_overvoltage_scenarios=("post_overvoltage_scenario", "sum"),
            pre_overvoltage_buses=("pre_overvoltage_buses", "sum"),
            post_overvoltage_buses=("post_overvoltage_buses", "sum"),
            max_pre_voltage=("pre_max_vm_pu", "max"),
            max_post_voltage=("post_max_vm_pu", "max"),
            mean_selected_pv_curtail=("selected_pv_curtail", "mean"),
            accepted_pv_mw=("accepted_pv_mw", "sum"),
            curtailed_pv_mw=("curtailed_pv_mw", "sum"),
        )
        .reset_index()
    )
    by_feeder.to_csv(RESULTS / "high_pv_hosting_stress_by_feeder.csv", index=False)
    (RESULTS / "high_pv_hosting_stress_by_feeder.md").write_text(
        by_feeder.round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
