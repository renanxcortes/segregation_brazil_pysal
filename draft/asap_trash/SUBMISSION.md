# ASAP submission package

**Manuscript:** *Multidimensional Racial Residential Segregation across Brazilian
Cities: A Nationwide Assessment with 2022 Census Data*

**Target journal:** Applied Spatial Analysis and Policy (Springer) —
https://link.springer.com/journal/12061

**Article type:** Original / research article. Springer sets no hard word or
figure limit for this journal; this manuscript is ~7,000 words with 8 figures and
6 tables.

**Source of truth:** `manuscript.tex` in this folder. It builds two versions from
one file via the `\ifanon` toggle near the top:
`\anontrue` (default) = blinded for double-blind review; `\anonfalse` = identified
/ camera-ready. The manuscript body diverges from `../draft_v5.tex`: it adds a
"Policy implications" subsection, a policy framing in the abstract/introduction,
and a "Statements and Declarations" section, and it drops the standalone
"Reproducibility" section (folded into Data/Code availability).

---

## 1. What ASAP / Springer requires

Verified from the journal's submission-guidelines page (search-indexed) and
Springer's standard *Instructions for Authors* on 2026-08-30. The live guidelines
page is behind an SSO redirect; **re-check every item on the journal site before
submitting**, especially the double-blind mechanics, which the journal changed
when it moved submission systems.

| Item | ASAP / Springer rule | Status in this package |
|---|---|---|
| Manuscript file | LaTeX accepted. Springer recommends the **Springer Nature `sn-jnl`** template for new submissions. PDF built from `.tex` for review; source + files at revision. | `sn-jnl.cls` + `sn-basic.bst` bundled (from the official Springer Nature template, class v0.1 2019/11/18). `\documentclass[pdflatex,sn-basic]{sn-jnl}`. |
| Reference style | **Springer "Basic" — Harvard name–year.** In-text `(Author Year)`, no comma; two authors `(A and B Year)`; 3+ `(A et al. Year)`. Reference list: `Smaglik, P. (2004). Centre stage in Missouri. Nature, 431(7009), 720–721.` | `sn-basic.bst`, applied automatically by the class. `natbib` `\citet`/`\citep` in the body work unchanged. `references.bib` here diverges from `../references.bib`: proper nouns in titles are brace-protected (the style is sentence-case) and duplicate DOI/URL fields removed. **Check the rendered list against a recent ASAP article.** |
| Abstract | 150–250 words, unstructured, **no citations, no undefined abbreviations**. | ~215 words; no `\cite`; "Massey and Denton", "PySAL", "LOESS" are names, not abbreviations. |
| Keywords | 4–6. | 6: Residential segregation; Race; Brazil; 2022 Census; Spatial demography; Urban policy. |
| Title page / author info | **Double-blind:** author names, affiliations, ORCID, and contribution/competing-interest/funding statements are entered **in the submission system**, not in the manuscript. The uploaded manuscript must carry **no author-identifying information** (body, acknowledgements, file metadata, or self-citations phrased to reveal identity). | `\anontrue` build blanks the author block and the acknowledgements, and replaces the repo URL with an "anonymised archive" statement. See §3. |
| Section headings | Numbered, decimal, up to three levels (1 / 1.1 / 1.1.1). | Already so. |
| Figures | Numbered, cited in order, captions below. Preferred formats **EPS / PDF (vector)** or **TIFF**; raster line-art 1200 dpi, halftone 300 dpi, combination 600 dpi. RGB or greyscale. **Subfigures discouraged — one file per figure.** | 8 figures. The two multi-panel figures were pre-composited to single PNGs (`fig_maps_national_combined.png`, `fig_maps_cities_combined.png`) by `scripts`-adjacent tooling. **All 8 are currently PNG — re-export to vector PDF/EPS at the required dpi before the revision stage** (see §5). |
| Tables | Editable (not images), numbered, captions above, no vertical rules. | 6 tables. `tab1_descriptive.tex` … `tab5_regional.tex` in this folder are `sn-jnl`-adapted copies of `../../outputs/tables/*` (the `\resizebox` wrapper in the originals is incompatible with the `sn-jnl` `table` environment); the "nine indices" table is inline in `manuscript.tex`. booktabs, caption above, no vertical rules. OK. |
| Statements & Declarations | Section after the conclusion: Funding, Competing interests, Ethics approval, Consent, Data availability, Code availability. **The author-contribution statement must NOT appear in the manuscript or any file** (double-anonymous) — it is entered in the submission system and published by the journal alongside the article. | Present as "Statements and Declarations"; the author-contribution statement has been removed from the manuscript and lives in `author_contributions.md` for pasting into the system. |
| Data & code availability | Required statement. | Provided (see §4). |
| ORCID | Required for the corresponding author; entered in the system. | Author to supply. |
| Cover letter | Standard. | Points in §3. |

---

## 2. Files to upload

| # | File | Notes |
|---|---|---|
| 1 | `manuscript.pdf` | Built from `manuscript.tex` with `\anontrue`. Anonymised — no name, affiliation, email, acknowledgements, or identifying metadata. Check PDF document properties (`pdfinfo` / Acrobat) and strip the author field. |
| 2 | `manuscript.tex` + `sn-jnl.cls` + `sn-basic.bst` + `references.bib` + `manuscript.bbl` | Source bundle, usually requested at revision. `\graphicspath` points at `./` and `../../figures/`; tables `\input` from `../../outputs/tables/`. |
| 3–10 | `figure_1` … `figure_8` | One file per figure, **vector PDF or EPS** (or TIFF at required dpi). Order: (1) `fig_distributions`, (2) `fig_correlation`, (3) `fig_measure_clustering`, (4) `fig_rankings`, (5) `fig_regional`, (6) `fig_minorityshare`, (7) `fig_maps_national_combined`, (8) `fig_maps_cities_combined`. Current sources are PNG in `../../figures/` — re-export (see §5). |
| 11 | Tables | Tables 1–5 (`table1_descriptive`, `table_summary_stats`, `table2_correlation`, `table3_rank_correlation`, `table4_regional`) — rendered from `../../outputs/tables/`. |
| 12 | `cover_letter.pdf` | Anonymised (no author identifiers, no suggested-reviewers section). Source: `cover_letter.md`. |
| 12a | `author_contributions.md` | Not uploaded — the statement is pasted into the submission system's "Author contributions" field. |
| 13 | Anonymised code archive | Zip of the `segbr` package + driver scripts + `environment.yml`/`requirements-lock.txt` + `MANIFEST.md` + run order, with author identifiers removed, OR an anonymous repository view link. Referenced by the Code availability statement in the anon build. |

---

## 3. Cover-letter points

- **What the paper delivers.** The first *nationwide* portrait of racial
  residential segregation in Brazil that is at once (a) **multidimensional** — all
  five Massey–Denton dimensions, nine indices, five of them spatially explicit —
  and (b) based on the **2022 Census**, the most recent tract data available.
- **Fit with ASAP's scope.** The paper is an *application* of spatial analysis at
  national scale with an explicit policy dimension: it shows that the dimension of
  segregation a city chooses to measure determines which cities are flagged and
  which policy lever is implied, and it argues for a multidimensional monitoring
  dashboard (Section "Policy implications"). Barros & Feitosa (2018), a close
  methodological antecedent, appeared in a sibling Springer/urban-analytics venue.
- **Advance over the reference nationwide study.** Sousa Filho et al. (2023) is
  dissimilarity-index only and uses 2010 tract data. This paper (i) moves to 2022,
  (ii) adds exposure, concentration, centralization and clustering, (iii) adds
  spatially explicit measures, and (iv) shows the dimensions disagree — the
  exposure ranking of the macro-regions is the reverse of the evenness ranking,
  and "the most segregated city" has no dimension-independent answer
  (Dissimilarity vs Isolation ranking: Kendall τ ≈ −0.26). It confirms and
  extends their South/Southeast evenness finding rather than overturning it.
- **Method transparency.** Fully open, reproducible pipeline (`segbr` package +
  scripts + pinned environment); every figure and table regenerates with one
  command.
- **Scope limit stated up front.** Statistical inference is deliberately out of
  scope and flagged for future work; the paper is a point-estimation description.
- **Not under consideration elsewhere; no prior publication; no competing
  interests.**
- **Suggested reviewers:** [author to provide 3 — name, affiliation, email,
  ORCID; no recent co-authorship or shared institution].
- **Reviewers to exclude (optional):** [author].

---

## 4. Data & code availability statement

> The data are public. The IBGE Censo Demográfico 2022 aggregates by census tract
> ("Agregados por setores censitários — cor ou raça") and the 2022 census-tract
> shapefiles are distributed by the Instituto Brasileiro de Geografia e
> Estatística (IBGE) at https://www.ibge.gov.br. All code used to assemble the
> city universe, compute the nine segregation indices and generate every figure
> and table in this article — the `segbr` Python package, the driver scripts, a
> pinned environment specification, a manifest of the IBGE source files
> (`MANIFEST.md`) and a documented run order — is available at
> `https://github.com/[REPOSITORY-URL]` (for review: anonymised archive attached).
> The analysis reproduces end to end from the committed city-level results table
> with a single command.

The `\anonfalse` build of `manuscript.tex` carries the `REPOSITORY-URL`
placeholder in the Code availability statement — set it (and make the repo public)
together with this paragraph before the camera-ready stage.

---

## 5. Still to do (author to resolve)

1. **Re-check the live submission guidelines** at
   link.springer.com/journal/12061/submission-guidelines — the SSO wall blocked a
   direct read. Confirm: exact reference-style examples, the double-blind
   mechanics under the new submission system, figure dpi, and whether a
   structured abstract or a separate title page is now required.
2. **Figures to vector.** All 8 are PNG. Re-export each retained figure from the
   plotting scripts as vector **PDF or EPS** (line/combination art at the Springer
   dpi spec), one file per figure. Regenerate `fig_maps_national_combined` and
   `fig_maps_cities_combined` as true single-file vector composites rather than
   PNG montages, or split them and let the typesetter arrange the panels.
3. **Anonymisation.** Build with `\anontrue` (default). After producing the PDF,
   strip the author/title/producer fields from the document properties. Verify no
   identifying string survives: `pdftotext manuscript.pdf - | grep -iE
   "cortes|ufrgs|rio grande do sul|porto alegre"` should return only the
   legitimate in-text mentions of Porto Alegre as a study city.
4. **Repository URL + public repo** — set `REPOSITORY-URL` in the `\anonfalse`
   build and in §4; prepare the anonymised code archive for the review stage.
5. **ORCID** — obtain/confirm; enter in the submission system.
6. **Author info, funding, competing interests** — enter in the submission system
   (double-anonymous). **Author contributions:** paste the statement from
   `author_contributions.md` into the system's "Author contributions" field; it is
   not in the manuscript (removed per policy) and the journal publishes it with the
   article. Rewrite it with real initials/roles if authorship changes.
7. **Word count** — confirm the body is within any limit the journal states
   (none published as of this writing).
8. **Reference list spot-check** — compile and compare 3–4 entries (a journal
   article, the Telles book, the two Portuguese-language REBEP articles) against a
   recent ASAP article's reference list; fix any `sn-basic.bst` quirks (e.g.
   page-range dashes, the `deSouza2023` en-dashed page field).
9. **Policy framing** — the "Policy implications" subsection and the abstract's
   closing clause are new in v6; read them against the journal's expectations and
   sharpen with a concrete Brazilian policy instrument if one fits (e.g. Minha
   Casa Minha Vida siting, municipal Planos Diretores, ZEIS).

---

## 6. Package contents (`draft/asap/`)

| File | Purpose |
|---|---|
| `manuscript.tex` | Versioned source of truth. `pdflatex → bibtex → pdflatex ×2`. |
| `sn-jnl.cls`, `sn-basic.bst` | Springer Nature template files, bundled so the package builds offline. Also `sn-article.tex` (the upstream sample) and `sn-jnl-user-manual.pdf` for reference. |
| `references.bib` | Derived from `draft/references.bib` (17 entries) — brace-protected titles, de-duplicated DOI fields. |
| `tab1_descriptive.tex` … `tab5_regional.tex` | `sn-jnl`-adapted copies of `../../outputs/tables/*` (no `\resizebox`). |
| `fig_maps_national_combined.png`, `fig_maps_cities_combined.png` | Single-file composites of the two multi-panel figures (Springer discourages subfigures). Other 6 figures are pulled from `../../figures/`. |
| `cover_letter.md` / `cover_letter.pdf` | Anonymised cover letter. |
| `author_contributions.md` | Author-contribution statement for the submission system (not uploaded, not in the manuscript). |
| `SUBMISSION.md` | This file. |

Build artifacts (`.aux`, `.log`, `.bbl`, `.blg`, `.out`, `.pdf`) are not committed.
