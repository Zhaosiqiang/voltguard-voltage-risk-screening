"""Generate feeder scenarios for VoltGuard-CPGNN.

This is a first executable entry point, not the full experiment pipeline. It
creates reproducible AC power-flow scenarios for pandapower feeders when the
required dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def require_dependencies():
    try:
        import numpy as np
        import pandas as pd
        import pandapower as pp
        import pandapower.networks as pn
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: "
            + str(exc)
            + "\nInstall with: pip install -r VoltGuard-CPGNN/requirements.txt"
        ) from exc
    return np, pd, pp, pn


def load_network(pn, feeder: str):
    if feeder == "69":
        import pandapower as pp

        from ieee69_feeder import create_ieee69

        return create_ieee69(pp), "case69_project_local"
    candidates = {
        "33": ["case33bw", "case33"],
        "118": ["case118"],
    }[feeder]
    for name in candidates:
        if hasattr(pn, name):
            return getattr(pn, name)(), name
    available = [name for name in dir(pn) if "case" in name.lower() or "ieee" in name.lower()]
    raise SystemExit(
        f"No pandapower network found for feeder {feeder}. "
        f"Tried {candidates}. Available examples include: {available[:40]}"
    )


def attach_pv_generators(net, np, pp, penetration: float, rng):
    total_load = float(net.load.p_mw.sum()) if len(net.load) else 0.0
    target_pv = total_load * penetration
    if target_pv <= 0:
        return []

    load_buses = sorted(set(int(bus) for bus in net.load.bus.values))
    if not load_buses:
        return []
    count = max(1, min(len(load_buses), int(round(len(load_buses) * 0.25))))
    pv_buses = [int(bus) for bus in rng.choice(load_buses, size=count, replace=False)]
    per_bus = target_pv / count
    created = []
    for bus in pv_buses:
        pp.create_sgen(net, bus=bus, p_mw=per_bus, q_mvar=0.0, name=f"pv_{bus}")
        created.append(bus)
    return created


def run_scenario(np, pp, pn, feeder: str, scenario_id: int, rng):
    net, network_name = load_network(pn, feeder)
    load_scale = float(rng.uniform(0.65, 1.35))
    pv_penetration = float(rng.choice([0.2, 0.4, 0.6, 0.8]))
    ev_scale = float(rng.choice([0.0, 0.1, 0.2, 0.3]))

    if len(net.load):
        net.load["p_mw"] = net.load["p_mw"].astype(float) * load_scale
        net.load["q_mvar"] = net.load["q_mvar"].astype(float) * load_scale

        ev_count = max(1, int(round(len(net.load) * 0.15)))
        ev_rows = rng.choice(list(net.load.index), size=ev_count, replace=False)
        net.load.loc[ev_rows, "p_mw"] += ev_scale * float(net.load.p_mw.mean())

    pv_buses = attach_pv_generators(net, np, pp, pv_penetration, rng)

    try:
        pp.runpp(net, algorithm="nr", init="auto", calculate_voltage_angles=False, numba=False)
        converged = bool(net.converged)
    except Exception as exc:
        converged = False
        error = f"{type(exc).__name__}: {exc}"
    else:
        error = ""

    if not converged:
        return {
            "feeder": feeder,
            "network_name": network_name,
            "scenario_id": scenario_id,
            "converged": False,
            "load_scale": load_scale,
            "pv_penetration": pv_penetration,
            "ev_scale": ev_scale,
            "pv_buses": pv_buses,
            "error": error,
        }, []

    bus_rows = []
    load_by_bus = {int(bus): 0.0 for bus in net.bus.index}
    qload_by_bus = {int(bus): 0.0 for bus in net.bus.index}
    for _, load in net.load.iterrows():
        if bool(load.get("in_service", True)):
            bus = int(load.bus)
            load_by_bus[bus] = load_by_bus.get(bus, 0.0) + float(load.p_mw)
            qload_by_bus[bus] = qload_by_bus.get(bus, 0.0) + float(load.q_mvar)

    pv_by_bus = {int(bus): 0.0 for bus in net.bus.index}
    if len(net.sgen):
        for _, sgen in net.sgen.iterrows():
            if bool(sgen.get("in_service", True)):
                bus = int(sgen.bus)
                pv_by_bus[bus] = pv_by_bus.get(bus, 0.0) + float(sgen.p_mw)

    degree_by_bus = {int(bus): 0 for bus in net.bus.index}
    neighbors_by_bus = {int(bus): [] for bus in net.bus.index}
    for _, line in net.line.iterrows():
        if bool(line.get("in_service", True)):
            from_bus = int(line.from_bus)
            to_bus = int(line.to_bus)
            degree_by_bus[from_bus] = degree_by_bus.get(from_bus, 0) + 1
            degree_by_bus[to_bus] = degree_by_bus.get(to_bus, 0) + 1
            neighbors_by_bus.setdefault(from_bus, []).append(to_bus)
            neighbors_by_bus.setdefault(to_bus, []).append(from_bus)

    slack_buses = set(int(bus) for bus in net.ext_grid.bus.values) if len(net.ext_grid) else set()
    n_bus = max(1, len(net.bus) - 1)
    for bus, row in net.res_bus.iterrows():
        vm = float(row.vm_pu)
        bus_int = int(bus)
        neighbors = neighbors_by_bus.get(bus_int, [])
        neighbor_load = sum(load_by_bus.get(nb, 0.0) for nb in neighbors)
        neighbor_pv = sum(pv_by_bus.get(nb, 0.0) for nb in neighbors)
        neighbor_net = neighbor_load - neighbor_pv
        bus_rows.append(
            {
                "feeder": feeder,
                "scenario_id": scenario_id,
                "network_name": network_name,
                "bus": bus_int,
                "bus_norm": bus_int / n_bus,
                "vn_kv": float(net.bus.loc[bus, "vn_kv"]),
                "degree": int(degree_by_bus.get(bus_int, 0)),
                "is_slack": int(bus_int in slack_buses),
                "load_p_mw": float(load_by_bus.get(bus_int, 0.0)),
                "load_q_mvar": float(qload_by_bus.get(bus_int, 0.0)),
                "pv_p_mw": float(pv_by_bus.get(bus_int, 0.0)),
                "net_p_mw": float(load_by_bus.get(bus_int, 0.0) - pv_by_bus.get(bus_int, 0.0)),
                "neighbor_load_p_mw": float(neighbor_load),
                "neighbor_pv_p_mw": float(neighbor_pv),
                "neighbor_net_p_mw": float(neighbor_net),
                "load_scale": load_scale,
                "pv_penetration": pv_penetration,
                "ev_scale": ev_scale,
                "vm_pu": vm,
                "voltage_violation": bool(vm < 0.95 or vm > 1.05),
            }
        )

    summary = {
        "feeder": feeder,
        "network_name": network_name,
        "scenario_id": scenario_id,
        "converged": True,
        "load_scale": load_scale,
        "pv_penetration": pv_penetration,
        "ev_scale": ev_scale,
        "pv_buses": pv_buses,
        "min_vm_pu": min(row["vm_pu"] for row in bus_rows),
        "max_vm_pu": max(row["vm_pu"] for row in bus_rows),
        "violation_any": any(row["voltage_violation"] for row in bus_rows),
        "error": error,
    }
    return summary, bus_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feeders", nargs="+", default=["33", "69", "118"], choices=["33", "69", "118"])
    parser.add_argument("--scenarios", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--outdir", type=Path, default=Path("VoltGuard-CPGNN/experiments/results"))
    args = parser.parse_args(argv)

    np, pd, pp, pn = require_dependencies()
    rng = np.random.default_rng(args.seed)
    args.outdir.mkdir(parents=True, exist_ok=True)

    summaries = []
    bus_rows = []
    for feeder in args.feeders:
        for scenario_id in range(args.scenarios):
            summary, rows = run_scenario(np, pp, pn, feeder, scenario_id, rng)
            summaries.append(summary)
            bus_rows.extend(rows)

    summary_path = args.outdir / "scenario_summary.csv"
    bus_path = args.outdir / "bus_voltage_labels.csv"
    meta_path = args.outdir / "scenario_generation_meta.json"
    pd.DataFrame(summaries).to_csv(summary_path, index=False)
    pd.DataFrame(bus_rows).to_csv(bus_path, index=False)
    meta_path.write_text(
        json.dumps(
            {
                "feeders": args.feeders,
                "scenarios_per_feeder": args.scenarios,
                "seed": args.seed,
                "summary_path": str(summary_path),
                "bus_path": str(bus_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {summary_path}")
    print(f"Wrote {bus_path}")
    print(f"Wrote {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
