# Experiments

This folder contains the reproducible experiment pipeline for VoltGuard.

Current status: executable experiments have been run for IEEE 33-bus and IEEE
69-bus as the main distribution feeders, with IEEE 118-bus retained as a
supplementary stress test. The selected residual learner uses scikit-learn with
topology/electrical features. A lightweight neural graph residual is evaluated
only as an ablation.

Recommended setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r VoltGuard-CPGNN/requirements.txt
```

Neural-ablation dependencies:

```bash
pip install -r VoltGuard-CPGNN/requirements-optional-gnn.txt
```

Executed stages:

1. `generate_scenarios.py` - create IEEE 33/69-bus operating scenarios,
   supplementary IEEE 118-bus scenarios, and AC power-flow labels.
2. `evaluate_models.py` - train baseline regressors, topology-aware residual
   model, neural graph residual ablation, conformal intervals, per-family
   calibration tables, multi-seed statistics, and scenario-level screening
   metrics.
3. `evaluate_control_benchmark.py` - run a traditional AC-audited corrective
   grid-search benchmark over flexible-load relief and PV curtailment.
4. `evaluate_sensitivity.py` - run conformal risk-level sensitivity at nominal
   coverage 95%, 90%, 85%, and 80%.
5. `evaluate_asymmetric_conformal.py` - audit one-sided lower/upper conformal
   radii against the main symmetric absolute-residual intervals.
6. `evaluate_calibration_budget_sensitivity.py` - resample calibration
   scenarios to quantify how calibration budget affects coverage, width,
   missed violations, and empty conditioned families.
7. `evaluate_family_recalibration.py` - audit undercovered topology/PV/loading
   families and quantify inflate-only recalibration tradeoffs.
8. `evaluate_paired_seed_deltas.py` - compute paired seed-level deltas between
   the main VoltGuard model and boosting plus global conformal.
9. `evaluate_feature_ablation.py` - test local-only, local+topology, full
   topology/electrical, and direct-versus-residual estimator variants.
10. `evaluate_ev_conditioning.py` - test whether EV scale should be added to
   conformal conditioning families or kept as a point-estimator feature.
11. `evaluate_energy_management_value.py` - translate calibrated intervals into
   screened-safe ratio, avoided AC-optimization calls, risky-scenario recall,
   accepted PV proxy, relieved-load proxy, and action-cost sensitivity.
12. `evaluate_energy_management_value_multiseed.py` - repeat the
   energy-management screening metrics over the three configured random seeds
   and report mean, standard deviation, and 95% confidence intervals.
13. `evaluate_shift_energy_management_value.py` - repeat the primary
   screening-value metrics across random, synthetic time-block, PV-shift, and
   topology-held-out splits over the configured seeds.
14. `evaluate_topology_transfer_bidirectional.py` - repeat the topology-held-out
   screening audit in both 33-to-69 and 69-to-33 directions with target-feeder
   calibration.
15. `evaluate_screened_safe_release.py` - audit whether scenarios released
   without downstream AC optimization are actually safe, including released
   risky scenarios, released violation severity, and released PV/load proxies.
16. `evaluate_screened_safe_release_multiseed.py` - repeat the release audit
   over the three configured random seeds and report mean, standard deviation,
   and 95% confidence intervals for released risky scenarios and severity.
17. `evaluate_forecast_noise_robustness.py` - perturb only pre-dispatch
   load/PV/EV forecast features, recompute LinDistFlow inputs, and quantify
   robustness of calibration and screening metrics.
18. `evaluate_risk_ranking.py` - evaluate scenario-level risk ranking for
   downstream AC optimization prioritization.
19. `evaluate_pv_shift_recalibration.py` - audit whether a small target
   high-PV AC-audited calibration set repairs PV-shift coverage and quantify
   the interval-width/false-alarm cost.
20. `evaluate_pv_shift_recalibration_energy_value.py` - translate PV-shift
   target recalibration into screened-safe scenarios, avoided AC calls,
   missed violations, and interval-width tradeoffs.
21. `evaluate_risk_stratified_calibration.py` - audit bus-level and
   scenario-level calibration in true-violation, boundary-safe, near-safe, and
   interior-safe voltage strata.
22. `evaluate_screening_budget.py` - evaluate limited-budget AC-optimization
   triage using interval risk rankings and the AC grid-search audit.
23. `evaluate_screening_budget_multiseed.py` - repeat limited-budget AC triage
   over the three seed-specific AC candidate grids.
24. `evaluate_statistical_evidence.py` - convert the main split/seed
   prediction and budgeted-AC triage results into paired delta, bootstrap
   interval, and better-unit-fraction evidence.
25. `evaluate_candidate_action_screening.py` - rank the nine downstream
   corrective action candidates per scenario before AC audit and quantify
   top-k candidate pruning against full AC grid search.
26. `evaluate_candidate_action_screening_multiseed.py` - repeat the top-three
   candidate-action pruning audit over all configured random seeds, recomputing
   AC candidate outcomes per seed.
27. `evaluate_action_cost_tradeoff.py` - audit risk-versus-action-cost weights
   for VoltGuard candidate-action pruning before AC audit.
28. `evaluate_action_cost_tradeoff_multiseed.py` - repeat the risk-cost
   candidate-action tradeoff over all configured random seeds using saved AC
   candidate outcomes.
29. `evaluate_runtime_benchmark.py` - measure online VoltGuard screening time,
   full AC grid-search time, and budgeted screen-then-AC runtime.
30. `evaluate_physics_consistency.py` - audit branch-level LinDistFlow
   voltage-drop residuals for AC labels and representative saved predictions.
31. `evaluate_high_pv_hosting_stress.py` - run an AC-only high-PV/light-load
   overvoltage and PV-curtailment stress audit on IEEE 33/69 feeders.
32. `evaluate_high_pv_hosting_frontier.py` - retain the full AC PV-curtailment
   frontier for accepted PV versus overvoltage reduction.
33. `evaluate_energy_management_frontier.py` - assemble the completed release,
   budgeted triage, candidate-action pruning, and high-PV hosting audits into a
   consolidated operating frontier.
34. `write_reproducibility_manifest.py` - record reproduction commands and
   SHA256 checksums for source, result, and submission artifacts.
35. `validate_project.py` - verify the ECM:X-route manuscript, raw artifacts,
   split coverage, neural-ablation boundary, energy-management results, and PDF
   smoke-test outputs.

Executed commands:

```bash
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/generate_scenarios.py --feeders 33 69 118 --scenarios 300 --seed 42
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_models.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_control_benchmark.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_sensitivity.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_asymmetric_conformal.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_calibration_budget_sensitivity.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_family_recalibration.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_paired_seed_deltas.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_feature_ablation.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_ev_conditioning.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_energy_management_value.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_energy_management_value_multiseed.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_shift_energy_management_value.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_topology_transfer_bidirectional.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screened_safe_release.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screened_safe_release_multiseed.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_forecast_noise_robustness.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_risk_ranking.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_pv_shift_recalibration.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_pv_shift_recalibration_energy_value.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_risk_stratified_calibration.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screening_budget.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_screening_budget_multiseed.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_statistical_evidence.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_candidate_action_screening.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_candidate_action_screening_multiseed.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_action_cost_tradeoff.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_action_cost_tradeoff_multiseed.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_runtime_benchmark.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_physics_consistency.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_high_pv_hosting_stress.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_high_pv_hosting_frontier.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/evaluate_energy_management_frontier.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/write_reproducibility_manifest.py
VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/validate_project.py
```
