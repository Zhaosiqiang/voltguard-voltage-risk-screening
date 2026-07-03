"""Assemble the three differentiated VoltGuard submission manuscripts.

The generated manuscripts are formal article drafts only. Author-facing upload
checklists, figure-production notes, and unresolved declaration gates are kept
in separate packet files so they do not leak into the submitted manuscript body.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("VoltGuard-CPGNN")
RESULTS = ROOT / "experiments" / "results"

AUTHORS = [
    {
        "name": "Siqiang Zhao",
        "role": "Corresponding author",
        "email": "2023141520257@stu.scu.edu.cn",
        "affiliation": "Sichuan University-Pittsburgh Institute, Chengdu, China",
    },
    {
        "name": "Fengxiang Zhang",
        "email": "zfengxiang309@gmail.com",
        "affiliation": "Southwest Jiaotong University, Chengdu, China",
    },
]


def author_yaml(style: str) -> list[str]:
    if style == "elsevier":
        return ['author: "Siqiang Zhao (corresponding author), Fengxiang Zhang"']
    lines = ["author:"]
    for author in AUTHORS:
        label = author["name"]
        if "role" in author:
            label += " (corresponding author)"
        lines.append(f'  - "{label}"')
    return lines


def author_information() -> str:
    lines = [
        "# Title Page",
        "",
        "## Author Information",
        "",
        "| Author | Email | Affiliation | Contribution note |",
        "|---|---|---|---|",
    ]
    for author in AUTHORS:
        notes = author.get("role", "")
        lines.append(
            f"| {author['name']} | {author['email']} | {author['affiliation']} | {notes} |"
        )
    return "\n".join(lines)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


TABLE_LABEL_REPLACEMENTS = [
    ("LinDistFlow physical backbone", "LDF"),
    ("LinDistFlow + global quantile", "LDF-GQ"),
    ("Boosting point + global conformal", "Boost-GC"),
    ("Boosting + global conformal", "Boost-GC"),
    ("Gradient-boosted quantile regression", "GB-quantile"),
    ("Gaussian-process UQ baseline", "GP-UQ"),
    ("Neural graph residual ablation", "GNN ablation"),
    ("VoltGuard topology-aware residual", "VoltGuard"),
    ("VoltGuard topology+PV+loading", "VoltGuard"),
    ("VoltGuard interval-risk", "VoltGuard"),
    ("LinDistFlow point-risk", "LDF point"),
    ("Random budget expectation", "Random"),
    ("Oracle realized severity", "Oracle"),
    ("Full AC grid search on every scenario", "Full AC all"),
    ("VoltGuard-flagged scenarios then AC grid search", "Flagged+AC"),
    ("VoltGuard top-20% budget then AC grid search", "Top20+AC"),
    ("AC corrective grid-search benchmark", "AC grid-search"),
    ("Full AC grid search", "Full AC"),
    ("High-PV AC stress, 33/69", "High-PV 33/69"),
    ("Initially overvoltage 33/69", "Overvolt 33/69"),
    ("Source PV 0.6 calibration only", "Src only"),
    ("Source + 10% target high-PV calibration", "Src+10% target"),
    ("Source + 20% target high-PV calibration", "Src+20% target"),
    ("full topology/electrical", "full T/E"),
    ("local operating only", "local"),
    ("local+topology", "local+T"),
    ("topology+PV+loading conditioned", "T/PV/L"),
    ("topology+PV+loading no-shrinkage", "No shrinkage"),
    ("topology+PV+loading", "T/PV/L"),
    ("topology/PV/loading conformal", "T/PV/L"),
    ("topology/PV/loading", "T/PV/L"),
    ("PV conditioned", "PV-cond"),
    ("PV-conditioned", "PV-cond"),
    ("topology-conditioned", "Topo-cond"),
    ("global conformal", "Global"),
    ("learned 5/95% quantiles", "5/95% Q"),
    ("90% Gaussian interval", "Gaussian"),
    ("pooled residual quantile", "pooled Q"),
]

TABLE_HEADER_REPLACEMENTS = [
    ("Conformal variant", "Calib."),
    ("Interval source", "Interval"),
    ("False alarm", "FA"),
    ("False alarm mean", "FA mean"),
    ("Missed buses mean", "Missed mean"),
    ("Missed buses", "Missed"),
    ("Scenario recall", "Scen. recall"),
    ("Risky recall mean", "Risky recall"),
    ("Post-screen miss mean", "Post miss"),
    ("Post-action violating scenarios", "Post scen."),
    ("Post-action violating buses", "Post buses"),
    ("Released scenarios mean", "Released"),
    ("Safe-release precision mean", "Safe precision"),
    ("Released risky mean", "Risky released"),
    ("Released severity share mean", "Severity share"),
    ("Released violating buses mean", "Viol. buses"),
    ("AC calls avoided mean", "AC avoided"),
    ("AC calls avoided", "AC avoided"),
    ("Candidate AC audits", "AC audits"),
    ("Audits avoided", "Audits saved"),
    ("Full-best retained", "Best kept"),
    ("Same action as full", "Same action"),
    ("Extra violating scenarios", "Extra scen."),
    ("Extra violating buses", "Extra buses"),
    ("Calibration scale relative to current EV-conditioned split", "Scale"),
    ("Approx. minimum EV-family calibration samples", "Min EV calib."),
    ("Expected EV-conditioning status", "Status"),
]


def compact_markdown_table_labels(markdown: str) -> str:
    """Use compact labels inside tables so generated PDFs remain readable."""

    lines = []
    for line in markdown.splitlines():
        if line.lstrip().startswith("|") and "|" in line[1:]:
            for old, new in TABLE_LABEL_REPLACEMENTS + TABLE_HEADER_REPLACEMENTS:
                line = line.replace(old, new)
        lines.append(line)
    return "\n".join(lines)


def section_from(path: Path, heading: str) -> str:
    text = read(path)
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_start = text.find("\n## ", start + len(marker))
    if next_start < 0:
        return text[start:].strip()
    return text[start:next_start].strip()


def extract_manuscript_parts(text: str) -> dict[str, str]:
    lines = text.strip().splitlines()
    title = lines[0].removeprefix("# ").strip()
    abstract_match = re.search(r"^## Abstract\s*\n(?P<abstract>.*?)(?=\n## )", text, flags=re.S | re.M)
    if not abstract_match:
        raise ValueError("Source manuscript is missing an Abstract section")
    abstract = " ".join(abstract_match.group("abstract").strip().split())
    body = text[abstract_match.end() :].strip()
    body = remove_section(body, "Submission Strategy")
    body = renumber_top_level_sections(body)
    body = strip_manual_heading_numbers(body)
    body = promote_body_headings(body)
    return {"title": title, "abstract": abstract, "body": body}


def remove_section(markdown: str, title_fragment: str) -> str:
    pattern = re.compile(
        rf"^##\s+\d+\.\s+{re.escape(title_fragment)}\s*\n.*?(?=^##\s+\d+\.\s+|\Z)",
        flags=re.S | re.M,
    )
    return pattern.sub("", markdown).strip()


def remove_subsection(markdown: str, title_fragment: str) -> str:
    pattern = re.compile(
        rf"^##\s+(?:\d+(?:\.\d+)*\.?\s+)?{re.escape(title_fragment)}\s*\n.*?(?=^##\s+|^#\s+|\Z)",
        flags=re.S | re.M,
    )
    return pattern.sub("", markdown).strip()


def focus_ecmx_body(markdown: str) -> str:
    """Keep the ECM:X generated manuscript focused on the core method claim."""

    for title in [
        "Forecast-Noise Robustness",
        "Two-Stage Operating Value",
        "Energy Management Value of Screening",
        "Screened-Safe Release Audit",
        "Screening-Budget Triage Value",
        "Paired Statistical Evidence Audit",
        "Candidate-Action Screening Audit",
        "Risk-Cost Candidate-Action Tradeoff",
        "Consolidated Energy-Management Frontier",
        "Operational Runtime Benchmark",
        "Scenario Risk-Ranking Quality",
    ]:
        markdown = remove_subsection(markdown, title)
    return markdown


def renumber_top_level_sections(markdown: str) -> str:
    counter = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        title = match.group(1).strip()
        return f"## {counter}. {title}"

    return re.sub(r"^##\s+\d+\.\s+(.+)$", repl, markdown, flags=re.M)


def strip_manual_heading_numbers(markdown: str) -> str:
    return re.sub(r"^(#{2,6})\s+\d+(?:\.\d+)*\.?\s+(.+)$", r"\1 \2", markdown, flags=re.M)


def promote_body_headings(markdown: str) -> str:
    def repl(match: re.Match[str]) -> str:
        marks = match.group(1)
        return marks[1:] + " " + match.group(2)

    return re.sub(r"^(#{2,6})\s+(.+)$", repl, markdown, flags=re.M)


FIGURE_CATALOG = [
    (
        "fig01_graphical_abstract_workflow",
        "Graphical abstract and VoltGuard screening workflow.",
        "The figure summarizes the active-feeder inputs, LinDistFlow physical backbone, topology-aware residual correction, conformal voltage-risk intervals, and downstream AC-audited corrective optimization interface.",
    ),
    (
        "fig02_feeders_and_splits",
        "Main distribution feeders and generalization protocols.",
        "(a) IEEE 33-bus and 69-bus distribution feeders used as the main experimental systems; (b) executed split protocols for random interpolation, synthetic time-block, PV-shift, and topology-transfer audits.",
    ),
    (
        "fig03_conformal_ablation",
        "Conformal calibration variant comparison.",
        "(a) Empirical coverage across calibration variants; (b) mean interval width; (c) missed bus-level voltage violations.",
    ),
    (
        "fig04_per_family_calibration",
        "Per-family conditioned calibration audit.",
        "The bars show empirical coverage by topology/PV/loading family with sample counts and missed violations, exposing the small-family regimes where shrinkage matters.",
    ),
    (
        "fig05_shift_generalization",
        "Shift generalization across time, PV penetration, and topology transfer.",
        "(a) Multi-seed violation recall under random, synthetic time-block, PV-shift, and topology-transfer splits; (b) corresponding false-alarm rates.",
    ),
    (
        "fig06_operating_value",
        "Two-stage operating value.",
        "(a) Budgeted AC triage performance as the AC-call budget increases; (b) runtime audit comparing VoltGuard screening, budgeted workflows, and full AC search.",
    ),
    (
        "fig07_energy_frontier",
        "Energy-management screening frontier.",
        "(a) Screened-safe release frontier versus nominal coverage; (b) sharpness-risk tradeoff between interval width and missed bus violations.",
    ),
    (
        "fig08_screening_budget",
        "Screening-budget triage quality.",
        "Severity captured under limited AC-call budgets is compared across VoltGuard, boosting-global, random-budget, and oracle ranking policies.",
    ),
    (
        "fig09_candidate_action_screening",
        "Candidate-action screening value.",
        "(a) AC candidate audits avoided as the number of retained candidates varies; (b) extra post-action violating scenarios relative to full AC grid search.",
    ),
    (
        "fig10_risk_ranking_quality",
        "Scenario risk-ranking quality.",
        "(a) ROC-AUC and average-precision ranking metrics for scenario risk scores; (b) cumulative severity captured by the top-ranked scenario fraction.",
    ),
    (
        "fig11_oajpe_lindistflow_quantile_pipeline",
        "LinDistFlow-Quantile baseline pipeline.",
        "The baseline note uses forecast inputs, a squared-voltage LinDistFlow proxy, and one global empirical quantile before downstream AC audit.",
    ),
    (
        "fig12_oajpe_minimal_performance",
        "Minimal baseline performance summary.",
        "(a) LinDistFlow voltage error across seeds; (b) empirical coverage and mean interval width for the global quantile interval; (c) scenario-level screening behavior.",
    ),
]


ROUTE_FIGURES = {
    "ecmx": [item[0] for item in FIGURE_CATALOG[:5]],
    "ecm": ["fig01_graphical_abstract_workflow"],
    "oajpe": [
        "fig11_oajpe_lindistflow_quantile_pipeline",
        "fig12_oajpe_minimal_performance",
    ],
}


ROUTE_FIGURE_PLACEMENTS = {
    "ecmx": [
        ("Introduction", ["fig01_graphical_abstract_workflow"]),
        ("Experimental Design", ["fig02_feeders_and_splits"]),
        ("Conformal Ablation", ["fig03_conformal_ablation"]),
        ("Per-Family Calibration Analysis", ["fig04_per_family_calibration"]),
        ("Shift and Scenario-Level Results", ["fig05_shift_generalization"]),
    ],
    "ecm": [("System Integration Architecture", ["fig01_graphical_abstract_workflow"])],
    "oajpe": [
        ("Baseline Method", ["fig11_oajpe_lindistflow_quantile_pipeline"]),
        ("Results", ["fig12_oajpe_minimal_performance"]),
    ],
}


def figure_block(name: str, idx: int, route: str) -> str:
    catalog = {item[0]: item for item in FIGURE_CATALOG}
    _, title, caption = catalog[name]
    if route == "oajpe" and name == "fig11_oajpe_lindistflow_quantile_pipeline":
        return "\n".join(
            [
                r"\begin{figure*}[t]",
                r"\centering",
                rf"\includegraphics[width=0.94\textwidth]{{figures/{name}.pdf}}",
                rf"\caption{{{title} {caption}}}",
                rf"\label{{fig:{name}}}",
                r"\end{figure*}",
            ]
        )
    if route == "oajpe":
        return "\n".join(
            [
                r"\begin{figure}[t]",
                r"\centering",
                rf"\includegraphics[width=\linewidth]{{figures/{name}.pdf}}",
                rf"\caption{{{title} {caption}}}",
                rf"\label{{fig:{name}}}",
                r"\end{figure}",
            ]
        )
    return (
        f"![{title} {caption}](figures/{name}.pdf)"
        f"{{#fig:{name} width=110%}}"
    )


def heading_pattern(heading: str) -> re.Pattern[str]:
    return re.compile(rf"^(#+)\s+{re.escape(heading)}\s*$", flags=re.M)


def insert_after_section(markdown: str, heading: str, blocks: list[str]) -> str:
    match = heading_pattern(heading).search(markdown)
    if not match:
        raise ValueError(f"Figure placement heading not found: {heading}")
    level = len(match.group(1))
    next_heading = re.compile(rf"^#{{1,{level}}}\s+", flags=re.M)
    next_match = next_heading.search(markdown, match.end())
    insert_at = next_match.start() if next_match else len(markdown)
    figure_text = "\n\n" + "\n\n".join(blocks) + "\n\n"
    return markdown[:insert_at].rstrip() + figure_text + markdown[insert_at:].lstrip("\n")


def insert_figures(route: str, body: str) -> str:
    ordered_names = [
        name
        for _, names in ROUTE_FIGURE_PLACEMENTS[route]
        for name in names
    ]
    figure_numbers = {name: idx for idx, name in enumerate(ordered_names, start=1)}
    for heading, names in ROUTE_FIGURE_PLACEMENTS[route]:
        blocks = [figure_block(name, figure_numbers[name], route) for name in names]
        body = insert_after_section(body, heading, blocks)
    return body


def clean_declarations(route: str) -> str:
    if route in {"ecmx", "ecm"}:
        return "\n".join(
            [
                "# Declaration of Competing Interest {.unnumbered}",
                "",
                "The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.",
                "",
                "# Funding {.unnumbered}",
                "",
                "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.",
                "",
                "# Code and Data Availability {.unnumbered}",
                "",
                "The experiments use publicly available IEEE test systems implemented through pandapower and a project-local IEEE 69-bus feeder implementation. The local reproducibility package includes the scenario generator, configured evaluation pipeline, conformal calibration code, raw predictions, conformal scores, runtime tables, post-action AC audit outputs, DMS prototype logs, reviewer-requested baseline comparisons, and energy-management value metrics. File-level checksums and reproduction commands are recorded in `experiments/results/reproducibility_manifest.json` and `experiments/results/reproducibility_manifest.md`. The Python implementation, synthetic scenario-generation scripts, trained model artifacts, table-generation scripts, manuscript sources, and release PDFs are archived in the GitHub repository `Zhaosiqiang/voltguard-voltage-risk-screening`, release `v1.0.0-submission`, and on Zenodo with DOI `10.5281/zenodo.21149702`.",
                "",
                "# Declaration of Generative AI and AI-Assisted Technologies in the Writing Process {.unnumbered}",
                "",
                "During the preparation of this work, the authors used AI-assisted coding and language tools for drafting support, code scaffolding, consistency checks, and language refinement. The authors reviewed and edited all generated text and code, verified the equations and numerical claims, and take full responsibility for the content of the article.",
            ]
        )
    return "\n".join(
        [
            "# Acknowledgment {.unnumbered}",
            "",
            "The authors thank the maintainers of the open-source power-system modeling tools and public benchmark feeders used in this study.",
            "",
            "# Funding {.unnumbered}",
            "",
            "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.",
            "",
            "# Code and Data Availability {.unnumbered}",
            "",
            "The experiments use publicly available IEEE test systems implemented through pandapower and a project-local IEEE 69-bus feeder implementation. The baseline implementation, scenario-generation scripts, table-generation scripts, manuscript sources, and release PDFs are archived in the GitHub repository `Zhaosiqiang/voltguard-voltage-risk-screening`, release `v1.0.0-submission`, and on Zenodo with DOI `10.5281/zenodo.21149702`.",
            "",
            "# Conflict of Interest {.unnumbered}",
            "",
            "The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.",
            "",
            "# AI Tool Use Disclosure {.unnumbered}",
            "",
            "During the preparation of this work, the authors used AI-assisted coding and language tools for drafting support, code scaffolding, consistency checks, and language refinement. The authors reviewed and edited all generated text and code, verified the equations and numerical claims, and take full responsibility for the content of the article.",
        ]
    )


ROUTES = {
    "ecmx": {
        "path": ROOT / "submission_manuscript_ecmx.md",
        "source": ROOT / "manuscript_draft.md",
        "references": ROOT / "submission_references_ecmx_ecm.md",
        "journal": "Energy Conversion and Management: X",
        "style": "elsevier",
        "title": "VoltGuard: Topology-Aware Voltage-Risk Screening with Conformal Calibration for Active Distribution Networks",
        "target": "Energy Conversion and Management: X (main complete AI + energy-management route).",
        "positioning": "Full method, full uncertainty boundary, and full energy-management evidence.",
        "highlights": [
            "LinDistFlow residual learning supports renewable-hosting voltage-risk screening.",
            "Topology/PV/loading conformal calibration reduces missed voltage violations.",
            "IEEE 33-bus and 69-bus feeders are the main distribution tests.",
            "Shift and per-family audits define the method boundary.",
            "Neural graph residual learning is retained only as an ablation.",
        ],
        "keywords": [
            "Physics-informed machine learning",
            "Conformal prediction",
            "Topology-aware learning",
            "Active distribution networks",
            "Voltage security",
            "Risk screening",
            "Renewable hosting",
        ],
    },
    "ecm": {
        "path": ROOT / "submission_manuscript_ecm.md",
        "source": ROOT / "manuscript_ecm_engineering.md",
        "references": ROOT / "submission_references_ecmx_ecm.md",
        "journal": "Energy Conversion and Management",
        "style": "elsevier",
        "title": "VoltGuard-ECM: A DMS Integration Architecture for AC-Audited Voltage-Risk Screening in High-DER Distribution Networks",
        "target": "Energy Conversion and Management engineering route (system implementation and runtime/application route).",
        "positioning": "DMS integration architecture, data contracts, fallback rules, and AC-audit handoff semantics.",
        "highlights": [
            "VoltGuard-ECM frames voltage-risk screening as DMS integration.",
            "The paper specifies data contracts for release, watch, and audit queues.",
            "Fallback rules govern telemetry faults and out-of-envelope forecasts.",
            "The screen is a front end for AC power flow, OPF, or MPC.",
            "No method-performance claim is reused from the main manuscript.",
        ],
        "keywords": [
            "Distribution operation",
            "Voltage-risk screening",
            "DMS integration",
            "Queue semantics",
            "DER operation",
            "AC audit",
            "Fallback rules",
        ],
    },
    "oajpe": {
        "path": ROOT / "submission_manuscript_oajpe.md",
        "source": ROOT / "manuscript_oajpe_minimal.md",
        "references": ROOT / "submission_references_oajpe.md",
        "journal": "IEEE Open Access Journal of Power and Energy",
        "style": "ieee",
        "title": "LinDistFlow-Quantile Screen: A Baseline Heuristic for Distribution Voltage-Risk Filtering",
        "target": "IEEE Open Access Journal of Power and Energy fallback route (baseline LinDistFlow-quantile engineering note).",
        "positioning": "Baseline LinDistFlow screening heuristic with one global quantile and no residual learner or conditioned calibration.",
        "highlights": [
            "A baseline heuristic combines LinDistFlow and one empirical quantile.",
            "The note reports LinDistFlow-only behavior on IEEE 33/69 scenarios.",
            "The global quantile exposes the conservatism of an unconditioned radius.",
            "No residual learner or family-conditioned calibration claim is made.",
            "The result is a reproducible baseline, not a control method.",
        ],
        "keywords": [
            "LinDistFlow",
            "Quantile calibration",
            "Voltage risk",
            "Distribution feeders",
            "Screening baseline",
        ],
    },
}


def front_matter(route: str, config: dict, parts: dict[str, str]) -> str:
    keywords = "; ".join(config["keywords"])
    if config["style"] == "elsevier":
        return "\n".join(
            [
                "# Title Page {.unnumbered}",
                "",
                f"**Journal:** {config['journal']}",
                "",
                f"**Article title:** {config['title']}",
                "",
                "**Authors and affiliations:**",
                "",
                "Siqiang Zhao$^{a,*}$; Fengxiang Zhang$^{b}$",
                "",
                "$^{a}$ Sichuan University-Pittsburgh Institute, Chengdu, China",
                "",
                "$^{b}$ Southwest Jiaotong University, Chengdu, China",
                "",
                "$^{*}$ Corresponding author. Email: 2023141520257@stu.scu.edu.cn",
                "",
                "# Abstract {.unnumbered}",
                "",
                parts["abstract"],
                "",
                "# Keywords {.unnumbered}",
                "",
                keywords,
            ]
        )
    return "\n".join(
        [
            "Siqiang Zhao, Sichuan University-Pittsburgh Institute, Chengdu, China, 2023141520257@stu.scu.edu.cn; Fengxiang Zhang, Southwest Jiaotong University, Chengdu, China, zfengxiang309@gmail.com.",
            "",
            "**Corresponding author:** Siqiang Zhao, 2023141520257@stu.scu.edu.cn.",
            "",
            "# Abstract {.unnumbered}",
            "",
            parts["abstract"],
            "",
            "# Index Terms {.unnumbered}",
            "",
            keywords,
        ]
    )


def write_highlights(route: str, config: dict) -> None:
    if config["style"] != "elsevier":
        return
    path = ROOT / f"{route}_highlights.txt"
    lines = [f"- {item}" for item in config["highlights"]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def assemble_route(route: str, config: dict) -> str:
    parts = extract_manuscript_parts(read(config["source"]))
    if route == "ecmx":
        parts["body"] = focus_ecmx_body(parts["body"])
    body = insert_figures(route, parts["body"])
    references = read(config.get("references", ROOT / "submission_references.md"))
    references = re.sub(r"^# References\s*", "# References {.unnumbered}\n", references)
    write_highlights(route, config)

    out = []
    out.append("---")
    out.append(f'title: "{config["title"]}"')
    out.extend(author_yaml(config["style"]))
    if config["style"] == "elsevier":
        out.append("documentclass: elsarticle")
        out.append("classoption: preprint,12pt")
    else:
        out.append("documentclass: IEEEtran")
        out.append("classoption: journal")
    out.append("header-includes:")
    out.append("  - \\usepackage{graphicx}")
    out.append('date: "Generated ' + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + '"')
    if config["style"] == "elsevier":
        out.append("geometry: margin=1in")
    out.append('mainfont: "Times New Roman"')
    out.append('mathfont: "STIX Two Math"')
    out.append("---\n")
    out.append(front_matter(route, config, parts) + "\n")
    out.append(body + "\n")
    out.append(clean_declarations(route) + "\n")
    out.append(references + "\n")

    return compact_markdown_table_labels("\n".join(out)) + "\n"


def main() -> int:
    for route, config in ROUTES.items():
        text = assemble_route(route, config)
        config["path"].write_text(text, encoding="utf-8")
        print(f"Wrote {config['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
