# REBEP submission package

**Manuscript:** *Multidimensional Racial Residential Segregation across Brazilian
Cities: A Nationwide Assessment with 2022 Census Data*

**Target journal:** Revista Brasileira de Estudos de População (REBEP) — SciELO /
ABEP, https://rebep.org.br

**Article type:** Original Article (*Artigo Original*) — cap 8,000 words (excluding
title, abstracts, keywords, references), up to 5 illustrations. The manuscript now
has 5 figures (2 correlation/clustering figures merged into one two-panel figure;
the regional box-plot figure and the six-city tract-level map figure were cut,
their content folded into prose/tables) + 5 tables. Body word count is ~4,200
words (well under the 8,000 cap). `manuscript.docx` (built by `build_docx.py`) is
the current submission-ready export.

---

## 1. What REBEP requires (verified 2026-08-28)

Sources:
- https://rebep.org.br/revista/about/submissions ("Diretrizes para Autores" /
  "Condições para submissão")

| Item | REBEP rule |
|---|---|
| Manuscript file format | **Word (.doc/.docx) only.** Double-spaced, Arial or Times New Roman 12 pt. No LaTeX class or template is offered or accepted. ODT/RTF not mentioned. |
| Reference style | **ABNT** (NBR 6023 for the list, NBR 10520 for citations). Author-date-page in text, e.g. `(Mortara, 1982a, p. 427)`; `a/b/c` suffix for same-author-same-year. |
| Abstract | ~200 words, **in Portuguese, English AND Spanish** (faithful translations, not adaptations). Unstructured. |
| Title & keywords | Required in **all three languages**. Up to **5 keywords**, drawn from a standard thesaurus (IBICT, UNESCO, ERIC). |
| Title/abstract/keywords in the file | Must also appear inside the manuscript file itself. |
| Length cap | Original Article: **8,000 words max** (title, abstracts, keywords and references excluded). |
| Illustrations | Original Article: **max 5**. Figures/graphs/maps as **separate editable files** — EPS, WMF or editable PDF, **300 dpi minimum**. Placed in the text at their approximate position as well. |
| Tables | Formatted as **editable objects (Word tables)**, *not* as images. Numbered consecutively. |
| Bilingual/trilingual | **Yes — trilingual** (PT / EN / ES) for title, abstract, keywords. |
| ORCID | **Mandatory** for every author; entered in the submission system. |
| Author data | Full name, e-mail, country, ORCID, complete affiliation, short biography (credentials, where trained, current professional activity) — entered in the system, not the manuscript. |
| Anonymisation / blind review | **Required.** No author identification anywhere in the document, **including file metadata / document properties**. |
| Funding / acknowledgements / author contributions / conflicts | **Not in the manuscript body.** Go in the *Formulário com informações complementares da submissão*. Author contributions use the **CRediT** taxonomy. |
| Extra required documents | *Termo de Originalidade* (originality statement) and *Formulário com informações complementares da submissão*, both as PDF. Ethics-committee documentation if human subjects / LGPD-sensitive data (not applicable here — public aggregate census data). |
| Section numbering | Not specified in the guidelines. |

**Consequence for this package:** `manuscript.tex` is the versioned **source of
truth**. REBEP will not take the `.tex` or its PDF — the author exports the content
to a Word file, applies the REBEP formatting (double spacing, Arial/Times 12 pt),
converts the reference list to ABNT, and strips identifying metadata before upload.

---

## 2. Files to upload

| # | File | Notes |
|---|---|---|
| 1 | `manuscript.docx` | Exported from `manuscript.tex` (compiled with `\anontrue`). Anonymised — no names, affiliation, e-mail, acknowledgements, or identifying metadata. Contains PT + EN + ES title/abstract/keywords (Task 27). Tables pasted as editable Word tables. |
| 2–6 | `figure_1.eps` … `figure_5.eps` | One file per figure, EPS or editable PDF, ≥ 300 dpi. Current sources are PNG in `figures/` — see "still to do". Order: (1) `fig_distributions`, (2) `fig_correlation` (+ `fig_measure_clustering` — decide whether these are one figure or two), (3) `fig_rankings`, (4) `fig_regional`, (5) `fig_map_national_dissim` + `fig_map_national_spatial` (two-panel), plus `fig_minorityshare` and the six `seg_profile_*` city maps — **the manuscript currently has more than 5 figures; must be cut or merged to 5.** |
| 7 | Tables (in the manuscript) | Tables 1–5 (`table1_descriptive`, `table_summary_stats`, `table2_correlation`, `table3_rank_correlation`, `table4_regional`) plus the "nine indices" summary table. Rendered as Word tables, not images. |
| 8 | `cover_letter.pdf` | See §3. |
| 9 | `termo_de_originalidade.pdf` | REBEP form. |
| 10 | `formulario_informacoes_complementares.pdf` | REBEP form — carries funding, CRediT author contributions, acknowledgements, conflict-of-interest. |
| 11 | (identified manuscript) | Keep a `\anonfalse` build for the camera-ready stage; not uploaded at submission. |

`manuscript.tex` builds both the anonymised and the identified version from one
source via the `\newif\ifanon` toggle near the top of the file.

---

## 3. Cover-letter points

- **What the paper delivers:** the first *nationwide* portrait of racial residential
  segregation in Brazil that is simultaneously (a) **multidimensional** — all five
  Massey–Denton dimensions, nine indices, four of them spatially explicit — and
  (b) based on the **2022 Census**, the most recent tract data available.
- **Advance over the reference nationwide study.** Sousa Filho et al. (2023,
  *REBEP* 40, DOI 10.20947/S0102-3098a0247) is *dissimilarity-index only* and uses
  *2010* tract data. This paper (i) moves to 2022, (ii) adds exposure, concentration,
  centralization and clustering, (iii) adds spatially explicit measures, and (iv)
  shows the dimensions disagree — the exposure ranking of the macro-regions is the
  *reverse* of the evenness ranking, and "the most segregated city" has no
  dimension-independent answer (Dissimilarity vs Isolation ranking: Kendall
  τ ≈ −0.26). It confirms and extends their South/Southeast evenness finding rather
  than overturning it.
- **Fit with REBEP's scope.** REBEP publishes population studies with a spatial /
  demographic emphasis and has an established line on Brazilian residential
  segregation — Sousa Filho et al. (2023) and Barros & Feitosa (2024, *REBEP* 41,
  DOI 10.20947/S0102-3098a0262) both appeared there. This manuscript speaks
  directly to that conversation and to the journal's readership.
- **Method transparency.** Fully open, reproducible pipeline (Python `segbr`
  package + scripts + pinned environment); every figure and table regenerates with
  one command.
- **Not under consideration elsewhere; no prior publication; no conflicts of
  interest.**
- **Suggested reviewers:** [TBD by author] — 3 names with affiliation, e-mail,
  ORCID; no recent co-authorship or same-institution conflict.
- **Reviewers to exclude (optional):** [TBD by author].

---

## 4. Data & code availability statement

> The IBGE Censo Demográfico 2022 aggregates by census tract ("Agregados por
> setores censitários — cor ou raça") and the 2022 census-tract shapefiles are
> publicly available from IBGE. All code used to assemble the city universe,
> compute the nine segregation indices and generate every figure and table in this
> article — the `segbr` Python package, the driver scripts, a pinned environment
> specification, a manifest of the IBGE source files (`MANIFEST.md`) and a
> documented run order — is available at
> `[REPOSITORY-URL]`. The analysis reproduces end to end from the committed
> city-level results table with a single command.

(Matches §Reproducibility of the manuscript, which also carries the
`REPOSITORY-URL` placeholder — replace both together.)

---

## 5. Resolved automatically (2026-09-08)

1. **Reference style — DONE.** `manuscript.docx` is generated by `build_docx.py`,
   which runs `pandoc --citeproc` against `references.bib` with the
   `abnt.csl` style (Associação Brasileira de Normas Técnicas CSL, NBR
   6023/NBR 10520). In-text citations render as `SOBRENOME; SOBRENOME (ano)`
   and the reference list as `SOBRENOME, Nome. Título. **Periódico**, v., n.,
   p., mês. ano.`, with surnames capitalised and `et al.` from the fourth
   author on. Spot-check a few entries against a current REBEP article before
   submitting, but no manual reformatting is required.
2. **Illustration count — DONE.** Cut from 8 figure environments to **5**:
   the correlation heatmap and the hierarchical-clustering dendrogram were
   merged into one two-panel figure; the regional box-plot figure was
   dropped (Table 4 already reports the same regional medians numerically);
   the six-city tract-level map grid was dropped (the point it illustrated,
   the centre-periphery gradient, is now attributed to the cited literature
   instead). The two-panel national map figure (Dissimilarity + Spatial
   Dissimilarity) is retained.
3. **Word count — DONE.** ~4,200 words in the body (Introduction through
   Conclusion), well under the 8,000-word cap.
4. **Word file format — DONE.** `build_docx.py` produces `manuscript.docx`
   directly: Times New Roman 12pt and double line spacing are baked into a
   pandoc reference-doc template; all six tables (Table 1 descriptive,
   Table 2 the nine indices, Table 3 summary stats, Table 4 Spearman
   correlation, Table 5 Kendall rank correlation, Table 6 regional medians)
   render as native editable Word tables (not images); figures are embedded
   PNGs.
5. **Anonymisation — DONE for the manuscript body and file metadata.**
   Built with `\anontrue`; `build_docx.py` additionally blanks
   `dc:creator`/`cp:lastModifiedBy` in the docx's `docProps/core.xml` after
   conversion. **Still worth a manual read-through:** the reference list
   necessarily includes Rey, Cortes & Knaap (2021), a prior paper by this
   manuscript's author — a normal, impersonally-phrased citation (never
   "our earlier work"), but a sharp reviewer could notice the shared surname.
   This is a common and generally accepted tension in blind review; flagging
   it here rather than removing a citation the argument needs.
6. **Em-dashes — DONE.** Removed throughout (`draft_v5.tex` and
   `manuscript.tex`), each instance rewritten with the punctuation the
   sentence actually needs (colon, parenthesis, comma, or a split sentence).
6b. **`REPOSITORY-URL` de-anonymisation risk — RESOLVED.** The project's
   real GitHub remote (`github.com/renanxcortes/segregation_brazil_pysal`)
   contains the author's name, so it cannot appear in the blind-review
   copy. Per the author's decision, §Reproducibility now states the
   repository is withheld during peer review and will be made public upon
   acceptance (code shareable with reviewers/editors on request in the
   meantime); the Open Science section of `complementary_info_draft.md`
   was updated to match. No `REPOSITORY-URL` placeholder remains.

7. **Figure files at 300 dpi editable PDF — DONE.** `export_submission_figures.py`
   re-draws the 5 retained illustrations from the same data loader as
   `scripts/figures.py` and writes true vector PDFs (matplotlib's PDF
   backend; only the heatmap/scatter layers are rasterised, at 300 dpi) to
   `draft/rebep/figures_submission/Figure1.pdf` … `Figure5.pdf`. Run
   `"C:/Users/renan/anaconda3/python.exe" draft/rebep/export_submission_figures.py`
   (needs the geopandas/pysal stack — see the project's `python-env` note)
   after any change to the underlying data or plots.
8. **Tables as editable files — DONE.** `export_submission_tables.py`
   recomputes each of the 6 manuscript tables from the same source data
   (not hardcoded) and writes one `.xlsx` per table to
   `draft/rebep/tables_submission/Table1.xlsx` … `Table6.xlsx`, caption in
   row 1. Run with the same Anaconda Python as above.
9. **Termo de Originalidade / Formulário complementar — DRAFTED, not filed.**
   Both are Google Docs templates REBEP hosts at fixed URLs (see below);
   I cannot open/fill a Google Doc directly. `originality_statement_draft.md`
   and `complementary_info_draft.md` in this folder have ready-to-paste text
   for every section. Funding and acknowledgements are still blank pending
   confirmation. The IntechOpen book-chapter question (§3 practical note in
   the parent journal-options review) is resolved: confirmed with the
   author (2026-09-08) that the chapter draft (`draft/draft_v4.tex`) was
   abandoned and never submitted or published, so no conflict with the
   originality declaration.
   - Termo de Originalidade: https://docs.google.com/document/d/14E-Y8_d9oX__uXGDaNeUQR6eqyCEo1wS/edit
   - Formulário complementar: https://docs.google.com/document/d/14Ae33zWhpB3kKFnBYR67zPvlbcb0TNXc/edit

## 6. Still to do (author to resolve — cannot be automated from here)

1. **Trilingual front matter proof-read.** The Portuguese and Spanish
   title/abstract/keywords were produced by translation (Task 27) and were
   only lightly touched here (em-dash removal). They still need a native PT
   and a native ES speaker's proof-read before submission, and the keywords
   should be checked against a controlled thesaurus (IBICT/UNESCO/ERIC).
2. **ORCID, affiliation, biography** for every author — entered directly in
   the REBEP submission system, not in the manuscript file; needs personal
   data only the author has.
3. **Funding and acknowledgements** — blank in `complementary_info_draft.md`;
   fill in before pasting into the REBEP form.
4. **Ethics** — public aggregate census data, no human subjects; state "not
   applicable" where the system asks (already drafted that way in
   `complementary_info_draft.md`), unless the editor requests otherwise.
5. **Section numbering** — not specified by REBEP; the current numbered
   scheme is fine but confirm against a recent REBEP article's layout.
6. **After acceptance:** replace the "withheld during peer review" wording
   in §Reproducibility (manuscript) and §6 (complementary form) with the
   real repository URL, and make the repo public at that point.

---

## 7. Package contents (`draft/rebep/`)

| File | Purpose |
|---|---|
| `manuscript.tex` | Versioned source of truth. Compiles from `draft/rebep/` (`pdflatex → bibtex → pdflatex × 2`). `\graphicspath` points at `../../figures/`; tables `\input` from `../../outputs/tables/`. 22 pages at double spacing. The manuscript body mirrors `../draft_v5.tex` verbatim (both are em-dash-free); any edit must be made in both files. |
| `build_docx.py` | Generates `manuscript.docx` (gitignored, rebuilt from source): inlines the `\input` tables, runs `pandoc --citeproc` with `abnt.csl` for ABNT-formatted citations and references, applies Times New Roman 12pt / double spacing via a patched reference-doc template, and strips identifying docx metadata. Run `python build_docx.py` from `draft/rebep/` after any edit to `manuscript.tex`. **This is the file to upload to REBEP.** |
| `abnt.csl` | ABNT NBR 6023/10520 citation style (Citation Style Language), from the CSL styles repository. Used by `build_docx.py`. |
| `references.bib` | Copy of `draft/references.bib` (17 entries) — kept local so the package is self-contained. |
| `export_submission_figures.py` | Writes the 5 illustrations as separate 300dpi vector PDFs to `figures_submission/` (gitignored). Needs the Anaconda geopandas/pysal Python (`C:/Users/renan/anaconda3/python.exe`). |
| `export_submission_tables.py` | Writes the 6 tables as separate editable `.xlsx` files to `tables_submission/` (gitignored). Same Python as above. |
| `originality_statement_draft.md` | Ready-to-paste text for REBEP's *Termo de Originalidade* Google Doc template. |
| `complementary_info_draft.md` | Ready-to-paste text for REBEP's *Formulário com informações complementares* (CRediT, acknowledgements, funding, conflicts, ethics, open science). Funding/acknowledgements blank pending confirmation. |
| `SUBMISSION.md` | This file. |

Build artifacts (`.aux`, `.log`, `.bbl`, `.blg`, `.pdf`, `.out`, `.docx`,
`_reference.docx`, `figures_submission/`, `tables_submission/`) are not
committed; regenerate with `pdflatex`/`bibtex`, `python build_docx.py`,
`export_submission_figures.py` or `export_submission_tables.py`.
