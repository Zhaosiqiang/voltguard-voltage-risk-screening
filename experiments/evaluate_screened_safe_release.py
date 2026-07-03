"""Audit reliability of scenarios released by the VoltGuard screen.

This experiment complements the AC-call avoidance tables. It asks whether the
scenarios *not* sent to downstream AC optimization are actually safe, and how
large the residual violation severity is when a screening method releases a
risky scenario. The unit of analysis is a scenario, not a bus row.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
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
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")


def scenario_truth(test: pd.DataFrame) -> pd.DataFrame:
    tmp = test[
        ["feeder", "scenario_id", "bus", "vm_pu", "voltage_violation", "pv_p_mw", "load_p_mw"]
    ].copy()
    tmp["under_margin"] = np.maximum(0.0, LOWER_LIMIT - tmp["vm_pu"])
    tmp["over_margin"] = np.maximum(0.0, tmp["vm_pu"] - UPPER_LIMIT)
    tmp["bus_severity"] = tmp[["under_margin", "over_margin"]].max(axis=1)
    return (
        tmp.groupby(["feeder", "scenario_id"])
        .agg(
            actual_risky=("voltage_violation", "max"),
            actual_violating_buses=("voltage_violation", "sum"),
            actual_severity=("bus_severity", "max"),
            total_bus_severity=("bus_severity", "sum"),
            available_pv_mw=("pv_p_mw", "sum"),
            load_mw=("load_p_mw", "sum"),
            min_vm_pu=("vm_pu", "min"),
            max_vm_pu=("vm_pu", "max"),
        )
        .reset_index()
    )


def release_metrics(
    test: pd.DataFrame,
    lower: np.ndarray,
    upper: np.ndarray,
    method: str,
    variant: str,
    alpha: float | None,
    protocol: str,
) -> dict[str, float | int | str | None]:
    risk = (lower < LOWER_LIMIT) | (upper > UPPER_LIMIT)
    tmp = test[["feeder", "scenario_id"]].copy()
    tmp["risk_flag"] = risk
    tmp["width"] = upper - lower
    screen = (
        tmp.groupby(["feeder", "scenario_id"])
        .agg(risk_flag=("risk_flag", "max"), mean_width=("width", "mean"))
        .reset_index()
    )
    scenario = scenario_truth(test).merge(screen, on=["feeder", "scenario_id"], how="inner")
    if len(scenario) != len(screen):
        raise RuntimeError("Scenario truth and screening table have inconsistent coverage")

    released = scenario[~scenario["risk_flag"].astype(bool)].copy()
    risky = scenario["actual_risky"].astype(bool)
    released_risky = released["actual_risky"].astype(bool)
    total_risky = int(risky.sum())
    total_severity = float(scenario["actual_severity"].sum())
    total_bus_severity = float(scenario["total_bus_severity"].sum())
    released_count = int(len(released))
    released_risky_count = int(released_risky.sum())
    released_clean = released_count - released_risky_count
    released_severity = float(released["actual_severity"].sum())
    released_bus_severity = float(released["total_bus_severity"].sum())
    released_violating_buses = int(released["actual_violating_buses"].sum())

    return {
        "method": method,
        "variant": variant,
        "protocol": protocol,
        "alpha": alpha,
        "nominal_coverage": None if alpha is None else 1.0 - alpha,
        "test_scenarios": int(len(scenario)),
        "actual_risky_scenarios": total_risky,
        "released_scenarios": released_count,
        "release_ratio": float(released_count / max(1, len(scenario))),
        "released_clean_scenarios": released_clean,
        "released_risky_scenarios": released_risky_count,
        "safe_release_precision": float(released_clean / max(1, released_count)),
        "released_risky_share": float(released_risky_count / max(1, total_risky)),
        "released_violation_severity": released_severity,
        "released_severity_share": float(released_severity / total_severity) if total_severity else 0.0,
        "max_released_severity": float(released["actual_severity"].max()) if released_count else 0.0,
        "released_bus_severity": released_bus_severity,
        "released_bus_severity_share": float(released_bus_severity / total_bus_severity)
        if total_bus_severity
        else 0.0,
        "released_violating_buses": released_violating_buses,
        "flagged_for_ac": int(scenario["risk_flag"].sum()),
        "ac_calls_avoided": released_count,
        "mean_interval_width": float(scenario["mean_width"].mean()),
        "released_available_pv_mw": float(released["available_pv_mw"].sum()),
        "released_load_mw": float(released["load_mw"].sum()),
        "released_risky_available_pv_mw": float(released.loc[released_risky, "available_pv_mw"].sum()),
        "released_risky_load_mw": float(released.loc[released_risky, "load_mw"].sum()),
    }


def point_rows(test: pd.DataFrame, preds: dict, methods: list[tuple[str, str]]) -> list[dict]:
    rows = []
    for method, variant in methods:
        pred = preds[method].pred_test
        rows.append(
            release_metrics(
                test,
                pred,
                pred,
                method=method,
                variant=variant,
                alpha=None,
                protocol="point_gate",
            )
        )
    return rows


def conformal_rows(config: dict, calib: pd.DataFrame, test: pd.DataFrame, preds: dict) -> list[dict]:
    rows = []
    methods = [
        ("Boosting point + global conformal", "global", []),
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
    ]
    for alpha in config["alpha_grid"]:
        for method, variant, group_cols in methods:
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
            rows.append(
                release_metrics(
                    test,
                    lower,
                    upper,
                    method=method,
                    variant=variant,
                    alpha=float(alpha),
                    protocol="conformal_interval",
                )
            )
    return rows


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
    rows.extend(
        point_rows(
            test,
            preds,
            [
                ("LinDistFlow physical backbone", "point_only"),
                ("Boosting point + global conformal", "point_only"),
                ("VoltGuard topology-aware residual", "point_only"),
            ],
        )
    )
    rows.extend(conformal_rows(config, calib, test, preds))
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "screened_safe_release_metrics.csv", index=False)

    display_cols = [
        "method",
        "variant",
        "protocol",
        "nominal_coverage",
        "released_scenarios",
        "safe_release_precision",
        "released_risky_scenarios",
        "released_risky_share",
        "released_severity_share",
        "max_released_severity",
        "released_violating_buses",
        "ac_calls_avoided",
        "mean_interval_width",
        "released_available_pv_mw",
    ]
    (RESULTS / "screened_safe_release_metrics.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["variant"] == "topology_pv_loading_conditioned")
        & (table["alpha"] == float(config["primary_alpha"]))
    ].iloc[0]
    point_vg = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["variant"] == "point_only")
    ].iloc[0]
    point_ldf = table[
        (table["method"] == "LinDistFlow physical backbone")
        & (table["variant"] == "point_only")
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "point_gate_rows": int((table["protocol"] == "point_gate").sum()),
        "conformal_rows": int((table["protocol"] == "conformal_interval").sum()),
        "primary_alpha": float(config["primary_alpha"]),
        "primary_released_scenarios": int(primary["released_scenarios"]),
        "primary_safe_release_precision": float(primary["safe_release_precision"]),
        "primary_released_risky_scenarios": int(primary["released_risky_scenarios"]),
        "primary_released_severity_share": float(primary["released_severity_share"]),
        "primary_ac_calls_avoided": int(primary["ac_calls_avoided"]),
        "primary_mean_interval_width": float(primary["mean_interval_width"]),
        "point_vg_released_risky_scenarios": int(point_vg["released_risky_scenarios"]),
        "point_ldf_released_risky_scenarios": int(point_ldf["released_risky_scenarios"]),
        "point_ldf_released_severity_share": float(point_ldf["released_severity_share"]),
    }
    (RESULTS / "screened_safe_release_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
