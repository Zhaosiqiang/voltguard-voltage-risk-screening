# Figure Descriptions

No article figures are generated in this package. The following descriptions
specify what should be plotted after author approval.

## Figure 1. VoltGuard Screening Framework

Four-panel workflow:

- Panel A: active distribution feeder with PV, EV load, flexible demand, and
  slack/root bus.
- Panel B: squared-voltage LinDistFlow backbone computing a physical voltage
  proxy from forecast injections and feeder topology.
- Panel C: topology-aware residual learner correcting the physical proxy;
  neural graph residual is shown only as an ablation branch.
- Panel D: conformal intervals generate voltage-risk flags that trigger
  downstream AC-audited grid search, OPF, or MPC.

## Figure 2. Main Feeders and Split Protocols

Show IEEE 33-bus and IEEE 69-bus as main radial distribution feeders, with IEEE
118-bus clearly labeled as supplementary stress test. Add a small split diagram
for random interpolation, synthetic time-block, PV-shift, and topology-held-out
33-to-69 transfer.

## Figure 3. Calibration Variant Comparison

Bar chart from `conformal_ablation_metrics.csv` and
`calibration_budget_sensitivity_metrics.csv` for the representative random
split:

- global,
- PV-conditioned,
- topology-conditioned,
- topology+PV+loading conditioned,
- topology+PV+loading no-shrinkage.

Use paired bars or grouped points for coverage, interval width, recall, and
missed violations.
Add a small inset showing calibration fraction versus coverage, interval
width, missed violations, and empty conditioned families for the main
VoltGuard variant.

## Figure 4. Per-Family Coverage, Width, and Recalibration Audit

Heatmap or faceted dot plot from `per_family_conformal_metrics.csv`. X-axis:
PV bin. Y-axis: feeder and load family. Color: empirical coverage. Dot size or
label: calibration sample count. A second panel should use
`family_recalibration_audit.csv` to show current versus audited inflate-only
width and missed violations for undercovered families, especially the 33-bus
PV 0.6 high-load regime.

## Figure 5. Shift Generalization

Line or grouped bar chart from `multi_seed_summary.csv` comparing global
boosting conformal and VoltGuard across:

- random interpolation,
- synthetic time-block,
- PV-penetration shift,
- topology-held-out 33-to-69.

Plot recall and false-alarm rate together to show the shift tradeoff.

## Figure 6. Two-Stage Operating Value

Flow chart plus small result table:

- VoltGuard screens risky scenarios.
- AC-audited corrective grid search evaluates candidate load-relief and PV
  curtailment actions.
- Show post-action violating scenarios, violating buses, and action cost from
  `control_grid_search_summary.csv`.

## Figure 7. Energy-Management Screening and Release Reliability

Three-panel chart from `energy_management_value_metrics.csv`,
`energy_management_value_multiseed_metrics.csv`,
`shift_energy_management_value_metrics.csv`,
`screened_safe_release_metrics.csv`, and
`screened_safe_release_multiseed_metrics.csv`:

- Panel A: nominal coverage on the x-axis; interval width, missed bus
  violations, and AC optimization calls avoided as paired lines or aligned
  small multiples. This shows the screening sharpness versus missed-violation
  tradeoff.
- Panel B: nominal coverage on the x-axis; accepted PV proxy, curtailed PV
  proxy, relieved load proxy, and proxy action cost. This shows how the
  calibrated risk level changes DER operating consequences without claiming a
  globally optimal dispatch.
- Panel C: release protocol on the x-axis; released scenarios, released risky
  scenarios, and released severity share, with multi-seed mean/95% CI when
  available. This audits whether scenarios not sent to AC optimization are
  clean at the scenario level.

## Figure 8. Screening-Budget Triage Value

Two-panel line chart from `screening_budget_metrics.csv`:

- Panel A: AC-call budget on the x-axis; severity capture and post-policy
  severity reduction on the y-axis for VoltGuard, boosting global conformal,
  random budget expectation, and oracle realized-severity ranking.
- Panel B: AC calls avoided, post-policy violating scenarios, and action-cost
  proxy. This panel should make clear that risk ranking improves severity
  triage but that final violation removal is limited by the downstream
  corrective action grid.

## Figure 9. Candidate-Action Screening Value

Two-panel plot from `candidate_action_screening_metrics.csv` and
`action_cost_tradeoff_metrics.csv`:

- Panel A: top-k candidate actions per scenario on the x-axis; candidate AC
  audits avoided and full-best action retention on paired y-axes for VoltGuard
  interval-risk, LinDistFlow point-risk, and cheapest-first pruning.
- Panel B: extra post-action violating scenarios/buses versus full AC grid
  search, with action-cost delta as a marker label. This figure should show
  that VoltGuard can reduce candidate AC audits without replacing the final
  AC-audited action selection.
- Panel C if space allows: action-cost weight on the x-axis for top-three
  candidate screening, with action-cost delta and extra violating scenarios on
  aligned axes. This shows the cost-safety tradeoff rather than hiding the
  operating tuning choice.

## Figure 10. Scenario Risk-Ranking Quality

Two-panel plot from `scenario_risk_ranking_metrics.csv` and
`scenario_risk_ranking_raw.csv`:

- Panel A: bar chart comparing ROC-AUC, average precision, and Spearman
  severity correlation for global conformal, topology+PV+loading conditioned
  VoltGuard, boosting global conformal, and neural graph ablation.
- Panel B: cumulative severity capture curve as scenarios are sorted by
  interval risk score. This shows whether the screening layer prioritizes the
  scenarios with the largest realized voltage-violation severity.
