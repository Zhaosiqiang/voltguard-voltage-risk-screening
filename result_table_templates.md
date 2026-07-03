# Executed Result Table Index

This file is no longer a placeholder template. It records the tables that are
now populated by the executable pipeline and identifies the authoritative raw
result files used by the manuscript.

## Table 1. Scenario and Dataset Summary

Source files:

- `experiments/results/scenario_summary.csv`
- `experiments/results/dataset_split_summary.md`

Scope:

- IEEE 33-bus and IEEE 69-bus are the main distribution feeders.
- IEEE 118-bus is retained only as a supplementary stress test.
- Random interpolation, synthetic time-block, PV-penetration shift, and
  topology-held-out 33-to-69 transfer are executed splits.

## Table 2. Voltage Prediction and Screening Metrics

Source file:

- `experiments/results/model_voltage_screening_metrics.md`

Representative rows:

| Method | Variant | RMSE | Coverage | Width | Recall | False alarm | Missed |
|---|---|---:|---:|---:|---:|---:|---:|
| Boosting point + global conformal | global | 0.00041 | 0.90850 | 0.00110 | 0.99674 | 0.00250 | 3 |
| VoltGuard topology-aware residual | topology+PV+loading | 0.00011 | 0.93660 | 0.00043 | 0.99891 | 0.00058 | 1 |
| Neural graph residual ablation | topology | 0.00171 | 0.91340 | 0.00540 | 0.99783 | 0.02327 | 2 |

## Table 3. Multi-Seed Statistics

Source files:

- `experiments/results/multi_seed_summary.md`
- `experiments/results/scenario_level_metrics.md`

The main random split is evaluated with seeds 7, 17, and 42. The manuscript
reports mean values and uses the full CSV/Markdown output for seed-level
traceability.

## Table 4. Paired Seed-Delta Statistics

Source files:

- `experiments/results/paired_seed_delta_summary.md`
- `experiments/results/paired_seed_delta_summary.csv`
- `experiments/results/paired_seed_deltas_raw.csv`

Report paired deltas between VoltGuard topology+PV+loading conditioned
calibration and boosting plus global conformal under the same split seed. This
table is especially important for showing both the random/time-block gains and
the bounded, target-calibrated nature of the topology-held-out transfer claim.

## Table 5. Feature/Residual Ablation

Source files:

- `experiments/results/feature_residual_ablation.md`
- `experiments/results/feature_residual_ablation.csv`
- `experiments/results/feature_residual_ablation_raw.csv`
- `experiments/results/feature_residual_ablation_summary.json`

Reported fields include direct versus residual formulation, local-only versus
topology/electrical feature families, RMSE, empirical coverage, width,
recall, false-alarm rate, and missed violations over three random seeds.

## Table 6. Conformal Calibration Ablation

Source file:

- `experiments/results/conformal_ablation_metrics.md`

Compared variants:

- global conformal,
- PV-conditioned conformal,
- topology-conditioned conformal,
- topology+PV+loading conditioned conformal,
- topology+PV+loading no-shrinkage.

## Table 6A. Calibration-Budget Sensitivity

Source files:

- `experiments/results/calibration_budget_sensitivity_metrics.md`
- `experiments/results/calibration_budget_sensitivity_metrics.csv`
- `experiments/results/calibration_budget_sensitivity_raw.csv`
- `experiments/results/calibration_budget_sensitivity_summary.json`

Reported fields include scenario-level calibration fraction, repeated
calibration-scenario samples, family coverage of the calibration set,
empirical coverage, interval width, violation recall, false alarms, and missed
violations. This table quantifies the deployment calibration burden for
conditioned conformal screening.

## Table 7. Asymmetric Conformal Calibration Audit

Source files:

- `experiments/results/asymmetric_conformal_metrics.md`
- `experiments/results/asymmetric_conformal_metrics.csv`
- `experiments/results/asymmetric_conformal_family_radii.csv`
- `experiments/results/asymmetric_conformal_summary.json`

Reported fields compare the main symmetric absolute-residual intervals with
one-sided lower/upper conformal radii. This audit tests whether tail-aware
calibration can reduce interval width or missed voltage violations without
claiming a new unconditional coverage guarantee.

## Table 8. EV-Conditioning Conformal Ablation

Source files:

- `experiments/results/ev_conditioning_ablation.md`
- `experiments/results/ev_conditioning_ablation.csv`
- `experiments/results/ev_conditioning_family_counts.csv`

Report whether adding EV scale to conformal families improves or fragments
calibration. This table justifies using EV as a point-estimator feature while
leaving the main conformal key at topology/PV/loading granularity.

## Table 9. Per-Family Calibration Analysis

Source file:

- `experiments/results/per_family_conformal_metrics.md`

Reported fields include calibration sample count, test sample count, empirical
coverage, interval width, violation recall, false-alarm rate, and missed
violations. Low-coverage families are kept in the paper as evidence that
family-level coverage must be audited rather than assumed, with separate
attention to whether the family actually contains voltage violations.

## Table 10. Family Recalibration Audit

Source files:

- `experiments/results/family_recalibration_audit.md`
- `experiments/results/family_recalibration_audit.csv`
- `experiments/results/family_recalibration_summary.json`

Reported fields include current family coverage, audited inflate-only coverage,
width increase, recall, missed violations, and false-alarm rate. This is a
post-hoc AC audit for recalibration needs; it is not used to train the primary
intervals.

## Table 11. Risk-Stratified Calibration and Screening

Source files:

- `experiments/results/risk_stratified_calibration_bus.md`
- `experiments/results/risk_stratified_calibration_bus.csv`
- `experiments/results/risk_stratified_calibration_scenario.md`
- `experiments/results/risk_stratified_calibration_scenario.csv`
- `experiments/results/risk_stratified_calibration_summary.json`

Reported fields include true-violation, boundary-safe, near-safe, and
interior-safe strata at both bus and scenario levels. This table checks whether
the screening intervals remain sharp near voltage limits rather than only
reporting aggregate coverage.

## Table 12. Shift and Scenario-Level Screening

Source file:

- `experiments/results/scenario_level_metrics.md`

The table supports random interpolation, synthetic time-block,
PV-penetration-shift, topology-held-out, and supplementary IEEE 118-bus stress
test statements.

## Table 13. PV-Shift Target Recalibration Audit

Source files:

- `experiments/results/pv_shift_recalibration_metrics.md`
- `experiments/results/pv_shift_recalibration_metrics.csv`
- `experiments/results/pv_shift_recalibration_raw.csv`
- `experiments/results/pv_shift_recalibration_target_splits.csv`
- `experiments/results/pv_shift_recalibration_summary.json`
- `experiments/results/pv_shift_recalibration_energy_value_metrics.md`
- `experiments/results/pv_shift_recalibration_energy_value_metrics.csv`
- `experiments/results/pv_shift_recalibration_energy_value_raw.csv`
- `experiments/results/pv_shift_recalibration_energy_value_summary.json`

Reported fields include source-only PV-shift calibration, added target high-PV
calibration fraction, target calibration/evaluation scenario counts,
coverage, width, recall, false-alarm rate, missed violations, screened-safe
scenarios, avoided AC calls, and the recalibration operating tradeoff. This audit
quantifies explicit recalibration under PV penetration shift rather than
claiming unconditional conformal safety.

## Table 14. Forecast-Noise Robustness Audit

Source files:

- `experiments/results/forecast_noise_robustness_metrics.md`
- `experiments/results/forecast_noise_robustness_metrics.csv`
- `experiments/results/forecast_noise_robustness_raw.csv`
- `experiments/results/forecast_noise_robustness_summary.json`

Reported fields include forecast-noise standard deviation, RMSE, coverage,
interval width, bus-level recall, false-alarm rate, missed bus violations,
scenario recall, and missed risky scenarios. The audit perturbs only
pre-dispatch load/PV/EV forecast features, recomputes topology-aware
LinDistFlow inputs, and keeps AC labels fixed.

## Table 15. Branch-Level Physics Consistency Audit

Source files:

- `experiments/results/physics_consistency_audit.md`
- `experiments/results/physics_consistency_audit.csv`
- `experiments/results/physics_consistency_summary.json`
- `experiments/results/physics_consistency_audit_raw.csv`

Reported fields include branch-drop RMSE, branch-drop MAE, 95th-percentile
maximum absolute branch-drop residual, and violating-scenario-only residuals.
This audit measures LinDistFlow voltage-drop consistency of saved predictions;
it is not an AC feasibility certificate.

## Table 16. AC-Audited Corrective Benchmark

Source files:

- `experiments/results/control_grid_search_summary.json`
- `experiments/results/control_grid_search_selected_actions.csv`
- `experiments/results/control_grid_search_candidate_actions.csv`

The benchmark searches load-relief and PV-curtailment actions in `{0%, 10%,
20%}` and audits candidate actions with AC power flow. It is the downstream
corrective layer, not the VoltGuard screening layer.

## Table 17. High-PV Renewable-Hosting Stress Audit

Source files:

- `experiments/results/high_pv_hosting_stress_by_feeder.md`
- `experiments/results/high_pv_hosting_stress_by_feeder.csv`
- `experiments/results/high_pv_hosting_stress_summary.json`
- `experiments/results/high_pv_hosting_stress_raw.csv`
- `experiments/results/high_pv_hosting_frontier_metrics.md`
- `experiments/results/high_pv_hosting_frontier_metrics.csv`
- `experiments/results/high_pv_hosting_frontier_raw.csv`
- `experiments/results/high_pv_hosting_frontier_summary.json`

Report pre/post overvoltage scenarios, overvoltage buses, selected PV
curtailment, accepted PV, curtailed PV, and maximum voltage. This is an AC-only
hosting stress audit for the downstream interface, not additional training data.
The frontier companion reports the full accepted-PV/curtailed-PV/overvoltage
reduction curve over the same 0%-50% PV-curtailment grid, both pooled and by
feeder.

## Table 18. Energy-Management Screening Value

Source files:

- `experiments/results/energy_management_value_metrics.md`
- `experiments/results/energy_management_value_metrics.csv`
- `experiments/results/energy_management_value_multiseed_metrics.md`
- `experiments/results/energy_management_value_multiseed_metrics.csv`
- `experiments/results/energy_management_value_multiseed_raw.csv`
- `experiments/results/energy_management_value_multiseed_summary.json`
- `experiments/results/shift_energy_management_value_metrics.md`
- `experiments/results/shift_energy_management_value_metrics.csv`
- `experiments/results/shift_energy_management_value_raw.csv`
- `experiments/results/shift_energy_management_value_summary.json`
- `experiments/results/topology_transfer_bidirectional_metrics.md`
- `experiments/results/topology_transfer_bidirectional_metrics.csv`
- `experiments/results/topology_transfer_bidirectional_raw.csv`
- `experiments/results/topology_transfer_bidirectional_summary.json`

Reported fields include screened-safe ratio, AC optimization calls avoided,
risky-scenario recall, post-screening miss rate, bus-level recall, missed bus
violations, interval width, accepted PV proxy, curtailed PV proxy, relieved
load proxy, and proxy action cost over nominal coverage levels 95%, 90%, 85%,
and 80%. The multi-seed companion repeats these screening-value quantities
over the three configured random seeds and reports mean, standard deviation,
and 95% confidence intervals. The shift-aware companion repeats the primary
screening-value audit for random interpolation, synthetic time-block,
PV-penetration shift, and topology-held-out transfer. The bidirectional
topology-transfer companion repeats the target-calibrated transfer audit for
both 33-to-69 and 69-to-33 directions.

## Table 18A. Consolidated Energy-Management Frontier

Source files:

- `experiments/results/energy_management_frontier_metrics.md`
- `experiments/results/energy_management_frontier_metrics.csv`
- `experiments/results/energy_management_frontier_summary.json`

Reported fields include frontier type, operating setting, risk tolerance,
nominal coverage, avoided scenario-level AC calls, avoided candidate-action AC
audits, severity capture, post-policy violating scenarios/buses, screened-safe
scenarios, missed risky scenarios, interval width, accepted PV, curtailed PV,
relieved load, action cost, and the relevant comparison delta. This table
consolidates the completed release, budgeted triage, action-pruning, and
high-PV hosting audits into one operating frontier for the ECM:X energy-
management story.

## Table 19. Screened-Safe Release Reliability

Source files:

- `experiments/results/screened_safe_release_metrics.md`
- `experiments/results/screened_safe_release_metrics.csv`
- `experiments/results/screened_safe_release_summary.json`
- `experiments/results/screened_safe_release_multiseed_metrics.md`
- `experiments/results/screened_safe_release_multiseed_metrics.csv`
- `experiments/results/screened_safe_release_multiseed_raw.csv`
- `experiments/results/screened_safe_release_multiseed_summary.json`

Reported fields include released scenarios, safe-release precision, released
risky scenarios, released violation severity share, maximum released severity,
released violating buses, avoided AC calls, interval width, and released PV/load
proxies. The multi-seed companion reports mean, standard deviation, and 95%
confidence intervals over the three configured random seeds. This table audits
the scenario-level reliability of not sending a forecasted scenario to
downstream AC optimization.

## Table 20. Screening-Budget Triage Value

Source files:

- `experiments/results/screening_budget_metrics.md`
- `experiments/results/screening_budget_metrics.csv`
- `experiments/results/screening_budget_summary.json`
- `experiments/results/screening_budget_multiseed_metrics.md`
- `experiments/results/screening_budget_multiseed_metrics.csv`
- `experiments/results/screening_budget_multiseed_raw.csv`
- `experiments/results/screening_budget_multiseed_summary.json`

Reported fields include AC-call budget, AC calls avoided, risky-scenario recall
under budget, realized severity capture, post-policy severity reduction,
post-policy violating scenarios, post-policy violating buses, and action-cost
proxy. This table evaluates whether the interval risk score is useful when
only a limited number of scenarios can be sent to downstream AC-audited
correction. The multi-seed companion repeats the audit over the three
seed-specific AC candidate grids.

## Table 21. Paired Statistical Evidence Audit

Source files:

- `experiments/results/statistical_evidence_metrics.md`
- `experiments/results/statistical_evidence_metrics.csv`
- `experiments/results/statistical_evidence_raw.csv`
- `experiments/results/statistical_evidence_summary.json`

Reported fields include experiment family, paired comparison, metric, preferred
direction, paired-unit count, mean delta, delta standard deviation, bootstrap
95% confidence interval, better-unit fraction, and all-units-better flag. This
table audits whether the main prediction and operating-value claims are stable
over completed split/seed units without claiming universal validity under
arbitrary feeder, time, or PV-shift distributions.

## Table 22. Candidate-Action Screening Audit

Source files:

- `experiments/results/candidate_action_screening_metrics.md`
- `experiments/results/candidate_action_screening_metrics.csv`
- `experiments/results/candidate_action_screening_scores.csv`
- `experiments/results/candidate_action_screening_raw_predictions.csv`
- `experiments/results/candidate_action_screening_summary.json`
- `experiments/results/candidate_action_screening_multiseed_metrics.md`
- `experiments/results/candidate_action_screening_multiseed_metrics.csv`
- `experiments/results/candidate_action_screening_multiseed_raw.csv`
- `experiments/results/candidate_action_screening_multiseed_ac_candidates.csv`
- `experiments/results/candidate_action_screening_multiseed_scores.csv`
- `experiments/results/candidate_action_screening_multiseed_raw_predictions.csv`
- `experiments/results/candidate_action_screening_multiseed_summary.json`

Reported fields include top-k corrective action candidates per scenario,
candidate AC audits avoided, full-best action retention, same-action rate,
post-action violating scenarios/buses relative to full grid search, and proxy
action-cost deltas. This table tests whether VoltGuard can prune the
downstream action grid before AC audit; it is not an AC feasibility
certificate. The multi-seed companion recomputes the AC candidate grid for
each configured random split and reports mean, standard deviation, and 95%
confidence intervals for top-three candidate pruning.

## Table 23. Risk-Cost Candidate-Action Tradeoff

Source files:

- `experiments/results/action_cost_tradeoff_metrics.md`
- `experiments/results/action_cost_tradeoff_metrics.csv`
- `experiments/results/action_cost_tradeoff_summary.json`
- `experiments/results/action_cost_tradeoff_multiseed_metrics.md`
- `experiments/results/action_cost_tradeoff_multiseed_metrics.csv`
- `experiments/results/action_cost_tradeoff_multiseed_raw.csv`
- `experiments/results/action_cost_tradeoff_multiseed_summary.json`

Reported fields include candidate AC audits avoided, action-cost weight,
top-k candidate count, retained full-grid action, post-action violations, and
action-cost delta. This is a sensitivity audit showing how far action cost can
be emphasized before voltage violations increase. The multi-seed companion
repeats the risk-cost curve over all configured random seeds using saved AC
candidate outcomes and reports robust zero-extra-violation settings.

## Table 24. Operational Runtime Benchmark

Source files:

- `experiments/results/runtime_operational_benchmark.md`
- `experiments/results/runtime_operational_benchmark.csv`
- `experiments/results/runtime_operational_summary.json`
- `experiments/results/runtime_ac_grid_raw.csv`

Reported fields include online screening time, full AC grid-search time,
screen-then-AC estimated time, top-budget estimated time, per-scenario runtime,
and speedup relative to auditing every scenario with AC grid search.

## Table 25. Scenario Risk-Ranking Quality

Source files:

- `experiments/results/scenario_risk_ranking_metrics.md`
- `experiments/results/scenario_risk_ranking_metrics.csv`
- `experiments/results/scenario_risk_ranking_summary.json`

Reported fields include ROC-AUC, average precision, Spearman correlation
between interval risk score and realized voltage-violation severity, top-k
risky capture, top-k severity capture, and bottom-k safe-screen precision.

## Figure Plan

| Figure | Purpose | Source data |
|---|---|---|
| Fig. 1 | VoltGuard screening framework and two-stage operating interface | `figure_descriptions.md` |
| Fig. 2 | Main feeders and split protocols | `scenario_summary.csv`, `dataset_split_summary.md` |
| Fig. 3 | Feature/residual ablation | `feature_residual_ablation.csv` |
| Fig. 4 | Calibration variant comparison | `conformal_ablation_metrics.csv` |
| Fig. 5 | Per-family coverage, width, recalibration, and asymmetric conformal audit | `per_family_conformal_metrics.csv`, `family_recalibration_audit.csv`, `asymmetric_conformal_metrics.csv` |
| Fig. 6 | Shift generalization and target recalibration | `scenario_level_metrics.csv`, `multi_seed_summary.csv`, `pv_shift_recalibration_metrics.csv`, `pv_shift_recalibration_energy_value_metrics.csv` |
| Fig. 7 | Forecast-noise robustness | `forecast_noise_robustness_metrics.csv` |
| Fig. 8 | AC-audited corrective value | `control_grid_search_summary.json`, `control_grid_search_selected_actions.csv` |
| Fig. 9 | Energy-management screening sensitivity and screened-safe release reliability | `energy_management_value_metrics.csv`, `energy_management_value_multiseed_metrics.csv`, `shift_energy_management_value_metrics.csv`, `screened_safe_release_metrics.csv` |
| Fig. 10 | Screening-budget triage and candidate-action pruning value | `screening_budget_metrics.csv`, `candidate_action_screening_metrics.csv`, `action_cost_tradeoff_metrics.csv` |
| Fig. 11 | Operational runtime value | `runtime_operational_benchmark.csv` |
| Fig. 12 | Scenario risk-ranking quality | `scenario_risk_ranking_metrics.csv`, `scenario_risk_ranking_raw.csv` |
| Fig. 13 | Branch-level physics consistency | `physics_consistency_audit.csv` |
