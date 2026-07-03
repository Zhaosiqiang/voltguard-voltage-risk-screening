# OAJPE Upload Input Packet

Source checked on 2026-07-02:

- IEEE Open Access Journal of Power and Energy author information page:
  https://ieee-pes.org/publications/open-access-journal-of-power-and-energy/
- IEEE Author Center generative AI policy page:
  https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/

This packet keeps OAJPE-specific submission checks outside the formal article
manuscript.

## Route Lock

| Field | Current value | Author action |
|---|---|---|
| Target journal | IEEE Open Access Journal of Power and Energy | Confirm in the live submission portal |
| Article type | Short engineering note / regular paper, depending on live portal options | Confirm against the live IEEE PES instructions |
| Manuscript boundary | Baseline LinDistFlow screening heuristic with one empirical quantile | Do not add VoltGuard full-method claims |
| Excluded claims | Graph neural residuals, family-conditioned conformal calibration, topology-shift superiority | Keep these out of the OAJPE note |

## Required Author Metadata

| Field | Current value |
|---|---|
| Full author list in final order | Siqiang Zhao; Fengxiang Zhang |
| Affiliation for each author | Siqiang Zhao: Sichuan University-Pittsburgh Institute, Chengdu, China; Fengxiang Zhang: Southwest Jiaotong University, Chengdu, China |
| Corresponding author | Siqiang Zhao |
| Corresponding email | 2023141520257@stu.scu.edu.cn |

## OAJPE-Specific Checks

The IEEE PES author page for OAJPE reports, for 2026 submissions, an
open-access article processing charge of US$2160 and pricing up to a maximum of
11.5 pages in the final accepted version. The same page states that the
abstract should be 150--200 words and that up to ten keywords are reviewed with
the paper.

Before upload, confirm the live page limit, APC, abstract length, keyword
limit, source-file requirements, figure/table requirements, data/code
availability wording, and AI/tool-use disclosure field in the IEEE submission
portal. IEEE's AI-use policy requires disclosure of AI-generated content in the
article, with the AI system and affected article sections identified; AI must
not be listed as an author.

## Prepared Local Files

| Upload component | Local file |
|---|---|
| Main editable manuscript | `submission_manuscript_oajpe.md` |
| LaTeX conversion aid | `submission_manuscript_oajpe.tex` |
| PDF smoke test | `submission_build/submission_manuscript_oajpe.pdf` |
| Reproducibility manifest | `experiments/results/reproducibility_manifest.json` |
| Validation summary | `experiments/results/project_validation_summary.json` |

