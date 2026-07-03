# Professional Review Action Matrix

This matrix records how the July 3, 2026 professional review report was acted
on. It is a revision-control artifact, not manuscript text.

| Report requirement | Action taken | Evidence |
|---|---|---|
| Reduce defensive writing in the main method abstract/introduction | Rewrote the VoltGuard abstract and introduction to lead with the calibrated screening contribution; moved scope language to a dedicated subsection | `manuscript_draft.md`, Section 1.1 |
| Add a clear Scope subsection | Added "Scope and Companion-Paper Positioning" | `manuscript_draft.md` |
| Add comparison with at least three competing approaches | Added LinDistFlow, random forest, gradient boosting, global conformal boosting, quantile regression, Gaussian-process UQ, and neural graph residual comparison | `manuscript_draft.md`, Section 6.5; `experiments/results/review_baseline_comparison_metrics.md` |
| Add quantile regression and Gaussian-process baselines | Implemented and ran reviewer-requested baseline script | `experiments/evaluate_review_baselines.py`; `review_baseline_comparison_metrics.csv` |
| Expand IEEE 118-bus or replace with SMART-DS/OpenDSS | Expanded IEEE 118-bus into a detailed stress-audit table and explicitly preserved 33/69 as main distribution evidence | `manuscript_draft.md`, Section 6.12 |
| Discuss realistic feeder/real-world validation gap | Added real-world validation discussion in all three papers | `manuscript_draft.md`; `manuscript_ecm_engineering.md`; `manuscript_oajpe_minimal.md` |
| Add failure mode analysis | Added detailed analysis of the one missed bus-level violation: feeder 33, scenario 153, bus 7 | `manuscript_draft.md`, Section 6.13 |
| Add computational cost table and breakeven analysis | Added training, online screening, AC grid-search timing, speedups, and breakeven calculation | `manuscript_draft.md`, Section 6.14; `runtime_operational_benchmark.csv` |
| Shorten main method title | Shortened to "VoltGuard: Topology-Aware Voltage-Risk Screening with Conformal Calibration for Active Distribution Networks" | `manuscript_draft.md`; `write_submission_manuscript.py` |
| Standardize voltage notation | Retained squared-voltage LinDistFlow notation and magnitude-domain intervals | `manuscript_draft.md`, Sections 3-4 |
| Improve figure readability | Earlier figure-generation revision enlarged fonts, added subfigure labels, and enlarged the graphical abstract scenario block | `experiments/generate_submission_figures.py`; `figures/` |
| Add model maintenance and retraining discussion | Added recalibration triggers for topology, DER changes, residual drift, and forecast-envelope shift | `manuscript_draft.md`, Discussion |
| Add DMS algorithms | Added Algorithm 1 input validation/queue assignment, Algorithm 2 fallback evaluation, Algorithm 3 rolling drift audit | `manuscript_ecm_engineering.md` |
| Add detailed DMS workflow flowchart | Existing graphical workflow is referenced and complemented with explicit workflow sequence and algorithms | `manuscript_ecm_engineering.md`; `fig01_graphical_abstract_workflow.pdf` |
| Add DMS prototype demonstration with 1000+ scenarios over a week | Implemented and ran 1008-cycle weekly DMS prototype simulation | `experiments/evaluate_dms_prototype.py`; `dms_prototype_weekly_log.csv`; `dms_prototype_queue_summary.md` |
| Clarify generalization to non-VoltGuard screening methods | Added general screening-module interface requirements | `manuscript_ecm_engineering.md`, Section 2.3 |
| Add stakeholder requirements | Added operator, utility IT, and regulator/compliance requirements | `manuscript_ecm_engineering.md`, Section 4 |
| Add DMS standards and protocols | Added IEC 61970/61968 CIM, IEEE 2030.5, and OpenFMB discussion | `manuscript_ecm_engineering.md`, Section 2.2 |
| Add acronym table | Added DMS/DER/OPF/MPC/SCADA/AMI/CIM/IEC acronym table | `manuscript_ecm_engineering.md`, Section 2.1 |
| Reconsider DMS target journal | Added venue-fit paragraph discussing ECM, EPSR, and IEEE Transactions on Power Systems fit | `manuscript_ecm_engineering.md`, Discussion |
| Strengthen standalone motivation for LinDistFlow baseline | Added standardized-baseline motivation and companion-paper positioning | `manuscript_oajpe_minimal.md`, Introduction |
| Add baseline design rationale | Added comparison with flat voltage, historical envelope, and linear sensitivity regression | `manuscript_oajpe_minimal.md`, Section 2.3; `baseline_design_rationale_metrics.md` |
| Add direct comparison with VoltGuard | Added side-by-side LinDistFlow vs VoltGuard table and interpretation | `manuscript_oajpe_minimal.md`, Section 4.2 |
| Discuss when baseline is sufficient vs learning needed | Added interpretation after the VoltGuard comparison table | `manuscript_oajpe_minimal.md`, Section 4.2 |
| Reconsider baseline venue | Added technical-note/arXiv/supplement venue positioning | `manuscript_oajpe_minimal.md`, Boundary and Use |
| Commit to code/data release | Updated generated declarations to "Code and Data Availability", published the package on GitHub, and added release metadata/checklist for DOI handoff | `experiments/write_submission_manuscript.py`; `GITHUB_ZENODO_RELEASE_CHECKLIST.md`; `CITATION.cff`; `https://github.com/Zhaosiqiang/voltguard-voltage-risk-screening/releases/tag/v1.0.0-submission` |
| Add cross-referencing paragraphs across all papers | Added companion-paper positioning to the introductions | all three `manuscript_*.md` source files |
| Expand related work and comparison table | Added method-positioning comparison tables to the main method paper, the DMS integration paper, and the baseline note | `manuscript_draft.md`, Related Work; `manuscript_ecm_engineering.md`, Section 2.4; `manuscript_oajpe_minimal.md`, Section 1.1 |
