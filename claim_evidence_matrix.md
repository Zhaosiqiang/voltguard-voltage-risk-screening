# Claim/Evidence/Reviewer-Risk Control Matrix

This matrix controls what each manuscript may claim. It is intentionally
conservative because the project contains three drafts that could otherwise
look like one method repackaged three ways.

Across all drafts, any learned or physical estimator must be described as a
screening layer unless an AC-audited feasibility or control proof is actually
provided.

| Claim | Evidence artifact | Reviewer risk | Do Not Claim |
|---|---|---|---|
| ECM:X is the method paper: topology-aware residual learning plus topology/PV/loading conditioned conformal calibration improves voltage-risk interval screening. | `submission_manuscript_ecmx.md`; `experiments/results/model_voltage_metrics.md`; `experiments/results/conformal_ablation_metrics.csv`; `experiments/results/per_family_conformal_metrics.csv` | Contribution dilution if operating-value studies dominate the narrative. | Do not present candidate-action pruning, runtime, or energy frontier as central contributions. |
| The method is a screening layer, not an AC feasibility certificate. | `manuscript_draft.md`; `submission_manuscript_ecmx.md`; `experiments/results/control_grid_search_summary.json` | Reviewers may read risk flags as feasibility guarantees. | Do not claim AC feasibility, OPF/MPC replacement, or universal safety. |
| Neural graph residual learning is only an ablation. | `experiments/results/evaluation_metrics_all_runs.csv`; `submission_manuscript_ecmx.md` | Reviewers may expect GNN novelty if the title or abstract overemphasizes graph learning. | Do not call the paper a graph-neural method. |
| Topology-held-out and PV-shift tests bound the calibration claim. | `experiments/results/topology_transfer_bidirectional_metrics.csv`; `experiments/results/pv_shift_recalibration_metrics.md` | Shift experiments can be mistaken for unconditional robustness. | Do not claim distribution-free safety under arbitrary topology or PV drift. |

The topology-held-out wording is retained here as a reviewer-facing search key
for the transfer audit.
| Family recalibration is an audit, not a new guarantee. | `experiments/results/family_recalibration_audit.csv`; `experiments/results/family_recalibration_audit.md` | Reviewers may ask whether undercovered families invalidate the method. | Say family recalibration diagnoses and repairs local undercoverage under the stated protocol. |
| Calibration-budget sensitivity shows the need for family diversity. | `experiments/results/calibration_budget_sensitivity_metrics.md`; `experiments/results/calibration_budget_sensitivity_raw.csv` | Small family sample sizes can create overconfident intervals. | Do not imply family-wise guarantees when calibration families are missing. |
| Forecast-noise robustness is supporting evidence only. | `experiments/results/forecast_noise_robustness_metrics.md`; `experiments/results/forecast_noise_robustness_raw.csv` | Forecast-noise tests may appear to assume fixed AC labels under perturbation. | Do not claim complete forecast-error robustness. |
| PV-shift recalibration and energy-value artifacts are project-level supporting audits, not the ECM:X main contribution. | `experiments/results/pv_shift_recalibration_energy_value_metrics.md`; `experiments/results/energy_management_frontier_metrics.md` | Reviewers may see a second energy-management paper embedded inside the method paper. | Keep them outside the main ECM:X evidence set unless writing a separate controller study. |
| ECM is the DMS integration paper. | `submission_manuscript_ecm.md`; `manuscript_ecm_engineering.md`; `submission_variant_strategy.md` | Duplicate-publication risk if ECM reuses ECM:X result numbers. | Do not reuse ECM:X RMSE, coverage, interval width, release count, AC-call avoidance, or runtime claims. |
| OAJPE is the LinDistFlow-global-quantile baseline note. | `submission_manuscript_oajpe.md`; `experiments/results/oajpe_lindistflow_quantile_metrics.md`; `experiments/results/oajpe_lindistflow_quantile_summary.json`; `experiments/results/baseline_design_rationale_metrics.md` | Baseline may look like a truncated learned-method paper. | Do not include residual learning, family-conditioned calibration, graph models, or AC-budget/runtime as baseline contributions; a clearly labeled VoltGuard comparison is allowed only for context. |

## Supporting Audit Artifacts

These artifacts may support reviewer responses or supplemental audits, but they
do not change the primary claim boundary above: `risk_stratified_calibration_bus.md`,
`asymmetric_conformal_metrics.md`, `model_voltage_screening_metrics.md`,
`physics_consistency_audit.md`, `screening_budget_metrics.md`,
`screening_budget_multiseed_metrics.md`, `statistical_evidence_metrics.md`,
`shift_energy_management_value_metrics.md`,
`topology_transfer_bidirectional_metrics.md`,
`candidate_action_screening_metrics.md`,
`candidate_action_screening_multiseed_metrics.md`,
`action_cost_tradeoff_metrics.md`,
`action_cost_tradeoff_multiseed_metrics.md`, and
`high_pv_hosting_frontier_metrics.md`.

## Submission Separation

Energy Conversion and Management: X receives the method paper only. The ECM
DMS paper and OAJPE baseline note answer different questions and must not be
submitted as shorter or longer versions of the same manuscript. Any later
submission must be rechecked against this matrix and, where required, disclose
related work transparently.
