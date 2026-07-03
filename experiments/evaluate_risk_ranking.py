"""Scenario-level risk-ranking evaluation for VoltGuard.

The screening claim is stronger if calibrated intervals not only flag risky
buses, but also prioritize scenarios for downstream AC-audited optimization.
This script evaluates scenario-level ranking quality from saved bus-level raw
predictions. It does not retrain models.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
LOWER_LIMIT = 0.95
UPPER_LIMIT = 1.05
TOP_K = [10, 20, 30]
BOTTOM_K = [5, 10, 20]


def safe_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return float("nan")
    return float(roc_auc_score(labels, scores))


def scenario_frame(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.copy()
    raw["true_under_margin"] = np.maximum(0.0, LOWER_LIMIT - raw["vm_pu"])
    raw["true_over_margin"] = np.maximum(0.0, raw["vm_pu"] - UPPER_LIMIT)
    raw["true_severity"] = raw[["true_under_margin", "true_over_margin"]].max(axis=1)
    raw["pred_under_margin"] = np.maximum(0.0, LOWER_LIMIT - raw["lower"])
    raw["pred_over_margin"] = np.maximum(0.0, raw["upper"] - UPPER_LIMIT)
    raw["pred_interval_margin"] = raw[["pred_under_margin", "pred_over_margin"]].max(axis=1)
    raw["interval_width"] = raw["upper"] - raw["lower"]
    return (
        raw.groupby(["method", "conformal_variant", "feeder", "scenario_id"], dropna=False)
        .agg(
            actual_risky=("voltage_violation", "max"),
            actual_severity=("true_severity", "max"),
            predicted_risky=("risk_flag", "max"),
            risk_score=("pred_interval_margin", "max"),
            mean_interval_width=("interval_width", "mean"),
        )
        .reset_index()
    )


def ranking_metrics(group: pd.DataFrame) -> dict:
    labels = group["actual_risky"].astype(int).to_numpy()
    scores = group["risk_score"].to_numpy()
    severity = group["actual_severity"].to_numpy()
    ranked = group.sort_values(["risk_score", "mean_interval_width"], ascending=[False, False]).reset_index(drop=True)
    safe_ranked = group.sort_values(["risk_score", "mean_interval_width"], ascending=[True, True]).reset_index(drop=True)
    total_risky = max(1, int(labels.sum()))
    total_severity = float(severity.sum())
    out = {
        "test_scenarios": int(len(group)),
        "risky_scenarios": int(labels.sum()),
        "roc_auc": safe_auc(labels, scores),
        "average_precision": float(average_precision_score(labels, scores)) if len(np.unique(labels)) > 1 else float("nan"),
        "spearman_score_severity": float(group[["risk_score", "actual_severity"]].corr(method="spearman").iloc[0, 1]),
    }
    for k in TOP_K:
        top = ranked.head(k)
        out[f"top{k}_risky_capture"] = float(top["actual_risky"].sum() / total_risky)
        out[f"top{k}_precision"] = float(top["actual_risky"].mean())
        out[f"top{k}_severity_capture"] = (
            float(top["actual_severity"].sum() / total_severity) if total_severity > 0 else float("nan")
        )
    for k in BOTTOM_K:
        bottom = safe_ranked.head(k)
        out[f"bottom{k}_safe_precision"] = float((~bottom["actual_risky"].astype(bool)).mean())
        out[f"bottom{k}_missed_risky"] = int(bottom["actual_risky"].sum())
    return out


def main() -> int:
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    scenario = scenario_frame(raw)
    scenario.to_csv(RESULTS / "scenario_risk_ranking_raw.csv", index=False)

    rows = []
    for (method, variant), group in scenario.groupby(["method", "conformal_variant"], dropna=False):
        row = {"method": method, "conformal_variant": variant}
        row.update(ranking_metrics(group))
        rows.append(row)
    table = pd.DataFrame(rows).sort_values(
        ["average_precision", "spearman_score_severity"],
        ascending=[False, False],
    )
    table.to_csv(RESULTS / "scenario_risk_ranking_metrics.csv", index=False)
    (RESULTS / "scenario_risk_ranking_metrics.md").write_text(
        table.round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    primary = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["conformal_variant"] == "topology_pv_loading_conditioned")
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "primary_average_precision": float(primary["average_precision"]),
        "primary_spearman_score_severity": float(primary["spearman_score_severity"]),
        "primary_top20_severity_capture": float(primary["top20_severity_capture"]),
        "primary_bottom10_safe_precision": float(primary["bottom10_safe_precision"]),
    }
    (RESULTS / "scenario_risk_ranking_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
