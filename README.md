# VoltGuard-CPGNN

Fresh paper workspace for a new AI + electrical engineering study:

**VoltGuard: Topology-Aware Voltage-Risk Screening with Conformal Calibration
for Active Distribution Networks**

This project is intentionally independent from any previous local manuscript
package. It targets a cycle-first high-impact journal path while keeping
IEEE-style engineering discipline.

## Core Idea

High photovoltaic, EV, and flexible-load penetration makes distribution
voltage security hard to assess from noisy forecasts and sparse measurements.
Pure point predictors can be accurate on average but unreliable at the voltage
limits that matter operationally. VoltGuard combines:

- a squared-voltage LinDistFlow physical backbone,
- topology-aware residual learning,
- conformal calibration for voltage uncertainty intervals,
- a risk-screening index that can trigger downstream AC-audited grid search,
  OPF, or MPC.

The paper is designed around a concrete operating problem: estimating and
screening voltage violations in IEEE 33-bus and IEEE 69-bus distribution feeders
under renewable and load uncertainty, then comparing against physics-only,
classical machine-learning, conformal, neural-ablation, and optimization-style
corrective-control baselines. It now also reports paired seed-level deltas,
tests EV-conditioned calibration, audits undercovered calibration families,
audits asymmetric one-sided conformal calibration,
evaluates scenario-level risk ranking, audits forecast-noise robustness,
audits PV-shift target recalibration and its screened-safe release tradeoff,
audits risk-stratified calibration near voltage limits, audits the true safety of screened-safe released scenarios,
including three-seed screening-value and release reliability checks, repeats
the screening-value audit across random/time-block/PV-shift/topology-held-out
splits, adds a bidirectional 33-to-69/69-to-33 topology-transfer audit, and
tests limited-budget AC-audited optimization triage, including severity capture, post-policy
severity reduction, avoided AC calls, action-cost proxies, candidate-action
AC-audit pruning with a three-seed companion audit, a three-seed budgeted
triage companion audit, risk-versus-action-cost
tradeoffs with a three-seed companion audit, calibration-budget
sensitivity, and operational runtime speedup under budgeted AC-audit triage. It
also audits feature/residual
ablations and branch-level LinDistFlow voltage-drop
consistency for saved predictions so the topology-aware and physics-informed
claims are checked against computable evidence rather than left as prose. A
supplementary high-PV hosting stress audit covers overvoltage and
PV-curtailment behavior in IEEE 33/69, including a full accepted-PV versus
overvoltage-reduction frontier over the 0%-50% curtailment grid. IEEE 118-bus is retained only as a
supplementary stress test.

## Files

- `topic_scoping.md` - final topic selection, novelty, venue rationale, and
  rejected alternatives.
- `manuscript_draft.md` - English paper draft with problem formulation,
  methodology, experiments, and discussion.
- `experiment_plan.md` - reproducible experiment design, datasets, baselines,
  metrics, and expected tables/figures.
- `implementation_roadmap.md` - executable roadmap from scenario generation to
  manuscript finalization.
- `result_table_templates.md` - executed table index with authoritative source
  result files.
- `experiment_results.md` - executed first-pass numerical results and claim
  boundaries.
- `figure_descriptions.md` - concrete article figure descriptions; no figures
  are generated yet.
- `submission_strategy.md` - target journal strategy and fast-review path.
- `submission_variant_strategy.md` - route-differentiation rules for the
  ECM:X full-method, ECM engineering-system, and OAJPE minimal-pipeline
  drafts.
- `venue_source_audit.md` - official scope, speed, and metric audit for the
  cycle-first high-impact route.
- `high_impact_venue_matrix.md` - ranked venue matrix with route decisions.
- `claim_evidence_matrix.md` - claim-to-artifact and reviewer-risk matrix
  used to keep the ECM:X manuscript grounded in completed evidence.
- `experiments/results/statistical_evidence_metrics.md` - paired split/seed
  delta audit with bootstrap intervals for the main prediction and budgeted
  AC-triage claims.
- `references.bib` - BibTeX bibliography backing the numbered submission
  references.
- `submission_references.md` - numbered reference list used by the generated
  ECM:X manuscript.
- `completion_audit.md` - current completion status against the active goal.
- `submission_ancillaries.md` - cover letter, highlights, keywords, and
  declaration templates.
- `ecmx_highlights.txt` - separate editable highlights file for ECM:X upload.
- `ecmx_cover_letter.md` - separate editable cover-letter draft for ECM:X
  upload.
- `ecmx_submission_readiness_checklist.md` - official-guide-aligned ECM:X
  upload checklist and remaining manual gates.
- `ecmx_upload_input_packet.md` - fill-in packet for author metadata,
  declarations, portal text, figure decisions, and hard-stop upload checks.
- `submission_manuscript_ecmx.md` - primary assembled ECM:X submission
  manuscript.
- `submission_manuscript_ecmx.tex` - Pandoc-generated LaTeX conversion aid for
  the primary ECM:X manuscript.
- `submission_manuscript_ecm.md` - differentiated engineering-system version
  emphasizing AC-call reduction, runtime, and downstream AC audit.
- `submission_manuscript_oajpe.md` - differentiated minimal fallback version
  emphasizing LinDistFlow residual correction, quantile intervals, RMSE,
  coverage, and AC-call reduction.
- `submission_compile_report.md` - PDF smoke-test report and remaining upload
  boundaries.
- `author_declaration_gate.md` - real metadata and declaration gate that blocks
  upload until filled by the author.
- `experiments/results/reproducibility_manifest.json` - file-level checksums,
  commands, and artifact inventory for local reproducibility.
- `experiments/results/reproducibility_manifest.md` - readable summary of the
  reproducibility manifest.
- `GITHUB_ZENODO_RELEASE_CHECKLIST.md` - repository and DOI-release preparation
  checklist for the manuscript package.
- `CITATION.cff` - citation metadata stub for the planned public release.
- `.zenodo.json` - Zenodo metadata for DOI minting after repository integration.
- `LICENSE` - MIT license for code, experiment scripts, configuration files,
  and reproducibility artifacts.

## Recommended High-Impact Target

Cycle-first route: **Energy Conversion and Management: X**, because the revised
paper is an active-distribution energy-management manuscript and the official
ScienceDirect page reports IF 7.6, CiteScore 11.3, 3 days to first decision, 31
days to decision after review, and 81 days to acceptance.
The exact source URLs and the recheck rule are recorded in
`venue_source_audit.md`; reverify the live ScienceDirect journal and Journal
Insights pages before upload.

Second route: **Energy and AI**, if the paper is reframed toward trustworthy AI
and calibrated uncertainty for energy systems.

Stretch routes: **Advances in Applied Energy** or **Applied Energy**, if the
paper is extended with IEEE 123-bus/OpenDSS or SMART-DS validation and a full
OPF/MPC downstream benchmark.
