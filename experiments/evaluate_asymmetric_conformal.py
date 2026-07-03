"""Asymmetric conformal calibration audit.

VoltGuard's main intervals use a symmetric absolute-residual conformal radius.
Voltage screening, however, has separate lower and upper operating limits.
This audit tests whether one-sided lower/upper conformal radii improve interval
efficiency or screening behavior. It uses saved calibration and test
predictions from the representative random split and does not retrain models.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import (
    interval_metrics,
    risk_from_interval,
    scenario_metrics,
    screening_metrics,
    voltage_metrics,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
ALPHA = 0.10
MIN_GROUP = 50


def finite_quantile(scores: np.ndarray, alpha: float) -> float:
    if len(scores) == 0:
        return 0.0
    q_level = min(1.0, np.ceil((len(scores) + 1) * (1.0 - alpha)) / len(scores))
    return float(np.quantile(scores, q_level))


def asymmetric_by_group(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    group_cols: list[str],
    alpha: float = ALPHA,
    min_group: int = MIN_GROUP,
    shrinkage: bool = True,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    lower_scores = np.maximum(0.0, calib["pred"].to_numpy() - calib["vm_pu"].to_numpy())
    upper_scores = np.maximum(0.0, calib["vm_pu"].to_numpy() - calib["pred"].to_numpy())
    global_lower = finite_quantile(lower_scores, alpha / 2.0)
    global_upper = finite_quantile(upper_scores, alpha / 2.0)
    lower_q = np.full(len(test), global_lower)
    upper_q = np.full(len(test), global_upper)
    family_rows = []

    if group_cols:
        calib_tmp = calib[group_cols].copy()
        calib_tmp["lower_score"] = lower_scores
        calib_tmp["upper_score"] = upper_scores
        test_tmp = test[group_cols].copy()
        for key, group in calib_tmp.groupby(group_cols, dropna=False):
            if not isinstance(key, tuple):
                key = (key,)
            n = len(group)
            ql_group = finite_quantile(group["lower_score"].to_numpy(), alpha / 2.0)
            qu_group = finite_quantile(group["upper_score"].to_numpy(), alpha / 2.0)
            if shrinkage:
                weight = n / (n + min_group)
                ql = weight * ql_group + (1.0 - weight) * global_lower
                qu = weight * qu_group + (1.0 - weight) * global_upper
            else:
                ql, qu = ql_group, qu_group
            mask = np.ones(len(test_tmp), dtype=bool)
            for col, value in zip(group_cols, key, strict=True):
                mask &= test_tmp[col].to_numpy() == value
            lower_q[mask] = ql
            upper_q[mask] = qu
            family_rows.append(
                {
                    "family": "|".join(f"{col}={value}" for col, value in zip(group_cols, key, strict=True)),
                    "calibration_samples": n,
                    "lower_q": ql,
                    "upper_q": qu,
                    "asymmetry_ratio": qu / max(ql, 1e-12),
                }
            )
    else:
        family_rows.append(
            {
                "family": "__global__",
                "calibration_samples": len(calib),
                "lower_q": global_lower,
                "upper_q": global_upper,
                "asymmetry_ratio": global_upper / max(global_lower, 1e-12),
            }
        )

    lower = test["y_pred"].to_numpy() - lower_q
    upper = test["y_pred"].to_numpy() + upper_q
    return lower, upper, pd.DataFrame(family_rows)


def metrics_row(
    test: pd.DataFrame,
    lower: np.ndarray,
    upper: np.ndarray,
    method: str,
    base_variant: str,
    calibration: str,
) -> dict:
    y_true = test["vm_pu"].to_numpy()
    risk = risk_from_interval(lower, upper)
    return {
        "method": method,
        "base_variant": base_variant,
        "calibration": calibration,
        **voltage_metrics(y_true, test["y_pred"].to_numpy()),
        **interval_metrics(y_true, lower, upper),
        **screening_metrics(y_true, risk),
        **scenario_metrics(test, risk),
    }


def main() -> int:
    raw = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    scores = pd.read_csv(RESULTS / "conformal_scores_random_seed7.csv")
    rows = []
    family_frames = []
    configs = [
        ("Boosting point + global conformal", "global", []),
        ("VoltGuard topology-aware residual", "global", []),
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
    ]
    for method, variant, groups in configs:
        test = raw[(raw["method"] == method) & (raw["conformal_variant"] == variant)].copy()
        calib = scores[(scores["method"] == method) & (scores["conformal_variant"] == variant)].copy()
        rows.append(metrics_row(test, test["lower"].to_numpy(), test["upper"].to_numpy(), method, variant, "symmetric"))
        lower, upper, families = asymmetric_by_group(calib, test, groups)
        rows.append(metrics_row(test, lower, upper, method, variant, "asymmetric"))
        families["method"] = method
        families["base_variant"] = variant
        families["calibration"] = "asymmetric"
        family_frames.append(families)

    table = pd.DataFrame(rows)
    baseline = table[table["calibration"] == "symmetric"][
        ["method", "base_variant", "avg_width", "recall", "false_alarm_rate", "missed_violations"]
    ].rename(
        columns={
            "avg_width": "symmetric_width",
            "recall": "symmetric_recall",
            "false_alarm_rate": "symmetric_false_alarm_rate",
            "missed_violations": "symmetric_missed_violations",
        }
    )
    table = table.merge(baseline, on=["method", "base_variant"], how="left")
    table["width_delta_vs_symmetric"] = table["avg_width"] - table["symmetric_width"]
    table["missed_delta_vs_symmetric"] = table["missed_violations"] - table["symmetric_missed_violations"]
    table["false_alarm_delta_vs_symmetric"] = table["false_alarm_rate"] - table["symmetric_false_alarm_rate"]
    table.to_csv(RESULTS / "asymmetric_conformal_metrics.csv", index=False)

    display_cols = [
        "method",
        "base_variant",
        "calibration",
        "coverage",
        "avg_width",
        "width_delta_vs_symmetric",
        "recall",
        "false_alarm_rate",
        "missed_violations",
        "missed_delta_vs_symmetric",
        "scenario_recall",
        "missed_risky_scenarios",
    ]
    (RESULTS / "asymmetric_conformal_metrics.md").write_text(
        table[display_cols].round(6).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    family_table = pd.concat(family_frames, ignore_index=True)
    family_table.to_csv(RESULTS / "asymmetric_conformal_family_radii.csv", index=False)

    primary_sym = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["base_variant"] == "topology_pv_loading_conditioned")
        & (table["calibration"] == "symmetric")
    ].iloc[0]
    primary_asym = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["base_variant"] == "topology_pv_loading_conditioned")
        & (table["calibration"] == "asymmetric")
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "family_rows": int(len(family_table)),
        "primary_symmetric_width": float(primary_sym["avg_width"]),
        "primary_asymmetric_width": float(primary_asym["avg_width"]),
        "primary_width_delta": float(primary_asym["width_delta_vs_symmetric"]),
        "primary_symmetric_recall": float(primary_sym["recall"]),
        "primary_asymmetric_recall": float(primary_asym["recall"]),
        "primary_symmetric_missed": int(primary_sym["missed_violations"]),
        "primary_asymmetric_missed": int(primary_asym["missed_violations"]),
        "primary_asymmetric_scenario_recall": float(primary_asym["scenario_recall"]),
    }
    (RESULTS / "asymmetric_conformal_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
