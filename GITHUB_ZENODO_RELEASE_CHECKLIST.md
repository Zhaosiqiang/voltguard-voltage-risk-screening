# GitHub and Zenodo Release Checklist

This checklist prepares the VoltGuard paper collection for a public
GitHub/Zenodo archive. It records the release scope promised in the manuscript
Code and Data Availability sections.

## Repository Scope

The public repository should contain:

- scenario-generation code for the IEEE 33-bus, IEEE 69-bus, and supplementary
  IEEE 118-bus experiments;
- model-evaluation code for the topology-aware residual learner, neural graph
  residual ablation, reviewer-requested quantile-regression and
  Gaussian-process baselines, and LinDistFlow baseline;
- conformal calibration, family-conditioned calibration, shrinkage fallback,
  and per-family metric scripts;
- DMS prototype script and the 1008-cycle weekly queue log generator;
- table-generation scripts, manuscript-generation scripts, and validation
  script;
- raw predictions, conformal scores, family labels, runtime outputs,
  post-action AC audit summaries, and reviewer-requested baseline comparison
  artifacts;
- manuscript source files, generated submission markdown/TeX, and final PDF
  builds.

## Files To Exclude Before Public Upload

- local virtual environments, caches, and `__pycache__` folders;
- editor-specific metadata;
- temporary PDF render folders under `/tmp`;
- any private utility data, if future feeder pilots are added.

## DOI Release Steps

1. Create a public GitHub repository named `voltguard-voltage-risk-screening`.
2. Upload the cleaned project tree with this checklist, `README.md`,
   `CITATION.cff`, `requirements.txt`, manuscript sources, scripts, and
   reproducibility manifest.
3. Run `python VoltGuard-CPGNN/experiments/validate_project.py` from the parent
   directory and archive the pass output.
4. Create a GitHub release tagged `v1.0.0-submission`.
5. Connect the GitHub repository to Zenodo and mint a DOI for the release.
6. Replace the manuscript placeholder phrase "public GitHub/Zenodo archive
   before publication" with the final repository URL and DOI after upload.

## Current Local Evidence

- `experiments/results/reproducibility_manifest.json`
- `experiments/results/reproducibility_manifest.md`
- `experiments/results/review_baseline_comparison_metrics.csv`
- `experiments/results/baseline_design_rationale_metrics.csv`
- `experiments/results/dms_prototype_weekly_log.csv`
- `submission_build/submission_manuscript_ecmx.pdf`
- `submission_build/submission_manuscript_ecm.pdf`
- `submission_build/submission_manuscript_oajpe.pdf`

