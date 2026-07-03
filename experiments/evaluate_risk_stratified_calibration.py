"""Risk-stratified calibration and screening audit.

This audit asks whether the calibrated intervals remain useful in the voltage
regions that matter operationally: true violations, nonviolating buses close to
the statutory limits, near-safe buses, and interior-safe buses. It uses saved
raw predictions only and therefore checks the submitted artifacts rather than
retraining a model.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
LOWER_LIMIT = 0.95
UPPER_LIMIT = 1.05
BOUNDARY_MARGIN = 0.002
NEAR_MARGIN = 0.010


def add_bus_strata(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy()
    frame["covered"] = (frame["lower"] <= frame["vm_pu"]) & (frame["vm_pu"] <= frame["upper"])
    frame["interval_width"] = frame["upper"] - frame["lower"]
    frame["true_under_margin"] = np.maximum(0.0, LOWER_LIMIT - frame["vm_pu"])
    frame["true_over_margin"] = np.maximum(0.0, frame["vm_pu"] - UPPER_LIMIT)
    frame["true_violation_severity"] = frame[["true_under_margin", "true_over_margin"]].max(axis=1)
    frame["safe_margin_to_limit"] = np.minimum(frame["vm_pu"] - LOWER_LIMIT, UPPER_LIMIT - frame["vm_pu"])

    conditions = [
        frame["true_violation_severity"] > 0.0,
        frame["safe_margin_to_limit"] <= BOUNDARY_MARGIN,
        frame["safe_margin_to_limit"] <= NEAR_MARGIN,
    ]
    choices = ["violating", "boundary_safe", "near_safe"]
    frame["risk_stratum"] = np.select(conditions, choices, default="interior_safe")
    return frame


def bus_metrics(group: pd.DataFrame) -> dict:
    actual = group["voltage_violation"].astype(bool)
    flagged = group["risk_flag"].astype(bool)
    safe = ~actual
    risky_count = int(actual.sum())
    safe_count = int(safe.sum())
    missed = int((actual & ~flagged).sum())
    false_alarm = int((safe & flagged).sum())
    return {
        "bus_samples": int(len(group)),
        "violating_buses": risky_count,
        "safe_buses": safe_count,
        "coverage": float(group["covered"].mean()),
        "avg_width": float(group["interval_width"].mean()),
        "risk_flag_rate": float(flagged.mean()),
        "violation_recall": float((risky_count - missed) / risky_count) if risky_count else float("nan"),
        "false_alarm_rate": float(false_alarm / safe_count) if safe_count else float("nan"),
        "missed_violations": missed,
        "false_alarm_buses": false_alarm,
        "mean_true_severity": float(group["true_violation_severity"].mean()),
        "max_true_severity": float(group["true_violation_severity"].max()),
    }


def scenario_frame(bus_frame: pd.DataFrame) -> pd.DataFrame:
    scenario = (
        bus_frame.groupby(["method", "conformal_variant", "feeder", "scenario_id"], dropna=False)
        .agg(
            actual_risky=("voltage_violation", "max"),
            risk_flag=("risk_flag", "max"),
            scenario_coverage=("covered", "mean"),
            mean_width=("interval_width", "mean"),
            max_true_severity=("true_violation_severity", "max"),
            min_safe_margin=("safe_margin_to_limit", "min"),
            missed_buses=("voltage_violation", lambda values: 0),
        )
        .reset_index()
    )
    missed = (
        bus_frame.assign(missed=lambda df: df["voltage_violation"].astype(bool) & ~df["risk_flag"].astype(bool))
        .groupby(["method", "conformal_variant", "feeder", "scenario_id"], dropna=False)["missed"]
        .sum()
        .reset_index(name="missed_buses")
    )
    scenario = scenario.drop(columns=["missed_buses"]).merge(
        missed,
        on=["method", "conformal_variant", "feeder", "scenario_id"],
        how="inner",
    )

    conditions = [
        scenario["max_true_severity"] > 0.0,
        scenario["min_safe_margin"] <= BOUNDARY_MARGIN,
        scenario["min_safe_margin"] <= NEAR_MARGIN,
    ]
    choices = ["violating", "boundary_safe", "near_safe"]
    scenario["risk_stratum"] = np.select(conditions, choices, default="interior_safe")
    return scenario


def scenario_metrics(group: pd.DataFrame) -> dict:
    actual = group["actual_risky"].astype(bool)
    flagged = group["risk_flag"].astype(bool)
    safe = ~actual
    risky_count = int(actual.sum())
    safe_count = int(safe.sum())
    missed = int((actual & ~flagged).sum())
    false_alarm = int((safe & flagged).sum())
    return {
        "scenarios": int(len(group)),
        "risky_scenarios": risky_count,
        "safe_scenarios": safe_count,
        "scenario_coverage_mean": float(group["scenario_coverage"].mean()),
        "mean_interval_width": float(group["mean_width"].mean()),
        "risk_flag_rate": float(flagged.mean()),
        "scenario_recall": float((risky_count - missed) / risky_count) if risky_count else float("nan"),
        "scenario_false_alarm_rate": float(false_alarm / safe_count) if safe_count else float("nan"),
        "missed_risky_scenarios": missed,
        "false_alarm_scenarios": false_alarm,
        "missed_buses_inside_stratum": int(group["missed_buses"].sum()),
        "mean_true_severity": float(group["max_true_severity"].mean()),
        "max_true_severity": float(group["max_true_severity"].max()),
    }


def grouped_table(frame: pd.DataFrame, metric_fn) -> pd.DataFrame:
    rows = []
    for (method, variant, stratum), group in frame.groupby(
        ["method", "conformal_variant", "risk_stratum"],
        dropna=False,
    ):
        row = {
            "method": method,
            "conformal_variant": variant,
            "risk_stratum": stratum,
        }
        row.update(metric_fn(group))
        rows.append(row)
    order = {"violating": 0, "boundary_safe": 1, "near_safe": 2, "interior_safe": 3}
    table = pd.DataFrame(rows)
    table["_order"] = table["risk_stratum"].map(order)
    return table.sort_values(["method", "conformal_variant", "_order"]).drop(columns=["_order"])


def main() -> int:
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    bus = add_bus_strata(raw)
    bus_table = grouped_table(bus, bus_metrics)
    scenario = scenario_frame(bus)
    scenario_table = grouped_table(scenario, scenario_metrics)

    bus_table.to_csv(RESULTS / "risk_stratified_calibration_bus.csv", index=False)
    scenario_table.to_csv(RESULTS / "risk_stratified_calibration_scenario.csv", index=False)

    bus_display_cols = [
        "method",
        "conformal_variant",
        "risk_stratum",
        "bus_samples",
        "coverage",
        "avg_width",
        "risk_flag_rate",
        "violation_recall",
        "false_alarm_rate",
        "missed_violations",
        "false_alarm_buses",
    ]
    scenario_display_cols = [
        "method",
        "conformal_variant",
        "risk_stratum",
        "scenarios",
        "scenario_coverage_mean",
        "mean_interval_width",
        "risk_flag_rate",
        "scenario_recall",
        "scenario_false_alarm_rate",
        "missed_risky_scenarios",
        "false_alarm_scenarios",
    ]
    (RESULTS / "risk_stratified_calibration_bus.md").write_text(
        bus_table[bus_display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    (RESULTS / "risk_stratified_calibration_scenario.md").write_text(
        scenario_table[scenario_display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_bus = bus_table[
        (bus_table["method"] == "VoltGuard topology-aware residual")
        & (bus_table["conformal_variant"] == "topology_pv_loading_conditioned")
    ]
    primary_scenario = scenario_table[
        (scenario_table["method"] == "VoltGuard topology-aware residual")
        & (scenario_table["conformal_variant"] == "topology_pv_loading_conditioned")
    ]
    primary_violating_bus = primary_bus[primary_bus["risk_stratum"] == "violating"].iloc[0]
    primary_boundary_bus = primary_bus[primary_bus["risk_stratum"] == "boundary_safe"].iloc[0]
    primary_violating_scenario = primary_scenario[primary_scenario["risk_stratum"] == "violating"].iloc[0]
    primary_safe_scenarios = primary_scenario[primary_scenario["risk_stratum"].isin(["boundary_safe", "near_safe", "interior_safe"])]
    summary = {
        "bus_rows": int(len(bus_table)),
        "scenario_rows": int(len(scenario_table)),
        "primary_violating_bus_recall": float(primary_violating_bus["violation_recall"]),
        "primary_violating_bus_missed": int(primary_violating_bus["missed_violations"]),
        "primary_boundary_safe_bus_false_alarm_rate": float(primary_boundary_bus["false_alarm_rate"]),
        "primary_violating_scenario_recall": float(primary_violating_scenario["scenario_recall"]),
        "primary_safe_scenario_false_alarms": int(primary_safe_scenarios["false_alarm_scenarios"].sum()),
        "boundary_margin_pu": BOUNDARY_MARGIN,
        "near_margin_pu": NEAR_MARGIN,
    }
    (RESULTS / "risk_stratified_calibration_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
