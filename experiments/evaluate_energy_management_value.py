"""Energy-management value metrics for the ECM:X framing.

The table translates calibrated intervals into screening-layer quantities:
how many scenarios avoid downstream AC optimization, how many risky scenarios
are captured, and how much proxy PV/load action would be triggered at different
conformal risk levels. It does not claim VoltGuard replaces OPF/MPC.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from evaluate_models import (
    LOWER_LIMIT,
    UPPER_LIMIT,
    assign_random_split,
    conformal_by_group,
    fit_predictions,
    load_config,
    prepare_data,
    scenario_table,
    screening_metrics,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")


def scenario_energy_metrics(test: pd.DataFrame, lower, upper, y_pred, method: str, variant: str, alpha: float):
    risk = (lower < LOWER_LIMIT) | (upper > UPPER_LIMIT)
    under = lower < LOWER_LIMIT
    over = upper > UPPER_LIMIT
    tmp = test[
        ["feeder", "scenario_id", "bus", "vm_pu", "voltage_violation", "pv_p_mw", "load_p_mw"]
    ].copy()
    tmp["risk"] = risk
    tmp["under_risk"] = under
    tmp["over_risk"] = over
    tmp["width"] = upper - lower
    scenario = (
        tmp.groupby(["feeder", "scenario_id"])
        .agg(
            risky=("voltage_violation", "max"),
            risk_flag=("risk", "max"),
            under_risk=("under_risk", "max"),
            over_risk=("over_risk", "max"),
            available_pv_mw=("pv_p_mw", "sum"),
            load_mw=("load_p_mw", "sum"),
            mean_width=("width", "mean"),
        )
        .reset_index()
    )
    risky_count = int(scenario["risky"].sum())
    screened_safe = int((~scenario["risk_flag"].astype(bool)).sum())
    missed = int((scenario["risky"].astype(bool) & ~scenario["risk_flag"].astype(bool)).sum())
    scenario["curtailed_pv_proxy_mw"] = scenario["available_pv_mw"] * scenario["over_risk"] * 0.10
    scenario["accepted_pv_proxy_mw"] = scenario["available_pv_mw"] - scenario["curtailed_pv_proxy_mw"]
    scenario["relieved_load_proxy_mw"] = scenario["load_mw"] * scenario["under_risk"] * 0.10
    bus_metrics = screening_metrics(test["vm_pu"].to_numpy(), risk)
    return {
        "method": method,
        "variant": variant,
        "alpha": alpha,
        "nominal_coverage": 1.0 - alpha,
        "test_scenarios": int(len(scenario)),
        "risky_scenarios": risky_count,
        "screened_safe_scenarios": screened_safe,
        "screened_safe_ratio": screened_safe / max(1, len(scenario)),
        "ac_optimization_calls_avoided": screened_safe,
        "flagged_for_ac_optimization": int(scenario["risk_flag"].sum()),
        "risky_scenario_recall": (risky_count - missed) / max(1, risky_count),
        "post_screening_violation_miss_rate": missed / max(1, risky_count),
        "missed_risky_scenarios": missed,
        "bus_violation_recall": bus_metrics["recall"],
        "bus_false_alarm_rate": bus_metrics["false_alarm_rate"],
        "missed_bus_violations": bus_metrics["missed_violations"],
        "mean_interval_width": float(scenario["mean_width"].mean()),
        "available_pv_mw": float(scenario["available_pv_mw"].sum()),
        "accepted_pv_proxy_mw": float(scenario["accepted_pv_proxy_mw"].sum()),
        "curtailed_pv_proxy_mw": float(scenario["curtailed_pv_proxy_mw"].sum()),
        "relieved_load_proxy_mw": float(scenario["relieved_load_proxy_mw"].sum()),
        "proxy_action_cost_mw": float(
            scenario["curtailed_pv_proxy_mw"].sum() + scenario["relieved_load_proxy_mw"].sum()
        ),
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
    preds = fit_predictions(train, calib, test, int(config["representative_seed"]))

    rows = []
    for alpha in config["alpha_grid"]:
        for method, variant, group_cols in [
            ("Boosting point + global conformal", "global", []),
            ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
        ]:
            pred = preds[method]
            lower, upper, _, _ = conformal_by_group(
                calib,
                test,
                pred.pred_calib,
                pred.pred_test,
                group_cols,
                alpha=float(alpha),
                min_group=int(config["min_group_samples"]),
                shrinkage=True,
            )
            rows.append(scenario_energy_metrics(test, lower, upper, pred.pred_test, method, variant, float(alpha)))

    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "energy_management_value_metrics.csv", index=False)
    (RESULTS / "energy_management_value_metrics.md").write_text(
        table.round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        "rows": int(len(table)),
        "methods": sorted(table["method"].unique()),
        "alphas": [float(value) for value in config["alpha_grid"]],
    }
    (RESULTS / "energy_management_value_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
