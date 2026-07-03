"""Evaluate the OAJPE-only LinDistFlow plus global-quantile baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from evaluate_models import (
    RESULTS,
    apply_split,
    assign_random_split,
    conformal_by_group,
    interval_metrics,
    prepare_data,
    risk_from_interval,
    scenario_metrics,
    scenario_table,
    screening_metrics,
    voltage_metrics,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config = json.loads((ROOT / "experiments" / "experiment_config.json").read_text(encoding="utf-8"))
    data = prepare_data(config)
    data = data[data["feeder"].isin(config["main_feeders"])].copy()
    scenarios = scenario_table(data)

    rows = []
    raw_frames = []
    seeds = config["evaluation_seeds"]
    representative_seed = int(config.get("representative_seed", seeds[0]))
    for seed in seeds:
        split_table = assign_random_split(scenarios, int(seed))
        frame = apply_split(data, split_table)
        calib = frame[frame["split"] == "calib"].copy()
        test = frame[frame["split"] == "test"].copy()
        pred_calib = calib["ldf_vm_pu"].to_numpy(dtype=float)
        pred_test = test["ldf_vm_pu"].to_numpy(dtype=float)
        y_test = test["vm_pu"].to_numpy(dtype=float)
        lower, upper, q_used, fam = conformal_by_group(
            calib,
            test,
            pred_calib,
            pred_test,
            group_cols=[],
            alpha=float(config["primary_alpha"]),
            min_group=int(config["min_group_samples"]),
            shrinkage=True,
        )
        risk = risk_from_interval(lower, upper)
        scenario = scenario_metrics(test, risk)
        row = {
            "split_name": "random_interpolation",
            "seed": int(seed),
            "method": "LinDistFlow physical backbone + global quantile",
            "conformal_variant": "global",
            **voltage_metrics(y_test, pred_test),
            **interval_metrics(y_test, lower, upper),
            **screening_metrics(y_test, risk),
            **scenario,
            "global_q": float(q_used[0]) if len(q_used) else 0.0,
            "calibration_samples": int(fam["calibration_samples"].iloc[0]),
            "test_bus_rows": int(len(test)),
            "test_scenarios": int(test[["feeder", "scenario_id"]].drop_duplicates().shape[0]),
        }
        rows.append(row)
        if int(seed) == representative_seed:
            raw = test[["feeder", "scenario_id", "bus", "vm_pu", "voltage_violation", "pv_bin", "load_bin"]].copy()
            raw["method"] = row["method"]
            raw["conformal_variant"] = "global"
            raw["y_pred"] = pred_test
            raw["lower"] = lower
            raw["upper"] = upper
            raw["q_used"] = q_used
            raw["risk_flag"] = risk
            raw_frames.append(raw)

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "oajpe_lindistflow_quantile_metrics.csv", index=False)
    mean = out.select_dtypes("number").mean(numeric_only=True).to_dict()
    summary = {
        "method": "LinDistFlow physical backbone + global quantile",
        "seeds": [int(seed) for seed in seeds],
        "representative_seed": representative_seed,
        "representative": out[out["seed"] == representative_seed].iloc[0].to_dict(),
        "mean_numeric": {key: float(value) for key, value in mean.items()},
        "scope": "OAJPE baseline only; no residual learner, no topology/PV/loading conditioning, no VoltGuard interval module.",
    }
    (RESULTS / "oajpe_lindistflow_quantile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    md = out.round(6).to_markdown(index=False)
    (RESULTS / "oajpe_lindistflow_quantile_metrics.md").write_text(md + "\n", encoding="utf-8")
    if raw_frames:
        pd.concat(raw_frames, ignore_index=True).to_csv(
            RESULTS / "oajpe_lindistflow_quantile_raw_seed7.csv", index=False
        )
    print(json.dumps({"status": "wrote", "rows": len(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
