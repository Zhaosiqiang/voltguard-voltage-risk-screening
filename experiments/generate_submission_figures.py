"""Generate journal-ready SVG figures for the VoltGuard manuscripts.

The SVG files are the canonical artwork. PDF companions are emitted for LaTeX
compilation because many TeX engines do not include SVG directly.
"""

from __future__ import annotations

import html
import json
import textwrap
import base64
from pathlib import Path

import cairosvg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"
FIGURES = ROOT / "figures"

BLUE = "#2f5d7c"
TEAL = "#2b8c8c"
GREEN = "#5f8f6f"
AMBER = "#c99a4a"
RED = "#b75d69"
PURPLE = "#6d5f8f"
GRAY = "#68707d"
LIGHT = "#f7f8fa"
GRID = "#d9dee7"
INK = "#202a35"


def setup() -> None:
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 14,
            "font.weight": "bold",
            "axes.titlesize": 17,
            "axes.titleweight": "bold",
            "axes.labelsize": 14,
            "axes.labelweight": "bold",
            "legend.fontsize": 12,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlepad": 12,
            "lines.linewidth": 3.0,
            "lines.markersize": 7,
        }
    )


def wrap_label(value: str, width: int = 12) -> str:
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False))


def style_axes(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, color=GRID, lw=0.8, alpha=0.55)
    ax.tick_params(axis="x", labelrotation=0, width=1.2, colors=INK)
    ax.tick_params(axis="y", labelrotation=0, width=1.2, colors=INK)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontweight("bold")
    ax.spines["bottom"].set_color("#aeb7c2")
    ax.spines["left"].set_color("#aeb7c2")
    ax.spines["bottom"].set_linewidth(1.2)
    ax.spines["left"].set_linewidth(1.2)
    legend = ax.get_legend()
    if legend is not None:
        legend.get_frame().set_linewidth(0)
        for text in legend.get_texts():
            text.set_fontweight("bold")


def top_label(ax: plt.Axes, text: str) -> None:
    ax.text(
        0.0,
        1.02,
        text,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=13,
        fontweight="bold",
        color=GRAY,
    )


def label_panels(axes) -> None:
    flat = np.atleast_1d(axes).ravel()
    for idx, ax in enumerate(flat):
        ax.text(
            -0.02,
            1.08,
            f"({chr(ord('a') + idx)})",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=16,
            fontweight="bold",
            color=INK,
        )


def save_matplotlib(fig: plt.Figure, name: str) -> tuple[Path, Path]:
    svg = FIGURES / f"{name}.svg"
    pdf = FIGURES / f"{name}.pdf"
    fig.savefig(svg, format="svg", bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, format="pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return svg, pdf


def write_svg(name: str, svg_text: str) -> tuple[Path, Path]:
    svg = FIGURES / f"{name}.svg"
    pdf = FIGURES / f"{name}.pdf"
    svg.write_text(svg_text, encoding="utf-8")
    cairosvg.svg2pdf(bytestring=svg_text.encode("utf-8"), write_to=str(pdf))
    return svg, pdf


def image_data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def svg_text(text: str) -> str:
    return html.escape(text, quote=True)


def workflow_icon(kind: str, cx: int, cy: int, scale: float = 1.0) -> str:
    s = scale
    if kind == "feeder":
        return f"""<g transform="translate({cx},{cy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path d="M-58 0 H-25 M-25 0 V-38 M-25 0 V38 M-25 -38 H24 M-25 38 H24 M24 -38 H58 M24 38 H58" stroke="{BLUE}" stroke-width="4"/>
  <circle cx="-58" cy="0" r="8" fill="white" stroke="{BLUE}" stroke-width="4"/>
  <circle cx="-25" cy="0" r="8" fill="white" stroke="{TEAL}" stroke-width="4"/>
  <circle cx="24" cy="-38" r="8" fill="white" stroke="{TEAL}" stroke-width="4"/>
  <circle cx="24" cy="38" r="8" fill="white" stroke="{AMBER}" stroke-width="4"/>
  <path d="M50 -62 l12 -20 l12 20 M62 -80 v34" stroke="{AMBER}" stroke-width="3"/>
  <path d="M45 58 h34 l-5 24 h-34 z" fill="#d8edf1" stroke="{TEAL}" stroke-width="3"/>
</g>"""
    if kind == "forecast":
        return f"""<g transform="translate({cx},{cy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path d="M-52 12 c-20 0 -28 -24 -12 -38 c3 -30 48 -34 60 -8 c22 -5 38 10 38 29 c0 18 -13 31 -34 31 h-52z" fill="#f7fbfb" stroke="{TEAL}" stroke-width="4"/>
  <path d="M-26 5 l16 -18 l18 12 l22 -26" stroke="{TEAL}" stroke-width="4"/>
  <rect x="-24" y="34" width="12" height="26" fill="#d8edf1" stroke="{TEAL}" stroke-width="3"/>
  <rect x="0" y="24" width="12" height="36" fill="#f6dfb6" stroke="{AMBER}" stroke-width="3"/>
  <rect x="24" y="12" width="12" height="48" fill="#d8edf1" stroke="{TEAL}" stroke-width="3"/>
</g>"""
    if kind == "physics":
        return f"""<g transform="translate({cx},{cy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <rect x="-58" y="-46" width="116" height="92" rx="16" fill="#eef5fa" stroke="{BLUE}" stroke-width="4"/>
  <path d="M-34 -26 v52 M-34 -26 h16 M-34 26 h34 M18 -28 v24 M18 -4 h24 M18 24 h24" stroke="{BLUE}" stroke-width="4"/>
  <path d="M-7 -18 c12 8 12 28 0 36" stroke="{TEAL}" stroke-width="4"/>
</g>"""
    if kind == "graph":
        return f"""<g transform="translate({cx},{cy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path d="M-44 -28 L0 -48 L46 -22 M-44 -28 L-32 30 L8 48 L46 -22 M0 -48 L8 48 M-32 30 L46 -22" stroke="{BLUE}" stroke-width="3.5"/>
  <circle cx="-44" cy="-28" r="13" fill="#d8edf1" stroke="{TEAL}" stroke-width="4"/>
  <circle cx="0" cy="-48" r="13" fill="#f6dfb6" stroke="{AMBER}" stroke-width="4"/>
  <circle cx="46" cy="-22" r="13" fill="#d8edf1" stroke="{TEAL}" stroke-width="4"/>
  <circle cx="-32" cy="30" r="13" fill="white" stroke="{BLUE}" stroke-width="4"/>
  <circle cx="8" cy="48" r="13" fill="white" stroke="{TEAL}" stroke-width="4"/>
</g>"""
    if kind == "shield":
        return f"""<g transform="translate({cx},{cy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path d="M0 -58 C18 -38 34 -35 55 -34 V3 C55 34 28 52 0 64 C-28 52 -55 34 -55 3 V-34 C-34 -35 -18 -38 0 -58z" fill="#fff6e6" stroke="{AMBER}" stroke-width="4"/>
  <path d="M-30 20 c16 -44 44 -44 60 0" stroke="{BLUE}" stroke-width="4"/>
  <path d="M-42 20 H42 M0 -10 V34" stroke="{GRAY}" stroke-width="3" stroke-dasharray="6 7"/>
</g>"""
    if kind == "audit":
        return f"""<g transform="translate({cx},{cy}) scale({s})" fill="none" stroke-linecap="round" stroke-linejoin="round">
  <path d="M-52 18 a54 54 0 1 1 104 0" stroke="{BLUE}" stroke-width="4"/>
  <path d="M-34 14 a36 36 0 0 1 68 0" stroke="{TEAL}" stroke-width="8"/>
  <path d="M20 12 a36 36 0 0 1 15 27" stroke="{RED}" stroke-width="8"/>
  <path d="M0 18 L23 -20" stroke="{BLUE}" stroke-width="4"/>
  <circle cx="36" cy="40" r="24" fill="#f8fafc" stroke="{TEAL}" stroke-width="4"/>
  <path d="M24 40 l9 9 l18 -22" stroke="{TEAL}" stroke-width="5"/>
</g>"""
    return ""


def fig01_graphical_abstract() -> tuple[Path, Path]:
    scenario_uri = image_data_uri(FIGURES / "assets" / "active_distribution_scenario_inset.png")

    def card(x: int, y: int, w: int, h: int, title: str, fill: str, stroke: str, icon_kind: str) -> str:
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2.4"/>'
            f'{workflow_icon(icon_kind, x + w/2, y + 50, 0.52)}'
            f'<text x="{x + w/2}" y="{y + 112}" text-anchor="middle" '
            f'font-size="24" font-weight="700" fill="{INK}">{svg_text(title)}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1900" height="680" viewBox="0 0 1900 680" font-family="Times New Roman, Times, serif">
  <defs>
    <linearGradient id="dataFill" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#fbfcfd"/>
      <stop offset="100%" stop-color="#edf3f6"/>
    </linearGradient>
    <linearGradient id="modelFill" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#f7fbfb"/>
      <stop offset="100%" stop-color="#e4f1f0"/>
    </linearGradient>
    <linearGradient id="actionFill" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#fffaf1"/>
      <stop offset="100%" stop-color="#f7e9ce"/>
    </linearGradient>
    <filter id="softShadow" x="-10%" y="-10%" width="120%" height="125%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#203040" flood-opacity="0.12"/>
    </filter>
    <clipPath id="scenarioInsetClip">
      <rect x="82" y="164" width="842" height="428" rx="26"/>
    </clipPath>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M1,1 L7,4 L1,7" fill="{GRAY}"/>
    </marker>
    <marker id="smallArrow" markerWidth="6" markerHeight="6" refX="5.5" refY="3" orient="auto">
      <path d="M1,1 L5.5,3 L1,5" fill="{GRAY}"/>
    </marker>
  </defs>
  <rect width="1900" height="680" fill="white"/>
  <rect x="32" y="34" width="930" height="590" rx="38" fill="url(#dataFill)" stroke="{GRID}" stroke-width="2.6" filter="url(#softShadow)"/>
  <text x="78" y="98" font-size="40" font-weight="700" fill="{INK}">Scenarios</text>
  <text x="78" y="138" font-size="22" font-weight="700" fill="{GRAY}">DER forecasts + topology + voltage-risk hot spots</text>
  <rect x="72" y="154" width="862" height="448" rx="30" fill="white" stroke="{GRID}" stroke-width="1.8"/>
  <image href="{scenario_uri}" x="82" y="164" width="842" height="428" preserveAspectRatio="xMidYMid slice" clip-path="url(#scenarioInsetClip)"/>

  <path d="M976 302 H1000" stroke="{GRAY}" stroke-width="3.2" fill="none" marker-end="url(#smallArrow)"/>
  <rect x="1010" y="98" width="845" height="312" rx="32" fill="#fbfcfd" stroke="{GRID}" stroke-width="2.2"/>
  <text x="1050" y="150" font-size="28" font-weight="700" fill="{GRAY}">Screening layer</text>
  {card(1050, 198, 196, 142, "LinDistFlow", "#eef5fa", BLUE, "physics")}
  {card(1302, 198, 196, 142, "Residual", "url(#modelFill)", TEAL, "graph")}
  {card(1554, 198, 196, 142, "Conformal", "#fff6e6", AMBER, "shield")}
  <path d="M1258 269 H1295" stroke="{GRAY}" stroke-width="3.0" fill="none" marker-end="url(#arrow)"/>
  <path d="M1510 269 H1547" stroke="{GRAY}" stroke-width="3.0" fill="none" marker-end="url(#arrow)"/>

  <path d="M1652 360 V458" stroke="{TEAL}" stroke-width="3.0" fill="none" marker-end="url(#arrow)"/>
  <rect x="1020" y="458" width="815" height="150" rx="30" fill="url(#actionFill)" stroke="#ead8ba" stroke-width="2.2"/>
  {workflow_icon("audit", 1108, 535, 0.64)}
  <text x="1210" y="520" font-size="29" font-weight="700" fill="{INK}">Operating queue</text>
  <rect x="1210" y="545" width="124" height="42" rx="21" fill="white" stroke="{GREEN}" stroke-width="2.2"/>
  <text x="1272" y="573" text-anchor="middle" font-size="19" font-weight="700" fill="{INK}">Release</text>
  <rect x="1356" y="545" width="116" height="42" rx="21" fill="white" stroke="{AMBER}" stroke-width="2.2"/>
  <text x="1414" y="573" text-anchor="middle" font-size="19" font-weight="700" fill="{INK}">Watch</text>
  <rect x="1494" y="545" width="120" height="42" rx="21" fill="white" stroke="{RED}" stroke-width="2.2"/>
  <text x="1554" y="573" text-anchor="middle" font-size="19" font-weight="700" fill="{INK}">Correct</text>
  <rect x="1650" y="527" width="150" height="66" rx="33" fill="#f8eef0" stroke="{RED}" stroke-width="2.4"/>
  <text x="1725" y="568" text-anchor="middle" font-size="22" font-weight="700" fill="{INK}">AC audit</text>
</svg>"""
    return write_svg("fig01_graphical_abstract_workflow", svg)


def fig02_feeders_splits() -> tuple[Path, Path]:
    fig, axes = plt.subplots(1, 2, figsize=(14.8, 5.4), gridspec_kw={"width_ratios": [1.35, 1]})
    label_panels(axes)
    ax = axes[0]
    ax.set_title("Distribution feeders used in the study", loc="left", fontweight="bold")
    ax.axis("off")
    rng = np.random.default_rng(7)
    for offset, label, n in [(0.0, "IEEE 33-bus", 33), (0.58, "IEEE 69-bus", 69)]:
        xs = np.linspace(0.05, 0.92, 12)
        ys = 0.72 - offset + 0.07 * np.sin(np.linspace(0, 2.6 * np.pi, 12))
        ax.plot(xs, ys, color=BLUE, lw=3.0)
        idx = np.linspace(0, 11, 7, dtype=int)
        ax.scatter(xs[idx], ys[idx], s=95, facecolor="white", edgecolor=TEAL, lw=2.5, zorder=3)
        branches = rng.choice(idx[1:-1], size=3, replace=False)
        for b in branches:
            bx, by = xs[b], ys[b]
            ax.plot([bx, bx + 0.08], [by, by + 0.08], color=BLUE, lw=2.4)
            ax.scatter([bx + 0.08], [by + 0.08], s=75, facecolor="white", edgecolor=AMBER, lw=2.4)
        ax.text(
            0.05,
            0.88 - offset,
            label,
            transform=ax.transAxes,
            fontweight="bold",
            color=INK,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5, "alpha": 0.95},
        )

    ax = axes[1]
    ax.set_title("Executed split protocols", loc="left", fontweight="bold")
    splits = ["Random", "Time\nblock", "PV\nshift", "33->69"]
    metrics = ["Train/cal/test", "Scenario-level", "Shift", "Transfer"]
    mat = np.array([[1, 1, 0.4, 0.3], [1, 1, 0.5, 0.3], [0.6, 0.7, 1, 0.4], [0.5, 0.5, 0.5, 1]])
    evidence_cmap = LinearSegmentedColormap.from_list(
        "voltguard_evidence",
        ["#f7f8fa", "#d7dfbd", "#68b7b3", "#3477a1", "#182b56"],
    )
    im = ax.imshow(mat, cmap=evidence_cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(splits)), splits)
    ax.set_yticks(range(len(metrics)), metrics)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(
                j,
                i,
                "yes" if mat[i, j] > 0.85 else "audit",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="white" if mat[i, j] > 0.72 else INK,
            )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_title("Evidence\nstrength", fontsize=12, fontweight="bold", pad=8)
    fig.tight_layout()
    return save_matplotlib(fig, "fig02_feeders_and_splits")


def fig03_conformal_ablation() -> tuple[Path, Path]:
    df = pd.read_csv(RESULTS / "conformal_ablation_metrics.csv")
    d = df[
        (df["split_name"] == "random_interpolation")
        & (df["seed"] == 7)
        & (df["method"] == "VoltGuard topology-aware residual")
        & df["conformal_variant"].isin(
            ["global", "pv_conditioned", "topology_conditioned", "topology_pv_loading_conditioned", "topology_pv_loading_no_shrinkage"]
        )
    ].copy()
    order = ["global", "pv_conditioned", "topology_conditioned", "topology_pv_loading_conditioned", "topology_pv_loading_no_shrinkage"]
    labels = ["Global", "PV", "Topology", "Topo+PV\n+load", "No\nshrinkage"]
    d["order"] = d["conformal_variant"].map({v: i for i, v in enumerate(order)})
    d = d.sort_values("order")
    x = np.arange(len(d))
    fig, ax = plt.subplots(1, 3, figsize=(16.2, 5.2))
    label_panels(ax)
    ax[0].bar(x, d["coverage"], color=TEAL)
    ax[0].axhline(0.90, color=GRAY, ls="--", lw=2)
    ax[0].set_title("Coverage")
    ax[0].set_ylim(0.88, max(0.97, d["coverage"].max() + 0.01))
    ax[1].bar(x, d["avg_width"] * 1e4, color=BLUE)
    ax[1].set_title("Mean interval width")
    top_label(ax[1], "1e-4 p.u.")
    ax[2].bar(x, d["missed_violations"], color=RED)
    ax[2].set_title("Missed bus violations")
    for a in ax:
        a.set_xticks(x, labels)
        style_axes(a, "y")
    fig.tight_layout()
    return save_matplotlib(fig, "fig03_conformal_ablation")


def compact_family_label(value: str) -> str:
    parts = {}
    for item in value.split("|"):
        if "=" in item:
            key, val = item.split("=", 1)
            parts[key.strip()] = val.strip()
    feeder = parts.get("feeder", "?").replace("ieee", "F").replace("_bus", "")
    pv = parts.get("pv_bin", "?").replace("pv_", "PV ")
    load = parts.get("load_bin", "?").replace("_", " ")
    return f"{feeder} / {pv} / {load}"


def fig04_family_calibration() -> tuple[Path, Path]:
    df = pd.read_csv(RESULTS / "per_family_conformal_metrics.csv")
    d = df[
        (df["split_name"] == "random_interpolation")
        & (df["seed"] == 7)
        & (df["method"] == "VoltGuard topology-aware residual")
        & (df["conformal_variant"] == "topology_pv_loading_conditioned")
        & (df["family"] != "__global__")
    ].copy()
    d = d.sort_values(["missed_violations", "test_samples"], ascending=[False, False]).head(16)
    d = d.sort_values("coverage")
    fig, ax = plt.subplots(figsize=(12.2, 7.4))
    y = np.arange(len(d))
    colors = np.where(d["coverage"] >= 0.90, GREEN, np.where(d["coverage"] >= 0.85, AMBER, RED))
    ax.barh(y, d["coverage"], color=colors)
    ax.axvline(0.90, color=GRAY, ls="--", lw=2)
    ax.set_yticks(y, [compact_family_label(f) for f in d["family"]], fontsize=12)
    ax.set_xlim(0.70, 1.08)
    ax.set_xlabel("Empirical coverage")
    for yi, (_, row) in enumerate(d.iterrows()):
        ax.text(
            1.015,
            yi,
            f"n={int(row['calibration_samples'])}, miss={int(row['missed_violations'])}",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=GRAY,
        )
    style_axes(ax, "x")
    fig.tight_layout()
    return save_matplotlib(fig, "fig04_per_family_calibration")


def fig05_shift_generalization() -> tuple[Path, Path]:
    df = pd.read_csv(RESULTS / "multi_seed_summary.csv")
    d = df[
        df["method"].isin(["Boosting point + global conformal", "VoltGuard topology-aware residual"])
        & df["conformal_variant"].isin(["global", "topology_pv_loading_conditioned"])
    ].copy()
    d = d[
        ((d["method"] == "Boosting point + global conformal") & (d["conformal_variant"] == "global"))
        | ((d["method"] == "VoltGuard topology-aware residual") & (d["conformal_variant"] == "topology_pv_loading_conditioned"))
    ]
    split_order = ["random_interpolation", "synthetic_time_block", "pv_penetration_shift", "topology_heldout_33_to_69"]
    labels = ["Random", "Time\nblock", "PV\nshift", "33->69"]
    fig, ax = plt.subplots(1, 2, figsize=(13.8, 5.2), sharex=True)
    label_panels(ax)
    for method, color, marker in [
        ("Boosting point + global conformal", GRAY, "o"),
        ("VoltGuard topology-aware residual", TEAL, "s"),
    ]:
        vals = []
        fa = []
        for s in split_order:
            row = d[(d["split_name"] == s) & (d["method"] == method)]
            vals.append(float(row["recall_mean"].iloc[0]) if not row.empty else np.nan)
            fa.append(float(row["false_alarm_rate_mean"].iloc[0]) if not row.empty else np.nan)
        ax[0].plot(labels, vals, marker=marker, color=color, lw=3, label=method.replace("VoltGuard topology-aware residual", "VoltGuard"))
        ax[1].plot(labels, fa, marker=marker, color=color, lw=3, label=method.replace("VoltGuard topology-aware residual", "VoltGuard"))
    ax[0].set_title("Violation recall")
    ax[1].set_title("False-alarm rate")
    ax[0].set_ylim(0.98, 1.002)
    ax[1].set_ylim(bottom=0)
    for a in ax:
        style_axes(a, "y")
    ax[0].legend(frameon=False, loc="lower left")
    fig.tight_layout()
    return save_matplotlib(fig, "fig05_shift_generalization")


def fig06_operating_value() -> tuple[Path, Path]:
    budget = pd.read_csv(RESULTS / "screening_budget_metrics.csv")
    d = budget[(budget["method"] == "VoltGuard topology-aware residual") & (budget["variant"] == "topology_pv_loading_conditioned")].copy()
    runtime = pd.read_csv(RESULTS / "runtime_operational_benchmark.csv")
    fig, ax = plt.subplots(1, 2, figsize=(13.8, 5.2))
    label_panels(ax)
    ax[0].plot(d["budget_fraction"] * 100, d["severity_capture_under_budget"], color=TEAL, marker="o", lw=3, label="severity captured")
    ax[0].plot(d["budget_fraction"] * 100, d["scenario_violation_reduction_ratio"], color=AMBER, marker="s", lw=3, label="scenario reduction")
    ax[0].set_xlabel("AC-call budget (%)")
    top_label(ax[0], "Ratio")
    ax[0].set_title("Budgeted AC triage")
    ax[0].legend(frameon=False)
    top = runtime.sort_values("seconds", ascending=False)
    ax[1].barh([wrap_label(v, 22) for v in top["workflow"]], top["seconds"], color=[GRAY, BLUE, TEAL, GREEN][: len(top)])
    ax[1].set_xscale("log")
    ax[1].set_xlabel("Seconds (log scale)")
    ax[1].set_title("Runtime audit")
    for a in ax:
        style_axes(a, "x")
    fig.tight_layout()
    return save_matplotlib(fig, "fig06_operating_value")


def fig07_energy_frontier() -> tuple[Path, Path]:
    df = pd.read_csv(RESULTS / "energy_management_frontier_metrics.csv")
    d = df[df["frontier"] == "conformal_release"].copy()
    fig, ax = plt.subplots(1, 2, figsize=(13.8, 5.2))
    label_panels(ax)
    ax[0].plot(d["nominal_coverage"], d["screened_safe_scenarios_mean"], color=TEAL, marker="o", lw=3)
    ax[0].set_xlabel("Nominal coverage")
    top_label(ax[0], "Screened-safe scenarios")
    ax[0].set_title("Release frontier")
    ax[1].plot(d["nominal_coverage"], d["mean_interval_width"] * 1e4, color=BLUE, marker="s", lw=3, label="width")
    ax[1].plot(d["nominal_coverage"], d["missed_bus_violations_mean"], color=RED, marker="^", lw=3, label="missed buses")
    ax[1].set_xlabel("Nominal coverage")
    ax[1].set_title("Sharpness-risk tradeoff")
    ax[1].legend(frameon=False)
    for a in ax:
        style_axes(a, "both")
    fig.tight_layout()
    return save_matplotlib(fig, "fig07_energy_frontier")


def fig08_screening_budget() -> tuple[Path, Path]:
    df = pd.read_csv(RESULTS / "screening_budget_metrics.csv")
    policies = [
        ("VoltGuard topology-aware residual", "topology_pv_loading_conditioned", TEAL, "VoltGuard"),
        ("Boosting point + global conformal", "global", GRAY, "Boosting global"),
        ("Random budget expectation", "random", AMBER, "Random budget"),
        ("Oracle realized severity", "oracle", RED, "Oracle severity"),
    ]
    fig, ax = plt.subplots(figsize=(11.2, 5.8))
    for method, variant, color, label in policies:
        d = df[(df["method"] == method) & (df["variant"] == variant)]
        if d.empty:
            continue
        ax.plot(d["budget_fraction"] * 100, d["severity_capture_under_budget"], marker="o", lw=3, color=color, label=label)
    ax.set_xlabel("AC-call budget (%)")
    top_label(ax, "Realized severity captured")
    ax.set_ylim(0, 1.05)
    style_axes(ax, "both")
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    return save_matplotlib(fig, "fig08_screening_budget")


def fig09_candidate_actions() -> tuple[Path, Path]:
    df = pd.read_csv(RESULTS / "candidate_action_screening_metrics.csv")
    fig, ax = plt.subplots(1, 2, figsize=(13.8, 5.2))
    label_panels(ax)
    for policy, color in [("VoltGuard interval-risk", TEAL), ("LinDistFlow point-risk", BLUE), ("Cheapest-first", AMBER)]:
        d = df[df["policy"] == policy]
        if d.empty:
            continue
        ax[0].plot(d["top_k_candidates"], d["candidate_ac_audits_avoided"], marker="o", lw=3, color=color, label=policy)
        ax[1].plot(d["top_k_candidates"], d["extra_violating_scenarios_vs_full"], marker="o", lw=3, color=color, label=policy)
    ax[0].set_title("AC candidate audits avoided")
    ax[1].set_title("Extra violating scenarios vs full AC")
    for a in ax:
        a.set_xlabel("Top-k candidates per scenario")
        style_axes(a, "both")
    ax[0].legend(frameon=False, fontsize=12)
    fig.tight_layout()
    return save_matplotlib(fig, "fig09_candidate_action_screening")


def fig10_risk_ranking() -> tuple[Path, Path]:
    metrics = pd.read_csv(RESULTS / "scenario_risk_ranking_metrics.csv")
    raw = pd.read_csv(RESULTS / "scenario_risk_ranking_raw.csv")
    m = metrics.head(5).copy()
    variant_labels = {
        "global": "Global",
        "topology_conditioned": "Topology",
        "topology_pv_loading_conditioned": "Topo+PV\n+load",
        "pv_conditioned": "PV",
        "topology_pv_loading_no_shrinkage": "No\nshrinkage",
    }
    labels = [variant_labels.get(v, wrap_label(v.replace("_", " "), 12)) for v in m["conformal_variant"]]
    fig, ax = plt.subplots(1, 2, figsize=(14.6, 5.4))
    label_panels(ax)
    x = np.arange(len(m))
    ax[0].bar(x - 0.2, m["roc_auc"], width=0.4, color=TEAL, label="ROC-AUC")
    ax[0].bar(x + 0.2, m["average_precision"], width=0.4, color=BLUE, label="Avg. precision")
    ax[0].set_xticks(x, labels, fontsize=12)
    ax[0].set_ylim(0.8, 1.02)
    ax[0].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2)
    ax[0].set_title("Ranking metrics")
    if {"rank_fraction", "cumulative_severity_share", "method_label"}.issubset(raw.columns):
        for label, color in [("VoltGuard", TEAL), ("Boosting global", GRAY)]:
            d = raw[raw["method_label"].str.contains(label, case=False, na=False)]
            if not d.empty:
                ax[1].plot(d["rank_fraction"], d["cumulative_severity_share"], color=color, lw=3, label=label)
    else:
        vg = metrics[metrics["method"].str.contains("VoltGuard")].iloc[0]
        ax[1].plot([0.1, 0.2, 0.3], [vg["top10_severity_capture"], vg["top20_severity_capture"], vg["top30_severity_capture"]], color=TEAL, marker="o", lw=3, label="VoltGuard")
    ax[1].set_xlabel("Top-ranked scenario fraction")
    top_label(ax[1], "Severity captured")
    ax[1].set_title("Cumulative severity capture")
    style_axes(ax[0], "y")
    style_axes(ax[1], "both")
    ax[1].legend(frameon=False)
    fig.tight_layout()
    return save_matplotlib(fig, "fig10_risk_ranking_quality")


def fig11_oajpe_baseline_pipeline() -> tuple[Path, Path]:
    scenario_uri = image_data_uri(FIGURES / "assets" / "active_distribution_scenario_inset.png")

    def box(x: int, y: int, w: int, h: int, title: str, fill: str, stroke: str, icon_kind: str) -> str:
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>'
            f'{workflow_icon(icon_kind, x + w/2, y + 48, 0.46)}'
            f'<text x="{x + w/2}" y="{y + 104}" text-anchor="middle" font-size="25" font-weight="700" fill="{INK}">{svg_text(title)}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1550" height="540" viewBox="0 0 1550 540" font-family="Times New Roman, Times, serif">
  <defs>
    <linearGradient id="baselineFill" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#fbfcfd"/>
      <stop offset="100%" stop-color="#eef4f5"/>
    </linearGradient>
    <linearGradient id="gateFill" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#fffaf1"/>
      <stop offset="100%" stop-color="#f7e9ce"/>
    </linearGradient>
    <clipPath id="baselineScenarioClip">
      <rect x="66" y="150" width="510" height="300" rx="20"/>
    </clipPath>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M1,1 L7,4 L1,7" fill="{GRAY}"/>
    </marker>
    <marker id="smallArrow" markerWidth="6" markerHeight="6" refX="5.5" refY="3" orient="auto">
      <path d="M1,1 L5.5,3 L1,5" fill="{GRAY}"/>
    </marker>
  </defs>
  <rect width="1550" height="540" fill="white"/>
  <rect x="34" y="44" width="574" height="432" rx="32" fill="url(#baselineFill)" stroke="{GRID}" stroke-width="2.4"/>
  <text x="66" y="100" font-size="30" font-weight="700" fill="{INK}">Forecast scenarios</text>
  <text x="66" y="136" font-size="18" font-weight="700" fill="{GRAY}">DER forecasts, topology, voltage-risk cues</text>
  <rect x="62" y="146" width="518" height="308" rx="22" fill="white" stroke="{GRID}" stroke-width="1.5"/>
  <image href="{scenario_uri}" x="66" y="150" width="510" height="300" preserveAspectRatio="xMidYMid slice" clip-path="url(#baselineScenarioClip)"/>

  <path d="M620 248 H634" stroke="{GRAY}" stroke-width="3.2" fill="none" marker-end="url(#smallArrow)"/>
  <rect x="648" y="70" width="850" height="270" rx="30" fill="url(#baselineFill)" stroke="{GRID}" stroke-width="2.2"/>
  <text x="684" y="120" font-size="27" font-weight="700" fill="{GRAY}">Baseline filter</text>
  {box(720, 170, 165, 124, "Forecasts", "#f8fafc", BLUE, "forecast")}
  <path d="M896 232 H944" stroke="{GRAY}" stroke-width="3.0" fill="none" marker-end="url(#arrow)"/>
  {box(955, 170, 180, 124, "LinDistFlow", "#eef5fa", BLUE, "physics")}
  <path d="M1146 232 H1204" stroke="{GRAY}" stroke-width="3.0" fill="none" marker-end="url(#arrow)"/>
  {box(1215, 170, 165, 124, "Quantile", "url(#gateFill)", AMBER, "shield")}

  <path d="M1298 300 V382" stroke="{TEAL}" stroke-width="3.2" fill="none" marker-end="url(#arrow)"/>
  <rect x="648" y="382" width="850" height="112" rx="30" fill="#fbfcfd" stroke="{GRID}" stroke-width="2.2"/>
  <text x="688" y="450" font-size="27" font-weight="700" fill="{INK}">Screened output</text>
  <rect x="915" y="417" width="128" height="42" rx="21" fill="white" stroke="{GREEN}" stroke-width="2.2"/>
  <text x="979" y="445" text-anchor="middle" font-size="20" font-weight="700" fill="{INK}">Release</text>
  <rect x="1064" y="417" width="118" height="42" rx="21" fill="white" stroke="{AMBER}" stroke-width="2.2"/>
  <text x="1123" y="445" text-anchor="middle" font-size="20" font-weight="700" fill="{INK}">Route</text>
  <path d="M1192 438 H1254" stroke="{GRAY}" stroke-width="2.8" fill="none" marker-end="url(#arrow)"/>
  <rect x="1264" y="406" width="190" height="64" rx="32" fill="#f8eef0" stroke="{RED}" stroke-width="2.5"/>
  {workflow_icon("audit", 1310, 437, 0.30)}
  <text x="1384" y="446" text-anchor="middle" font-size="24" font-weight="700" fill="{INK}">AC audit</text>
</svg>"""
    return write_svg("fig11_oajpe_lindistflow_quantile_pipeline", svg)


def fig12_oajpe_minimal_performance() -> tuple[Path, Path]:
    metrics = pd.read_csv(RESULTS / "oajpe_lindistflow_quantile_metrics.csv")
    primary = metrics[metrics["seed"] == 7].iloc[0]
    fig, ax = plt.subplots(1, 3, figsize=(16.0, 5.2))
    label_panels(ax)
    ax[0].bar([str(int(seed)) for seed in metrics["seed"]], metrics["rmse"] * 1e3, color=BLUE)
    ax[0].set_title("LinDistFlow error")
    ax[0].set_xlabel("Seed")
    top_label(ax[0], "1e-3 p.u.")
    ax[1].bar(["Coverage", "Width"], [float(primary["coverage"]), float(primary["avg_width"]) * 1000], color=[TEAL, AMBER])
    ax[1].set_title("Global quantile")
    top_label(ax[1], "coverage / width x1000")
    ax[2].bar(
        ["Scenario\nrecall", "False\nalarm"],
        [float(primary["scenario_recall"]), float(primary["scenario_false_alarm_rate"])],
        color=[GREEN, RED],
    )
    ax[2].set_title("Scenario screening")
    top_label(ax[2], "rate")
    for a in ax:
        style_axes(a, "y")
    fig.tight_layout()
    return save_matplotlib(fig, "fig12_oajpe_minimal_performance")


def main() -> int:
    setup()
    generated = [
        fig01_graphical_abstract(),
        fig02_feeders_splits(),
        fig03_conformal_ablation(),
        fig04_family_calibration(),
        fig05_shift_generalization(),
        fig06_operating_value(),
        fig07_energy_frontier(),
        fig08_screening_budget(),
        fig09_candidate_actions(),
        fig10_risk_ranking(),
        fig11_oajpe_baseline_pipeline(),
        fig12_oajpe_minimal_performance(),
    ]
    manifest = {
        "canonical_format": "svg",
        "latex_companion_format": "pdf",
        "figures": [
            {
                "svg": str(svg.relative_to(ROOT)),
                "pdf": str(pdf.relative_to(ROOT)),
                "bytes_svg": svg.stat().st_size,
                "bytes_pdf": pdf.stat().st_size,
            }
            for svg, pdf in generated
        ],
    }
    (FIGURES / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": "wrote", "figures": len(generated)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
