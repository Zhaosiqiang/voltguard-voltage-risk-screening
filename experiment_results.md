# Executed Experiment Results

The current pipeline implements the tightened VoltGuard claim: topology-aware
residual learning with conformal calibration for voltage-risk screening.
Neural graph residual learning is executed only as an ablation.

## Dataset

- Main feeders: IEEE 33-bus and project-local IEEE 69-bus radial distribution
  feeders.
- Supplementary stress test: IEEE 118-bus.
- Scenarios: 300 AC-solvable scenarios per feeder.
- Main bus-level rows: 30,600 across 600 distribution-feeder scenarios.
- Supplementary rows: 35,400 for IEEE 118-bus.

## Representative Random Split

Source: `experiments/results/model_voltage_screening_metrics.md`

| Method | Variant | RMSE | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|---:|
| Boosting point + global conformal | global | 0.00041 | 0.90850 | 0.00110 | 0.99674 | 0.00250 | 3 |
| VoltGuard topology-aware residual | topology+PV+loading | 0.00011 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |
| Neural graph residual ablation | topology | 0.00171 | 0.91340 | 0.00540 | 0.99783 | 0.02327 | 2 |

The neural ablation has high recall but worse RMSE, wider intervals, and a
higher false-alarm rate. It is therefore not the main estimator.

## Multi-Seed Summary

Source: `experiments/results/multi_seed_summary.md`

| Method | Variant | RMSE mean | Coverage mean | Width mean | Recall mean | False alarm mean | Missed mean |
|---|---|---:|---:|---:|---:|---:|---:|
| Boosting point + global conformal | global | 0.00076 | 0.90468 | 0.00127 | 0.99811 | 0.00240 | 1.67 |
| VoltGuard topology-aware residual | topology+PV+loading | 0.00017 | 0.92397 | 0.00049 | 0.99964 | 0.00171 | 0.33 |

## Paired Seed-Delta Statistics

Source: `experiments/results/paired_seed_delta_summary.md`

The paired comparison subtracts boosting plus global conformal from VoltGuard
topology+PV+loading conditioned calibration for the same split seed. On random
interpolation, VoltGuard reduces missed bus-level violations by 1.33 on
average, improves recall by 0.00152, and narrows intervals by 0.00078 p.u. On
synthetic time-block splits, it also reduces missed violations by 1.33. Under
PV-penetration shift, recall improves slightly but empirical coverage drops
below nominal because the test distribution is shifted. Topology-held-out
33-to-69 transfer has no missed-violation increase and lowers false alarms,
but it remains a controlled transfer with target-feeder calibration rather than
a topology-invariant safety proof.

## Feature/Residual Ablation

Source: `experiments/results/feature_residual_ablation.md`

The feature/residual ablation evaluates whether the main estimator is more
than a generic tree regressor. Across three random seeds, the residual learner
with only local operating features has 0.00073 RMSE, 0.00207 mean interval
width, 0.99621 recall, and 3.33 missed bus-level violations. Adding topology
and neighbor electrical features reduces the full residual model to 0.00017
RMSE, 0.00050 width, 0.99964 recall, and 0.33 missed violations. Compared
with direct full ExtraTrees, the residual full model has lower RMSE, narrower
intervals, and lower false-alarm rate. The manuscript therefore claims a
topology/electrical feature advantage strongly and a residualization advantage
more narrowly.

## Conformal Ablation

Source: `experiments/results/conformal_ablation_metrics.md`

| Variant | Coverage | Width | Recall | False alarm | Missed |
|---|---:|---:|---:|---:|---:|
| global | 0.94984 | 0.00053 | 0.99891 | 0.00115 | 1 |
| PV-conditioned | 0.94510 | 0.00049 | 0.99891 | 0.00058 | 1 |
| topology-conditioned | 0.95523 | 0.00053 | 0.99891 | 0.00154 | 1 |
| topology+PV+loading conditioned | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |
| topology+PV+loading no-shrinkage | 0.91258 | 0.00042 | 0.99891 | 0.00038 | 1 |

## Calibration-Budget Sensitivity

Source: `experiments/results/calibration_budget_sensitivity_metrics.md`

This audit tests whether the conditioned conformal result depends on having a
large AC-audited calibration set. It samples calibration scenarios, not
individual buses, at 10%, 25%, 50%, 75%, and 100% of the representative
calibration split and repeats the partial-budget cases 20 times. For
VoltGuard topology+PV+loading conditioned calibration, 10% calibration uses
only 12 scenarios and observes 8.4 of 16 test families on average, leaving 7.6
empty test families that must fall back toward global calibration. Even so,
coverage remains 0.92903 with 0.00047 average width and 0.9 missed bus
violations on average. At 25% calibration, observed families rise to 13.35 and
coverage reaches 0.93528. Full calibration covers all 16 families, gives
0.93660 coverage, and misses one bus-level violation. The deployment message
is therefore nuanced: small calibration budgets can work because shrinkage and
fallback prevent collapse, but family-conditioned claims require enough
scenario diversity to cover the feeder/PV/loading families.

## Asymmetric Conformal Audit

Source: `experiments/results/asymmetric_conformal_metrics.md`

The main manuscript keeps symmetric absolute-residual conformal intervals
because they match the split-conformal construction used throughout the paper.
However, voltage operation has separate lower and upper limits, so the audit
also computes one-sided lower and upper conformal radii from the saved
calibration predictions. For the main topology+PV+loading VoltGuard variant,
asymmetric calibration reduces average width from 0.000433 to 0.000411 p.u.,
removes the single missed bus-level violation, and keeps scenario recall at
1.0. The tradeoff is lower empirical coverage, from 0.93660 to 0.91977. The
paper therefore reports asymmetric conformal calibration as a tail-aware
extension and reviewer-facing ablation, not as a replacement for the main
coverage claim.

## EV-Conditioning Ablation

Source: `experiments/results/ev_conditioning_ablation.md`

EV scale is included as an operating feature, but adding it to the conformal
family key is not beneficial at the current sample size. Topology+PV+loading+EV
conditioning increases the family count from 16 to 55, reduces the minimum
calibration-family size from 198 to 33, creates seven empty-test families, and
does not reduce missed violations or improve recall. It also increases interval
width and false alarms. The paper therefore treats EV demand as a
residual-learning feature and leaves EV-specific conformal conditioning to
larger calibration sets.

## Per-Family Calibration

Full table: `experiments/results/per_family_conformal_metrics.md`.

The per-family table reports calibration samples, test samples, empirical
coverage, interval width, recall, false-alarm rate, and missed violations for
each feeder/PV/loading family. It exposes low-coverage families such as IEEE
33-bus PV 0.8 low-load, which has no actual violations, and the risk-relevant
IEEE 33-bus PV 0.6 high-load family, which has one missed bus-level violation.
This supports the paper's discussion that family-level calibration must be
reported explicitly.

## Family Recalibration Audit

Source: `experiments/results/family_recalibration_audit.md`

The per-family audit uses the representative test split only as a post-hoc AC
diagnostic. It does not train on test labels. Five of 16 topology/PV/loading
families fall below the nominal 90% empirical coverage target. If only those
undercovered families receive an inflate-only radius update, weighted interval
width increases from 0.000433 to 0.000451 p.u. while missed bus-level
violations remain at one. The weakest coverage family is the 33-bus, PV 0.8,
low-load regime, whose coverage improves from 0.76768 to 0.90909 but has no
actual violations. The risk-relevant 33-bus PV 0.6 high-load family improves
coverage from 0.84242 to 0.90909 while its single missed violation remains.
This supports explicit family-level recalibration rather than unconditional
conformal safety claims.

## Risk-Stratified Calibration and Screening

Source files:

- `experiments/results/risk_stratified_calibration_bus.md`
- `experiments/results/risk_stratified_calibration_scenario.md`

This audit stratifies the representative random-split test set into true
violations, boundary-safe buses/scenarios within 0.002 p.u. of a voltage
limit, near-safe cases within 0.010 p.u., and interior-safe cases. It checks
whether the screening claim holds at the voltage boundary rather than only in
aggregate. On the true-violation bus stratum, VoltGuard topology+PV+loading
conditioned calibration has 0.99891 recall and one missed bus-level violation,
versus 0.99674 recall and three missed violations for boosting plus global
conformal. On the 55 boundary-safe bus samples, VoltGuard triggers three false
alarm buses (0.05455 false-alarm rate), compared with 13 for boosting and 45
for the neural graph residual ablation. At scenario level, VoltGuard recalls
all 93 risky scenarios and produces zero false-alarm scenarios across the
boundary-safe, near-safe, and interior-safe strata. This supports the narrower
claim that the main value is sharp calibrated screening near operating limits,
not merely lower average voltage RMSE.

## Shift Splits

The executed splits are random interpolation, synthetic time-block,
PV-penetration shift, and topology-held-out transfer from IEEE 33-bus training
to IEEE 69-bus calibration/testing. PV-shift tests preserve high recall but
show degraded empirical coverage, while topology-held-out transfer remains a
controlled target-calibrated transfer rather than arbitrary topology-shift
evidence. These results motivate bounded conformal claims rather than
unconditional safety language.

## PV-Shift Target Recalibration Audit

Source: `experiments/results/pv_shift_recalibration_metrics.md`

The PV-shift split trains on low/medium PV scenarios, calibrates on PV 0.6
scenarios, and evaluates on the PV 0.8 high-PV bin. This intentionally violates
the exchangeability intuition behind split conformal calibration. A target
recalibration audit therefore moves a small, disjoint subset of early high-PV
AC-audited scenarios into the calibration set and evaluates on the remaining
high-PV scenarios, without retraining the point estimator. For VoltGuard
topology+PV+loading conditioned calibration, source-only high-PV coverage is
0.76915 with one missed bus-level violation. Using about 16 high-PV target
calibration scenarios on average raises coverage to 0.89527 and removes the
missed violation, while widening intervals from 0.00081 to 0.00189 p.u. and
increasing false-alarm rate from 0.00147 to 0.00398. This result strengthens,
rather than weakens, the paper's theoretical boundary: PV shift requires
explicit target recalibration if near-nominal coverage is required.

Source: `experiments/results/pv_shift_recalibration_energy_value_metrics.md`

The same target-recalibration protocol is translated into operating screening
metrics on the remaining high-PV scenarios. With source-only calibration,
VoltGuard screens 57.00 high-PV scenarios as safe on average and avoids the
same number of downstream AC calls, but leaves one missed bus-level violation.
Adding the 10% target high-PV calibration set removes the missed bus-level
violation and keeps risky-scenario recall at 1.00000, but screened-safe
releases fall to 49.67 scenarios and mean interval width rises from 0.00081 to
0.00209 p.u. The result gives an operational cost for recalibration rather than
presenting recalibration as a free repair.

## Forecast-Noise Robustness Audit

Source: `experiments/results/forecast_noise_robustness_metrics.md`

The main method uses pre-dispatch load, PV, and EV forecasts or
pseudo-measurements. To test whether the screening result depends on unrealistically
perfect operating inputs, the robustness audit perturbs only those input
features, recomputes neighbor features and the LinDistFlow backbone from the
noisy injections, and keeps the AC voltage labels fixed. In the representative
random split, VoltGuard topology+PV+loading conditioned calibration degrades
smoothly as forecast noise increases. With 10% multiplicative forecast noise,
RMSE increases to 0.00208 p.u., empirical coverage is 0.89330, bus-level
violation recall remains 0.98480, and missed bus-level violations increase to
14, while scenario-level recall remains 1.000. With 20% noise, one risky
scenario is missed. The result supports operational robustness for moderate
forecast error, but it also shows that high forecast error requires more
conservative or noise-aware calibration.

## Branch-Level Physics Consistency Audit

Source: `experiments/results/physics_consistency_audit.md`

The physics-consistency audit computes the branch-level LinDistFlow
voltage-drop residual on the representative random-split test scenarios using
saved predictions and pre-dispatch injections. It is not an AC feasibility
certificate: the AC-label residual is nonzero because the proxy omits losses
and full AC effects. VoltGuard topology+PV+loading conditioned predictions
achieve a mean branch-drop RMSE of 0.000250, below boosting plus
global conformal at 0.000563, while the neural graph residual ablation has a
larger residual of 0.003139. This supports the narrow physics-informed claim
that the selected residual learner stays closer to the LinDistFlow
voltage-drop structure than the point baseline and the neural ablation.

## Operating Value

The AC corrective grid-search benchmark is evaluated as a downstream optimizer,
not as part of VoltGuard itself. On the representative IEEE 33/69 random split,
it evaluates 120 test scenarios, all AC-converged, and leaves 51 post-action
violating scenarios with 398 violating buses. This confirms that corrective
optimization remains necessary after risk screening.

## High-PV Renewable-Hosting Stress Audit

Source: `experiments/results/high_pv_hosting_stress_by_feeder.md`
Companion frontier: `experiments/results/high_pv_hosting_frontier_metrics.md`

The main 33/69 learned benchmark is dominated by undervoltage events, so a
separate AC-only high-PV stress audit evaluates overvoltage/PV-curtailment
behavior under light load, 100%-400% PV penetration, and slack/tap settings
from 1.00 to 1.04 p.u. Across 270 converged stress scenarios, 132 have
pre-action overvoltage. A PV-curtailment grid from 0% to 50% reduces
post-action overvoltage scenarios to 43 and overvoltage buses from 2262 to 552,
while accepting 468.05 MW and curtailing 316.74 MW across initially
overvoltage cases. This is reported as a hosting stress audit for the downstream
operating interface, not as additional model-training evidence.

The frontier companion keeps all 1620 AC candidate outcomes from the same 270
stress scenarios. On the 132 initially overvoltage scenarios, 20% uniform PV
curtailment accepts 627.83 MW of PV and reduces overvoltage scenarios from 132
to 101; 30% curtailment accepts 549.35 MW and reduces them to 82; 50%
curtailment accepts 392.39 MW and reduces overvoltage scenarios to 43 and
overvoltage buses from 2262 to 552. The table is the accepted-PV versus
overvoltage-reduction curve requested by the energy-management framing.

## Energy-Management Screening Value

Source: `experiments/results/energy_management_value_metrics.md`

At 90% nominal coverage, VoltGuard screens 27 of 120 scenarios as safe before
downstream AC optimization, keeps risky-scenario recall at 1.000, misses no
risky scenarios at scenario level, and reduces missed bus-level violations to
one versus three for boosting plus global conformal. Its mean interval width is
0.00046 versus 0.00110 for the global conformal comparator. At 80% nominal
coverage, VoltGuard misses ten fewer bus-level violations than boosting plus
global conformal. The proxy action quantities report accepted PV, curtailed PV,
relieved load, and action cost; in the representative split the risk flags
trigger flexible-load relief rather than PV curtailment.

Source: `experiments/results/energy_management_value_multiseed_metrics.md`

The energy-management screening table is also repeated over seeds 7, 17, and
42. At the primary 90% nominal coverage level, VoltGuard avoids 27.33 AC
optimization calls on average, keeps mean risky-scenario recall at 1.00000,
and has a mean post-screening miss rate of 0.00000 at scenario level. Its
mean missed bus-level violations are 0.33 versus 1.67 for boosting plus global
conformal, while the mean interval width is 0.00051 versus 0.00127. This
turns the screening-value claim into a multi-seed operating statistic rather
than a single representative split.

Source: `experiments/results/shift_energy_management_value_metrics.md`

The same primary 90% nominal screening audit is repeated across random
interpolation, synthetic time-block, PV-penetration shift, and
topology-held-out 33-to-69 transfer. Across these four split families and
three seeds, VoltGuard keeps mean scenario-level risky recall at 1.00000 and
mean post-screening risky-scenario miss rate at 0.00000. Avoided AC calls vary
with test-set composition: 27.33 for random interpolation, 17.00 for synthetic
time-block, 57.00 for PV shift, and 15.67 for topology-held-out transfer.
Bus-level misses remain split-dependent, so this table is reported as
empirical split-protocol evidence rather than arbitrary-shift safety.

Source: `experiments/results/topology_transfer_bidirectional_metrics.md`

The topology-transfer stress test is also repeated in both feeder directions.
For 33-to-69 transfer, VoltGuard lowers RMSE from 0.00127 to 0.00068 p.u.,
narrows intervals from 0.00273 to 0.00203 p.u., and removes the remaining 0.33
mean missed bus-level violations relative to boosting plus global conformal.
For 69-to-33 transfer, both methods keep scenario-level recall at 1.00000 with
zero missed risky scenarios; VoltGuard improves empirical coverage from
0.89282 to 0.90948, while its mean interval width and false-alarm rate are
slightly higher. This makes the topology-transfer claim bidirectional but
bounded: target-feeder calibration is used, and the result is not a proof of
unconditional topology invariance.

## Screened-Safe Release Audit

Source: `experiments/results/screened_safe_release_metrics.md`

The release audit evaluates the scenarios that the screening layer would not
send to downstream AC optimization. At 90% nominal coverage, VoltGuard
releases 27 of 120 scenarios, avoids 27 AC calls, and all released scenarios
are truly non-violating: released risky scenarios are zero, released violation
severity share is 0.00000, and released violating buses are zero. The
LinDistFlow point-only gate releases 29 scenarios but includes two truly risky
scenarios and six violating buses, even though the released severity share is
small. This makes the energy-management claim more precise: VoltGuard's value
is not only ranking high-risk scenarios, but also identifying a clean
screened-safe subset under the representative calibration protocol.

Source: `experiments/results/screened_safe_release_multiseed_metrics.md`

The same release audit is repeated over three random seeds at the primary
90% nominal conformal level. VoltGuard topology+PV+loading conditioned
calibration releases 27.33 scenarios on average, with mean safe-release
precision 1.00000, mean released risky scenarios 0.00000, a 95% confidence
interval of 0.00000 for released risky scenarios, and mean released severity
share 0.00000. LinDistFlow point-only gating releases slightly more scenarios
but releases 1.67 truly risky scenarios on average. This multi-seed result
turns the release claim from a representative example into a stability audit.

## Screening-Budget Triage Value

Source: `experiments/results/screening_budget_metrics.md`
Multi-seed companion: `experiments/results/screening_budget_multiseed_metrics.md`

The screening-budget experiment asks what happens when only a fraction of the
120 test scenarios can be passed to the downstream AC-audited grid-search
benchmark. Scenarios outside the budget are left uncorrected, so the metric is
a direct triage test rather than another interval-threshold table. With a 20%
AC-call budget, VoltGuard topology+PV+loading conditioned calibration sends 24
scenarios to AC audit, avoids 96 calls, captures 52.59% of realized violation
severity, and reduces total severity by 21.42%. A random 20% budget captures
19.98% of severity and reduces severity by 12.06%. At 50% budget, VoltGuard
captures 90.59% of severity while avoiding 60 AC calls. The post-policy
violating-scenario count is reported but not overclaimed, because the coarse
grid-search backend can leave severe scenarios unresolved.

The same calculation is repeated over seeds 7, 17, and 42 using the saved
seed-specific AC candidate grids from the candidate-action audit. At 20% AC
budget, VoltGuard avoids 96 scenario-level AC grid searches on average,
captures 34.05% of realized pre-action severity, and reduces total severity by
19.71%. This is a 13.98 percentage-point severity-capture gain over random
budgeting. LinDistFlow point-risk and oracle severity rankings capture more raw
pre-action severity at the same budget, but VoltGuard leaves fewer post-policy
violating scenarios and buses, which is the more direct downstream operating
metric for the coarse corrective grid.

## Paired Statistical Evidence Audit

Source: `experiments/results/statistical_evidence_metrics.md`
Raw deltas: `experiments/results/statistical_evidence_raw.csv`

The paired statistical audit converts the main split/seed results into
directional evidence rather than relying on a single representative table. The
prediction comparison pairs VoltGuard topology+PV+loading conditioned
calibration against boosting plus global conformal over 12 split-seed units
from random interpolation, synthetic time block, PV penetration shift, and
target-calibrated topology-held-out transfer. VoltGuard improves RMSE in all
12 units with mean delta -0.000848 p.u. and bootstrap 95% CI
[-0.001069, -0.000654]. It also narrows intervals in all 12 units with mean
width delta -0.000645 p.u. Recall, false-alarm, and missed-violation gains are
positive on average but not uniform in every unit, which is why the manuscript
states them as empirical stability evidence rather than universal dominance.

The operating comparison uses the three seed-specific 20% AC-call budgeted
triage units. VoltGuard improves severity capture over random budgeting in all
three seeds, with mean absolute gain 0.139817 and bootstrap 95% CI
[0.110381, 0.169674]. It leaves fewer post-policy violating buses than
LinDistFlow point-risk in all three seeds, with mean delta -153.0 buses. The
same table also records where VoltGuard is not dominant: LinDistFlow and oracle
severity rankings capture more raw pre-action severity under the budget, but
the coarse corrective grid leaves more post-policy violations for those
rankings. This keeps the operating claim centered on calibrated triage and
post-policy AC audit outcomes.

## Consolidated Energy-Management Frontier

Source: `experiments/results/energy_management_frontier_metrics.md`

The consolidated frontier collects the completed operating audits into one
engineering view. It reports four tunable decisions: conformal screened-safe
release, limited-budget AC triage, candidate-action pruning, and high-PV
hosting stress. The primary rows show 27.33 avoided scenario-level AC calls at
90% nominal release with zero missed risky scenarios, 96 avoided scenario-level
AC calls at a 20% budget with 0.13982 severity-capture gain over random
budgeting, 720 avoided candidate AC audits for top-three action pruning with
zero extra violating buses at cost weight 0.5, and 392.39 MW accepted PV at
50% curtailment in the high-PV stress audit. This table is the clearest
energy-management bridge between prediction, screening, and downstream AC
audit workload.

## Candidate-Action Screening Audit

Source: `experiments/results/candidate_action_screening_metrics.md`

The candidate-action audit moves from scenario triage to the downstream action
grid itself. For each of 120 test scenarios, the AC corrective benchmark has
nine candidate load-relief/PV-curtailment actions, for 1080 candidate AC
power-flow audits. VoltGuard ranks these candidates from pre-AC forecast
features and conformal voltage intervals. Keeping only the top three
VoltGuard-ranked actions per scenario reduces candidate AC audits from 1080 to
360, avoiding 720 audits or 66.7% of candidate evaluations. In this
representative split it retains the full grid-search post-action violation
count: no extra violating scenarios and no extra violating buses relative to
full AC grid search, although the proxy action cost increases by 7.24 MW.

The comparison is useful because cheaper or physics-only pruning is not
equivalent. LinDistFlow point-risk top-three pruning still leaves one extra
violating scenario and two extra violating buses relative to full grid search.
Cheapest-first top-three pruning avoids the same number of AC audits but leaves
30 extra violating scenarios and 428 extra violating buses. This strengthens
the two-stage energy-management claim: VoltGuard can act as an AC-audit
candidate-pruning layer, while the final corrective action is still selected
by AC-audited grid search.

Source: `experiments/results/candidate_action_screening_multiseed_metrics.md`

The top-three candidate-pruning audit is repeated over seeds 7, 17, and 42,
with the AC candidate grid recomputed for each seed-specific test set. The
full backend evaluates 1080 candidate AC power flows per seed. VoltGuard
top-three pruning evaluates 360 and avoids 720 candidate AC audits per seed on
average, while adding zero post-action violating scenarios and zero violating
buses relative to full grid search. LinDistFlow point-risk pruning leaves 0.67
extra violating scenarios and 1.33 extra violating buses on average, while
cheapest-first leaves 29.33 extra violating scenarios and 364.33 extra
violating buses. VoltGuard's safety-equivalent pruning is not cost-free: the
mean proxy action-cost delta is 11.59 MW relative to full grid search.

## Risk-Cost Candidate-Action Tradeoff

Source: `experiments/results/action_cost_tradeoff_metrics.md`

The previous candidate-action audit ranks actions primarily by predicted
voltage risk, which can be conservative in action cost. The risk-cost audit
therefore adds a normalized action-cost term to the VoltGuard candidate score
and evaluates cost weights over a grid. For top-three candidate screening,
the risk-first setting keeps the full-grid post-action violation count but
adds 6.88 MW of proxy action cost. A moderate cost weight of 0.5 still audits
only 360 of 1080 candidate actions, avoids 720 AC audits, keeps zero extra
violating scenarios and zero extra violating buses relative to full grid
search, and recovers the full-grid action cost in this representative split.
When the cost weight is pushed to 1.0, the screen begins to admit one extra
violating scenario and two extra violating buses. The result is reported as an
operating sensitivity curve, not as a universal optimal tuning rule.

Source: `experiments/results/action_cost_tradeoff_multiseed_metrics.md`

The risk-cost tradeoff is repeated over the same three random seeds using the
saved seed-specific AC candidate outcomes and VoltGuard action scores. For
top-three pruning, the risk-first setting has zero extra post-action violating
scenarios and buses in every seed, but it adds 10.75 MW of proxy action cost on
average. A moderate cost weight of 0.5 keeps the same 360 audited candidate
actions, avoids 720 candidate AC audits per seed, maintains zero extra
violating scenarios and buses in all seeds, and reduces the mean action-cost
delta to 0.15 MW. Pushing the weight to 1.0 admits one extra violating scenario
and 2.67 extra violating buses on average. This strengthens the energy-
management interpretation: the action-pruning layer exposes a tunable risk-cost
interface, but final feasibility remains AC-audited.

## Operational Runtime Benchmark

Source: `experiments/results/runtime_operational_benchmark.md`

The runtime benchmark measures the local Python prototype on the representative
random split. Online VoltGuard screening evaluates 120 scenarios in 0.0305 s
or 0.254 ms/scenario, while full AC grid search on every scenario takes
206.98 s for 1080 candidate AC power-flow audits. At 90% nominal coverage, the
binary VoltGuard gate flags 93 of 120 scenarios, giving a 1.29x
screen-then-AC speedup. Under the 20% AC-call budget used in the triage
experiment, the estimated wall-clock time drops to 41.43 s, about 5.00x faster
than full AC grid search. This supports the paper's runtime claim as
prioritization value rather than AC-optimization replacement.

## Scenario Risk-Ranking Quality

Source: `experiments/results/scenario_risk_ranking_metrics.md`

The scenario risk-ranking experiment evaluates whether interval margins can
prioritize forecasted operating points for downstream AC-audited optimization.
VoltGuard topology+PV+loading conditioned calibration achieves 1.00000 ROC-AUC,
1.00000 average precision, 0.99985 Spearman correlation between interval risk
score and realized severity, 45.59% top-20 severity capture, and 100%
bottom-10 safe-screen precision. The global VoltGuard variant is essentially
tied on scenario ranking, so the paper separates the ranking claim from the
conditioned-calibration missed-violation and interval-sharpness claim.

## Generated Artifacts

- `raw_predictions_random_seed7.csv`
- `conformal_scores_random_seed7.csv`
- `per_family_conformal_metrics.csv`
- `scenario_level_metrics.csv`
- `conformal_ablation_metrics.csv`
- `operating_value_metrics.csv`
- `runtime_metrics.csv`
- `control_grid_search_selected_actions.csv`
- `control_grid_search_candidate_actions.csv`
- `energy_management_value_metrics.csv`
- `energy_management_value_summary.json`
- `energy_management_value_multiseed_metrics.csv`
- `energy_management_value_multiseed_raw.csv`
- `energy_management_value_multiseed_summary.json`
- `energy_management_frontier_metrics.csv`
- `energy_management_frontier_summary.json`
- `shift_energy_management_value_metrics.csv`
- `shift_energy_management_value_raw.csv`
- `shift_energy_management_value_summary.json`
- `pv_shift_recalibration_energy_value_metrics.csv`
- `pv_shift_recalibration_energy_value_raw.csv`
- `pv_shift_recalibration_energy_value_summary.json`
- `screened_safe_release_metrics.csv`
- `screened_safe_release_summary.json`
- `screened_safe_release_multiseed_metrics.csv`
- `screened_safe_release_multiseed_raw.csv`
- `screened_safe_release_multiseed_summary.json`
- `candidate_action_screening_metrics.csv`
- `candidate_action_screening_summary.json`
- `action_cost_tradeoff_metrics.csv`
- `action_cost_tradeoff_summary.json`
- `scenario_risk_ranking_metrics.csv`
- `scenario_risk_ranking_summary.json`
- `feature_residual_ablation.csv`
- `feature_residual_ablation_summary.json`
- `physics_consistency_audit.csv`
- `physics_consistency_summary.json`
- `screening_budget_metrics.csv`
- `screening_budget_summary.json`
- `screening_budget_multiseed_metrics.csv`
- `screening_budget_multiseed_raw.csv`
- `screening_budget_multiseed_summary.json`
- `statistical_evidence_metrics.csv`
- `statistical_evidence_raw.csv`
- `statistical_evidence_summary.json`
- `runtime_operational_benchmark.csv`
- `runtime_operational_summary.json`
- `high_pv_hosting_stress_by_feeder.csv`
- `high_pv_hosting_stress_summary.json`
- `high_pv_hosting_frontier_metrics.csv`
- `high_pv_hosting_frontier_raw.csv`
- `high_pv_hosting_frontier_summary.json`
- `experiments/results/reproducibility_manifest.json`
