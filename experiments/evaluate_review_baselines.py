"""Reviewer-requested baseline comparisons for the VoltGuard manuscript.

This script adds two statistical uncertainty baselines requested by the
professional review report: quantile regression and Gaussian-process UQ. The
experiment is intentionally scoped to the representative random split (seed 7)
so that it augments, rather than replaces, the main multi-seed study.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evaluate_models import (
    FEATURES,
    LOWER_LIMIT,
    UPPER_LIMIT,
    assign_random_split,
    apply_split,
    format_markdown,
    load_config,
    prepare_data,
    scenario_table,
)


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"


def metric_row(method: str, y: np.ndarray, pred: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict:
    violation = (y < LOWER_LIMIT) | (y > UPPER_LIMIT)
    risk = (lower < LOWER_LIMIT) | (upper > UPPER_LIMIT)
    tp = int(np.sum(risk & violation))
    fp = int(np.sum(risk & ~violation))
    fn = int(np.sum(~risk & violation))
    tn = int(np.sum(~risk & ~violation))
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    false_alarm = fp / (fp + tn) if fp + tn else 0.0
    return {
        "split_name": "random_interpolation",
        "seed": 7,
        "method": method,
        "mae": float(np.mean(np.abs(y - pred))),
        "rmse": float(np.sqrt(np.mean((y - pred) ** 2))),
        "max_abs_error": float(np.max(np.abs(y - pred))),
        "coverage": float(np.mean((y >= lower) & (y <= upper))),
        "avg_width": float(np.mean(upper - lower)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alarm_rate": false_alarm,
        "missed_violations": fn,
    }


def main() -> None:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    split = assign_random_split(scenario_table(data), seed=7)
    data = apply_split(data, split)
    train = data[data["split"] == "train"].copy()
    test = data[data["split"] == "test"].copy()

    x_train = train[FEATURES].to_numpy(dtype=float)
    y_train = train["vm_pu"].to_numpy(dtype=float)
    x_test = test[FEATURES].to_numpy(dtype=float)
    y_test = test["vm_pu"].to_numpy(dtype=float)

    rows = []

    lower_model = HistGradientBoostingRegressor(loss="quantile", quantile=0.05, max_iter=220, random_state=7)
    median_model = HistGradientBoostingRegressor(loss="quantile", quantile=0.50, max_iter=220, random_state=7)
    upper_model = HistGradientBoostingRegressor(loss="quantile", quantile=0.95, max_iter=220, random_state=7)
    lower_model.fit(x_train, y_train)
    median_model.fit(x_train, y_train)
    upper_model.fit(x_train, y_train)
    q_lower = lower_model.predict(x_test)
    q_pred = median_model.predict(x_test)
    q_upper = upper_model.predict(x_test)
    rows.append(metric_row("Gradient-boosted quantile regression", y_test, q_pred, q_lower, q_upper))

    rng = np.random.default_rng(7)
    sample_n = min(900, len(train))
    sample_idx = rng.choice(len(train), size=sample_n, replace=False)
    kernel = ConstantKernel(1.0, constant_value_bounds="fixed") * RBF(1.0, length_scale_bounds="fixed") + WhiteKernel(
        noise_level=1e-5, noise_level_bounds="fixed"
    )
    gpr = make_pipeline(
        StandardScaler(),
        GaussianProcessRegressor(kernel=kernel, alpha=1e-8, optimizer=None, normalize_y=True, random_state=7),
    )
    gpr.fit(x_train[sample_idx], y_train[sample_idx])
    gp_model = gpr.named_steps["gaussianprocessregressor"]
    scaled_test = gpr.named_steps["standardscaler"].transform(x_test)
    gp_pred, gp_std = gp_model.predict(scaled_test, return_std=True)
    z90 = 1.6448536269514722
    rows.append(
        metric_row(
            "Gaussian-process UQ baseline",
            y_test,
            gp_pred,
            gp_pred - z90 * gp_std,
            gp_pred + z90 * gp_std,
        )
    )

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "review_baseline_comparison_metrics.csv", index=False)
    format_markdown(out, RESULTS / "review_baseline_comparison_metrics.md")
    summary = {
        "rows": int(len(out)),
        "seed": 7,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "gpr_training_subsample_rows": int(sample_n),
        "methods": out["method"].tolist(),
    }
    (RESULTS / "review_baseline_comparison_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
