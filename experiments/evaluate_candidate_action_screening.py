"""Candidate-action screening audit for downstream corrective search.

The main paper positions VoltGuard as a front end for AC-audited corrective
optimization. This audit moves one step closer to that interface: for each
test scenario, the downstream grid search has nine load-relief/PV-curtailment
candidate actions. VoltGuard ranks those candidate actions from forecast
features and conformal intervals before AC power flow is run. We then ask how
many candidate AC audits can be skipped while retaining the full grid-search
action quality.

This is an operating-value audit, not a conformal feasibility certificate for
post-action candidates.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor

from evaluate_models import (
    FEATURES,
    LOWER_LIMIT,
    UPPER_LIMIT,
    add_lindistflow_backbone,
    assign_random_split,
    conformal_by_group,
    load_config,
    load_network,
    prepare_data,
    scenario_table,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
ACTION_K = [1, 2, 3, 5, 9]


def feeder_neighbors(feeder: str) -> dict[int, list[int]]:
    import pandapower.networks as pn

    net = load_network(pn, feeder)
    neighbors: dict[int, list[int]] = {int(bus): [] for bus in net.bus.index}
    for _, line in net.line.iterrows():
        if not bool(line.get("in_service", True)):
            continue
        i = int(line.from_bus)
        j = int(line.to_bus)
        neighbors.setdefault(i, []).append(j)
        neighbors.setdefault(j, []).append(i)
    return neighbors


def refresh_neighbor_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in ["neighbor_load_p_mw", "neighbor_pv_p_mw", "neighbor_net_p_mw"]:
        out[col] = 0.0
    for feeder, feeder_frame in out.groupby("feeder"):
        neighbors = feeder_neighbors(str(feeder))
        for _, group in feeder_frame.groupby(["scenario_id", "load_relief", "pv_curtail"], dropna=False):
            by_bus = group.set_index("bus")
            for idx, row in group.iterrows():
                nbs = [bus for bus in neighbors.get(int(row["bus"]), []) if bus in by_bus.index]
                if not nbs:
                    continue
                out.at[idx, "neighbor_load_p_mw"] = float(by_bus.loc[nbs, "load_p_mw"].sum())
                out.at[idx, "neighbor_pv_p_mw"] = float(by_bus.loc[nbs, "pv_p_mw"].sum())
                out.at[idx, "neighbor_net_p_mw"] = float(by_bus.loc[nbs, "net_p_mw"].sum())
    return out


def candidate_bus_frame(test: pd.DataFrame, config: dict, data: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for action_index, (load_relief, pv_curtail) in enumerate(
        (lr, pc) for lr in config["control_grid"] for pc in config["control_grid"]
    ):
        cand = test.copy()
        cand["load_relief"] = float(load_relief)
        cand["pv_curtail"] = float(pv_curtail)
        cand["action_index"] = int(action_index)
        cand["load_p_mw"] = cand["load_p_mw"] * (1.0 - float(load_relief))
        cand["load_q_mvar"] = cand["load_q_mvar"] * (1.0 - float(load_relief))
        cand["pv_p_mw"] = cand["pv_p_mw"] * (1.0 - float(pv_curtail))
        cand["net_p_mw"] = cand["load_p_mw"] - cand["pv_p_mw"]
        cand["load_scale"] = cand["load_scale"] * (1.0 - float(load_relief))
        cand["pv_penetration"] = cand["pv_penetration"] * (1.0 - float(pv_curtail))
        pieces.append(cand)
    out = pd.concat(pieces, ignore_index=True)
    out = refresh_neighbor_features(out)
    out["original_scenario_id"] = out["scenario_id"].astype(int)
    out["scenario_id"] = out["original_scenario_id"] * 100 + out["action_index"].astype(int)
    out = add_lindistflow_backbone(out)
    out["scenario_id"] = out["original_scenario_id"]
    out = out.drop(columns=["original_scenario_id"])
    feeder_categories = sorted(data["feeder"].unique(), key=lambda value: int(value))
    out["feeder_code"] = pd.Categorical(out["feeder"], categories=feeder_categories).codes
    out["pv_bin"] = out["pv_penetration"].round(2).astype(str)
    median_load = float(data["load_scale"].median())
    out["load_bin"] = np.where(out["load_scale"] >= median_load, "high_load", "low_load")
    return out


def train_voltguard(train: pd.DataFrame, calib: pd.DataFrame, seed: int):
    feature_cols = FEATURES + ["feeder_code"]
    x_train = train[feature_cols].to_numpy()
    residual_train = train["vm_pu"].to_numpy() - train["ldf_vm_pu"].to_numpy()
    model = ExtraTreesRegressor(n_estimators=200, random_state=seed + 100, min_samples_leaf=3, n_jobs=-1)
    model.fit(x_train, residual_train)
    pred_calib = calib["ldf_vm_pu"].to_numpy() + model.predict(calib[feature_cols].to_numpy())
    return model, pred_calib


def actual_best(candidates: pd.DataFrame) -> pd.DataFrame:
    ordered = candidates.sort_values(
        ["feeder", "scenario_id", "violating_buses", "violating_scenario", "action_cost_proxy_mw", "pv_curtail", "load_relief"],
        ascending=[True, True, True, True, True, True, True],
    )
    return ordered.groupby(["feeder", "scenario_id"], dropna=False).head(1).copy()


def choose_subset(group: pd.DataFrame, policy: str, k: int) -> pd.DataFrame:
    if policy == "VoltGuard interval-risk":
        sort_cols = ["predicted_risk_buses", "predicted_interval_severity", "predicted_mean_width", "action_cost_proxy_mw"]
    elif policy == "LinDistFlow point-risk":
        sort_cols = ["ldf_point_severity", "action_cost_proxy_mw"]
    elif policy == "Cheapest-first":
        sort_cols = ["action_cost_proxy_mw", "pv_curtail", "load_relief"]
    else:
        raise ValueError(policy)
    return group.sort_values(sort_cols, ascending=True).head(k)


def choose_actual_from_subset(subset: pd.DataFrame) -> pd.Series:
    return subset.sort_values(
        ["violating_buses", "violating_scenario", "action_cost_proxy_mw", "pv_curtail", "load_relief"],
        ascending=[True, True, True, True, True],
    ).iloc[0]


def policy_rows(candidates: pd.DataFrame, full_best: pd.DataFrame, policy: str, k: int, grid_size: int) -> dict:
    chosen = []
    full_key = full_best.set_index(["feeder", "scenario_id"])[["load_relief", "pv_curtail", "violating_buses", "violating_scenario", "action_cost_proxy_mw"]]
    full_in_subset = []
    for (feeder, scenario_id), group in candidates.groupby(["feeder", "scenario_id"], dropna=False):
        if k >= grid_size:
            subset = group
        elif policy == "Full AC grid search":
            subset = group
        else:
            subset = choose_subset(group, policy, k)
        full = full_key.loc[(feeder, scenario_id)]
        full_in_subset.append(
            bool(((subset["load_relief"] == full["load_relief"]) & (subset["pv_curtail"] == full["pv_curtail"])).any())
        )
        row = choose_actual_from_subset(subset)
        chosen.append(row)
    table = pd.DataFrame(chosen)
    merged = table.merge(
        full_best[["feeder", "scenario_id", "load_relief", "pv_curtail", "violating_buses", "violating_scenario", "action_cost_proxy_mw"]].rename(
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
    return {
        "policy": policy,
        "top_k_candidates": int(k),
        "test_scenarios": int(scenarios),
        "candidate_grid_size": int(grid_size),
        "candidate_ac_audits": int(scenarios * min(k, grid_size)),
        "candidate_ac_audits_avoided": int(scenarios * max(0, grid_size - min(k, grid_size))),
        "audit_reduction_ratio": float(max(0, grid_size - min(k, grid_size)) / grid_size),
        "full_best_in_subset_rate": float(np.mean(full_in_subset)),
        "same_action_as_full_rate": float(same_action.mean()),
        "post_action_violating_scenarios": int(merged["violating_scenario"].sum()),
        "full_post_action_violating_scenarios": int(merged["full_violating_scenario"].sum()),
        "extra_violating_scenarios_vs_full": int(merged["violating_scenario"].sum() - merged["full_violating_scenario"].sum()),
        "post_action_violating_buses": int(merged["violating_buses"].sum()),
        "full_post_action_violating_buses": int(merged["full_violating_buses"].sum()),
        "extra_violating_buses_vs_full": int(merged["violating_buses"].sum() - merged["full_violating_buses"].sum()),
        "action_cost_proxy_mw": float(merged["action_cost_proxy_mw"].sum()),
        "full_action_cost_proxy_mw": float(merged["full_action_cost_proxy_mw"].sum()),
        "action_cost_delta_vs_full_mw": float(merged["action_cost_proxy_mw"].sum() - merged["full_action_cost_proxy_mw"].sum()),
        "accepted_pv_mw": float(merged["accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(merged["curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(merged["relieved_load_mw"].sum()),
    }


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    split_table = assign_random_split(scenarios, int(config["representative_seed"]))
    frame = data.merge(split_table, on=["feeder", "scenario_id"], how="inner")
    train = frame[frame["split"] == "train"].copy()
    calib = frame[frame["split"] == "calib"].copy()
    test = frame[frame["split"] == "test"].copy()

    ac_candidates = pd.read_csv(RESULTS / "control_grid_search_candidate_actions.csv")
    ac_candidates["feeder"] = ac_candidates["feeder"].astype(str)
    for col in ["load_relief", "pv_curtail"]:
        ac_candidates[col] = ac_candidates[col].astype(float).round(10)
    bus_candidates = candidate_bus_frame(test, config, data)
    model, pred_calib = train_voltguard(train, calib, int(config["representative_seed"]))
    feature_cols = FEATURES + ["feeder_code"]
    pred = bus_candidates["ldf_vm_pu"].to_numpy() + model.predict(bus_candidates[feature_cols].to_numpy())
    lower, upper, _, _ = conformal_by_group(
        calib,
        bus_candidates,
        pred_calib,
        pred,
        ["feeder", "pv_bin", "load_bin"],
        alpha=float(config["primary_alpha"]),
        min_group=int(config["min_group_samples"]),
        shrinkage=True,
    )
    raw_pred = bus_candidates[["feeder", "scenario_id", "bus", "load_relief", "pv_curtail"]].copy()
    raw_pred["pred_vm_pu"] = pred
    raw_pred["lower"] = lower
    raw_pred["upper"] = upper
    raw_pred["width"] = upper - lower
    raw_pred.to_csv(RESULTS / "candidate_action_screening_raw_predictions.csv", index=False)
    raw_pred["pred_risk_bus"] = (raw_pred["lower"] < LOWER_LIMIT) | (raw_pred["upper"] > UPPER_LIMIT)
    raw_pred["pred_interval_severity"] = np.maximum(
        np.maximum(0.0, LOWER_LIMIT - raw_pred["lower"]),
        np.maximum(0.0, raw_pred["upper"] - UPPER_LIMIT),
    )
    raw_pred = raw_pred.merge(
        bus_candidates[["feeder", "scenario_id", "bus", "load_relief", "pv_curtail", "ldf_vm_pu"]],
        on=["feeder", "scenario_id", "bus", "load_relief", "pv_curtail"],
        how="left",
    )
    raw_pred["ldf_point_severity"] = np.maximum(
        np.maximum(0.0, LOWER_LIMIT - raw_pred["ldf_vm_pu"]),
        np.maximum(0.0, raw_pred["ldf_vm_pu"] - UPPER_LIMIT),
    )
    scores = (
        raw_pred.groupby(["feeder", "scenario_id", "load_relief", "pv_curtail"], dropna=False)
        .agg(
            predicted_risk_buses=("pred_risk_bus", "sum"),
            predicted_interval_severity=("pred_interval_severity", "max"),
            predicted_mean_width=("width", "mean"),
            ldf_point_severity=("ldf_point_severity", "max"),
        )
        .reset_index()
    )
    scores.to_csv(RESULTS / "candidate_action_screening_scores.csv", index=False)

    candidates = ac_candidates.merge(scores, on=["feeder", "scenario_id", "load_relief", "pv_curtail"], how="inner")
    grid_size = len(config["control_grid"]) ** 2
    full = actual_best(candidates)
    rows = [policy_rows(candidates, full, "Full AC grid search", grid_size, grid_size)]
    for policy in ["VoltGuard interval-risk", "LinDistFlow point-risk", "Cheapest-first"]:
        for k in ACTION_K:
            if k >= grid_size and policy != "VoltGuard interval-risk":
                continue
            rows.append(policy_rows(candidates, full, policy, k, grid_size))
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "candidate_action_screening_metrics.csv", index=False)
    display_cols = [
        "policy",
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
    (RESULTS / "candidate_action_screening_metrics.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    primary = table[(table["policy"] == "VoltGuard interval-risk") & (table["top_k_candidates"] == 3)].iloc[0]
    summary = {
        "rows": int(len(table)),
        "test_scenarios": int(primary["test_scenarios"]),
        "candidate_grid_size": int(grid_size),
        "primary_policy": "VoltGuard interval-risk",
        "primary_top_k": 3,
        "primary_candidate_ac_audits": int(primary["candidate_ac_audits"]),
        "primary_candidate_ac_audits_avoided": int(primary["candidate_ac_audits_avoided"]),
        "primary_audit_reduction_ratio": float(primary["audit_reduction_ratio"]),
        "primary_full_best_in_subset_rate": float(primary["full_best_in_subset_rate"]),
        "primary_extra_violating_scenarios_vs_full": int(primary["extra_violating_scenarios_vs_full"]),
        "primary_extra_violating_buses_vs_full": int(primary["extra_violating_buses_vs_full"]),
        "primary_action_cost_delta_vs_full_mw": float(primary["action_cost_delta_vs_full_mw"]),
    }
    (RESULTS / "candidate_action_screening_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
