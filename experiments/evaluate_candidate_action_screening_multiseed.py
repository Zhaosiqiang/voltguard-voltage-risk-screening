"""Multi-seed AC candidate-action screening audit.

The representative candidate-action audit shows that VoltGuard can prune the
nine downstream load-relief/PV-curtailment candidates before AC power flow. This
script repeats the same top-three candidate pruning test over all configured
random split seeds. It reruns the AC grid search for each seed-specific test set
and reports mean, standard deviation, and confidence intervals for action
quality and avoided AC audits.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pandapower as pp

from evaluate_candidate_action_screening import (
    actual_best,
    candidate_bus_frame,
    policy_rows,
    train_voltguard,
)
from evaluate_models import (
    FEATURES,
    LOWER_LIMIT,
    UPPER_LIMIT,
    assign_random_split,
    conformal_by_group,
    load_config,
    load_network,
    prepare_data,
    scenario_table,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
POLICIES = ["VoltGuard interval-risk", "LinDistFlow point-risk", "Cheapest-first"]
TOP_K = 3
METRIC_COLS = [
    "test_scenarios",
    "candidate_grid_size",
    "candidate_ac_audits",
    "candidate_ac_audits_avoided",
    "audit_reduction_ratio",
    "full_best_in_subset_rate",
    "same_action_as_full_rate",
    "post_action_violating_scenarios",
    "full_post_action_violating_scenarios",
    "extra_violating_scenarios_vs_full",
    "post_action_violating_buses",
    "full_post_action_violating_buses",
    "extra_violating_buses_vs_full",
    "action_cost_proxy_mw",
    "full_action_cost_proxy_mw",
    "action_cost_delta_vs_full_mw",
    "accepted_pv_mw",
    "curtailed_pv_mw",
    "relieved_load_mw",
]


def run_ac_action_on_net(net, group: pd.DataFrame, load_relief: float, pv_curtail: float):
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
            pp.create_sgen(net, bus=int(bus), p_mw=pv, q_mvar=0.0, name=f"multiseed_pv_{bus}")

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


def ac_candidates_for_test(test: pd.DataFrame, grid: list[float]) -> pd.DataFrame:
    import pandapower.networks as pn

    rows = []
    for (feeder, scenario_id), group in test.groupby(["feeder", "scenario_id"]):
        net = load_network(pn, str(feeder))
        for load_relief in grid:
            for pv_curtail in grid:
                result = run_ac_action_on_net(
                    net,
                    group,
                    load_relief=float(load_relief),
                    pv_curtail=float(pv_curtail),
                )
                if result is None:
                    continue
                result.update({"feeder": str(feeder), "scenario_id": int(scenario_id)})
                rows.append(result)
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("No AC candidate actions converged")
    for col in ["load_relief", "pv_curtail"]:
        out[col] = out[col].astype(float).round(10)
    return out


def candidate_scores(
    data: pd.DataFrame,
    train: pd.DataFrame,
    calib: pd.DataFrame,
    test: pd.DataFrame,
    config: dict,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    bus_candidates = candidate_bus_frame(test, config, data)
    model, pred_calib = train_voltguard(train, calib, seed)
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
    raw = bus_candidates[["feeder", "scenario_id", "bus", "load_relief", "pv_curtail"]].copy()
    raw["seed"] = seed
    raw["pred_vm_pu"] = pred
    raw["lower"] = lower
    raw["upper"] = upper
    raw["width"] = upper - lower
    raw["pred_risk_bus"] = (raw["lower"] < LOWER_LIMIT) | (raw["upper"] > UPPER_LIMIT)
    raw["pred_interval_severity"] = np.maximum(
        np.maximum(0.0, LOWER_LIMIT - raw["lower"]),
        np.maximum(0.0, raw["upper"] - UPPER_LIMIT),
    )
    raw = raw.merge(
        bus_candidates[["feeder", "scenario_id", "bus", "load_relief", "pv_curtail", "ldf_vm_pu"]],
        on=["feeder", "scenario_id", "bus", "load_relief", "pv_curtail"],
        how="left",
    )
    raw["ldf_point_severity"] = np.maximum(
        np.maximum(0.0, LOWER_LIMIT - raw["ldf_vm_pu"]),
        np.maximum(0.0, raw["ldf_vm_pu"] - UPPER_LIMIT),
    )
    scores = (
        raw.groupby(["seed", "feeder", "scenario_id", "load_relief", "pv_curtail"], dropna=False)
        .agg(
            predicted_risk_buses=("pred_risk_bus", "sum"),
            predicted_interval_severity=("pred_interval_severity", "max"),
            predicted_mean_width=("width", "mean"),
            ldf_point_severity=("ldf_point_severity", "max"),
        )
        .reset_index()
    )
    return raw, scores


def aggregate(raw_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (policy, top_k), group in raw_metrics.groupby(["policy", "top_k_candidates"], dropna=False):
        row = {"policy": policy, "top_k_candidates": int(top_k), "runs": int(len(group))}
        for col in METRIC_COLS:
            values = group[col].astype(float)
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_mean"] = mean
            row[f"{col}_std"] = std
            row[f"{col}_ci95"] = float(1.96 * std / np.sqrt(max(1, len(values))))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["policy", "top_k_candidates"]).reset_index(drop=True)


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    grid = [float(value) for value in config["control_grid"]]
    grid_size = len(grid) ** 2

    all_ac_candidates = []
    all_scores = []
    all_raw_predictions = []
    rows = []
    for seed in config["evaluation_seeds"]:
        seed = int(seed)
        print(f"candidate-action multiseed audit: seed={seed}", flush=True)
        split_table = assign_random_split(scenarios, seed)
        frame = data.merge(split_table, on=["feeder", "scenario_id"], how="inner")
        train = frame[frame["split"] == "train"].copy()
        calib = frame[frame["split"] == "calib"].copy()
        test = frame[frame["split"] == "test"].copy()

        ac_candidates = ac_candidates_for_test(test, grid)
        ac_candidates["seed"] = seed
        raw_pred, scores = candidate_scores(data, train, calib, test, config, seed)
        scores["seed"] = seed
        candidates = ac_candidates.merge(
            scores,
            on=["seed", "feeder", "scenario_id", "load_relief", "pv_curtail"],
            how="inner",
        )
        if len(candidates) != len(ac_candidates):
            raise RuntimeError(f"Seed {seed}: candidate-score merge lost rows")

        full = actual_best(candidates)
        full_row = policy_rows(candidates, full, "Full AC grid search", grid_size, grid_size)
        full_row["seed"] = seed
        rows.append(full_row)
        for policy in POLICIES:
            row = policy_rows(candidates, full, policy, TOP_K, grid_size)
            row["seed"] = seed
            rows.append(row)

        all_ac_candidates.append(ac_candidates)
        all_scores.append(scores)
        all_raw_predictions.append(raw_pred)

    raw_metrics = pd.DataFrame(rows)
    metrics = aggregate(raw_metrics)
    ac_table = pd.concat(all_ac_candidates, ignore_index=True)
    score_table = pd.concat(all_scores, ignore_index=True)
    raw_prediction_table = pd.concat(all_raw_predictions, ignore_index=True)

    raw_metrics.to_csv(RESULTS / "candidate_action_screening_multiseed_raw.csv", index=False)
    metrics.to_csv(RESULTS / "candidate_action_screening_multiseed_metrics.csv", index=False)
    ac_table.to_csv(RESULTS / "candidate_action_screening_multiseed_ac_candidates.csv", index=False)
    score_table.to_csv(RESULTS / "candidate_action_screening_multiseed_scores.csv", index=False)
    raw_prediction_table.to_csv(RESULTS / "candidate_action_screening_multiseed_raw_predictions.csv", index=False)

    display_cols = [
        "policy",
        "top_k_candidates",
        "candidate_ac_audits_mean",
        "candidate_ac_audits_avoided_mean",
        "full_best_in_subset_rate_mean",
        "same_action_as_full_rate_mean",
        "post_action_violating_scenarios_mean",
        "extra_violating_scenarios_vs_full_mean",
        "post_action_violating_buses_mean",
        "extra_violating_buses_vs_full_mean",
        "action_cost_delta_vs_full_mw_mean",
    ]
    (RESULTS / "candidate_action_screening_multiseed_metrics.md").write_text(
        metrics[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = metrics[metrics["policy"] == "VoltGuard interval-risk"].iloc[0]
    ldf = metrics[metrics["policy"] == "LinDistFlow point-risk"].iloc[0]
    cheapest = metrics[metrics["policy"] == "Cheapest-first"].iloc[0]
    summary = {
        "rows": int(len(metrics)),
        "raw_rows": int(len(raw_metrics)),
        "seeds": [int(seed) for seed in config["evaluation_seeds"]],
        "test_scenarios_per_seed": int(primary["test_scenarios_mean"]),
        "candidate_grid_size": int(grid_size),
        "top_k": TOP_K,
        "primary_policy": "VoltGuard interval-risk",
        "primary_candidate_ac_audits_mean": float(primary["candidate_ac_audits_mean"]),
        "primary_candidate_ac_audits_avoided_mean": float(primary["candidate_ac_audits_avoided_mean"]),
        "primary_audit_reduction_ratio_mean": float(primary["audit_reduction_ratio_mean"]),
        "primary_full_best_in_subset_rate_mean": float(primary["full_best_in_subset_rate_mean"]),
        "primary_extra_violating_scenarios_vs_full_mean": float(
            primary["extra_violating_scenarios_vs_full_mean"]
        ),
        "primary_extra_violating_buses_vs_full_mean": float(primary["extra_violating_buses_vs_full_mean"]),
        "primary_action_cost_delta_vs_full_mw_mean": float(primary["action_cost_delta_vs_full_mw_mean"]),
        "ldf_extra_violating_scenarios_vs_full_mean": float(ldf["extra_violating_scenarios_vs_full_mean"]),
        "cheapest_extra_violating_scenarios_vs_full_mean": float(
            cheapest["extra_violating_scenarios_vs_full_mean"]
        ),
        "ac_candidate_rows": int(len(ac_table)),
        "score_rows": int(len(score_table)),
        "raw_prediction_rows": int(len(raw_prediction_table)),
    }
    (RESULTS / "candidate_action_screening_multiseed_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
