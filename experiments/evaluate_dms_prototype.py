"""Simulated DMS prototype for the VoltGuard-ECM integration paper."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"
LOWER_LIMIT = 0.95
UPPER_LIMIT = 1.05


def markdown(df: pd.DataFrame, path: Path, digits: int = 4) -> None:
    path.write_text(df.round(digits).to_markdown(index=False) + "\n", encoding="utf-8")


def main() -> None:
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    primary = raw[
        (raw["method"] == "VoltGuard topology-aware residual")
        & (raw["conformal_variant"] == "topology_pv_loading_conditioned")
    ].copy()
    scenarios = (
        primary.groupby(["feeder", "scenario_id"])
        .agg(
            min_vm=("vm_pu", "min"),
            max_vm=("vm_pu", "max"),
            risk_flag=("risk_flag", "max"),
            violation_any=("voltage_violation", "max"),
            pv_bin=("pv_bin", "first"),
            load_bin=("load_bin", "first"),
            min_lower=("lower", "min"),
            max_upper=("upper", "max"),
        )
        .reset_index()
    )

    rng = np.random.default_rng(17)
    cycles = 7 * 24 * 6
    records = []
    for cycle in range(cycles):
        row = scenarios.iloc[cycle % len(scenarios)]
        telemetry_age_min = float(rng.gamma(shape=2.0, scale=1.8))
        if rng.random() < 0.035:
            telemetry_age_min += float(rng.uniform(5.0, 18.0))
        unseen_topology = bool(rng.random() < 0.025)
        out_of_envelope = bool(rng.random() < 0.045)
        operator_override = bool(rng.random() < 0.018)
        stale_telemetry = telemetry_age_min > 5.0
        residual_alarm = bool(rng.random() < (0.015 + 0.02 * int(row["violation_any"])))
        interval_margin = min(float(row["min_lower"]) - LOWER_LIMIT, UPPER_LIMIT - float(row["max_upper"]))

        reasons = []
        if bool(row["risk_flag"]):
            reasons.append("interval_limit_intersection")
        if stale_telemetry:
            reasons.append("stale_telemetry")
        if unseen_topology:
            reasons.append("unseen_topology")
        if out_of_envelope:
            reasons.append("out_of_envelope_forecast")
        if residual_alarm:
            reasons.append("rolling_residual_alarm")
        if operator_override:
            reasons.append("operator_override")

        if reasons:
            queue = "corrective_audit"
        elif interval_margin < 0.003:
            queue = "watch"
            reasons.append("near_limit_margin")
        else:
            queue = "release"
            reasons.append("valid_low_risk")

        records.append(
            {
                "cycle": cycle,
                "day": cycle // (24 * 6) + 1,
                "hour": (cycle // 6) % 24,
                "feeder": row["feeder"],
                "scenario_id": int(row["scenario_id"]),
                "telemetry_age_min": telemetry_age_min,
                "stale_telemetry": stale_telemetry,
                "unseen_topology": unseen_topology,
                "out_of_envelope": out_of_envelope,
                "operator_override": operator_override,
                "residual_alarm": residual_alarm,
                "voltage_violation": bool(row["violation_any"]),
                "screen_risk_flag": bool(row["risk_flag"]),
                "queue": queue,
                "reason_code": ";".join(reasons),
            }
        )

    log = pd.DataFrame(records)
    log.to_csv(RESULTS / "dms_prototype_weekly_log.csv", index=False)

    by_queue = (
        log.groupby("queue")
        .agg(
            records=("queue", "size"),
            violations=("voltage_violation", "sum"),
            stale=("stale_telemetry", "sum"),
            unseen_topology=("unseen_topology", "sum"),
            out_of_envelope=("out_of_envelope", "sum"),
            operator_overrides=("operator_override", "sum"),
        )
        .reset_index()
    )
    by_queue["record_share"] = by_queue["records"] / len(log)
    by_queue.to_csv(RESULTS / "dms_prototype_queue_summary.csv", index=False)
    markdown(by_queue, RESULTS / "dms_prototype_queue_summary.md")

    audit = log[log["queue"] == "corrective_audit"]
    release = log[log["queue"] == "release"]
    summary = {
        "simulated_cycles": int(len(log)),
        "simulated_days": 7,
        "release_records": int(len(release)),
        "watch_records": int((log["queue"] == "watch").sum()),
        "corrective_audit_records": int(len(audit)),
        "released_violating_records": int(release["voltage_violation"].sum()),
        "audited_violating_records": int(audit["voltage_violation"].sum()),
        "operator_override_records": int(log["operator_override"].sum()),
        "stale_telemetry_records": int(log["stale_telemetry"].sum()),
        "unseen_topology_records": int(log["unseen_topology"].sum()),
        "out_of_envelope_records": int(log["out_of_envelope"].sum()),
        "residual_alarm_records": int(log["residual_alarm"].sum()),
    }
    (RESULTS / "dms_prototype_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
