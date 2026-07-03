"""Forecast-noise robustness audit for VoltGuard.

The manuscript describes VoltGuard as an operating-time screening layer fed by
load/PV/EV forecasts or pseudo-measurements. This audit perturbs only those
pre-dispatch input features, recomputes the LinDistFlow backbone from the
noisy injections, and keeps the AC voltage labels fixed. It therefore tests
how the submitted screening claim degrades when forecasts differ from realized
operating conditions.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor

from evaluate_models import (
    FEATURES,
    Prediction,
    add_lindistflow_backbone,
    assign_random_split,
    conformal_by_group,
    interval_metrics,
    load_config,
    load_network,
    prepare_data,
    risk_from_interval,
    scenario_metrics,
    scenario_table,
    screening_metrics,
    voltage_metrics,
)


RESULTS = Path("VoltGuard-CPGNN/experiments/results")
NOISE_LEVELS = [0.0, 0.05, 0.10, 0.20]


def fit_screening_predictions(train: pd.DataFrame, calib: pd.DataFrame, test: pd.DataFrame, seed: int) -> dict[str, Prediction]:
    feature_cols = FEATURES + ["feeder_code"]
    x_train = train[feature_cols].to_numpy()
    y_train = train["vm_pu"].to_numpy()
    x_calib = calib[feature_cols].to_numpy()
    x_test = test[feature_cols].to_numpy()
    ldf_train = train["ldf_vm_pu"].to_numpy()
    ldf_calib = calib["ldf_vm_pu"].to_numpy()
    ldf_test = test["ldf_vm_pu"].to_numpy()

    hgb = HistGradientBoostingRegressor(max_iter=220, learning_rate=0.06, max_leaf_nodes=31, random_state=seed)
    hgb.fit(x_train, y_train)
    residual = ExtraTreesRegressor(
        n_estimators=200,
        random_state=seed + 100,
        min_samples_leaf=3,
        n_jobs=-1,
    )
    residual.fit(x_train, y_train - ldf_train)
    return {
        "Boosting point + global conformal": Prediction(
            "Boosting point + global conformal",
            hgb.predict(x_calib),
            hgb.predict(x_test),
        ),
        "VoltGuard topology-aware residual": Prediction(
            "VoltGuard topology-aware residual",
            ldf_calib + residual.predict(x_calib),
            ldf_test + residual.predict(x_test),
        ),
    }


def feeder_neighbors(feeder: str) -> dict[int, list[int]]:
    import pandapower.networks as pn

    net = load_network(pn, feeder)
    neighbors: dict[int, list[int]] = {int(bus): [] for bus in net.bus.index}
    for _, line in net.line.iterrows():
        if not bool(line.get("in_service", True)):
            continue
        i = int(line.from_bus)
        j = int(line.to_bus)
        neighbors.setdefault(i, []).append(j)
        neighbors.setdefault(j, []).append(i)
    return neighbors


def recompute_neighbor_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for feeder, feeder_frame in out.groupby("feeder"):
        neighbors = feeder_neighbors(str(feeder))
        for (_, scenario_id), group in feeder_frame.groupby(["feeder", "scenario_id"]):
            by_bus = group.set_index("bus")
            for idx, row in group.iterrows():
                nbs = neighbors.get(int(row["bus"]), [])
                existing = [bus for bus in nbs if bus in by_bus.index]
                out.loc[idx, "neighbor_load_p_mw"] = float(by_bus.loc[existing, "load_p_mw"].sum()) if existing else 0.0
                out.loc[idx, "neighbor_pv_p_mw"] = float(by_bus.loc[existing, "pv_p_mw"].sum()) if existing else 0.0
                out.loc[idx, "neighbor_net_p_mw"] = float(by_bus.loc[existing, "net_p_mw"].sum()) if existing else 0.0
    return out


def apply_forecast_noise(frame: pd.DataFrame, sigma: float, seed: int) -> pd.DataFrame:
    if sigma == 0.0:
        return frame.copy()
    rng = np.random.default_rng(seed)
    out = frame.copy()
    scenario_index = out[["feeder", "scenario_id"]].drop_duplicates().reset_index(drop=True)
    scenario_errors = {}
    for _, row in scenario_index.iterrows():
        key = (str(row["feeder"]), int(row["scenario_id"]))
        scenario_errors[key] = {
            "load_scale": float(np.clip(rng.normal(0.0, sigma), -0.45, 0.45)),
            "pv_penetration": float(np.clip(rng.normal(0.0, sigma), -0.45, 0.45)),
            "ev_scale": float(np.clip(rng.normal(0.0, sigma), -0.45, 0.45)),
        }

    load_error = np.clip(rng.normal(0.0, sigma, len(out)), -0.45, 0.45)
    pv_error = np.clip(rng.normal(0.0, sigma, len(out)), -0.45, 0.45)
    out["load_p_mw"] = np.maximum(0.0, out["load_p_mw"].to_numpy() * (1.0 + load_error))
    out["load_q_mvar"] = np.maximum(0.0, out["load_q_mvar"].to_numpy() * (1.0 + load_error))
    out["pv_p_mw"] = np.maximum(0.0, out["pv_p_mw"].to_numpy() * (1.0 + pv_error))
    out["net_p_mw"] = out["load_p_mw"] - out["pv_p_mw"]

    for idx, row in out.iterrows():
        errors = scenario_errors[(str(row["feeder"]), int(row["scenario_id"]))]
        out.loc[idx, "load_scale"] = max(0.0, float(row["load_scale"]) * (1.0 + errors["load_scale"]))
        out.loc[idx, "pv_penetration"] = max(0.0, float(row["pv_penetration"]) * (1.0 + errors["pv_penetration"]))
        out.loc[idx, "ev_scale"] = max(0.0, float(row["ev_scale"]) * (1.0 + errors["ev_scale"]))

    out = recompute_neighbor_features(out)
    out = add_lindistflow_backbone(out.drop(columns=["ldf_u_pu", "ldf_vm_pu"], errors="ignore"))
    return out


def evaluate_one(noisy: pd.DataFrame, seed: int, config: dict, noise_sigma: float) -> list[dict]:
    scenarios = scenario_table(noisy)
    split_table = assign_random_split(scenarios, seed)
    frame = noisy.merge(split_table, on=["feeder", "scenario_id"], how="inner")
    train = frame[frame["split"] == "train"].copy()
    calib = frame[frame["split"] == "calib"].copy()
    test = frame[frame["split"] == "test"].copy()
    preds = fit_screening_predictions(train, calib, test, seed)
    rows = []
    for method, variant, group_cols in [
        ("Boosting point + global conformal", "global", []),
        ("VoltGuard topology-aware residual", "global", []),
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"]),
    ]:
        pred = preds[method]
        lower, upper, _, _ = conformal_by_group(
            calib,
            test,
            pred.pred_calib,
            pred.pred_test,
            group_cols=group_cols,
            alpha=float(config.get("alpha", 0.1)),
            min_group=int(config["min_group_samples"]),
            shrinkage=True,
        )
        risk = risk_from_interval(lower, upper)
        row = {
            "seed": int(seed),
            "forecast_noise_sigma": float(noise_sigma),
            "method": method,
            "conformal_variant": variant,
            "train_rows": int(len(train)),
            "calib_rows": int(len(calib)),
            "test_rows": int(len(test)),
            **voltage_metrics(test["vm_pu"].to_numpy(), pred.pred_test),
            **interval_metrics(test["vm_pu"].to_numpy(), lower, upper),
            **screening_metrics(test["vm_pu"].to_numpy(), risk),
            **scenario_metrics(test, risk),
        }
        rows.append(row)
    return rows


def main() -> int:
    config = load_config()
    base = prepare_data(config)
    base = base[base["feeder"].isin(config["main_feeders"])].copy()
    raw_rows = []
    audit_seeds = [int(config["representative_seed"])]
    for sigma in NOISE_LEVELS:
        for seed in audit_seeds:
            noisy = apply_forecast_noise(base, float(sigma), seed=10_000 + int(seed) * 100 + int(sigma * 1000))
            raw_rows.extend(evaluate_one(noisy, int(seed), config, float(sigma)))

    raw = pd.DataFrame(raw_rows)
    raw.to_csv(RESULTS / "forecast_noise_robustness_raw.csv", index=False)
    metric_cols = [
        "rmse",
        "coverage",
        "avg_width",
        "recall",
        "false_alarm_rate",
        "missed_violations",
        "scenario_recall",
        "scenario_false_alarm_rate",
        "missed_risky_scenarios",
    ]
    rows = []
    for key, group in raw.groupby(["method", "conformal_variant", "forecast_noise_sigma"], dropna=False):
        method, variant, sigma = key
        row = {
            "method": method,
            "conformal_variant": variant,
            "forecast_noise_sigma": float(sigma),
            "runs": int(len(group)),
        }
        for col in metric_cols:
            values = group[col].astype(float)
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        rows.append(row)
    table = pd.DataFrame(rows).sort_values(["method", "conformal_variant", "forecast_noise_sigma"])
    table.to_csv(RESULTS / "forecast_noise_robustness_metrics.csv", index=False)
    display_cols = [
        "method",
        "conformal_variant",
        "forecast_noise_sigma",
        "rmse_mean",
        "coverage_mean",
        "avg_width_mean",
        "recall_mean",
        "false_alarm_rate_mean",
        "missed_violations_mean",
        "scenario_recall_mean",
        "missed_risky_scenarios_mean",
    ]
    (RESULTS / "forecast_noise_robustness_metrics.md").write_text(
        table[display_cols].round(5).to_markdown(index=False) + "\n",
        encoding="utf-8",
    )

    primary_clean = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["conformal_variant"] == "topology_pv_loading_conditioned")
        & (table["forecast_noise_sigma"] == 0.0)
    ].iloc[0]
    primary_noisy = table[
        (table["method"] == "VoltGuard topology-aware residual")
        & (table["conformal_variant"] == "topology_pv_loading_conditioned")
        & (table["forecast_noise_sigma"] == 0.10)
    ].iloc[0]
    summary = {
        "rows": int(len(table)),
        "raw_rows": int(len(raw)),
        "audit_seeds": audit_seeds,
        "noise_levels": NOISE_LEVELS,
        "primary_clean_rmse": float(primary_clean["rmse_mean"]),
        "primary_clean_coverage": float(primary_clean["coverage_mean"]),
        "primary_clean_recall": float(primary_clean["recall_mean"]),
        "primary_10pct_rmse": float(primary_noisy["rmse_mean"]),
        "primary_10pct_coverage": float(primary_noisy["coverage_mean"]),
        "primary_10pct_recall": float(primary_noisy["recall_mean"]),
        "primary_10pct_missed": float(primary_noisy["missed_violations_mean"]),
        "primary_10pct_scenario_recall": float(primary_noisy["scenario_recall_mean"]),
    }
    (RESULTS / "forecast_noise_robustness_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
