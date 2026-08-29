# REBEP submission package

**Manuscript:** *Multidimensional Racial Residential Segregation across Brazilian
Cities: A Nationwide Assessment with 2022 Census Data*

**Target journal:** Revista Brasileira de Estudos de População (REBEP) — SciELO /
ABEP, https://rebep.org.br

**Article type:** Original Article (*Artigo Original*) — cap 8,000 words (excluding
title, abstracts, keywords, references), up to 5 illustrations. This manuscript has
5 figures + 5 tables; see "still to do" about the illustration count.

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
> specification and a manifest of the IBGE source files — is available at
> `[REPOSITORY-URL]`. The analysis reproduces end to end from the committed
> city-level results table with a single command.

(Matches §Reproducibility of the manuscript, which also carries the
`REPOSITORY-URL` placeholder — replace both together.)

---

## 5. Still to do (blocking items flagged, author to resolve)

**Could not fully verify from the guidelines page / needs confirmation:**

1. **Reference style — CONFIRM AND CONVERT.** `manuscript.tex` still uses
   `\bibliographystyle{plainnat}` with `natbib[round]`, which gives author-date
   `(Author, year)` citations — the closest available in this TinyTeX install.
   REBEP requires **ABNT NBR 6023 / NBR 10520**. `abntex2-alf.bst` is **not
   installed** in TinyTeX and was not added. On export to Word the entire reference
   list and all in-text citations must be reformatted to ABNT (add page numbers to
   direct quotations; ABNT uppercases author surnames in the list; `et al.` rules
   differ). Consider running the `.bib` through Zotero/Mendeley with an ABNT (ABNT
   NBR 6023:2018) CSL style for the Word version.
2. **Illustration count.** REBEP caps an Original Article at **5 illustrations**.
   The manuscript currently has ~8 figure environments (distributions, correlation,
   measure-clustering, rankings, regional, minority-share, national maps two-panel,
   six-city profile grid). Merge or drop to reach 5, or submit as a **Debate**
   piece (also 8,000 words, 5 illustrations — same cap) — either way the figure set
   must be cut. Decide which figures are essential.
3. **Figure files at 300 dpi in EPS / editable PDF.** Sources in `figures/` are
   PNG. Re-export each retained figure from the plotting scripts as EPS or
   vector PDF at ≥ 300 dpi, one file per figure.
4. **Word-count check.** Confirm the body is ≤ 8,000 words (excl. title, the three
   abstracts, keywords, references) after the Portuguese/Spanish additions.
5. **Trilingual front matter (Task 27).** Portuguese and Spanish title, ~200-word
   abstract and ≤ 5 keywords. Commented stubs are in `manuscript.tex`. Keywords
   should come from a controlled thesaurus (IBICT / UNESCO / ERIC).
6. **ORCID** for every author — obtain / confirm and enter in the submission
   system.
7. **Author affiliation, biography, funding, acknowledgements, CRediT author
   contributions, conflict-of-interest** — none belong in the manuscript body for
   REBEP; compile them into the *Formulário com informações complementares*.
8. **Anonymisation.** Build with `\anontrue` (default in the file). After exporting
   to Word, also strip identifying data from **document properties / metadata**.
   Check the repository URL and any acknowledgement wording do not de-anonymise.
9. **`REPOSITORY-URL` placeholder** — appears in the manuscript (§Reproducibility)
   and in §4 above; set to the public repo before submission and make the repo
   public (or provide an anonymous view link for review).
10. **REBEP forms** — download and complete the current *Termo de Originalidade*
    and *Formulário com informações complementares da submissão* (PDF).
11. **Ethics** — public aggregate census data, no human subjects; state "not
    applicable" where the system asks, unless the editor requests otherwise.
12. **Section numbering** — not specified by REBEP; the current numbered scheme is
    fine but confirm against a recent REBEP article's layout.

---

## 6. Package contents (`draft/rebep/`)

| File | Purpose |
|---|---|
| `manuscript.tex` | Versioned source of truth. Compiles from `draft/rebep/` (`pdflatex → bibtex → pdflatex × 2`). `\graphicspath` points at `../../figures/`; tables `\input` from `../../outputs/tables/`. 19 pp. at one-and-a-half spacing. |
| `references.bib` | Copy of `draft/references.bib` (17 entries) — kept local so the package is self-contained. Do not diverge from the original except for ABNT formatting done in Word. |
| `SUBMISSION.md` | This file. |

Build artifacts (`.aux`, `.log`, `.bbl`, `.blg`, `.pdf`, `.out`) are not committed.
