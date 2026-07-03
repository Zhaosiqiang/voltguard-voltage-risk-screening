"""Make Pandoc-generated LaTeX tables readable in submission PDFs.

Pandoc pipe tables with many columns are emitted as longtable columns with
fixed p-widths. In a manuscript PDF this can force labels such as "VoltGuard"
or "ablation" to stack vertically. This post-processor preserves the table
data but lets short labels use their natural width.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


LONGTABLE_SPEC = re.compile(
    r"\\begin\{longtable\}\[\]\{@\{\}\n(?P<spec>.*?)@\{\}\}",
    flags=re.S,
)

LONGTABLE_GROUP = re.compile(
    r"\{\\def\\LTcaptype\{none\} % do not increment counter\n"
    r"(?P<table>\\begin\{longtable\}.*?\\end\{longtable\})\n"
    r"\}",
    flags=re.S,
)

LONGTABLE_BLOCK = re.compile(r"\\begin\{longtable\}.*?\\end\{longtable\}", flags=re.S)

SIMPLE_LONGTABLE_SPEC = re.compile(r"\\begin\{longtable\}\[\]\{@\{\}(?P<spec>[lcr]+)@\{\}\}")

TABULAR_SPEC = re.compile(r"\\begin\{tabular\}\{(?P<spec>[^{}]+)\}")

HEADER_MINIPAGE = re.compile(
    r"\\begin\{minipage\}\[b\]\{\\linewidth\}\\ragged(?:right|left|center)\n"
    r"(?P<body>.*?)\n"
    r"\\end\{minipage\}",
    flags=re.S,
)


def compact_longtable_spec(match: re.Match[str]) -> str:
    spec = match.group("spec")
    aligns = []
    for align in re.findall(r"\\ragged(right|left|center)\\arraybackslash", spec):
        if align == "left":
            aligns.append("right")
        elif align == "center":
            aligns.append("center")
        else:
            aligns.append("left")
    if not aligns:
        return match.group(0)

    weights = table_widths(aligns)
    available = 2 * (len(aligns) - 1)
    cols = []
    for align, weight in zip(aligns, weights, strict=True):
        ragged = r"\centering\hyphenpenalty=10000\exhyphenpenalty=10000"
        cols.append(
            rf"  >{{{ragged}\arraybackslash}}m{{(\linewidth - {available}\tabcolsep) * \real{{{weight:.4f}}}}}"
        )
    return "\\begin{longtable}[]{@{}\n" + "\n".join(cols) + "@{}}"


def table_widths(aligns: list[str]) -> list[float]:
    ncols = len(aligns)
    text_cols = [idx for idx, align in enumerate(aligns) if align != "right"]
    if not text_cols:
        return [1.0 / ncols] * ncols
    if ncols == 3 and text_cols == [2]:
        return [0.12, 0.18, 0.70]
    if len(text_cols) == ncols:
        if ncols == 2:
            return [0.24, 0.76]
        if ncols == 3:
            return [0.30, 0.33, 0.37]
        if ncols == 4:
            return [0.29, 0.24, 0.25, 0.22]
        return [1.0 / ncols] * ncols

    weights = [0.0] * ncols
    if ncols >= 10:
        text_budget = min(0.42, 0.18 + 0.12 * max(0, len(text_cols) - 1))
    elif ncols >= 8:
        text_budget = min(0.44, 0.22 + 0.12 * max(0, len(text_cols) - 1))
    elif ncols >= 6:
        text_budget = min(0.46, 0.24 + 0.13 * max(0, len(text_cols) - 1))
    else:
        text_budget = min(0.50, 0.24 * len(text_cols))

    for pos, idx in enumerate(text_cols):
        if pos == 0:
            weights[idx] = min(0.24, text_budget * 0.62 if len(text_cols) > 1 else text_budget)
        else:
            weights[idx] = (text_budget - weights[text_cols[0]]) / (len(text_cols) - 1)

    numeric_cols = [idx for idx in range(ncols) if idx not in text_cols]
    numeric_width = (1.0 - sum(weights)) / max(1, len(numeric_cols))
    for idx in numeric_cols:
        weights[idx] = numeric_width
    return weights


def unwrap_header_minipage(match: re.Match[str]) -> str:
    return " ".join(match.group("body").strip().split())


def center_tabular_spec(match: re.Match[str]) -> str:
    spec = match.group("spec")
    centered = "".join("c" if char in "lcr" else char for char in spec)
    return rf"\begin{{tabular}}{{{centered}}}"


def center_simple_longtable_spec(match: re.Match[str]) -> str:
    spec = match.group("spec")
    return r"\begin{longtable}[]{@{}" + ("c" * len(spec)) + r"@{}}"


def normalize_header_labels(tex: str) -> str:
    replacements = {
        "RMSE mean": r"\shortstack{RMSE\\mean}",
        "Coverage mean": r"\shortstack{Coverage\\mean}",
        "Width mean": r"\shortstack{Width\\mean}",
        "Recall mean": r"\shortstack{Recall\\mean}",
        "FA mean": r"\shortstack{FA\\mean}",
        "Missed mean": r"\shortstack{Missed\\mean}",
        "Delta coverage": r"\shortstack{Delta\\coverage}",
        "Delta width": r"\shortstack{Delta\\width}",
        "Delta recall": r"\shortstack{Delta\\recall}",
        "Delta FA": r"\shortstack{Delta\\FA}",
        "Delta missed": r"\shortstack{Delta\\missed}",
        "Calib. fraction": r"\shortstack{Calib.\\frac.}",
        "Calib. scenarios": r"\shortstack{Calib.\\scen.}",
        "Observed families": r"\shortstack{Obs.\\fam.}",
        "Empty fam.": r"\shortstack{Empty\\fam.}",
        "Min EV calib.": r"\shortstack{Min EV\\calib.}",
        "Min calib.": r"\shortstack{Min\\calib.}",
        "Calib. n": r"\shortstack{Calib.\\n}",
        "Test n": r"\shortstack{Test\\n}",
        "Avg width": r"\shortstack{Avg.\\width}",
        "Violation recall": r"\shortstack{Violation\\recall}",
        "False alarm": r"\shortstack{False\\alarm}",
        "Missed violations": r"\shortstack{Missed\\viol.}",
        "Scenario recall": r"\shortstack{Scenario\\recall}",
        "Scenario FA": r"\shortstack{Scenario\\FA}",
        "Post-action viol.": r"\shortstack{Post-action\\viol.}",
        "Runtime s": r"\shortstack{Runtime\\s}",
        "AC scen.": r"\shortstack{AC\\scen.}",
    }
    for old, new in replacements.items():
        tex = tex.replace(old, new)
    compact_headers = {
        "& Coverage & Width & Recall": "& Cov. & Wid. & Recall",
        "& Coverage & Width &": "& Cov. & Wid. &",
        "Coverage & Width": "Cov. & Wid.",
    }
    for old, new in compact_headers.items():
        tex = tex.replace(old, new)
    return tex


def caption_for_longtable(table: str, number: int) -> str:
    compact = " ".join(table.split())
    rules = [
        ("Line of work", "Positioning relative to related work."),
        ("Line & Contribution & Screening gap", "ECM integration gap and role."),
        ("Integration line", "DMS integration positioning."),
        ("Acronym", "Acronym table."),
        ("Calib. fraction", "Calibration-budget sensitivity."),
        ("Method & Calib.", "Representative screening metrics."),
        ("Drop RMSE", "Physics-consistency audit."),
        ("RMSE mean", "Multi-seed screening summary."),
        ("Delta coverage", "Paired seed deltas relative to the global baseline."),
        ("Feature family", "Residual feature-family ablation."),
        ("Method & Interval", "Comparison with competing screening methods."),
        ("Variant & Coverage", "Conformal calibration variants."),
        ("Calibration & Coverage", "Asymmetric conformal calibration audit."),
        ("Conditioning key", "EV-conditioning family ablation."),
        ("Scale & Min EV", "EV family sample-size outlook."),
        ("Family & Calib.", "Per-family conformal calibration analysis."),
        ("Audit & Families", "Family recalibration audit."),
        ("Stratum & Bus", "Risk-stratified calibration audit."),
        ("PV protocol & Target calib. & Hi-PV test", "PV-shift recalibration protocol."),
        ("PV protocol & Target calib. & AC avoided", "PV-shift operating-screening protocol."),
        ("Method & Variant & RMSE", "IEEE 118-bus supplementary stress audit."),
        ("Workflow & AC scen.", "Operational runtime benchmark."),
        ("Queue & Records", "DMS prototype queue summary."),
        ("Artifact & Fields", "Implementation record contract."),
    ]
    for marker, caption in rules:
        if marker in compact:
            return caption
    return f"Tabulated results summary {number}."


def add_longtable_captions(tex: str) -> str:
    tex = LONGTABLE_GROUP.sub(lambda match: match.group("table"), tex)
    counter = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal counter
        table = match.group(0)
        if r"\caption{" in table:
            return table
        counter += 1
        caption = caption_for_longtable(table, counter)
        return table.replace(r"\toprule", rf"\caption{{{caption}}}\\\toprule", 1)

    return LONGTABLE_BLOCK.sub(repl, tex)


def format_tables(tex: str) -> str:
    tex = LONGTABLE_SPEC.sub(compact_longtable_spec, tex)
    tex = SIMPLE_LONGTABLE_SPEC.sub(center_simple_longtable_spec, tex)
    tex = TABULAR_SPEC.sub(center_tabular_spec, tex)
    tex = HEADER_MINIPAGE.sub(unwrap_header_minipage, tex)
    tex = add_longtable_captions(tex)
    tex = normalize_header_labels(tex)
    return tex


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: format_submission_tex_tables.py FILE.tex [...]", file=sys.stderr)
        return 2
    for name in argv[1:]:
        path = Path(name)
        text = path.read_text(encoding="utf-8")
        path.write_text(format_tables(text), encoding="utf-8")
        print(f"Formatted tables in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
