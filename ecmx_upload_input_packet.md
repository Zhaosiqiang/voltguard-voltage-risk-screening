# ECM:X Upload Input Packet

Source checked on 2026-07-02:

- Energy Conversion and Management: X journal page:
  https://www.sciencedirect.com/journal/energy-conversion-and-management-x
- Energy Conversion and Management: X Guide for Authors:
  https://www.sciencedirect.com/journal/energy-conversion-and-management-x/publish/guide-for-authors
- Elsevier declaration of competing interest tool:
  https://www.elsevier.com/declaration-of-competing-interests

This packet collects the author-only fields and upload decisions that must be
resolved before live submission. It does not invent real author metadata,
funding, conflicts, repository links, reviewer names, or journal portal choices.

## Route Lock

| Field | Current value | Author action |
|---|---|---|
| Target journal | Energy Conversion and Management: X | Confirm in the live submission portal |
| Article type | Original research paper | Confirm against the live Guide for Authors |
| Review model | Single anonymized | Do not anonymize unless the portal offers/requests another route |
| Main boundary statement | VoltGuard is a calibrated screening layer, not an AC feasibility certificate or OPF/MPC replacement | Keep this wording in cover letter and manuscript |
| First fallback | Energy and AI | Use only if reframing toward trustworthy AI/calibrated uncertainty |
| Stretch route | Advances in Applied Energy / Applied Energy | Use only after stronger external feeder and OPF/MPC validation |

## Required Author Metadata

Fill these fields before upload:

| Field | Required value |
|---|---|
| Full author list in final order | Siqiang Zhao; Fengxiang Zhang |
| Affiliation for each author | Siqiang Zhao: Sichuan University-Pittsburgh Institute, Chengdu, China; Fengxiang Zhang: Southwest Jiaotong University, Chengdu, China |
| ORCID for each author | [ORCID IDs, if available] |
| Corresponding author | Siqiang Zhao |
| Corresponding email | 2023141520257@stu.scu.edu.cn |
| Corresponding postal address | [address] |
| Author contribution roles | [CRediT roles per author] |
| Acknowledgements | [real acknowledgements or delete section] |
| Funding statement | [true grant statement or true no-funding statement] |
| Conflict of interest | [true no-conflict declaration or specific disclosure] |
| Prior publication/preprint status | [none / preprint URL / workshop relation] |
| Data/code repository | [GitHub, Zenodo, institutional archive, or release plan URL] |

## Files Prepared Locally

| Upload component | Local file |
|---|---|
| Main editable manuscript | `submission_manuscript_ecmx.md` |
| LaTeX conversion aid | `submission_manuscript_ecmx.tex` |
| PDF smoke test | `submission_build/submission_manuscript_ecmx.pdf` |
| Highlights | `ecmx_highlights.txt` |
| Cover letter | `ecmx_cover_letter.md` |
| Ancillary declarations draft | `submission_ancillaries.md` |
| Figure production plan | `figure_descriptions.md` |
| Reproducibility manifest | `experiments/results/reproducibility_manifest.json` |
| Validation summary | `experiments/results/project_validation_summary.json` |

## ECM:X Portal Text

### Title

VoltGuard: Physics-Informed Topology-Aware Residual Learning with Conformal
Calibration for Renewable-Hosting Voltage-Risk Screening in Active Distribution
Networks

### Short Running Title

VoltGuard for Voltage-Risk Screening

### Suggested Keywords

Physics-informed machine learning; conformal prediction; topology-aware
learning; active distribution networks; voltage security; risk screening;
renewable hosting; energy management; DER operation

### Highlights

Use `ecmx_highlights.txt`. The current file has five highlights and each line
is at or below the ECM:X 85-character limit.

### Data and Code Availability

Draft statement:

The experiments use publicly available IEEE test systems implemented through
pandapower and a project-local IEEE 69-bus feeder implementation. The local
reproducibility package includes the scenario generator, configured evaluation
pipeline, conformal calibration code, raw predictions, conformal scores,
runtime tables, post-action AC audit outputs, and energy-management value
metrics. File-level checksums and reproduction commands are recorded in
`experiments/results/reproducibility_manifest.json` and
`experiments/results/reproducibility_manifest.md`. The public repository or
archive URL is: [repository or archive URL].

### Generative AI / Tool Use

Draft statement for author adaptation:

During the preparation of this work, the authors used AI-assisted coding and
language tools for drafting support, code scaffolding, consistency checks, and
language refinement. The authors reviewed and edited all generated text and
code, verified the equations and numerical claims, and take full responsibility
for the content of the published article.

Do not use generative AI to create or alter final submitted figures unless the
live journal policy and author declaration explicitly permit the exact use.

### Competing Interest

The ECM:X guide points authors to the Elsevier declaration of competing
interest tool. Generate the final `.doc` or `.docx` file using the live tool.

Choose one truthfully:

- The authors declare that they have no known competing financial interests or
  personal relationships that could have appeared to influence the work
  reported in this paper.
- The authors declare the following competing interests: [specific disclosure].

### Funding

Choose one truthfully:

- This research did not receive any specific grant from funding agencies in the
  public, commercial, or not-for-profit sectors.
- This work was supported by [funding agency, grant number].

## Figure Decisions

No article figure files have been generated in this package. The manuscript is
therefore not upload-ready until the author either:

1. Produces final figure files from `figure_descriptions.md`, or
2. Confirms that the first submission will use table-only evidence and no
   separate figure uploads.

ECM:X requests a graphical abstract at submission. Prepare one separately if
the live portal still requires or strongly encourages it. The guide specifies a
minimum image size of 531 by 1328 pixels. Use author-approved vector or raster
artwork derived from the executed results; do not submit AI-generated images as
data evidence.

## Final Pre-Upload Checks

- Confirm inserted author names, affiliations, emails, and corresponding-author
  role in the assembled submission manuscript.
- Replace `[repository or archive URL]` in data availability.
- Remove unused choose-one declaration alternatives from `submission_ancillaries.md`.
- Verify reference metadata and DOI completeness.
- Confirm the current APC/license/waiver/institutional agreement in the portal.
- Confirm whether ECM:X requires separate source files, figures, graphical
  abstract, declaration of interest `.doc/.docx`, and highlights as separate
  uploads.
- Re-run `VoltGuard-CPGNN/.venv/bin/python VoltGuard-CPGNN/experiments/validate_project.py`.

## Hard Stop

Do not submit while any bracketed placeholders, choose-one alternatives, or
manual truth statements remain unresolved.
