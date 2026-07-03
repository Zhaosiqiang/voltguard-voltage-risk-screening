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
            "left": r"\raggedright",
            "right": r"\raggedleft",
            "center": r"\centering",
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

    weights = [0.0] * ncols
    if ncols >= 9:
        text_budget = min(0.34, 0.12 * len(text_cols))
    elif ncols >= 7:
        text_budget = min(0.36, 0.16 + 0.12 * max(0, len(text_cols) - 1))
    else:
        text_budget = min(0.42, 0.20 * len(text_cols))

    for pos, idx in enumerate(text_cols):
        if pos == 0:
            weights[idx] = min(0.20, text_budget * 0.58 if len(text_cols) > 1 else text_budget)
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
