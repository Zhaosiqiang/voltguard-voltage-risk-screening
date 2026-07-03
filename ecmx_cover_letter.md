# Cover Letter Draft for Energy Conversion and Management: X

Dear Editor,

We submit the manuscript entitled "VoltGuard: Physics-Informed
Topology-Aware Residual Learning with Conformal Calibration for
Renewable-Hosting Voltage-Risk Screening in Active Distribution Networks" for
consideration in Energy Conversion and Management: X.

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
inflate-only recalibration changes coverage and sharpness.

Additional energy-management metrics quantify clean screened-safe releases,
avoided AC optimization calls, post-screening miss rate, interval width,
accepted PV proxy, relieved-load proxy, and proxy action cost across conformal
risk levels. At 90% nominal coverage, VoltGuard reduces missed bus-level
violations from 3 to 1 relative to the global conformal comparator while
avoiding 27 of 120 downstream AC calls; a release audit finds zero truly risky
scenarios and zero violation severity among those 27 released scenarios. Across
three random seeds, the screening-value audit avoids 27.33 AC calls on average
with zero scenario-level post-screening misses, and the release audit keeps
zero released risky scenarios while releasing 27.33 scenarios on average. At
80% nominal coverage, it misses ten fewer bus-level violations than boosting
plus global conformal calibration. A shift-aware screening audit further keeps
zero scenario-level post-screening misses across random interpolation,
synthetic time-block, PV-penetration shift, and topology-held-out transfer
protocols, and a bidirectional 33-to-69/69-to-33 transfer audit keeps zero
mean missed risky scenarios in both directions under target-feeder calibration.
Under PV shift, adding 16 target high-PV calibration scenarios
removes the remaining bus-level miss, but reduces screened-safe releases from
57.00 to 49.67 scenarios and widens intervals, making the recalibration cost
explicit.
For renewable-hosting stress, an AC-only high-PV frontier keeps all 1620
curtailment candidate outcomes and shows that 50% curtailment accepts 392.39
MW of PV while reducing initially overvoltage scenarios from 132 to 43.
Scenario risk-ranking analysis further
shows that the topology+PV+loading conditioned variant
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
not as a replacement for AC optimal power flow or model predictive control. A
neural graph residual is included only as an ablation.

This manuscript is original, has not been published elsewhere, and is not under
consideration by another journal. All authors have approved the submission.

Sincerely,

Siqiang Zhao  
Corresponding author  
Sichuan University-Pittsburgh Institute, Chengdu, China  
2023141520257@stu.scu.edu.cn
