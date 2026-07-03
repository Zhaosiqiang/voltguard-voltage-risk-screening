# VoltGuard v1.0.0-submission

This release archives the revised VoltGuard paper collection after addressing
the July 3, 2026 professional review report.

## Included Manuscripts

- `submission_build/submission_manuscript_ecmx.pdf` - main VoltGuard method
  manuscript.
- `submission_build/submission_manuscript_ecm.pdf` - DMS integration
  architecture manuscript.
- `submission_build/submission_manuscript_oajpe.pdf` - LinDistFlow-quantile
  baseline note.

## Reviewer-Requested Additions

- reviewer-requested quantile-regression and Gaussian-process baseline
  comparison;
- expanded IEEE 118-bus stress audit;
- failure-mode analysis and computational breakeven discussion;
- DMS algorithms, stakeholder requirements, standards discussion, and
  1008-cycle prototype log;
- LinDistFlow baseline design-rationale comparison and direct VoltGuard
  comparison;
- cross-paper positioning, real-world-validation gap discussion, and
  GitHub/Zenodo release metadata.

## Reproducibility

Run validation from the parent directory:

```bash
python VoltGuard-CPGNN/experiments/validate_project.py
```

The latest local validation status before this release was `pass`.
