# Three Independent Manuscript Questions

This file prevents the three drafts from being treated as one paper packaged
three ways. The manuscripts are not simultaneous submissions. Each draft must
answer a different scientific or engineering question and must not reuse the
same central result package.

## Non-Overlap Rule

Do not submit more than one draft unless the later submission is rewritten as
a genuinely different study with appropriate disclosure. A draft is considered
overlapping if it reuses the same central claim, method hierarchy, and evidence
table. The current separation is:

- **ECM:X method paper:** asks whether topology-aware residual learning plus
  topology/PV/loading conditioned conformal calibration gives sharper and safer
  voltage-risk intervals than global or point baselines.
- **ECM DMS integration paper:** asks what DMS data contracts, queue semantics,
  fallback rules, and audit records are required before any calibrated screen
  can be used in operations.
- **OAJPE baseline note:** asks how a transparent LinDistFlow physical proxy
  with one pooled empirical quantile behaves as a reproducible lower-complexity
  reference.

## ECM:X Method Paper

Central contribution: topology-aware residual learning with conditioned
conformal calibration for voltage-risk screening.

Main evidence:

- LinDistFlow residual correction and topology/electrical features.
- Topology/PV/loading conditioned conformal calibration with shrinkage.
- Per-family calibration, conformal ablation, feature ablation, and shift
  tests that support the interval-screening claim.
- Neural graph residual learning only as an ablation.

Not central:

- DMS integration architecture.
- AC-call budgeting, candidate-action pruning, runtime, and energy frontier
  analyses. These may remain project artifacts or supplementary audits, but
  they should not define the ECM:X contribution.

## ECM DMS Integration Paper

Central contribution: system integration governance for calibrated
voltage-risk screening in a DMS.

Main evidence:

- Input data contract for forecasts, topology, feeder model, and telemetry.
- Release/watch/corrective-audit queue semantics.
- Fallback and drift-governance rules.
- Audit-record schema tying screening decisions to downstream AC outcomes.

Forbidden overlap:

- Do not reuse the ECM:X prediction RMSE, coverage, interval-width,
  release-count, AC-call-avoidance, or runtime result package.
- Do not claim learning-method novelty.
- Treat the screening model as a replaceable module inside a DMS architecture.

## OAJPE Baseline Note

Central contribution: a minimal LinDistFlow plus global-quantile reference
implementation.

Main evidence:

- Squared-voltage LinDistFlow equations.
- One pooled empirical quantile radius.
- LinDistFlow-only voltage error, global interval width/coverage, and
  scenario-level screening behavior.
- Reviewer-requested side-by-side comparison with VoltGuard is allowed only as
  context for interpreting when the baseline is sufficient; it must not become
  the baseline note's central contribution.

Forbidden overlap:

- No residual learner.
- No topology/PV/loading conditioned calibration.
- No graph model.
- No AC-call-budget, runtime, OPF/MPC, or energy-management result package.

This separation keeps the drafts reviewer-proof: they are not shorter and
longer versions of one paper, but answers to three different questions.
