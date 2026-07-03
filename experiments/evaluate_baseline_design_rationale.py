"""Design-rationale baselines for the LinDistFlow-quantile note."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from evaluate_models import (
    FEATURES,
    LOWER_LIMIT,
    UPPER_LIMIT,
    assign_random_split,
    apply_split,
    finite_sample_quantile,
    format_markdown,
    load_config,
    prepare_data,
    scenario_table,
)


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"


def metrics(method: str, y: np.ndarray, pred: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict:
    violation = (y < LOWER_LIMIT) | (y > UPPER_LIMIT)
    risk = (lower < LOWER_LIMIT) | (upper > UPPER_LIMIT)
    tp = int(np.sum(risk & violation))
    fp = int(np.sum(risk & ~violation))
    fn = int(np.sum(~risk & violation))
    tn = int(np.sum(~risk & ~violation))
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    false_alarm = fp / (fp + tn) if fp + tn else 0.0
    return {
        "method": method,
        "rmse": float(np.sqrt(np.mean((y - pred) ** 2))),
        "coverage": float(np.mean((y >= lower) & (y <= upper))),
        "avg_width": float(np.mean(upper - lower)),
        "precision": precision,
        "recall": recall,
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
    calib = data[data["split"] == "calib"].copy()
    test = data[data["split"] == "test"].copy()
    y_test = test["vm_pu"].to_numpy(dtype=float)

    rows = []

    flat_calib = np.ones(len(calib))
    flat_q = finite_sample_quantile(np.abs(calib["vm_pu"].to_numpy(dtype=float) - flat_calib), 0.1)
    flat_pred = np.ones(len(test))
    rows.append(metrics("Flat 1.0 p.u. + global quantile", y_test, flat_pred, flat_pred - flat_q, flat_pred + flat_q))

    envelope = (
        calib.groupby(["feeder", "bus"])
        .agg(bus_min=("vm_pu", "min"), bus_max=("vm_pu", "max"))
        .reset_index()
    )
    env_test = test.merge(envelope, on=["feeder", "bus"], how="left")
    global_min = float(calib["vm_pu"].min())
    global_max = float(calib["vm_pu"].max())
    env_lower = env_test["bus_min"].fillna(global_min).to_numpy(dtype=float)
    env_upper = env_test["bus_max"].fillna(global_max).to_numpy(dtype=float)
    env_pred = 0.5 * (env_lower + env_upper)
    rows.append(metrics("Historical bus envelope", y_test, env_pred, env_lower, env_upper))

    sensitivity_features = ["bus_norm", "load_p_mw", "load_q_mvar", "pv_p_mw", "net_p_mw", "load_scale", "pv_penetration"]
    sens = make_pipeline(StandardScaler(), LinearRegression())
    sens.fit(train[sensitivity_features], train["vm_pu"])
    sens_calib = sens.predict(calib[sensitivity_features])
    sens_q = finite_sample_quantile(np.abs(calib["vm_pu"].to_numpy(dtype=float) - sens_calib), 0.1)
    sens_pred = sens.predict(test[sensitivity_features])
    rows.append(metrics("Linear sensitivity regression + global quantile", y_test, sens_pred, sens_pred - sens_q, sens_pred + sens_q))

    ldf_calib = calib["ldf_vm_pu"].to_numpy(dtype=float)
    ldf_q = finite_sample_quantile(np.abs(calib["vm_pu"].to_numpy(dtype=float) - ldf_calib), 0.1)
    ldf_pred = test["ldf_vm_pu"].to_numpy(dtype=float)
    rows.append(metrics("LinDistFlow + global quantile", y_test, ldf_pred, ldf_pred - ldf_q, ldf_pred + ldf_q))

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "baseline_design_rationale_metrics.csv", index=False)
    format_markdown(out, RESULTS / "baseline_design_rationale_metrics.md")
    summary = {
        "seed": 7,
        "rows": int(len(out)),
        "methods": out["method"].tolist(),
        "lin_dist_flow_width": float(out.loc[out["method"] == "LinDistFlow + global quantile", "avg_width"].iloc[0]),
    }
    (RESULTS / "baseline_design_rationale_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
