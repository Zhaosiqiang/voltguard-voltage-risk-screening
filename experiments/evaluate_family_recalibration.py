"""Audit family-level conformal undercoverage and recalibration tradeoffs.

The primary conformal model is calibrated before test labels are observed. This
script is a post-hoc AC-audit diagnostic: it uses the representative test split
to identify operating families whose empirical coverage falls below the nominal
target and reports how much an inflate-only family radius update would cost in
interval width and false alarms. The audited radius is not fed back into model
training; it quantifies where explicit recalibration would be needed in
operation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import load_config


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
METHOD = "VoltGuard topology-aware residual"
VARIANT = "topology_pv_loading_conditioned"


def finite_sample_quantile(scores: np.ndarray, alpha: float) -> float:
    if len(scores) == 0:
        return 0.0
    q_level = min(1.0, np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores))
    return float(np.quantile(scores, q_level))


def metrics_for_radius(group: pd.DataFrame, q: float) -> dict:
    lower = group["y_pred"] - q
    upper = group["y_pred"] + q
    covered = (group["vm_pu"] >= lower) & (group["vm_pu"] <= upper)
    risk = (lower < 0.95) | (upper > 1.05)
    labels = group["voltage_violation"].astype(bool)
    negatives = ~labels
    return {
        "coverage": float(covered.mean()),
        "width": float(2.0 * q),
        "recall": float((labels & risk).sum() / max(1, labels.sum())),
        "false_alarm_rate": float(risk[negatives].mean()) if negatives.any() else 0.0,
        "missed_violations": int((labels & ~risk).sum()),
    }


def main() -> int:
    config = load_config()
    alpha = float(config["primary_alpha"])
    nominal = 1.0 - alpha
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    primary = raw[(raw["method"] == METHOD) & (raw["conformal_variant"] == VARIANT)].copy()
    primary["score"] = (primary["vm_pu"] - primary["y_pred"]).abs()

    rows = []
    for (feeder, pv_bin, load_bin), group in primary.groupby(["feeder", "pv_bin", "load_bin"], dropna=False):
        q_current = float(group["q_used"].iloc[0])
        q_required = finite_sample_quantile(group["score"].to_numpy(), alpha)
        q_audited = max(q_current, q_required)
        current = metrics_for_radius(group, q_current)
        audited = metrics_for_radius(group, q_audited)
        rows.append(
            {
                "family": f"feeder={feeder}|pv_bin={pv_bin}|load_bin={load_bin}",
                "test_samples": int(len(group)),
                "violating_buses": int(group["voltage_violation"].sum()),
                "nominal_coverage": nominal,
                "q_current": q_current,
                "q_required_for_empirical_target": q_required,
                "q_audited_inflate_only": q_audited,
                "undercovered": bool(current["coverage"] < nominal),
                "coverage_current": current["coverage"],
                "coverage_audited": audited["coverage"],
                "width_current": current["width"],
                "width_audited": audited["width"],
                "width_increase": audited["width"] - current["width"],
                "recall_current": current["recall"],
                "recall_audited": audited["recall"],
                "missed_current": current["missed_violations"],
                "missed_audited": audited["missed_violations"],
                "missed_recovered": current["missed_violations"] - audited["missed_violations"],
                "false_alarm_current": current["false_alarm_rate"],
                "false_alarm_audited": audited["false_alarm_rate"],
            }
        )

    table = pd.DataFrame(rows).sort_values(
        ["undercovered", "coverage_current", "missed_current"],
        ascending=[False, True, False],
    )
    table.to_csv(RESULTS / "family_recalibration_audit.csv", index=False)
    display_cols = [
        "family",
        "test_samples",
        "violating_buses",
        "coverage_current",
        "coverage_audited",
        "width_current",
        "width_audited",
        "recall_current",
        "recall_audited",
        "missed_current",
        "missed_audited",
        "false_alarm_current",
        "false_alarm_audited",
    ]
    (RESULTS / "family_recalibration_audit.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    def weighted_mean(frame: pd.DataFrame, value_col: str, weight_col: str = "test_samples") -> float:
        weights = frame[weight_col].to_numpy()
        values = frame[value_col].to_numpy()
        return float(np.average(values, weights=weights))

    # False-alarm rates are weighted by non-violating buses.
    nonviolating = table["test_samples"] - table["violating_buses"]
    current_fa = float(np.average(table["false_alarm_current"], weights=nonviolating))
    audited_fa = float(np.average(table["false_alarm_audited"], weights=nonviolating))
    worst = table.iloc[0]
    summary = {
        "rows": int(len(table)),
        "nominal_coverage": nominal,
        "undercovered_families": int(table["undercovered"].sum()),
        "missed_current_total": int(table["missed_current"].sum()),
        "missed_audited_total": int(table["missed_audited"].sum()),
        "missed_recovered_total": int(table["missed_recovered"].sum()),
        "weighted_width_current": weighted_mean(table, "width_current"),
        "weighted_width_audited": weighted_mean(table, "width_audited"),
        "weighted_false_alarm_current": current_fa,
        "weighted_false_alarm_audited": audited_fa,
        "worst_family": str(worst["family"]),
        "worst_family_coverage_current": float(worst["coverage_current"]),
        "worst_family_coverage_audited": float(worst["coverage_audited"]),
        "worst_family_missed_current": int(worst["missed_current"]),
        "worst_family_missed_audited": int(worst["missed_audited"]),
    }
    (RESULTS / "family_recalibration_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
