# Submission Compile Report

Generated for the revised three-route VoltGuard submission package: ECM:X full
method route, ECM engineering route, and OAJPE minimal fallback route.

## Artifacts

- `submission_manuscript_ecmx.md` - primary assembled ECM:X submission
  manuscript with the complete physics-informed topology-aware residual and
  topology/PV/loading conformal calibration evidence.
- `submission_manuscript_ecmx.tex` - Elsevier `elsarticle` LaTeX conversion aid.
- `submission_build/submission_manuscript_ecmx.pdf` - compiled PDF smoke-test
  output.
- `submission_manuscript_ecm.md/.tex` and
  `submission_build/submission_manuscript_ecm.pdf` - differentiated
  engineering-system version centered on AC-call reduction, runtime, and
  downstream audit efficiency.
- `submission_manuscript_oajpe.md/.tex` and
  `submission_build/submission_manuscript_oajpe.pdf` - differentiated minimal
  fallback version centered on LinDistFlow residual correction, quantile
  interval screening, RMSE, coverage, and AC-call reduction.
- `manuscript_ecm_engineering.md` and `manuscript_oajpe_minimal.md` - route
  source manuscripts that keep ECM and OAJPE materially distinct from the full
  ECM:X manuscript.
- `submission_variant_strategy.md` - publication-boundary memo for avoiding
  overlapping simultaneous submissions and self-plagiarism risk.
- `ecmx_highlights.txt` - separate editable highlights file for ECM:X upload.
- `ecm_highlights.txt` - separate editable highlights file for ECM upload.
- `ecmx_cover_letter.md` - separate editable cover-letter draft for ECM:X
  upload.
- `ecmx_submission_readiness_checklist.md` - official-guide-aligned upload
  checklist and remaining manual gates.
- `ecmx_upload_input_packet.md` - author-fill packet for portal metadata,
  declarations, data/code availability, figure decisions, and hard-stop checks.
- `oajpe_upload_input_packet.md` - OAJPE-specific upload packet for page
  limit, APC, abstract, keyword, AI disclosure, and route-boundary checks.
- `journal_format_audit.md` - official-source-based format audit for ECM:X,
  ECM, and OAJPE.
- `submission_references.md` - numbered references used by the generated
  manuscript.
- `figures/*.svg` - canonical vector artwork for the manuscripts, including
  the graphical abstract/workflow, conformal ablations, per-family calibration,
  shift audits, operating-value frontiers, candidate-action screening, risk
  ranking, and OAJPE baseline figures.
- `figures/*.pdf` - LaTeX compilation companions generated from the SVG
  artwork and embedded in the manuscript PDFs.
- `figures/figure_manifest.json` - figure inventory with SVG/PDF pairs.
- `experiments/results/reproducibility_manifest.json` and
  `experiments/results/reproducibility_manifest.md` - artifact inventory,
  commands, and checksums for local reproducibility. The validation summary is
  intentionally not checksummed because the validator rewrites it after checking
  the manifest.
- `author_declaration_gate.md` - manual metadata/declaration gate retained as
  a separate author checklist; it is not included in the assembled manuscript.
- `experiments/results/topology_transfer_bidirectional_metrics.md/.csv` -
  bidirectional 33-to-69 and 69-to-33 topology-transfer audit added to the
  ECM:X robustness evidence.
- `experiments/results/candidate_action_screening_multiseed_metrics.md/.csv`
  and raw companion files - three-seed downstream candidate-action pruning
  audit with seed-specific AC candidate grids.
- `experiments/results/action_cost_tradeoff_multiseed_metrics.md/.csv` -
  three-seed risk-cost candidate-action tradeoff audit using saved AC candidate
  outcomes.
- `experiments/results/high_pv_hosting_frontier_metrics.md/.csv` - AC-audited
  accepted-PV versus overvoltage-reduction frontier for the high-PV hosting
  stress scenarios.
- `experiments/results/energy_management_frontier_metrics.md/.csv` -
  consolidated energy-management frontier tying screened-safe release,
  budgeted AC triage, action pruning, and high-PV hosting results into one
  operating-value table.
- `experiments/results/screening_budget_multiseed_metrics.md/.csv` -
  three-seed limited-budget AC-audit triage using saved seed-specific AC
  candidate grids.
- `experiments/results/statistical_evidence_metrics.md/.csv` - paired
  split/seed delta audit with bootstrap intervals for prediction and budgeted
  AC-triage stability evidence.
- `experiments/results/ev_conditioning_sample_size_outlook.md/.csv` -
  supplementary EV-conditioning sample-support outlook for deciding when
  EV-conditioned calibration should be retested.

## Last Build Command

```bash
python VoltGuard-CPGNN/experiments/write_submission_manuscript.py
pandoc --number-sections VoltGuard-CPGNN/submission_manuscript_ecmx.md -s -o VoltGuard-CPGNN/submission_manuscript_ecmx.tex
tectonic -X compile VoltGuard-CPGNN/submission_manuscript_ecmx.tex --outdir VoltGuard-CPGNN/submission_build
pandoc --number-sections VoltGuard-CPGNN/submission_manuscript_ecm.md -s -o VoltGuard-CPGNN/submission_manuscript_ecm.tex
tectonic -X compile VoltGuard-CPGNN/submission_manuscript_ecm.tex --outdir VoltGuard-CPGNN/submission_build
pandoc --number-sections VoltGuard-CPGNN/submission_manuscript_oajpe.md -s -o VoltGuard-CPGNN/submission_manuscript_oajpe.tex
tectonic -X compile VoltGuard-CPGNN/submission_manuscript_oajpe.tex --outdir VoltGuard-CPGNN/submission_build
python VoltGuard-CPGNN/experiments/write_reproducibility_manifest.py
python VoltGuard-CPGNN/experiments/validate_project.py
```

## Status

- Build status: pass.
- PDF generated: yes.
- ECM:X and ECM LaTeX class: `elsarticle` with `preprint,12pt`.
- OAJPE LaTeX class: `IEEEtran` with `journal`.
- Author/declaration gate included in formal manuscripts: no.
- Internal submission metadata included in formal manuscripts: no.
- Figure-placeholder section included in formal manuscripts: no.
- Article figures generated: yes, as SVG with PDF compilation companions.
- Figures inserted into formal manuscripts: yes.
- ECM:X highlights file generated: yes.
- ECM highlights file generated: yes.
- ECM:X cover letter draft generated: yes.
- ECM:X readiness checklist generated: yes.
- ECM:X upload input packet generated: yes.
- Numbered references included: yes.
- Reproducibility manifest generated: yes.
- Reproducibility manifest result files: 107.
- Project validation: pass.
- Known layout warnings: underfull/overfull hbox warnings from long text,
  long URLs, and wide result tables; local Times/STIX font path warnings are
  emitted by Tectonic on this machine.

## Boundary

This is a submission-draft smoke test, not final Elsevier live-template
clearance. Before actual upload, the author must verify the clean
funding/conflict statements, repository availability language, and
target-journal declaration fields, then check the manuscript against the live
journal guide.
