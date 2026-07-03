"""EV-conditioning conformal ablation.

EV charging appears as a forecast feature in the scenario generator and
residual learner. This audit tests whether EV scale should also be a conformal
conditioning key. It reuses saved calibration nonconformity scores and
representative raw predictions, so it does not retrain the point model.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_models import load_config


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
METHOD = "VoltGuard topology-aware residual"
PRIMARY_VARIANT = "topology_pv_loading_conditioned"


VARIANTS = [
    ("topology+PV+loading", ["feeder", "pv_bin", "load_bin"]),
    ("topology+PV+loading+EV", ["feeder", "pv_bin", "load_bin", "ev_bin"]),
    ("topology+PV+EV", ["feeder", "pv_bin", "ev_bin"]),
    ("PV+loading+EV", ["pv_bin", "load_bin", "ev_bin"]),
    ("EV-only", ["ev_bin"]),
]


def finite_sample_quantile(scores: np.ndarray, alpha: float) -> float:
    if len(scores) == 0:
        return 0.0
    q_level = min(1.0, np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores))
    return float(np.quantile(scores, q_level))


def add_ev_bin(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["ev_bin"] = "ev_" + out["ev_scale"].round(1).astype(str)
    return out


def screening_metrics(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict:
    covered = (y_true >= lower) & (y_true <= upper)
    labels = (y_true < 0.95) | (y_true > 1.05)
    risk = (lower < 0.95) | (upper > 1.05)
    positives = labels
    negatives = ~labels
    tp = int((positives & risk).sum())
    return {
        "coverage": float(covered.mean()),
        "avg_width": float(np.mean(upper - lower)),
        "precision": float(tp / max(1, int(risk.sum()))),
        "recall": float(tp / max(1, int(positives.sum()))),
        "false_alarm_rate": float(risk[negatives].mean()) if negatives.any() else 0.0,
        "missed_violations": int((positives & ~risk).sum()),
    }


def evaluate_variant(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    group_cols: list[str],
    alpha: float,
    min_group: int,
) -> tuple[dict, pd.DataFrame]:
    global_q = finite_sample_quantile(calib["nonconformity_score"].to_numpy(), alpha)
    q_used = np.full(len(test), global_q, dtype=float)
    family_rows = []
    for key, group in calib.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        n = len(group)
        group_q = finite_sample_quantile(group["nonconformity_score"].to_numpy(), alpha)
        weight = n / (n + min_group)
        q = weight * group_q + (1.0 - weight) * global_q
        mask = np.ones(len(test), dtype=bool)
        for col, value in zip(group_cols, key, strict=True):
            mask &= test[col].to_numpy() == value
        q_used[mask] = q
        family_rows.append(
            {
                "family": "|".join(f"{col}={value}" for col, value in zip(group_cols, key, strict=True)),
                "calibration_samples": int(n),
                "test_samples": int(mask.sum()),
                "group_q": group_q,
                "q_used": q,
            }
        )
    lower = test["y_pred"].to_numpy() - q_used
    upper = test["y_pred"].to_numpy() + q_used
    metrics = screening_metrics(test["vm_pu"].to_numpy(), lower, upper)
    metrics.update(
        {
            "families": int(len(family_rows)),
            "min_calibration_samples": int(min(row["calibration_samples"] for row in family_rows)),
            "min_test_samples": int(min(row["test_samples"] for row in family_rows)),
            "empty_test_families": int(sum(row["test_samples"] == 0 for row in family_rows)),
        }
    )
    return metrics, pd.DataFrame(family_rows)


def main() -> int:
    config = load_config()
    alpha = float(config["primary_alpha"])
    min_group = int(config["min_group_samples"])

    labels = pd.read_csv(RESULTS / "bus_voltage_labels.csv")[
        ["feeder", "scenario_id", "bus", "ev_scale"]
    ].copy()
    labels["feeder"] = labels["feeder"].astype(str)

    calib = pd.read_csv(RESULTS / "conformal_scores_random_seed7.csv")
    test = pd.read_csv(RESULTS / "raw_predictions_random_seed7.csv")
    calib["feeder"] = calib["feeder"].astype(str)
    test["feeder"] = test["feeder"].astype(str)
    calib = calib[
        (calib["method"] == METHOD)
        & (calib["conformal_variant"] == PRIMARY_VARIANT)
    ].merge(labels, on=["feeder", "scenario_id", "bus"], how="left")
    test = test[
        (test["method"] == METHOD)
        & (test["conformal_variant"] == PRIMARY_VARIANT)
    ].merge(labels, on=["feeder", "scenario_id", "bus"], how="left")
    calib = add_ev_bin(calib)
    test = add_ev_bin(test)

    rows = []
    family_tables = []
    for variant_name, group_cols in VARIANTS:
        metrics, families = evaluate_variant(calib, test, group_cols, alpha, min_group)
        rows.append({"variant": variant_name, "group_cols": "+".join(group_cols), **metrics})
        families.insert(0, "variant", variant_name)
        family_tables.append(families)

    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "ev_conditioning_ablation.csv", index=False)
    (RESULTS / "ev_conditioning_ablation.md").write_text(
        table.round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    family_table = pd.concat(family_tables, ignore_index=True)
    family_table.to_csv(RESULTS / "ev_conditioning_family_counts.csv", index=False)

    primary = table[table["variant"] == "topology+PV+loading"].iloc[0]
    ev_full = table[table["variant"] == "topology+PV+loading+EV"].iloc[0]
    summary = {
        "rows": int(len(table)),
        "primary_missed": int(primary["missed_violations"]),
        "ev_full_missed": int(ev_full["missed_violations"]),
        "primary_families": int(primary["families"]),
        "ev_full_families": int(ev_full["families"]),
        "ev_full_min_calibration_samples": int(ev_full["min_calibration_samples"]),
        "ev_full_empty_test_families": int(ev_full["empty_test_families"]),
        "ev_full_width_delta": float(ev_full["avg_width"] - primary["avg_width"]),
        "ev_full_recall_delta": float(ev_full["recall"] - primary["recall"]),
    }
    (RESULTS / "ev_conditioning_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
