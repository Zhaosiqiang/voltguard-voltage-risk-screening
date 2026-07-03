"""Configured evaluation pipeline for VoltGuard.

This script implements the tightened paper claim:
physics-informed topology-aware residual learning plus conformal calibration
for voltage-risk screening. Neural graph residual learning is retained only as
a representative ablation, not as the selected main estimator.
"""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path("VoltGuard-CPGNN")
CONFIG_PATH = ROOT / "experiments" / "experiment_config.json"
RESULTS = ROOT / "experiments" / "results"
LOWER_LIMIT = 0.95
UPPER_LIMIT = 1.05


FEATURES = [
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
]


@dataclass
class Prediction:
    method: str
    pred_calib: np.ndarray
    pred_test: np.ndarray


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def format_markdown(df: pd.DataFrame, path: Path, digits: int = 5) -> None:
    path.write_text(df.round(digits).to_markdown(index=False) + "\n", encoding="utf-8")


def feeder_branch_model(feeder: str) -> tuple[list[dict], float, int]:
    import pandapower.networks as pn

    net = load_network(pn, feeder)
    slack_bus = int(net.ext_grid.bus.iloc[0]) if len(net.ext_grid) else int(net.bus.index.min())
    sn_mva = float(net.sn_mva)
    neighbors: dict[int, list[tuple[int, float, float]]] = {int(bus): [] for bus in net.bus.index}
    for _, line in net.line.iterrows():
        if not bool(line.get("in_service", True)):
            continue
        from_bus = int(line.from_bus)
        to_bus = int(line.to_bus)
        length = float(line.length_km)
        r_ohm = float(line.r_ohm_per_km) * length
        x_ohm = float(line.x_ohm_per_km) * length
        base_kv = float(net.bus.loc[from_bus, "vn_kv"])
        z_base = base_kv * base_kv / sn_mva
        r_pu = r_ohm / z_base
        x_pu = x_ohm / z_base
        neighbors.setdefault(from_bus, []).append((to_bus, r_pu, x_pu))
        neighbors.setdefault(to_bus, []).append((from_bus, r_pu, x_pu))

    parent = {slack_bus: None}
    queue: deque[int] = deque([slack_bus])
    branches = []
    while queue:
        bus = queue.popleft()
        for nb, r_pu, x_pu in neighbors.get(bus, []):
            if nb in parent:
                continue
            parent[nb] = bus
            queue.append(nb)
            branches.append({"from_bus": bus, "to_bus": nb, "r_pu": r_pu, "x_pu": x_pu})
    return branches, sn_mva, slack_bus


def downstream_sets(branches: list[dict], buses: list[int]) -> dict[int, set[int]]:
    children: dict[int, list[int]] = {bus: [] for bus in buses}
    for branch in branches:
        children.setdefault(int(branch["from_bus"]), []).append(int(branch["to_bus"]))
    cache: dict[int, set[int]] = {}

    def collect(bus: int) -> set[int]:
        if bus in cache:
            return cache[bus]
        found = {bus}
        for child in children.get(bus, []):
            found |= collect(child)
        cache[bus] = found
        return found

    for bus in buses:
        collect(bus)
    return cache


def add_lindistflow_backbone(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    out["ldf_u_pu"] = np.nan
    out["ldf_vm_pu"] = np.nan
    for feeder, feeder_frame in out.groupby("feeder"):
        branches, sn_mva, slack_bus = feeder_branch_model(str(feeder))
        buses = sorted(int(bus) for bus in feeder_frame["bus"].unique())
        downstream = downstream_sets(branches, buses)
        children: dict[int, list[dict]] = {bus: [] for bus in buses}
        for branch in branches:
            children.setdefault(int(branch["from_bus"]), []).append(branch)

        for (_, scenario_id), group in feeder_frame.groupby(["feeder", "scenario_id"]):
            scenario = group.set_index("bus")
            u_values = {slack_bus: 1.0}
            queue: deque[int] = deque([slack_bus])
            while queue:
                bus = queue.popleft()
                for branch in children.get(bus, []):
                    child = int(branch["to_bus"])
                    subtree = list(downstream[child])
                    p_pu = float(scenario.loc[subtree, "net_p_mw"].sum() / sn_mva)
                    q_pu = float(scenario.loc[subtree, "load_q_mvar"].sum() / sn_mva)
                    u_values[child] = u_values[bus] - 2.0 * (
                        float(branch["r_pu"]) * p_pu + float(branch["x_pu"]) * q_pu
                    )
                    queue.append(child)
            idx = group.index
            u_array = group["bus"].map(lambda bus: u_values.get(int(bus), 1.0)).to_numpy(dtype=float)
            out.loc[idx, "ldf_u_pu"] = u_array
            out.loc[idx, "ldf_vm_pu"] = np.sqrt(np.maximum(u_array, 1e-6))
    return out


def prepare_data(config: dict) -> pd.DataFrame:
    data = pd.read_csv(RESULTS / "bus_voltage_labels.csv")
    data["feeder"] = data["feeder"].astype(str)
    data = data[data["feeder"].isin(config["main_feeders"] + config["supplementary_feeders"])].copy()
    data = add_lindistflow_backbone(data)
    feeder_categories = sorted(data["feeder"].unique(), key=lambda value: int(value))
    data["feeder_code"] = pd.Categorical(data["feeder"], categories=feeder_categories).codes
    data["pv_bin"] = data["pv_penetration"].round(2).astype(str)
    data["load_bin"] = np.where(data["load_scale"] >= data["load_scale"].median(), "high_load", "low_load")
    data["scenario_key"] = data["feeder"] + "_" + data["scenario_id"].astype(str)
    return data


def scenario_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["feeder", "scenario_id"])
        .agg(
            pv_penetration=("pv_penetration", "first"),
            load_scale=("load_scale", "first"),
            min_vm=("vm_pu", "min"),
            max_vm=("vm_pu", "max"),
            violation_any=("voltage_violation", "max"),
        )
        .reset_index()
    )


def assign_random_split(scenarios: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for feeder, group in scenarios.groupby("feeder"):
        ids = group["scenario_id"].to_numpy()
        rng.shuffle(ids)
        n = len(ids)
        train_end = int(n * 0.6)
        calib_end = int(n * 0.8)
        for sid in ids[:train_end]:
            rows.append({"feeder": feeder, "scenario_id": int(sid), "split": "train"})
        for sid in ids[train_end:calib_end]:
            rows.append({"feeder": feeder, "scenario_id": int(sid), "split": "calib"})
        for sid in ids[calib_end:]:
            rows.append({"feeder": feeder, "scenario_id": int(sid), "split": "test"})
    return pd.DataFrame(rows)


def assign_time_block_split(scenarios: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feeder, group in scenarios.groupby("feeder"):
        ids = np.sort(group["scenario_id"].to_numpy())
        n = len(ids)
        train_end = int(n * 0.6)
        calib_end = int(n * 0.8)
        for sid in ids[:train_end]:
            rows.append({"feeder": feeder, "scenario_id": int(sid), "split": "train"})
        for sid in ids[train_end:calib_end]:
            rows.append({"feeder": feeder, "scenario_id": int(sid), "split": "calib"})
        for sid in ids[calib_end:]:
            rows.append({"feeder": feeder, "scenario_id": int(sid), "split": "test"})
    return pd.DataFrame(rows)


def assign_pv_shift_split(scenarios: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in scenarios.iterrows():
        pv = float(row["pv_penetration"])
        if pv <= 0.4:
            split = "train"
        elif pv <= 0.6:
            split = "calib"
        else:
            split = "test"
        rows.append({"feeder": row["feeder"], "scenario_id": int(row["scenario_id"]), "split": split})
    return pd.DataFrame(rows)


def assign_topology_heldout_split(scenarios: pd.DataFrame, main_feeders: list[str], seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    source, target = main_feeders[0], main_feeders[1]
    rows = []
    for sid in scenarios[scenarios["feeder"] == source]["scenario_id"].to_numpy():
        rows.append({"feeder": source, "scenario_id": int(sid), "split": "train"})
    target_ids = scenarios[scenarios["feeder"] == target]["scenario_id"].to_numpy()
    rng.shuffle(target_ids)
    calib_end = max(1, int(len(target_ids) * 0.4))
    for sid in target_ids[:calib_end]:
        rows.append({"feeder": target, "scenario_id": int(sid), "split": "calib"})
    for sid in target_ids[calib_end:]:
        rows.append({"feeder": target, "scenario_id": int(sid), "split": "test"})
    return pd.DataFrame(rows)


def apply_split(df: pd.DataFrame, split_table: pd.DataFrame) -> pd.DataFrame:
    out = df.merge(split_table, on=["feeder", "scenario_id"], how="left")
    return out[out["split"].notna()].copy()


def finite_sample_quantile(scores: np.ndarray, alpha: float) -> float:
    if len(scores) == 0:
        return 0.0
    q_level = min(1.0, np.ceil((len(scores) + 1) * (1 - alpha)) / len(scores))
    return float(np.quantile(scores, q_level))


def conformal_by_group(
    calib: pd.DataFrame,
    test: pd.DataFrame,
    pred_calib: np.ndarray,
    pred_test: np.ndarray,
    group_cols: list[str],
    alpha: float,
    min_group: int,
    shrinkage: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    scores = np.abs(calib["vm_pu"].to_numpy() - pred_calib)
    global_q = finite_sample_quantile(scores, alpha)
    q_used = np.full(len(test), global_q, dtype=float)
    family_rows = []

    if group_cols:
        calib_tmp = calib[group_cols].copy()
        calib_tmp["score"] = scores
        test_tmp = test[group_cols].copy()
        grouped = calib_tmp.groupby(group_cols, dropna=False)
        for key, group in grouped:
            group_scores = group["score"].to_numpy()
            n = len(group_scores)
            group_q = finite_sample_quantile(group_scores, alpha)
            if shrinkage:
                weight = n / (n + min_group)
                q = weight * group_q + (1.0 - weight) * global_q
            else:
                q = group_q if n >= max(10, min_group // 5) else global_q
            if not isinstance(key, tuple):
                key = (key,)
            mask = np.ones(len(test_tmp), dtype=bool)
            for col, value in zip(group_cols, key, strict=True):
                mask &= test_tmp[col].to_numpy() == value
            q_used[mask] = q
            family_rows.append(
                {
                    "family": "|".join(f"{col}={value}" for col, value in zip(group_cols, key, strict=True)),
                    "calibration_samples": n,
                    "group_q": group_q,
                    "q_used": q,
                    "shrinkage": shrinkage,
                }
            )
    else:
        family_rows.append(
            {
                "family": "__global__",
                "calibration_samples": len(scores),
                "group_q": global_q,
                "q_used": global_q,
                "shrinkage": shrinkage,
            }
        )

    lower = pred_test - q_used
    upper = pred_test + q_used
    return lower, upper, q_used, pd.DataFrame(family_rows)


def voltage_metrics(y_true: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, pred)),
        "rmse": float(mean_squared_error(y_true, pred) ** 0.5),
        "max_abs_error": float(np.max(np.abs(y_true - pred))),
    }


def interval_metrics(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict[str, float]:
    return {
        "coverage": float(np.mean((y_true >= lower) & (y_true <= upper))),
        "avg_width": float(np.mean(upper - lower)),
    }


def screening_metrics(y_true: np.ndarray, risk: np.ndarray) -> dict[str, float]:
    labels = (y_true < LOWER_LIMIT) | (y_true > UPPER_LIMIT)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels.astype(int),
        risk.astype(int),
        average="binary",
        zero_division=0,
    )
    negatives = ~labels
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_alarm_rate": float(np.mean(risk[negatives])) if np.any(negatives) else 0.0,
        "missed_violations": int(np.sum(labels & ~risk)),
    }


def scenario_metrics(test: pd.DataFrame, risk: np.ndarray) -> dict[str, float]:
    tmp = test[["feeder", "scenario_id", "voltage_violation"]].copy()
    tmp["risk"] = risk
    scen = tmp.groupby(["feeder", "scenario_id"]).agg(
        violation_any=("voltage_violation", "max"),
        risk_any=("risk", "max"),
    )
    labels = scen["violation_any"].astype(bool).to_numpy()
    pred = scen["risk_any"].astype(bool).to_numpy()
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels.astype(int),
        pred.astype(int),
        average="binary",
        zero_division=0,
    )
    negatives = ~labels
    return {
        "scenario_precision": float(precision),
        "scenario_recall": float(recall),
        "scenario_f1": float(f1),
        "scenario_false_alarm_rate": float(np.mean(pred[negatives])) if np.any(negatives) else 0.0,
        "missed_risky_scenarios": int(np.sum(labels & ~pred)),
        "test_scenarios": int(len(scen)),
    }


def risk_from_interval(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    return (lower < LOWER_LIMIT) | (upper > UPPER_LIMIT)


def under_over_from_interval(lower: np.ndarray, upper: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return lower < LOWER_LIMIT, upper > UPPER_LIMIT


def fit_predictions(train: pd.DataFrame, calib: pd.DataFrame, test: pd.DataFrame, seed: int) -> dict[str, Prediction]:
    feature_cols = FEATURES + ["feeder_code"]
    x_train = train[feature_cols].to_numpy()
    y_train = train["vm_pu"].to_numpy()
    x_calib = calib[feature_cols].to_numpy()
    x_test = test[feature_cols].to_numpy()
    ldf_train = train["ldf_vm_pu"].to_numpy()
    ldf_calib = calib["ldf_vm_pu"].to_numpy()
    ldf_test = test["ldf_vm_pu"].to_numpy()

    rf = RandomForestRegressor(n_estimators=120, random_state=seed, min_samples_leaf=4, n_jobs=-1)
    rf.fit(x_train, y_train)

    hgb = HistGradientBoostingRegressor(max_iter=220, learning_rate=0.06, max_leaf_nodes=31, random_state=seed)
    hgb.fit(x_train, y_train)

    residual_train = y_train - ldf_train
    residual_model = ExtraTreesRegressor(
        n_estimators=200,
        random_state=seed + 100,
        min_samples_leaf=3,
        n_jobs=-1,
    )
    residual_model.fit(x_train, residual_train)
    vg_calib = ldf_calib + residual_model.predict(x_calib)
    vg_test = ldf_test + residual_model.predict(x_test)

    return {
        "LinDistFlow physical backbone": Prediction("LinDistFlow physical backbone", ldf_calib, ldf_test),
        "Random forest": Prediction("Random forest", rf.predict(x_calib), rf.predict(x_test)),
        "Gradient boosting": Prediction("Gradient boosting", hgb.predict(x_calib), hgb.predict(x_test)),
        "Boosting point + global conformal": Prediction(
            "Boosting point + global conformal", hgb.predict(x_calib), hgb.predict(x_test)
        ),
        "VoltGuard topology-aware residual": Prediction(
            "VoltGuard topology-aware residual", vg_calib, vg_test
        ),
    }


def load_network(pn, feeder: str):
    if str(feeder) == "69":
        import pandapower as pp

        from ieee69_feeder import create_ieee69

        return create_ieee69(pp)
    mapping = {"33": "case33bw", "118": "case118"}
    return getattr(pn, mapping[str(feeder)])()


def feeder_adjacency(feeder: str, buses: list[int]) -> np.ndarray:
    import pandapower.networks as pn

    net = load_network(pn, feeder)
    bus_to_pos = {bus: i for i, bus in enumerate(buses)}
    adj = np.eye(len(buses), dtype=np.float32)
    for _, line in net.line.iterrows():
        if not bool(line.get("in_service", True)):
            continue
        i = bus_to_pos.get(int(line.from_bus))
        j = bus_to_pos.get(int(line.to_bus))
        if i is None or j is None:
            continue
        adj[i, j] = 1.0
        adj[j, i] = 1.0
    degree = np.maximum(adj.sum(axis=1, keepdims=True), 1.0)
    return adj / degree


def scenario_tensor(frame: pd.DataFrame, feature_cols: list[str], target_col: str):
    scenarios, targets = [], []
    buses = sorted(int(b) for b in frame["bus"].unique())
    for _, group in frame.groupby("scenario_id"):
        group = group.sort_values("bus")
        scenarios.append(group[feature_cols].to_numpy(dtype=np.float32))
        targets.append(group[target_col].to_numpy(dtype=np.float32))
    return np.stack(scenarios), np.stack(targets), buses


def train_neural_graph_ablation(
    train: pd.DataFrame,
    calib: pd.DataFrame,
    test: pd.DataFrame,
    feature_cols: list[str],
) -> Prediction | None:
    try:
        import torch
        import torch.nn as nn
    except Exception:
        return None

    torch.manual_seed(17)

    class GraphResidualNet(nn.Module):
        def __init__(self, in_dim: int, hidden_dim: int = 40, layers: int = 2):
            super().__init__()
            self.input = nn.Linear(in_dim, hidden_dim)
            self.self_layers = nn.ModuleList([nn.Linear(hidden_dim, hidden_dim) for _ in range(layers)])
            self.msg_layers = nn.ModuleList([nn.Linear(hidden_dim, hidden_dim) for _ in range(layers)])
            self.output = nn.Linear(hidden_dim, 1)

        def forward(self, x, adj):
            h = torch.relu(self.input(x))
            for self_layer, msg_layer in zip(self.self_layers, self.msg_layers, strict=True):
                msg = torch.einsum("ij,bjf->bif", adj, h)
                h = torch.relu(self_layer(h) + msg_layer(msg))
            return self.output(h).squeeze(-1)

    train = train.copy()
    calib = calib.copy()
    test = test.copy()
    train["base_pred"] = train["ldf_vm_pu"].to_numpy()
    calib["base_pred"] = calib["ldf_vm_pu"].to_numpy()
    test["base_pred"] = test["ldf_vm_pu"].to_numpy()
    train["base_residual"] = train["vm_pu"].to_numpy() - train["base_pred"].to_numpy()

    calib_pred = np.zeros(len(calib), dtype=float)
    test_pred = np.zeros(len(test), dtype=float)
    for feeder in sorted(train["feeder"].unique(), key=lambda value: int(value)):
        tr = train[train["feeder"] == feeder].copy()
        ca = calib[calib["feeder"] == feeder].copy()
        te = test[test["feeder"] == feeder].copy()
        if ca.empty or te.empty:
            continue
        x_tr, y_tr, buses = scenario_tensor(tr, feature_cols, "base_residual")
        x_ca, _, _ = scenario_tensor(ca, feature_cols, "vm_pu")
        x_te, _, _ = scenario_tensor(te, feature_cols, "vm_pu")
        mean = x_tr.reshape(-1, x_tr.shape[-1]).mean(axis=0, keepdims=True)
        std = x_tr.reshape(-1, x_tr.shape[-1]).std(axis=0, keepdims=True) + 1e-6
        x_tr, x_ca, x_te = (x_tr - mean) / std, (x_ca - mean) / std, (x_te - mean) / std

        model = GraphResidualNet(in_dim=x_tr.shape[-1])
        opt = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=1e-4)
        adj = torch.tensor(feeder_adjacency(feeder, buses), dtype=torch.float32)
        x_tensor = torch.tensor(x_tr, dtype=torch.float32)
        y_tensor = torch.tensor(y_tr, dtype=torch.float32)
        best_loss, patience = float("inf"), 0
        for _ in range(180):
            opt.zero_grad()
            loss = torch.mean((model(x_tensor, adj) - y_tensor) ** 2)
            loss.backward()
            opt.step()
            value = float(loss.detach())
            if value + 1e-8 < best_loss:
                best_loss, patience = value, 0
            else:
                patience += 1
            if patience > 25:
                break
        model.eval()
        with torch.no_grad():
            ca_res = model(torch.tensor(x_ca, dtype=torch.float32), adj).numpy().reshape(-1)
            te_res = model(torch.tensor(x_te, dtype=torch.float32), adj).numpy().reshape(-1)
        ca_sorted = ca.sort_values(["scenario_id", "bus"])
        te_sorted = te.sort_values(["scenario_id", "bus"])
        ca_values = ca_sorted["base_pred"].to_numpy() + ca_res
        te_values = te_sorted["base_pred"].to_numpy() + te_res
        calib_pred[calib.index.get_indexer(ca_sorted.index)] = ca_values
        test_pred[test.index.get_indexer(te_sorted.index)] = te_values

    return Prediction("Neural graph residual ablation", calib_pred, test_pred)


def aggregation(rows: list[dict], group_cols: list[str], metric_cols: Iterable[str]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    agg_rows = []
    for key, group in df.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key, strict=True))
        for col in metric_cols:
            values = group[col].astype(float)
            row[f"{col}_mean"] = float(values.mean())
            row[f"{col}_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            row[f"{col}_ci95"] = float(1.96 * row[f"{col}_std"] / np.sqrt(max(1, len(values))))
        row["runs"] = int(len(group))
        agg_rows.append(row)
    return pd.DataFrame(agg_rows)


def scenario_level_frame(test: pd.DataFrame, risk: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> pd.DataFrame:
    tmp = test[["feeder", "scenario_id", "pv_p_mw", "load_p_mw", "voltage_violation"]].copy()
    tmp["risk"] = risk
    tmp["under_risk"] = lower < LOWER_LIMIT
    tmp["over_risk"] = upper > UPPER_LIMIT
    return (
        tmp.groupby(["feeder", "scenario_id"])
        .agg(
            available_pv_mw=("pv_p_mw", "sum"),
            load_mw=("load_p_mw", "sum"),
            violation_any=("voltage_violation", "max"),
            risk_any=("risk", "max"),
            under_risk_any=("under_risk", "max"),
            over_risk_any=("over_risk", "max"),
        )
        .reset_index()
    )


def operating_value_from_risk(test: pd.DataFrame, lower: np.ndarray, upper: np.ndarray, config: dict) -> dict[str, float]:
    risk = risk_from_interval(lower, upper)
    scen = scenario_level_frame(test, risk, lower, upper)
    curtail_fraction = float(config["risk_trigger_action"]["pv_curtail_fraction"])
    relief_fraction = float(config["risk_trigger_action"]["load_relief_fraction"])
    scen["curtailed_pv_mw"] = scen["available_pv_mw"] * scen["over_risk_any"] * curtail_fraction
    scen["accepted_pv_mw"] = scen["available_pv_mw"] - scen["curtailed_pv_mw"]
    scen["relieved_load_mw"] = scen["load_mw"] * scen["under_risk_any"] * relief_fraction
    scen["missed_risky_scenario"] = scen["violation_any"] & ~scen["risk_any"]
    return {
        "available_pv_mw": float(scen["available_pv_mw"].sum()),
        "accepted_pv_mw": float(scen["accepted_pv_mw"].sum()),
        "curtailed_pv_mw": float(scen["curtailed_pv_mw"].sum()),
        "relieved_load_mw": float(scen["relieved_load_mw"].sum()),
        "curtailment_rate": float(scen["curtailed_pv_mw"].sum() / max(1e-9, scen["available_pv_mw"].sum())),
        "flexible_load_relief_scenarios": int(scen["under_risk_any"].sum()),
        "missed_risky_scenarios": int(scen["missed_risky_scenario"].sum()),
    }


def run_one_split(
    data: pd.DataFrame,
    split_table: pd.DataFrame,
    split_name: str,
    seed: int,
    config: dict,
    include_neural: bool,
) -> dict[str, pd.DataFrame | dict]:
    start = time.perf_counter()
    frame = apply_split(data, split_table)
    train = frame[frame["split"] == "train"].copy()
    calib = frame[frame["split"] == "calib"].copy()
    test = frame[frame["split"] == "test"].copy()
    feature_cols = FEATURES + ["feeder_code"]

    fit_start = time.perf_counter()
    predictions = fit_predictions(train, calib, test, seed)
    fit_seconds = time.perf_counter() - fit_start
    if include_neural:
        neural = train_neural_graph_ablation(train, calib, test, feature_cols)
        if neural is not None:
            predictions[neural.method] = neural

    alpha = float(config["primary_alpha"])
    min_group = int(config["min_group_samples"])
    y_test = test["vm_pu"].to_numpy()
    metric_rows, scenario_rows, operating_rows, ablation_rows, family_rows, raw_rows, score_rows = [], [], [], [], [], [], []
    runtime_rows = [
        {
            "split_name": split_name,
            "seed": seed,
            "train_rows": len(train),
            "calib_rows": len(calib),
            "test_rows": len(test),
            "model_fit_seconds": fit_seconds,
        }
    ]

    conformal_variants = {
        "global": ([], True),
        "pv_conditioned": (["pv_bin"], True),
        "topology_conditioned": (["feeder"], True),
        "topology_pv_loading_conditioned": (["feeder", "pv_bin", "load_bin"], True),
        "topology_pv_loading_no_shrinkage": (["feeder", "pv_bin", "load_bin"], False),
    }

    for method, pred in predictions.items():
        is_interval_method = method in {
            "Boosting point + global conformal",
            "VoltGuard topology-aware residual",
            "Neural graph residual ablation",
        }
        if not is_interval_method:
            risk = (pred.pred_test < LOWER_LIMIT) | (pred.pred_test > UPPER_LIMIT)
            base = {
                "split_name": split_name,
                "seed": seed,
                "method": method,
                "conformal_variant": "none",
                **voltage_metrics(y_test, pred.pred_test),
                "coverage": np.nan,
                "avg_width": np.nan,
                **screening_metrics(y_test, risk),
            }
            metric_rows.append(base)
            scenario_rows.append({"split_name": split_name, "seed": seed, "method": method, **scenario_metrics(test, risk)})
            continue

        variants = {"global": conformal_variants["global"]}
        if method == "VoltGuard topology-aware residual":
            variants = conformal_variants
        if method == "Neural graph residual ablation":
            variants = {"topology_conditioned": conformal_variants["topology_conditioned"]}

        for variant_name, (group_cols, shrinkage) in variants.items():
            lower, upper, q_used, fam = conformal_by_group(
                calib,
                test,
                pred.pred_calib,
                pred.pred_test,
                group_cols,
                alpha=alpha,
                min_group=min_group,
                shrinkage=shrinkage,
            )
            risk = risk_from_interval(lower, upper)
            metric = {
                "split_name": split_name,
                "seed": seed,
                "method": method,
                "conformal_variant": variant_name,
                **voltage_metrics(y_test, pred.pred_test),
                **interval_metrics(y_test, lower, upper),
                **screening_metrics(y_test, risk),
            }
            metric_rows.append(metric)
            scenario_rows.append(
                {
                    "split_name": split_name,
                    "seed": seed,
                    "method": method,
                    "conformal_variant": variant_name,
                    **scenario_metrics(test, risk),
                }
            )
            operating_rows.append(
                {
                    "split_name": split_name,
                    "seed": seed,
                    "method": method,
                    "conformal_variant": variant_name,
                    **operating_value_from_risk(test, lower, upper, config),
                }
            )
            ablation_rows.append(metric)

            fam = fam.copy()
            fam["split_name"] = split_name
            fam["seed"] = seed
            fam["method"] = method
            fam["conformal_variant"] = variant_name
            fam_metrics = []
            for _, frow in fam.iterrows():
                if frow["family"] == "__global__":
                    mask = np.ones(len(test), dtype=bool)
                else:
                    mask = np.ones(len(test), dtype=bool)
                    for part in str(frow["family"]).split("|"):
                        col, value = part.split("=", 1)
                        mask &= test[col].astype(str).to_numpy() == value
                if not np.any(mask):
                    continue
                fam_metrics.append(
                    {
                        **frow.to_dict(),
                        "test_samples": int(mask.sum()),
                        **interval_metrics(y_test[mask], lower[mask], upper[mask]),
                        **screening_metrics(y_test[mask], risk[mask]),
                    }
                )
            family_rows.extend(fam_metrics)

            if split_name == "random_interpolation" and seed == int(config["representative_seed"]):
                raw = test[["feeder", "scenario_id", "bus", "vm_pu", "voltage_violation", "pv_bin", "load_bin"]].copy()
                raw["method"] = method
                raw["conformal_variant"] = variant_name
                raw["y_pred"] = pred.pred_test
                raw["lower"] = lower
                raw["upper"] = upper
                raw["q_used"] = q_used
                raw["risk_flag"] = risk
                raw_rows.append(raw)
                scores = calib[["feeder", "scenario_id", "bus", "vm_pu", "pv_bin", "load_bin"]].copy()
                scores["method"] = method
                scores["conformal_variant"] = variant_name
                scores["pred"] = pred.pred_calib
                scores["nonconformity_score"] = np.abs(calib["vm_pu"].to_numpy() - pred.pred_calib)
                score_rows.append(scores)

    runtime_rows[0]["total_seconds"] = time.perf_counter() - start
    frame["split_name"] = split_name
    frame["seed"] = seed
    return {
        "metrics": pd.DataFrame(metric_rows),
        "scenario_metrics": pd.DataFrame(scenario_rows),
        "operating": pd.DataFrame(operating_rows),
        "ablation": pd.DataFrame(ablation_rows),
        "family": pd.DataFrame(family_rows),
        "runtime": pd.DataFrame(runtime_rows),
        "raw": pd.concat(raw_rows, ignore_index=True) if raw_rows else pd.DataFrame(),
        "scores": pd.concat(score_rows, ignore_index=True) if score_rows else pd.DataFrame(),
        "dataset": frame,
    }


def main() -> int:
    config = load_config()
    RESULTS.mkdir(parents=True, exist_ok=True)
    data = prepare_data(config)
    main_data = data[data["feeder"].isin(config["main_feeders"])].copy()
    supplementary_data = data[data["feeder"].isin(config["supplementary_feeders"])].copy()
    scenarios = scenario_table(main_data)

    all_metrics, all_scenario, all_operating, all_ablation, all_family, all_runtime = [], [], [], [], [], []
    raw_frames, score_frames, dataset_frames = [], [], []

    for seed in config["evaluation_seeds"]:
        split_tables = {
            "random_interpolation": assign_random_split(scenarios, seed),
            "synthetic_time_block": assign_time_block_split(scenarios),
            "pv_penetration_shift": assign_pv_shift_split(scenarios),
            "topology_heldout_33_to_69": assign_topology_heldout_split(scenarios, config["main_feeders"], seed),
        }
        for split_name, split_table in split_tables.items():
            result = run_one_split(
                main_data,
                split_table,
                split_name=split_name,
                seed=int(seed),
                config=config,
                include_neural=(split_name == "random_interpolation" and int(seed) == int(config["representative_seed"])),
            )
            all_metrics.append(result["metrics"])
            all_scenario.append(result["scenario_metrics"])
            all_operating.append(result["operating"])
            all_ablation.append(result["ablation"])
            all_family.append(result["family"])
            all_runtime.append(result["runtime"])
            dataset_frames.append(result["dataset"])
            if not result["raw"].empty:
                raw_frames.append(result["raw"])
            if not result["scores"].empty:
                score_frames.append(result["scores"])

    if not supplementary_data.empty:
        supp_scenarios = scenario_table(supplementary_data)
        split_table = assign_random_split(supp_scenarios, int(config["representative_seed"]))
        supp_result = run_one_split(
            supplementary_data,
            split_table,
            split_name="supplementary_118_random",
            seed=int(config["representative_seed"]),
            config=config,
            include_neural=False,
        )
        all_metrics.append(supp_result["metrics"])
        all_scenario.append(supp_result["scenario_metrics"])
        all_operating.append(supp_result["operating"])
        all_ablation.append(supp_result["ablation"])
        all_family.append(supp_result["family"])
        all_runtime.append(supp_result["runtime"])
        dataset_frames.append(supp_result["dataset"])

    metrics = pd.concat(all_metrics, ignore_index=True)
    scenario_metrics_df = pd.concat(all_scenario, ignore_index=True)
    operating = pd.concat(all_operating, ignore_index=True)
    ablation = pd.concat(all_ablation, ignore_index=True)
    family = pd.concat(all_family, ignore_index=True)
    runtime = pd.concat(all_runtime, ignore_index=True)
    datasets = pd.concat(dataset_frames, ignore_index=True)

    metrics.to_csv(RESULTS / "evaluation_metrics_all_runs.csv", index=False)
    scenario_metrics_df.to_csv(RESULTS / "scenario_level_metrics.csv", index=False)
    operating.to_csv(RESULTS / "operating_value_metrics.csv", index=False)
    ablation.to_csv(RESULTS / "conformal_ablation_metrics.csv", index=False)
    family.to_csv(RESULTS / "per_family_conformal_metrics.csv", index=False)
    runtime.to_csv(RESULTS / "runtime_metrics.csv", index=False)
    if raw_frames:
        pd.concat(raw_frames, ignore_index=True).to_csv(RESULTS / "raw_predictions_random_seed7.csv", index=False)
    if score_frames:
        pd.concat(score_frames, ignore_index=True).to_csv(RESULTS / "conformal_scores_random_seed7.csv", index=False)

    dataset_summary = (
        datasets.groupby(["split_name", "seed", "feeder", "split"])
        .agg(
            bus_rows=("bus", "count"),
            scenarios=("scenario_id", "nunique"),
            violations=("voltage_violation", "sum"),
            violation_rate=("voltage_violation", "mean"),
            min_vm=("vm_pu", "min"),
            max_vm=("vm_pu", "max"),
        )
        .reset_index()
    )
    dataset_summary.to_csv(RESULTS / "dataset_split_summary.csv", index=False)
    format_markdown(dataset_summary, RESULTS / "dataset_split_summary.md")

    metric_cols = [
        "mae",
        "rmse",
        "max_abs_error",
        "coverage",
        "avg_width",
        "recall",
        "false_alarm_rate",
        "missed_violations",
    ]
    multi_seed = aggregation(
        metrics[metrics["split_name"] != "supplementary_118_random"].dropna(subset=["coverage"]),
        ["split_name", "method", "conformal_variant"],
        metric_cols,
    )
    multi_seed.to_csv(RESULTS / "multi_seed_summary.csv", index=False)
    format_markdown(multi_seed, RESULTS / "multi_seed_summary.md")

    representative = metrics[
        (metrics["split_name"] == "random_interpolation")
        & (metrics["seed"] == int(config["representative_seed"]))
    ].copy()
    representative.to_csv(RESULTS / "model_voltage_screening_metrics.csv", index=False)
    format_markdown(
        representative[
            [
                "method",
                "conformal_variant",
                "mae",
                "rmse",
                "max_abs_error",
                "coverage",
                "avg_width",
                "precision",
                "recall",
                "false_alarm_rate",
                "missed_violations",
            ]
        ],
        RESULTS / "model_voltage_screening_metrics.md",
    )

    # Backward-compatible split tables for older manuscript assembly.
    voltage_cols = ["method", "conformal_variant", "mae", "rmse", "max_abs_error", "coverage", "avg_width"]
    screen_cols = ["method", "conformal_variant", "precision", "recall", "f1", "false_alarm_rate", "missed_violations"]
    representative[voltage_cols].to_csv(RESULTS / "model_voltage_metrics.csv", index=False)
    representative[screen_cols].to_csv(RESULTS / "model_screening_metrics.csv", index=False)
    format_markdown(representative[voltage_cols], RESULTS / "model_voltage_metrics.md")
    format_markdown(representative[screen_cols], RESULTS / "model_screening_metrics.md")

    format_markdown(scenario_metrics_df, RESULTS / "scenario_level_metrics.md")
    format_markdown(operating, RESULTS / "operating_value_metrics.md")
    format_markdown(ablation, RESULTS / "conformal_ablation_metrics.md")
    format_markdown(family, RESULTS / "per_family_conformal_metrics.md")
    format_markdown(runtime, RESULTS / "runtime_metrics.md")

    sensitivity = []
    random_seed = int(config["representative_seed"])
    random_split = assign_random_split(scenarios, random_seed)
    random_frame = apply_split(main_data, random_split)
    train = random_frame[random_frame["split"] == "train"].copy()
    calib = random_frame[random_frame["split"] == "calib"].copy()
    test = random_frame[random_frame["split"] == "test"].copy()
    preds = fit_predictions(train, calib, test, random_seed)
    y_test = test["vm_pu"].to_numpy()
    for alpha in config["alpha_grid"]:
        for method_name, variant, groups, shrink in [
            ("Boosting point + global conformal", "global", [], True),
            ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", ["feeder", "pv_bin", "load_bin"], True),
        ]:
            pred = preds[method_name]
            lower, upper, _, _ = conformal_by_group(
                calib, test, pred.pred_calib, pred.pred_test, groups, float(alpha), int(config["min_group_samples"]), shrink
            )
            risk = risk_from_interval(lower, upper)
            sensitivity.append(
                {
                    "method": method_name,
                    "conformal_variant": variant,
                    "alpha": float(alpha),
                    "nominal_coverage": 1.0 - float(alpha),
                    **interval_metrics(y_test, lower, upper),
                    **screening_metrics(y_test, risk),
                }
            )
    sensitivity_df = pd.DataFrame(sensitivity)
    sensitivity_df.to_csv(RESULTS / "conformal_sensitivity_metrics.csv", index=False)
    format_markdown(sensitivity_df, RESULTS / "conformal_sensitivity_metrics.md")

    primary = representative[
        (representative["method"] == "VoltGuard topology-aware residual")
        & (representative["conformal_variant"] == "topology_pv_loading_conditioned")
    ].iloc[0]
    boosting = representative[
        (representative["method"] == "Boosting point + global conformal")
        & (representative["conformal_variant"] == "global")
    ].iloc[0]
    summary = {
        "main_feeders": config["main_feeders"],
        "supplementary_feeders": config["supplementary_feeders"],
        "evaluation_seeds": config["evaluation_seeds"],
        "splits": ["random_interpolation", "synthetic_time_block", "pv_penetration_shift", "topology_heldout_33_to_69"],
        "representative_seed": random_seed,
        "primary_method": "VoltGuard topology-aware residual",
        "primary_conformal_variant": "topology_pv_loading_conditioned",
        "primary_rmse": float(primary["rmse"]),
        "primary_coverage": float(primary["coverage"]),
        "primary_width": float(primary["avg_width"]),
        "primary_recall": float(primary["recall"]),
        "primary_false_alarm_rate": float(primary["false_alarm_rate"]),
        "primary_missed_violations": int(primary["missed_violations"]),
        "boosting_global_missed_violations": int(boosting["missed_violations"]),
        "neural_ablation_ran": bool((representative["method"] == "Neural graph residual ablation").any()),
        "raw_predictions_saved": (RESULTS / "raw_predictions_random_seed7.csv").exists(),
        "conformal_scores_saved": (RESULTS / "conformal_scores_random_seed7.csv").exists(),
    }
    (RESULTS / "evaluation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (RESULTS / "conformal_sensitivity_summary.json").write_text(
        json.dumps({"rows": int(len(sensitivity_df)), "alphas": config["alpha_grid"]}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
