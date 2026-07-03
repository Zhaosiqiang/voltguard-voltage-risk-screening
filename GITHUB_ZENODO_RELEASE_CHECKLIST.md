# GitHub and Zenodo Release Checklist

This checklist records the public release of the VoltGuard paper collection
and the remaining DOI action for Zenodo.

GitHub repository:
`https://github.com/Zhaosiqiang/voltguard-voltage-risk-screening`

GitHub release:
`https://github.com/Zhaosiqiang/voltguard-voltage-risk-screening/releases/tag/v1.0.0-submission`

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
- `LICENSE`, `CITATION.cff`, and `.zenodo.json` for reuse, citation, and DOI
  metadata.

## Files To Exclude Before Public Upload

- local virtual environments, caches, and `__pycache__` folders;
- editor-specific metadata;
- temporary PDF render folders under `/tmp`;
- any private utility data, if future feeder pilots are added.

## DOI Release Status

Completed:

- public GitHub repository created;
- cleaned project tree pushed to `main`;
- validation pass archived locally;
- GitHub release tagged `v1.0.0-submission`;
- three manuscript PDFs attached to the release.

Remaining external-account action:

- connect the GitHub repository to Zenodo and mint a DOI. This requires the
  repository owner's Zenodo authorization or a `ZENODO_TOKEN`, which is not
  present in the current execution environment.

## Current Local Evidence

- `experiments/results/reproducibility_manifest.json`
- `experiments/results/reproducibility_manifest.md`
- `experiments/results/review_baseline_comparison_metrics.csv`
- `experiments/results/baseline_design_rationale_metrics.csv`
- `experiments/results/dms_prototype_weekly_log.csv`
- `submission_build/submission_manuscript_ecmx.pdf`
- `submission_build/submission_manuscript_ecm.pdf`
- `submission_build/submission_manuscript_oajpe.pdf`
