# Venue Source Audit

Generated for the revised Energy Conversion and Management: X cycle-first
route. This file separates official scope/speed evidence from route decisions.
All metrics, APCs, article types, and submission-system fields must be
rechecked immediately before live upload.

## Decision Rule

The route is selected by:

1. Short review cycle and transparent journal workflow.
2. Strong fit to active-distribution energy management and renewable operation.
3. Adequate impact and visibility without overclaiming a full OPF/MPC
   controller.
4. Stable fallback options if the editor asks for a different framing.

The current recommendation is:

1. **Energy Conversion and Management: X** as the main cycle-first target.
2. **Energy and AI** as the second route if the paper is reframed toward
   trustworthy AI and calibrated uncertainty for energy systems.
3. **Advances in Applied Energy** or **Applied Energy** as stretch routes if
   IEEE 123-bus/OpenDSS or SMART-DS validation and a stronger downstream
   OPF/MPC benchmark are added.
4. **IEEE Open Access Journal of Power and Energy**, IEEE Access, or Energies
   as fallback routes if the author prioritizes publication-cycle stability
   over impact.

## Official Evidence

Live public-page spot check on 2026-07-02 using the ScienceDirect journal and
Journal Insights pages. The values below are routing evidence, not permanent
bibliometric facts; they must be rechecked in the live portal before upload.

| Venue | Official source | Current evidence and implication |
|---|---|---|
| Energy Conversion and Management: X | https://www.sciencedirect.com/journal/energy-conversion-and-management-x and https://www.sciencedirect.com/journal/energy-conversion-and-management-x/about/insights | ScienceDirect reports impact factor 7.6, CiteScore 11.3, 3 days to first decision, 31 days to decision after review, and 81 days from submission to acceptance. The journal scope covers energy generation, utilization, conversion, storage, transmission, conservation, management, and sustainability, including renewable resources, electric energy, operation, performance, maintenance, control, modeling, analysis, and optimization. This is the best current fit for VoltGuard when framed as calibrated renewable-hosting voltage-risk screening and active-distribution energy management. |
| Energy and AI | https://www.sciencedirect.com/journal/energy-and-ai and https://www.sciencedirect.com/journal/energy-and-ai/about/insights | ScienceDirect reports impact factor 9.6, CiteScore 16.5, 6 days to first decision, 57 days to decision after review, and 116 days from submission to acceptance. The scope explicitly connects artificial intelligence and energy systems. This is a strong second route if the manuscript foregrounds trustworthy AI, calibrated uncertainty, and energy-system decision support. |
| Advances in Applied Energy | https://www.sciencedirect.com/journal/advances-in-applied-energy and https://www.sciencedirect.com/journal/advances-in-applied-energy/about/insights | ScienceDirect reports impact factor 13.8, CiteScore 32.6, 1 day to first decision, 22 days to decision after review, and 66 days from submission to acceptance. Its scope includes renewable energy, smart grids, distributed energy systems, e-mobility, and flexible system integration. VoltGuard should only use this route after adding broader feeder validation and a stronger operational benchmark. |
| Applied Energy | https://www.sciencedirect.com/journal/applied-energy and https://www.sciencedirect.com/journal/applied-energy/about/insights | ScienceDirect reports impact factor 11.0, CiteScore 20.1, 1 day to first decision, 54 days to decision after review, and 127 days from submission to acceptance. Its scope includes energy modeling, forecasting, optimization, decision-making, smart grids, AI applications in energy, and power-system planning/operation. It is a strong stretch target if the paper demonstrates larger-scale renewable-hosting value and stronger downstream optimization evidence. |
| IEEE Open Access Journal of Power and Energy | https://ieee-pes.org/publications/authors-kit/preparation-and-submission-of-papers-for-the-ieee-open-access-journal-of-power-and-energy/ | Strong power-and-energy engineering fit and useful fallback route. The IEEE PES author page reports a 2026 Article Processing Charge of US$2160, pricing up to a maximum of 11.5 final accepted pages, a 150--200 word abstract expectation, and up to ten keywords. It is no longer the primary recommendation because the current strategy prioritizes ECM:X visibility and fast Elsevier-cycle metrics, but the OAJPE minimal version now includes these submission checks. |
| IEEE AI/tool-use disclosure | https://www.ieee-ras.org/publications/guidelines-for-generative-ai-usage/ and https://ieee-aess.org/using-ai-generated-content-ieee-article-and-its-review | IEEE guidance requires disclosure of AI-generated content in the article, identification of the AI system and affected sections, and author responsibility for all content. AI systems must not be listed as authors. The OAJPE minimal route should retain a journal-compliant AI/tool-use disclosure before upload. |

## Source-Control Notes

- Use ScienceDirect journal and Journal Insights pages as the operational
  source for Elsevier scope, APC, impact, CiteScore, and timeline fields.
- Do not use search-engine snippets, third-party journal-metrics pages, or
  cached AI summaries as the final upload source when they disagree with the
  live ScienceDirect page.
- Bibliometric values can change after annual JCR/CiteScore updates. If any
  value changes before submission, update `submission_strategy.md`,
  `high_impact_venue_matrix.md`, the cover letter route paragraph, and the
  final manuscript discussion consistently.

## Manuscript Routing Consequences

For **Energy Conversion and Management: X**, the manuscript must foreground:

- renewable-hosting voltage-risk screening,
- active-distribution energy-management value,
- avoided AC optimization calls and risk-prioritized scenario triage,
- physics-informed residual learning and conformal uncertainty calibration,
- AC-audited screening boundaries rather than controller replacement claims.

For **Energy and AI**, the manuscript should emphasize:

- trustworthy AI for energy systems,
- conformal calibration under structured scenario families,
- uncertainty-aware decision support,
- graph/neural models only as ablation unless they clearly dominate.

For **Advances in Applied Energy** or **Applied Energy**, the manuscript needs
additional evidence:

- IEEE 123-bus/OpenDSS or SMART-DS external feeder validation,
- stronger PV hosting and cost/curtailment metrics,
- downstream OPF/MPC comparison rather than only AC-audited grid search,
- sensitivity to PV, EV, topology, and temporal shifts.

## Manual Checks Before Upload

- Current live Guide for Authors article type, word/figure limits, reference
  style, highlights, graphical abstract, and declaration requirements.
- Current APC, license, waiver, and institutional agreement status.
- Current JCR/CAS records from the author's institution or official indexing
  sources.
- Submission-system fields and journal-specific AI/tool-use disclosure.
- For OAJPE specifically, recheck the live IEEE PES author page for APC,
  abstract length, page limit, figure/table files, code/data availability, and
  AI/tool-use disclosure before upload.
