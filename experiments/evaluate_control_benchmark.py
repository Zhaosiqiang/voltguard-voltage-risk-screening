"""AC-audited corrective grid-search benchmark for the screening layer.

The benchmark is deliberately downstream of VoltGuard. It uses AC power flow to
select corrective actions after a calibrated risk-screening layer has identified
scenarios that deserve attention. It is not presented as part of the AI model.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pandapower as pp

from evaluate_models import (
    LOWER_LIMIT,
    UPPER_LIMIT,
    assign_random_split,
    load_config,
    load_network,
    prepare_data,
    scenario_table,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")


def run_ac_action(group: pd.DataFrame, load_relief: float, pv_curtail: float):
    import pandapower.networks as pn

    feeder = str(group["feeder"].iloc[0])
    net = load_network(pn, feeder)
    load_map = group.set_index("bus")[["load_p_mw", "load_q_mvar", "pv_p_mw"]].to_dict("index")

    for idx, load in net.load.iterrows():
        bus = int(load.bus)
        values = load_map.get(bus, {"load_p_mw": 0.0, "load_q_mvar": 0.0})
        net.load.at[idx, "p_mw"] = float(values["load_p_mw"]) * (1.0 - load_relief)
        net.load.at[idx, "q_mvar"] = float(values["load_q_mvar"]) * (1.0 - load_relief)

    if len(net.sgen):
        net.sgen.drop(net.sgen.index, inplace=True)
    for bus, values in load_map.items():
        pv = float(values["pv_p_mw"]) * (1.0 - pv_curtail)
        if pv > 0:
            pp.create_sgen(net, bus=int(bus), p_mw=pv, q_mvar=0.0, name=f"bench_pv_{bus}")

    try:
        pp.runpp(net, algorithm="nr", init="auto", calculate_voltage_angles=False, numba=False)
    except Exception:
        return None
    if not bool(net.converged):
        return None

    vm = net.res_bus.vm_pu.to_numpy()
    violations = (vm < LOWER_LIMIT) | (vm > UPPER_LIMIT)
    available_pv = float(group.groupby("bus")["pv_p_mw"].first().sum())
    original_load = float(group.groupby("bus")["load_p_mw"].first().sum())
    curtailed_pv = available_pv * pv_curtail
    relieved_load = original_load * load_relief
    return {
        "load_relief": load_relief,
        "pv_curtail": pv_curtail,
        "available_pv_mw": available_pv,
        "accepted_pv_mw": available_pv - curtailed_pv,
        "curtailed_pv_mw": curtailed_pv,
        "relieved_load_mw": relieved_load,
        "action_cost_proxy_mw": curtailed_pv + relieved_load,
        "violating_buses": int(violations.sum()),
        "violating_scenario": int(violations.any()),
        "min_vm_pu": float(vm.min()),
        "max_vm_pu": float(vm.max()),
    }


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    split_table = assign_random_split(scenarios, int(config["representative_seed"]))
    test_keys = split_table[split_table["split"] == "test"][["feeder", "scenario_id"]]
    test = data.merge(test_keys, on=["feeder", "scenario_id"], how="inner")

    grid = [float(value) for value in config["control_grid"]]
    selected_rows = []
    candidate_rows = []
    for (feeder, scenario_id), group in test.groupby(["feeder", "scenario_id"]):
        candidates = []
        for load_relief in grid:
            for pv_curtail in grid:
                result = run_ac_action(group, load_relief=load_relief, pv_curtail=pv_curtail)
                if result is None:
                    continue
                result.update({"feeder": feeder, "scenario_id": scenario_id})
                candidates.append(result)
                candidate_rows.append(result.copy())
        if not candidates:
            selected_rows.append(
                {
                    "feeder": feeder,
                    "scenario_id": scenario_id,
                    "converged": False,
                    "violating_buses": np.nan,
                    "violating_scenario": np.nan,
                }
            )
            continue
        best = sorted(
            candidates,
            key=lambda row: (
                row["violating_buses"],
                row["violating_scenario"],
                row["action_cost_proxy_mw"],
                row["pv_curtail"],
                row["load_relief"],
            ),
        )[0]
        best["converged"] = True
        selected_rows.append(best)

    selected = pd.DataFrame(selected_rows)
    selected.to_csv(RESULTS / "control_grid_search_selected_actions.csv", index=False)
    candidates = pd.DataFrame(candidate_rows)
    candidates.to_csv(RESULTS / "control_grid_search_candidate_actions.csv", index=False)

    converged = selected[selected["converged"] == True].copy()  # noqa: E712
    summary = {
        "method": "AC corrective grid-search benchmark",
        "role": "downstream corrective optimizer triggered after risk screening",
        "split_name": "random_interpolation",
        "seed": int(config["representative_seed"]),
        "test_scenarios": int(len(selected)),
        "converged_scenarios": int(len(converged)),
        "post_action_violating_scenarios": int(converged["violating_scenario"].sum()),
        "post_action_violating_buses": int(converged["violating_buses"].sum()),
        "post_action_scenario_violation_rate": float(converged["violating_scenario"].mean()),
        "post_action_bus_violations_per_scenario": float(converged["violating_buses"].mean()),
        "available_pv_mw": float(converged["available_pv_mw"].sum()),
        "accepted_pv_mw": float(converged["accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(converged["curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(converged["relieved_load_mw"].sum()),
        "action_cost_proxy_mw": float(converged["action_cost_proxy_mw"].sum()),
        "mean_load_relief": float(converged["load_relief"].mean()),
        "mean_pv_curtail": float(converged["pv_curtail"].mean()),
    }
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(RESULTS / "control_grid_search_summary.csv", index=False)
    (RESULTS / "control_grid_search_summary.md").write_text(
        summary_df.round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    (RESULTS / "control_grid_search_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
