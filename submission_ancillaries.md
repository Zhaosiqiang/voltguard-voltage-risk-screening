# Submission Ancillaries

Prepared for the cycle-first Energy Conversion and Management: X route. Fill
bracketed fields with real author and submission information before upload.

## Proposed Title

VoltGuard: Physics-Informed Topology-Aware Residual Learning with Conformal
Calibration for Renewable-Hosting Voltage-Risk Screening in Active Distribution
Networks

## Highlights

- LinDistFlow residual learning supports renewable-hosting voltage-risk screening.
- Topology/PV/loading conformal calibration reduces missed voltage violations.
- IEEE 33-bus and 69-bus feeders are the main distribution tests.
- Three-seed release audit finds zero risky released scenarios.
- VoltGuard screens risk before AC grid search, OPF, or MPC.

## Keywords

Physics-informed machine learning; conformal prediction; topology-aware
learning; active distribution networks; voltage security; risk screening;
renewable hosting; energy management; DER operation

## Cover Letter Draft

See also `ecmx_cover_letter.md`, which is prepared as the separate editable
cover-letter upload draft.

Dear Editor,

We submit the manuscript entitled "VoltGuard: Physics-Informed Topology-Aware
Residual Learning with Conformal Calibration for Renewable-Hosting Voltage-Risk
Screening in Active Distribution Networks" for consideration in Energy
Conversion and Management: X.

The manuscript addresses a practical active-distribution energy-management
problem: how to screen renewable-hosting voltage-risk scenarios under DER, PV,
EV, and flexible-load uncertainty without running expensive corrective
optimization for every forecasted operating point. VoltGuard combines a
squared-voltage LinDistFlow backbone, a topology-aware residual learner, and
split conformal calibration conditioned on feeder, PV, and loading families.
The method is positioned as a calibrated pre-optimization screening layer that
can trigger downstream AC-audited grid search, OPF, or MPC.

Executed experiments on IEEE 33-bus and IEEE 69-bus distribution feeders show
that VoltGuard improves the coverage-sharpness-risk tradeoff relative to global
conformal calibration. On the representative random split, it achieves 0.00011
p.u. RMSE, 93.66% empirical coverage for nominal 90% intervals, 99.89%
bus-level violation recall, and reduces missed bus-level violations from 3
under boosting plus global conformal calibration to 1. Across three random
seeds, it reduces the mean missed violations from 1.67 to 0.33 and the mean
interval width from 0.00127 to 0.00051 p.u. The family recalibration audit also
reports where conditioned conformal intervals remain weak and how much
inflate-only recalibration changes coverage and sharpness. Additional
energy-management metrics quantify clean screened-safe releases, avoided AC
optimization calls, post-screening miss rate, interval width, accepted PV
proxy, relieved-load proxy, and proxy action cost across conformal risk levels.
At 90% nominal coverage, VoltGuard reduces missed bus-level violations from 3
to 1 relative to the global conformal comparator while avoiding 27 of 120
downstream AC calls; a release audit finds zero truly risky scenarios and zero
violation severity among those 27 released scenarios. Across three random
seeds, the screening-value audit avoids 27.33 AC calls on average with zero
scenario-level post-screening misses, and the release audit keeps zero
released risky scenarios while releasing 27.33 scenarios on average. At 80%
nominal coverage, it misses ten fewer bus-level violations than boosting plus
global conformal calibration. A shift-aware screening audit further keeps zero
scenario-level post-screening misses across random interpolation, synthetic
time-block, PV-penetration shift, and topology-held-out transfer protocols.
The topology-transfer audit is repeated in both 33-to-69 and 69-to-33
directions with target-feeder calibration, keeping zero mean missed risky
scenarios in both directions.
Under PV shift, adding 16 target high-PV calibration scenarios removes the
remaining bus-level miss, but reduces screened-safe releases from 57.00 to
49.67 scenarios and widens intervals, making the recalibration cost explicit.
The separate high-PV hosting frontier keeps 1620 AC candidate outcomes over
the 0%-50% PV-curtailment grid and reports accepted PV, curtailed PV, and
overvoltage-reduction tradeoffs.
Scenario risk-ranking analysis further shows that the
topology+PV+loading conditioned variant
achieves 1.000 average precision and 0.99985 Spearman correlation between
interval risk score and realized violation severity. Under a 20%
AC-optimization-call budget, the same screening signal captures 52.59% of
realized violation severity while avoiding 96 of 120 AC calls, compared with
19.98% severity capture for a random budget. A three-seed candidate-action
audit further shows that top-three VoltGuard action pruning avoids 720 of 1080
candidate AC power-flow audits per seed on average without adding post-action
violating scenarios or buses relative to full grid search, at an explicit proxy
action-cost increase. A companion risk-cost audit reduces that mean cost
increase from 10.75 MW to 0.15 MW with the same zero-extra-violation outcome
across all three seeds, while over-emphasizing cost begins to add violations.

The downstream AC-audited grid-search benchmark is reported separately: it
reduces post-action violating scenarios to 51 of 120, confirming that
corrective optimization remains valuable after screening. We therefore present
VoltGuard as a risk-prioritization front end for renewable-hosting operation,
not as a replacement for AC optimal power flow or model predictive control.

The paper is intentionally careful about its boundary: it does not claim that a
neural GNN is the main contribution, does not claim AC feasibility
certification, and does not replace OPF/MPC. A neural graph residual is included
only as an ablation.

This manuscript is original, has not been published elsewhere, and is not under
consideration by another journal. All authors have approved the submission.

Sincerely,

Siqiang Zhao  
Corresponding author  
Sichuan University-Pittsburgh Institute, Chengdu, China  
2023141520257@stu.scu.edu.cn

## Data and Code Availability Draft

The experiments use publicly available IEEE test systems implemented through
pandapower and a project-local IEEE 69-bus feeder implementation. The local
reproducibility package includes the scenario generator, configured evaluation
pipeline, conformal calibration code, raw predictions, conformal scores,
runtime tables, post-action AC audit outputs, and energy-management value
metrics. File-level checksums and reproduction commands are recorded in
`experiments/results/reproducibility_manifest.json` and
`experiments/results/reproducibility_manifest.md`. The public repository or
archive URL will be inserted here before submission: [repository or archive
URL].

## Declaration of Competing Interest

[Choose one and delete the other before submission.]

The authors declare that they have no known competing financial interests or
personal relationships that could have appeared to influence the work reported
in this paper.

The authors declare the following competing interests: [specific disclosure].

## Funding

[Choose one and delete the other before submission.]

This research did not receive any specific grant from funding agencies in the
public, commercial, or not-for-profit sectors.

This work was supported by [funding agency, grant number].

## Author Contributions

Siqiang Zhao: Conceptualization, Methodology, Software, Validation, Formal
analysis, Writing - original draft, Corresponding author.

Fengxiang Zhang: [roles to be confirmed before submission].

## AI / Tool Use Disclosure

Drafting, code scaffolding, and language refinement used AI-assisted tools under
author supervision. The authors reviewed, verified, and edited all generated
text, code, equations, and numerical claims. The reported numerical results were
produced by executable scripts in the project workspace, not invented by an AI
tool. Final journal-specific AI/tool disclosure should be adapted to the target
journal's live policy.

## Figure Submission Note

No article figures have been generated yet at the user's request. Figure
descriptions, panel plans, and data sources are provided in
`figure_descriptions.md`.
