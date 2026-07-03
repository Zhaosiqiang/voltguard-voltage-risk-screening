"""Ablate topology/electrical features and residual formulation.

This script answers a reviewer-facing question: is the selected model more
than a generic tree regressor? It evaluates direct and residual variants under
the same topology/PV/loading conformal calibration protocol used by VoltGuard.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evaluate_models import (
    apply_split,
    assign_random_split,
    conformal_by_group,
    format_markdown,
    interval_metrics,
    load_config,
    prepare_data,
    risk_from_interval,
    scenario_table,
    screening_metrics,
    voltage_metrics,
)


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"


LOCAL_OPERATING = [
    "load_p_mw",
    "load_q_mvar",
    "pv_p_mw",
    "net_p_mw",
    "load_scale",
    "pv_penetration",
    "ev_scale",
]

LOCAL_TOPOLOGY = [
    "bus_norm",
    "vn_kv",
    "degree",
    "is_slack",
    *LOCAL_OPERATING,
    "feeder_code",
]

FULL_TOPOLOGY_ELECTRICAL = [
    "bus_norm",
    "vn_kv",
    "degree",
    "is_slack",
    "load_p_mw",
    "load_q_mvar",
    "pv_p_mw",
    "net_p_mw",
    "neighbor_load_p_mw",
    "neighbor_pv_p_mw",
    "neighbor_net_p_mw",
    "load_scale",
    "pv_penetration",
    "ev_scale",
    "ldf_vm_pu",
    "ldf_u_pu",
    "feeder_code",
]


def fit_direct_extra_trees(train: pd.DataFrame, calib: pd.DataFrame, test: pd.DataFrame, cols: list[str], seed: int):
    model = ExtraTreesRegressor(n_estimators=220, random_state=seed + 200, min_samples_leaf=3, n_jobs=-1)
    model.fit(train[cols].to_numpy(), train["vm_pu"].to_numpy())
    return model.predict(calib[cols].to_numpy()), model.predict(test[cols].to_numpy())


def fit_residual_extra_trees(train: pd.DataFrame, calib: pd.DataFrame, test: pd.DataFrame, cols: list[str], seed: int):
    train_base = train["ldf_vm_pu"].to_numpy()
    calib_base = calib["ldf_vm_pu"].to_numpy()
    test_base = test["ldf_vm_pu"].to_numpy()
    residual_model = ExtraTreesRegressor(
        n_estimators=220,
        random_state=seed + 300,
        min_samples_leaf=3,
        n_jobs=-1,
    )
    residual_model.fit(train[cols].to_numpy(), train["vm_pu"].to_numpy() - train_base)
    return (
        calib_base + residual_model.predict(calib[cols].to_numpy()),
        test_base + residual_model.predict(test[cols].to_numpy()),
    )


def evaluate_variant(
    train: pd.DataFrame,
    calib: pd.DataFrame,
    test: pd.DataFrame,
    pred_calib: np.ndarray,
    pred_test: np.ndarray,
    seed: int,
    variant: str,
    feature_family: str,
    alpha: float,
    min_group: int,
) -> dict:
    lower, upper, q_used, _ = conformal_by_group(
        calib,
        test,
        pred_calib,
        pred_test,
        ["feeder", "pv_bin", "load_bin"],
        alpha=alpha,
        min_group=min_group,
        shrinkage=True,
    )
    y_test = test["vm_pu"].to_numpy()
    risk = risk_from_interval(lower, upper)
    return {
        "seed": seed,
        "variant": variant,
        "feature_family": feature_family,
        **voltage_metrics(y_test, pred_test),
        **interval_metrics(y_test, lower, upper),
        **screening_metrics(y_test, risk),
        "mean_q_used": float(np.mean(q_used)),
    }


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "mae",
        "rmse",
        "max_abs_error",
        "coverage",
        "avg_width",
        "precision",
        "recall",
        "f1",
        "false_alarm_rate",
        "missed_violations",
        "mean_q_used",
    ]
    rows = []
    for key, group in df.groupby(["variant", "feature_family"], dropna=False):
        variant, feature_family = key
        row = {"variant": variant, "feature_family": feature_family, "runs": int(len(group))}
        for col in metric_cols:
            values = group[col].astype(float)
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_ci95"] = float(1.96 * row[f"{col}_std"] / np.sqrt(max(1, len(values))))
        rows.append(row)
    out = pd.DataFrame(rows)
    order = {
        "direct": 0,
        "residual": 1,
    }
    feature_order = {
        "local_operating": 0,
        "local_topology": 1,
        "full_topology_electrical": 2,
    }
    out["variant_order"] = out["variant"].map(order)
    out["feature_order"] = out["feature_family"].map(feature_order)
    return out.sort_values(["variant_order", "feature_order"]).drop(columns=["variant_order", "feature_order"])


def main() -> int:
    config = load_config()
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)
    alpha = float(config["primary_alpha"])
    min_group = int(config["min_group_samples"])

    all_rows = []
    for seed in config["evaluation_seeds"]:
        split = assign_random_split(scenarios, seed)
        frame = apply_split(data, split)
        train = frame[frame["split"] == "train"].copy()
        calib = frame[frame["split"] == "calib"].copy()
        test = frame[frame["split"] == "test"].copy()

        specs = [
            ("direct", "full_topology_electrical", FULL_TOPOLOGY_ELECTRICAL, fit_direct_extra_trees),
            ("residual", "local_operating", LOCAL_OPERATING, fit_residual_extra_trees),
            ("residual", "local_topology", LOCAL_TOPOLOGY, fit_residual_extra_trees),
            ("residual", "full_topology_electrical", FULL_TOPOLOGY_ELECTRICAL, fit_residual_extra_trees),
        ]
        for variant, feature_family, cols, fitter in specs:
            pred_calib, pred_test = fitter(train, calib, test, cols, int(seed))
            all_rows.append(
                evaluate_variant(
                    train,
                    calib,
                    test,
                    pred_calib,
                    pred_test,
                    int(seed),
                    variant,
                    feature_family,
                    alpha,
                    min_group,
                )
            )

    raw = pd.DataFrame(all_rows)
    summary = aggregate(raw)
    full_row = summary[
        (summary["variant"] == "residual")
        & (summary["feature_family"] == "full_topology_electrical")
    ].iloc[0]
    local_row = summary[
        (summary["variant"] == "residual")
        & (summary["feature_family"] == "local_operating")
    ].iloc[0]
    direct_row = summary[
        (summary["variant"] == "direct")
        & (summary["feature_family"] == "full_topology_electrical")
    ].iloc[0]
    out_summary = {
        "rows": int(len(summary)),
        "raw_rows": int(len(raw)),
        "runs_per_variant": int(len(config["evaluation_seeds"])),
        "full_residual_missed_mean": float(full_row["missed_violations_mean"]),
        "local_residual_missed_mean": float(local_row["missed_violations_mean"]),
        "direct_full_missed_mean": float(direct_row["missed_violations_mean"]),
        "full_vs_local_missed_delta": float(
            full_row["missed_violations_mean"] - local_row["missed_violations_mean"]
        ),
        "full_vs_direct_missed_delta": float(
            full_row["missed_violations_mean"] - direct_row["missed_violations_mean"]
        ),
        "full_residual_rmse_mean": float(full_row["rmse_mean"]),
        "local_residual_rmse_mean": float(local_row["rmse_mean"]),
        "direct_full_rmse_mean": float(direct_row["rmse_mean"]),
    }

    raw.to_csv(RESULTS / "feature_residual_ablation_raw.csv", index=False)
    summary.to_csv(RESULTS / "feature_residual_ablation.csv", index=False)
    format_markdown(summary, RESULTS / "feature_residual_ablation.md")
    (RESULTS / "feature_residual_ablation_summary.json").write_text(
        json.dumps(out_summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(out_summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
