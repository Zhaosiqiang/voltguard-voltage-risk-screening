# ECM:X Pre-Submission Readiness Checklist

Source checked on 2026-07-02:

- Energy Conversion and Management: X journal page:
  https://www.sciencedirect.com/journal/energy-conversion-and-management-x
- Energy Conversion and Management: X Guide for Authors:
  https://www.sciencedirect.com/journal/energy-conversion-and-management-x/publish/guide-for-authors

## Official-Fit Checks

| Check | Current evidence | Status |
|---|---|---|
| Target journal fit | ECM:X scope includes energy generation, utilization, conversion, storage, transmission, conservation, management, sustainability, renewable resources, operation, performance, maintenance, control, modeling, analysis, and optimization. VoltGuard is framed as renewable-hosting voltage-risk screening for active-distribution energy management. | ready |
| Article type | Guide lists Original research papers and Review articles. VoltGuard is prepared as an original research article. | ready_for_author_confirmation |
| Review model | Guide states single-anonymized peer review. The manuscript is not anonymized because this route does not require double-anonymized submission by default. | ready |
| Main claim boundary | Main text, cover letter, and declarations say VoltGuard is a screening front end, not an AC feasibility certificate or OPF/MPC replacement. | ready |

## Manuscript-File Checks

| Check | Current evidence | Status |
|---|---|---|
| Editable manuscript | `submission_manuscript_ecmx.md` and `submission_manuscript_ecmx.tex` are editable source files; `submission_build/submission_manuscript_ecmx.pdf` is the smoke-test PDF. | ready |
| Abstract length | `manuscript_draft.md` abstract is under the 250-word limit checked by `validate_project.py`. | ready |
| Highlights | `ecmx_highlights.txt` contains five highlights, each at or below 85 characters. | ready |
| Cover letter | `ecmx_cover_letter.md` is a focused cover letter draft and avoids funding details, author declarations, and reviewer suggestions. | ready |
| Keywords | `submission_ancillaries.md` includes energy-management, conformal prediction, active-distribution, and DER-operation keywords. | ready |
| Upload field packet | `ecmx_upload_input_packet.md` consolidates inserted author names, affiliations, emails, portal text, declarations, data/code availability, figure decisions, and hard-stop checks. | ready_for_remaining_author_completion |
| References | `submission_references.md` provides a numbered reference list and `references.bib` provides matching BibTeX entries. Author review for bibliographic accuracy and DOI completion remains recommended before upload. | ready_for_author_review |
| Figures | No article figure files are generated. `figure_descriptions.md` provides panel plans; final author-approved figure files remain manual. | manual_input_required |
| Tables | Manuscript tables are generated from executed results; long Pandoc/TeX table lines cause hbox warnings in the smoke-test PDF. | ready_for_template_cleanup |

## Ethics, Declarations, and Data

| Check | Current evidence | Status |
|---|---|---|
| Submission declaration | Cover letter includes originality and not-under-review language; author confirmation remains manual. | manual_input_required |
| Competing interests | `submission_ancillaries.md` provides choose-one competing-interest templates; final truth statement remains manual. | manual_input_required |
| Funding | `submission_ancillaries.md` provides no-funding and funded templates; final truth statement remains manual. | manual_input_required |
| Generative AI declaration | `submission_ancillaries.md` includes a draft AI/tool-use disclosure for author adaptation to Elsevier policy. | manual_input_required |
| Data/code availability | Data availability draft identifies pandapower IEEE systems, local IEEE 69-bus implementation, raw predictions, conformal scores, result tables, AC audit outputs, and the reproducibility manifest with checksums; repository URL remains manual. | manual_input_required |
| Declaration of interest file | `ecmx_upload_input_packet.md` points to the Elsevier declaration of competing interest tool; final `.doc` or `.docx` remains manual. | manual_input_required |
| APC/license | ECM:X journal page reports open access APC information; waiver, discount, license, and institutional agreement status remain manual. | manual_input_required |

## Upload Package

Ready local files:

- `submission_manuscript_ecmx.md`
- `submission_manuscript_ecmx.tex`
- `submission_build/submission_manuscript_ecmx.pdf`
- `ecmx_highlights.txt`
- `ecmx_cover_letter.md`
- `ecmx_upload_input_packet.md`
- `submission_ancillaries.md`
- `figure_descriptions.md`
- `experiments/results/project_validation_summary.json`
- `experiments/results/reproducibility_manifest.json`
- `experiments/results/reproducibility_manifest.md`

Not yet upload-ready without author input:

- ORCID IDs, corresponding-author postal address, and phone number if required
  by the submission system,
- repository or archive URL,
- final conflict-of-interest, funding, AI-use, data-availability, and
  CRediT statements,
- final figure files and graphical abstract decision,
- live submission-system article type, APC/license, and journal declaration
  confirmations.
