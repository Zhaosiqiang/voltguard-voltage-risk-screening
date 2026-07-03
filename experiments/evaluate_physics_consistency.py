"""Audit branch-level voltage-drop consistency for representative predictions.

The audit uses only the saved representative random-split predictions and
pre-dispatch scenario features. It does not train models or use test labels
except as the AC-reference comparison row.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import load_network


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"
RAW_PATH = RESULTS / "raw_predictions_random_seed7.csv"
LABEL_PATH = RESULTS / "bus_voltage_labels.csv"
LOWER_LIMIT = 0.95
UPPER_LIMIT = 1.05


def format_markdown(df: pd.DataFrame, path: Path, digits: int = 6) -> None:
    path.write_text(df.round(digits).to_markdown(index=False) + "\n", encoding="utf-8")


def feeder_branches(feeder: str) -> tuple[list[dict], float]:
    import pandapower.networks as pn

    net = load_network(pn, feeder)
    slack_bus = int(net.ext_grid.bus.iloc[0]) if len(net.ext_grid) else int(net.bus.index.min())
    sn_mva = float(net.sn_mva)

    neighbors: dict[int, list[tuple[int, float, float]]] = {int(bus): [] for bus in net.bus.index}
    for _, line in net.line.iterrows():
        if not bool(line.get("in_service", True)):
            continue
        from_bus = int(line.from_bus)
        to_bus = int(line.to_bus)
        length = float(line.length_km)
        r_ohm = float(line.r_ohm_per_km) * length
        x_ohm = float(line.x_ohm_per_km) * length
        base_kv = float(net.bus.loc[from_bus, "vn_kv"])
        z_base = base_kv * base_kv / sn_mva
        r_pu = r_ohm / z_base
        x_pu = x_ohm / z_base
        neighbors.setdefault(from_bus, []).append((to_bus, r_pu, x_pu))
        neighbors.setdefault(to_bus, []).append((from_bus, r_pu, x_pu))

    parent = {slack_bus: None}
    queue: deque[int] = deque([slack_bus])
    branches = []
    while queue:
        bus = queue.popleft()
        for nb, r_pu, x_pu in neighbors.get(bus, []):
            if nb in parent:
                continue
            parent[nb] = bus
            queue.append(nb)
            branches.append({"from_bus": bus, "to_bus": nb, "r_pu": r_pu, "x_pu": x_pu})
    return branches, sn_mva


def downstream_sets(branches: list[dict], buses: list[int]) -> dict[int, set[int]]:
    children: dict[int, list[int]] = {bus: [] for bus in buses}
    for branch in branches:
        children.setdefault(int(branch["from_bus"]), []).append(int(branch["to_bus"]))

    cache: dict[int, set[int]] = {}

    def collect(bus: int) -> set[int]:
        if bus in cache:
            return cache[bus]
        found = {bus}
        for child in children.get(bus, []):
            found |= collect(child)
        cache[bus] = found
        return found

    for bus in buses:
        collect(bus)
    return cache


def branch_residual_rows(frame: pd.DataFrame, pred_col: str, label: str, variant: str) -> list[dict]:
    rows = []
    for feeder, feeder_frame in frame.groupby("feeder"):
        branches, sn_mva = feeder_branches(str(feeder))
        buses = sorted(int(bus) for bus in feeder_frame["bus"].unique())
        downstream = downstream_sets(branches, buses)
        for scenario_id, scenario in feeder_frame.groupby("scenario_id"):
            scenario = scenario.set_index("bus")
            severity = np.maximum(LOWER_LIMIT - scenario["vm_pu"].to_numpy(), 0.0).sum()
            severity += np.maximum(scenario["vm_pu"].to_numpy() - UPPER_LIMIT, 0.0).sum()
            branch_values = []
            for branch in branches:
                i = int(branch["from_bus"])
                j = int(branch["to_bus"])
                subtree = list(downstream[j])
                p_pu = float(scenario.loc[subtree, "net_p_mw"].sum() / sn_mva)
                q_pu = float(scenario.loc[subtree, "load_q_mvar"].sum() / sn_mva)
                u_i = float(scenario.loc[i, pred_col] ** 2)
                u_j = float(scenario.loc[j, pred_col] ** 2)
                residual = u_j - u_i + 2.0 * (float(branch["r_pu"]) * p_pu + float(branch["x_pu"]) * q_pu)
                branch_values.append(residual)
            branch_array = np.asarray(branch_values, dtype=float)
            rows.append(
                {
                    "method": label,
                    "variant": variant,
                    "feeder": str(feeder),
                    "scenario_id": int(scenario_id),
                    "branch_count": int(len(branch_array)),
                    "drop_rmse": float(np.sqrt(np.mean(branch_array**2))),
                    "drop_mae": float(np.mean(np.abs(branch_array))),
                    "drop_max_abs": float(np.max(np.abs(branch_array))),
                    "scenario_violation_any": bool(scenario["voltage_violation"].max()),
                    "realized_severity": float(severity),
                }
            )
    return rows


def main() -> int:
    raw = pd.read_csv(RAW_PATH)
    labels = pd.read_csv(LABEL_PATH)
    raw["feeder"] = raw["feeder"].astype(str)
    labels["feeder"] = labels["feeder"].astype(str)

    test_keys = raw[["feeder", "scenario_id", "bus"]].drop_duplicates()
    feature_cols = [
        "feeder",
        "scenario_id",
        "bus",
        "load_q_mvar",
        "net_p_mw",
    ]
    feature_frame = test_keys.merge(labels[feature_cols], on=["feeder", "scenario_id", "bus"], how="left")

    audit_frames = []
    ac = raw[["feeder", "scenario_id", "bus", "vm_pu", "voltage_violation"]].drop_duplicates().merge(
        feature_frame, on=["feeder", "scenario_id", "bus"], how="left"
    )
    ac["prediction"] = ac["vm_pu"]
    audit_frames.extend(branch_residual_rows(ac, "prediction", "AC power-flow label", "reference"))

    selected = [
        ("LinDistFlow physical backbone", "none"),
        ("Boosting point + global conformal", "global"),
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned"),
        ("Neural graph residual ablation", "topology_conditioned"),
    ]
    for method, variant in selected:
        subset = raw[(raw["method"] == method) & (raw["conformal_variant"] == variant)].copy()
        if subset.empty:
            continue
        subset = subset.merge(feature_frame, on=["feeder", "scenario_id", "bus"], how="left")
        subset["prediction"] = subset["y_pred"]
        audit_frames.extend(branch_residual_rows(subset, "prediction", method, variant))

    scenario_audit = pd.DataFrame(audit_frames)
    summary = (
        scenario_audit.groupby(["method", "variant"], dropna=False)
        .agg(
            scenarios=("scenario_id", "count"),
            drop_rmse_mean=("drop_rmse", "mean"),
            drop_rmse_std=("drop_rmse", "std"),
            drop_mae_mean=("drop_mae", "mean"),
            drop_max_abs_p95=("drop_max_abs", lambda values: float(np.quantile(values, 0.95))),
            violating_scenario_drop_rmse=("drop_rmse", lambda values: float(values.mean())),
        )
        .reset_index()
    )
    violating = scenario_audit[scenario_audit["scenario_violation_any"]]
    if not violating.empty:
        vio_summary = (
            violating.groupby(["method", "variant"], dropna=False)["drop_rmse"]
            .mean()
            .rename("violating_only_drop_rmse")
            .reset_index()
        )
        summary = summary.drop(columns=["violating_scenario_drop_rmse"]).merge(
            vio_summary, on=["method", "variant"], how="left"
        )

    ac_rmse = float(
        summary.loc[summary["method"] == "AC power-flow label", "drop_rmse_mean"].iloc[0]
    )
    vg_rmse = float(
        summary.loc[summary["method"] == "VoltGuard topology-aware residual", "drop_rmse_mean"].iloc[0]
    )
    boost_rmse = float(
        summary.loc[summary["method"] == "Boosting point + global conformal", "drop_rmse_mean"].iloc[0]
    )
    out_summary = {
        "rows": int(len(summary)),
        "scenario_rows": int(len(scenario_audit)),
        "ac_label_drop_rmse_mean": ac_rmse,
        "voltguard_drop_rmse_mean": vg_rmse,
        "boosting_drop_rmse_mean": boost_rmse,
        "voltguard_vs_boosting_drop_rmse_delta": vg_rmse - boost_rmse,
        "interpretation": (
            "The audit measures LinDistFlow branch-drop consistency of saved predictions; "
            "the AC-label row is not zero because the proxy ignores losses and full AC effects."
        ),
    }

    scenario_audit.to_csv(RESULTS / "physics_consistency_audit_raw.csv", index=False)
    summary.to_csv(RESULTS / "physics_consistency_audit.csv", index=False)
    format_markdown(summary, RESULTS / "physics_consistency_audit.md")
    (RESULTS / "physics_consistency_summary.json").write_text(
        json.dumps(out_summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(out_summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
