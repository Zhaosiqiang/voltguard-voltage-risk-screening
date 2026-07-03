# Reproducible Experiment Plan

## Objective

Evaluate VoltGuard as a calibrated voltage-risk screening layer for active
distribution networks. The accepted claim is not "a stronger GNN"; it is that a
physics-informed topology-aware residual learner plus conditioned conformal
calibration improves the risk-sharpness tradeoff.

## Systems

- Main distribution feeders: IEEE 33-bus and IEEE 69-bus.
- Supplementary stress test: IEEE 118-bus.
- Future stretch validation: IEEE 123-bus/OpenDSS or SMART-DS.

## Scenario Generation

For each feeder, generate 300 AC-solvable scenarios with:

- randomized load scale,
- PV penetration in 20%, 40%, 60%, and 80% families,
- EV/flexible-load perturbation,
- randomized PV siting,
- AC power-flow voltage labels.

## Splits

- Random interpolation: scenario-disjoint 60/20/20.
- Synthetic time-block: ordered scenario blocks.
- PV-penetration shift: lower PV for training, high PV for testing.
- Topology-held-out: 33-bus training with 69-bus calibration/testing.

## Methods

- Squared-voltage LinDistFlow physical backbone.
- Random forest.
- Gradient boosting.
- Boosting plus global conformal.
- VoltGuard topology-aware residual with global, PV, topology, and
  topology+PV+loading conformal calibration.
- VoltGuard topology+PV+loading no-shrinkage ablation.
- Neural graph residual ablation.
- AC corrective grid-search benchmark as downstream optimizer.

## Metrics

- Bus-level MAE, RMSE, max error.
- Empirical coverage and interval width.
- Bus-level precision, recall, F1, false-alarm rate, missed violations.
- Scenario-level precision, recall, false-alarm rate, missed risky scenarios.
- Per-family calibration samples, test samples, coverage, width, recall, false
  alarm, missed violations.
- Runtime and AC post-action audit statistics.
