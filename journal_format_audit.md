# Journal Format Audit

Checked on 2026-07-02 against official journal and publisher pages.

## Energy Conversion and Management: X

Official source: https://www.sciencedirect.com/journal/energy-conversion-and-management-x/publish/guide-for-authors

Implemented format:

- Editable LaTeX source uses `elsarticle` with `preprint,12pt`.
- Title page includes article title, author names, affiliations, corresponding-author role, and email.
- Abstract is unnumbered and does not exceed 250 words.
- Keywords are limited to seven items.
- Highlights are written to a separate editable file, `ecmx_highlights.txt`, with 3--5 bullets and each bullet within 85 characters.
- Graphical abstract and figure files are not generated; figure and graphical-abstract descriptions are retained at the manuscript end.
- Math remains editable text.
- Declaration of competing interest, funding, data availability, and AI/tool-use disclosure are included after the main text.

## Energy Conversion and Management

Official source: https://www.sciencedirect.com/journal/energy-conversion-and-management/publish/guide-for-authors

Implemented format:

- Editable LaTeX source uses `elsarticle` with `preprint,12pt`.
- Title page includes article title, author names, affiliations, corresponding-author role, and email.
- Abstract is unnumbered and does not exceed 250 words.
- Keywords are limited to seven items.
- Highlights are written to a separate editable file, `ecm_highlights.txt`, with 3--5 bullets and each bullet within 85 characters.
- Graphical abstract and figure files are not generated; figure and graphical-abstract descriptions are retained at the manuscript end.
- Math remains editable text.
- Declaration of competing interest, funding, data availability, and AI/tool-use disclosure are included after the main text.

## IEEE Open Access Journal of Power and Energy

Official sources:

- https://ieee-pes.org/publications/authors-kit/preparation-and-submission-of-papers-for-the-ieee-open-access-journal-of-power-and-energy/
- https://ieee-pes.org/publications/authors-kit/preparation-of-a-formatted-technical-work/

Implemented format:

- Editable LaTeX source uses `IEEEtran` with the `journal` option.
- The IEEE template controls the double-column journal layout; no custom geometry override is inserted.
- Abstract is unnumbered, one paragraph, self-contained, and within the 150--200 word target.
- Keywords are formatted as `Index Terms`.
- Main sections are promoted to LaTeX `\section` level so IEEEtran supplies Roman-numeral section numbering.
- References use numbered citation style.
- Graphical abstract and figure files are not generated; figure and graphical-abstract descriptions are retained at the manuscript end.

