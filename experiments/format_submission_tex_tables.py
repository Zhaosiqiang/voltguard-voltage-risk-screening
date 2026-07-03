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
        ragged = {
            "left": r"\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000",
            "right": r"\raggedleft",
            "center": r"\centering\hyphenpenalty=10000\exhyphenpenalty=10000",
        }[align]
        cols.append(
            rf"  >{{{ragged}\arraybackslash}}p{{(\linewidth - {available}\tabcolsep) * \real{{{weight:.4f}}}}}"
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


def format_tables(tex: str) -> str:
    tex = LONGTABLE_SPEC.sub(compact_longtable_spec, tex)
    tex = HEADER_MINIPAGE.sub(unwrap_header_minipage, tex)
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
