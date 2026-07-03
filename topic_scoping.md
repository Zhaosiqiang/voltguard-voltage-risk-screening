# Topic Scoping: Revised VoltGuard Paper

## Selected Topic

**VoltGuard: Physics-Informed Topology-Aware Residual Learning with Conformal
Calibration for Renewable-Hosting Voltage-Risk Screening in Active Distribution
Networks**

The paper studies calibrated voltage-risk screening in active distribution
networks with uncertain load, PV, and EV operating conditions. The key claim is
not a graph-neural architecture claim. The selected method combines a
squared-voltage LinDistFlow physical backbone, topology-aware residual learning,
and split conformal calibration conditioned on feeder, PV, and loading family.

## Research Question

Can topology/PV/loading conditioned conformal calibration reduce missed voltage
violations and sharpen voltage-risk intervals relative to point predictors and
global conformal baselines, while remaining honest about AC feasibility and
distribution-shift limits?

## Novelty

- Physics-informed residual target rather than direct black-box voltage
  prediction.
- Conformal calibration reported at both global and per-family levels.
- Bus-level and scenario-level voltage-risk metrics.
- Two-stage operating interpretation: VoltGuard screens risk; AC-audited grid
  search, OPF, or MPC performs corrective action.
- Neural graph residual learning is evaluated only as an ablation.

## Target Route

The cycle-first route is Energy Conversion and Management: X. The second route
is Energy and AI. Advances in Applied Energy / Applied Energy are stretch
targets after adding unbalanced OpenDSS/SMART-DS validation and a stronger
OPF/MPC benchmark.
