# Cycle-First Submission Strategy

The revised paper should be routed as an AI-assisted active-distribution energy
management manuscript, not as a narrow IEEE voltage-prediction paper.

## Source Basis

Venue metrics in this file were checked on 2026-07-02 against the official
ScienceDirect journal and Journal Insights pages listed in
`venue_source_audit.md`. They should be treated as current routing inputs, not
as immutable facts. Recheck the live pages immediately before submission.

## First Target: Energy Conversion and Management: X

Energy Conversion and Management: X is the preferred route because it balances
cycle speed, impact factor, and thematic fit. The official ScienceDirect page
reports:

- Impact Factor: 7.6.
- CiteScore: 11.3.
- Submission to first decision: 3 days.
- Submission to decision after review: 31 days.
- Submission to acceptance: 81 days.
- Scope covering energy generation, utilization, conversion, storage,
  transmission, conservation, management, sustainability, renewable resources,
  operation, performance, maintenance, control, modeling, analysis, and
  optimization.

VoltGuard should therefore be framed as:

- a renewable-hosting voltage-risk screening layer,
- an active distribution energy-management method,
- a calibrated pre-optimization filter for DER/PV/EV/load scenarios,
- a modeling + analysis + optimization-interface contribution verified by AC
  power flow and downstream grid-search audit.

## Three Independent Manuscript Questions

The package now contains three drafts with different scientific questions.
They are not intended for simultaneous submission and must not reuse the same
central result package.

- **ECM:X method paper**: `submission_manuscript_ecmx.md` asks whether
  topology-aware residual learning plus topology/PV/loading conditioned
  conformal calibration improves voltage-risk interval screening. The main
  evidence is prediction, calibration, per-family, ablation, and shift
  behavior.
- **ECM DMS integration paper**: `submission_manuscript_ecm.md` asks what DMS
  data contracts, queue semantics, fallback rules, and audit records are
  required before a calibrated screen can influence operations. It does not
  reuse the ECM:X numerical result package.
- **OAJPE baseline note**: `submission_manuscript_oajpe.md` asks how a
  LinDistFlow physical proxy with one pooled empirical quantile behaves as a
  transparent baseline. It contains no residual learner, graph model,
  family-conditioned calibration, AC-budget, or runtime claim. It may include a
  clearly labeled comparison with VoltGuard to satisfy baseline-context review
  requests, but the learned-method result is not the note's contribution.

The differentiation rule is recorded in `submission_variant_strategy.md`.
Before any later submission, check text reuse, central-claim overlap, and
related-work disclosure requirements.

## Second Target: Energy and AI

Energy and AI is the second route. Its official page reports Impact Factor 9.6,
16.5 CiteScore, 6 days to first decision, 57 days to decision after review,
and 116 days to acceptance. It fits if the manuscript emphasizes trustworthy
AI, calibrated uncertainty, conformal learning, physics-data hybrid modeling,
and AI safety in energy applications.

## Stretch Routes: Advances in Applied Energy / Applied Energy

Advances in Applied Energy is attractive because the official page reports a
13.8 impact factor, 32.6 CiteScore, 1 day to first decision, 22 days to
decision after review, and 66 days to acceptance, and its scope covers applied
energy innovation, renewable energy, smart grids, distributed energy systems,
e-mobility, and flexible system integration. Applied Energy is also highly
relevant to energy-related modeling, forecasting, decision-making, and
power-system operation; its official page reports 11.0 impact factor and 127
days to acceptance, so it is a stronger but slower stretch route.

Use these routes only after adding at least one stronger external validation:

- IEEE 123-bus/OpenDSS or SMART-DS feeder,
- unbalanced or larger-scale distribution validation,
- downstream OPF/MPC benchmark beyond discrete grid search.

## Fallback Routes

IEEE Open Access Journal of Power and Energy remains technically credible and
well aligned with power-system scope, but it is no longer the first target
because the current strategy prioritizes a non-low impact factor once review
speed is acceptable. IEEE Access and Energies remain fallback-only routes.
