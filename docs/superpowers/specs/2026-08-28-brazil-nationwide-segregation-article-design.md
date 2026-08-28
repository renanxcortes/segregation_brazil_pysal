# Design Spec — Nationwide Multidimensional Racial Residential Segregation in Brazil (2022 Census)

**Date:** 2026-08-28
**Author:** Renan Xavier Cortes
**Status:** Draft for review
**Supersedes framing of:** `draft/draft_v4.*` (book chapter, inference-focused)

---

## 1. Summary

Convert the existing inference-focused book-chapter draft (`draft_v4`) into a
standalone **journal article** presenting a **nationwide, multidimensional,
point-estimation** portrait of racial residential segregation in Brazil using
**2022 Census** tract data.

The paper measures segregation for **all Brazilian municipalities with total
population > 100,000** (~320 cities), computing **nine indices spanning the five
Massey & Denton (1988) dimensions**, and analyzes how segregation levels,
dimensional structure, and regional patterns vary across the urban system.

**No statistical inference** (Monte Carlo tests, confidence intervals, Bayesian
models, comparative/decomposition tests). Inference is explicitly deferred to
future work.

---

## 2. Contribution

Sousa Filho et al. (2023, REBEP) provide the reference nationwide analysis:
~4,595 cities, **2010** Census, **Dissimilarity index only** (evenness
dimension), urban tracts.

This paper's incremental but defensible contribution:

1. **2022 Census** — first nationwide racial-segregation portrait on the newest data.
2. **All five dimensions** — nine measures (evenness, exposure, concentration,
   centralization, clustering), aspatial and spatial, not just D.
3. **Dimensional structure** — whether the dimensions agree or diverge across the
   Brazilian urban system; whether a single index (D) is an adequate summary.
4. **Reproducible open pipeline** — PySAL `segregation` module, public code + data
   manifest, runnable end-to-end.

Framing sentence (for abstract/intro):
> "Brazilian segregation scholarship has relied overwhelmingly on the
> Dissimilarity index computed on 2010-or-older data. We provide a nationwide,
> multidimensional assessment of racial residential segregation across ~320
> Brazilian cities using 2022 Census tract data and nine indices covering all
> five dimensions of Massey and Denton (1988)."

---

## 3. Relationship to `draft_v4`

| `draft_v4` element | Disposition |
| --- | --- |
| §1 Introduction — Massey dimensions, spatial/aspatial measures | **Keep**, becomes core |
| §1 Introduction — Ransom (1988), Carrington & Troske (1997), Allen et al. (2015) LR test, Lee et al. (2015) Bayesian CAR, Rey et al. (2021) comparative/Shapley, `cortes2020` inference module, JCSO reviewer-2 critique | **Cut or reduce to 1 short paragraph.** Without inference these are not load-bearing. Keep a 2–3 sentence mention of small-unit bias (Cortese 1976; Carrington & Troske 1997; Allen et al. 2015) as a **validity limitation** of D. |
| §2 Related work in Brazil | **Keep**, add explicit gap paragraph vs Sousa Filho (2023) |
| §3.1 Data | **Expand** — nationwide universe |
| §3.2 Segregation measures | **Keep**, minor edits |
| §3.3 Hypothesis Definitions (H0/H1 math, all `align*` blocks) | **Cut entirely** |
| §4.1 Point Estimation | **Keep and expand** into full Results |
| §4.2 Inference results + Figures 2–5 (`grid_plot_*` histograms) | **Cut entirely** |
| §5 Discussion — "Comparative framework detangling with shapley", "Street network based" | Reframe as **Future work** bullets |
| Title | Change (see §9) |
| `7_poa_vs_bh.ipynb`, comparative figures, 2010-vs-2022 figures | **Out of scope** — park for future paper |

---

## 4. Data

- **Source:** IBGE Censo Demográfico 2022 — "Agregados por setores censitários"
  (cor ou raça). File already in repo:
  `Agregados_por_setores_cor_ou_raca_BR_csv/Agregados_por_setores_cor_ou_raca_BR.csv`
  (`;`-separated).
- **Variables:** `V01317` (branca), `V01318` (preta), `V01319` (amarela),
  `V01320` (parda), `V01321` (indígena). `"X"` → 0; NA → 0; cast int32.
- **Group under study:** `pp_total = V01318 + V01320` (preta + parda).
- **Reference population:** `pop_total = V01317 + V01318 + V01319 + V01320 + V01321`.
- **Group ratio:** `ppp = pp_total / pop_total`.
- **Geometries:** IBGE malha de setores censitários 2022, per-UF shapefiles,
  already in repo: `shapefiles_2022/<UF>_setores_CD2022/<UF>_setores_CD2022.shp`
  for all 27 UFs. Join key: tract code (`CD_SETOR`); municipality key: `CD_MUN`.
- **CRS:** reproject to EPSG:3857 for distance-based measures (as current `utils`).

### 4.1 City universe

- **Rule:** municipalities with `pop_total` (summed over tracts, 2022) **> 100,000**.
  Expected ~320 municipalities. Produced by the logic already in
  `8_many_cities_exploration.ipynb` (`municipios_grandes`).
- **All tracts** included (no urban/rural restriction). Note in Methods that
  IBGE 2022 tract population is near-universal urban for cities this size;
  rural-tract sensitivity noted as a limitation.
- **Exclusions:** cities where geometry/data join fails, or where a spatial
  measure cannot be computed (see §6.3) — list them explicitly in an appendix.

### 4.2 Descriptive data table (Table 1)

Per macro-region and overall: number of cities, tract-count range (min/median/max),
population range, `ppp` (minority share) range.

---

## 5. Measures

Nine PySAL `segregation` single-group indices, PySAL defaults, organized by
Massey & Denton dimension:

| Dimension | Aspatial | Spatial |
| --- | --- | --- |
| Evenness | `Dissim`, `Gini`, `Entropy` | `SpatialDissim` |
| Exposure | `Isolation` | `DistanceDecayIsolation` |
| Concentration | — | `RelativeConcentration` |
| Centralization | — | `RelativeCentralization` |
| Clustering | — | `RelativeClustering` |

- Neighborhood definition: **Queen contiguity** (PySAL default) where relevant.
- `group_pop_var='pp_total'`, `total_pop_var='pop_total'`.
- Report the raw `.statistic` for each. **No bias correction** — small-unit
  upward bias of D discussed as a limitation (§8).
- Record PySAL / libpysal / segregation package versions and pin them.

---

## 6. Methods & computation

### 6.1 Pipeline refactor

Current logic lives in `utils.ipynb` (`process_mun`, `calculate_seg`,
`seg_profile_mun`) and is per-city, interactive, notebook-run.

Refactor into an importable module (e.g. `segbr/` package or `segbr_utils.py`):

- `load_census(csv_path) -> DataFrame` — read + clean once, reused across cities.
- `municipality_universe(df, threshold=100_000) -> DataFrame` — the >100k filter.
- `build_city_gdf(uf, cod_mun, census_df, shp_dir) -> GeoDataFrame` — per-city
  merge + clean + reproject (generalizes `process_mun`, reads from
  `shapefiles_2022/`).
- `compute_profile(gdf) -> dict` — the nine measures + metadata (n_tracts,
  pop_total, ppp, wall-time per measure, error flags).
- `run_all(universe_df, ...) -> DataFrame` — loop with checkpointing to
  `outputs/segregation_profiles_2022.parquet`; resumable; per-city try/except
  that records failures rather than aborting.

Keep the existing notebooks; the module is what the paper's results depend on.
One thin notebook (`9_run_nationwide.ipynb` or a `scripts/run_nationwide.py`)
drives `run_all` and the figure generation.

### 6.2 Outputs (committed artifacts)

- `outputs/segregation_profiles_2022.parquet` — one row per city, 9 measures + metadata.
- `outputs/failures_2022.csv` — cities dropped and why.
- `figures/` — regenerated, deterministic, one script per figure.
- `outputs/environment.txt` / pinned `requirements` or `environment.yml`.

### 6.3 Computational risk — O(n²) spatial measures on megacities

`DistanceDecayIsolation` and `RelativeClustering` build dense pairwise tract
distance matrices. São Paulo has ~30k tracts in 2022 → ~30k×30k matrix (~7 GB
float64). This may OOM or take very long for the largest ~10–20 cities.

**Mitigation options (decide during the writing-plan, in this order):**
1. Run as-is on a machine with enough RAM; time-box.
2. Chunked/blocked distance computation if PySAL allows.
3. Distance-banded / sparse weights with a cutoff for the spatial-decay measures.
4. If still infeasible for the largest cities: report those spatial measures as
   missing for N cities, disclose in the appendix, and keep aspatial +
   contiguity-based measures (which are sparse) for all.

Hardware actually used + per-measure timings go in Methods.

### 6.4 Reproducibility

Public repo (this one, cleaned), data manifest with IBGE download URLs and
checksums, pinned environment, `make`-style or documented run order.

---

## 7. Analysis plan / Results section

| § | Question | Artifact |
| --- | --- | --- |
| 5.1 Distribution of segregation | How segregated are Brazilian cities on each dimension? Spread? | Ridgeline or boxplots of each of the 9 measures, faceted / colored by macro-region. Summary table with mean/median/IQR. |
| 5.2 Do the dimensions agree? | Is D an adequate one-number summary? Which measures are redundant vs distinct? | Correlation matrix (Spearman) of the 9 measures across cities + brief PCA / clustering of cities by dimensional profile. |
| 5.3 Rankings | Which cities are most/least segregated, per dimension? Does the ranking depend on the dimension chosen? | Ranked bar charts (top/bottom 15) for D and 2–3 contrasting measures; rank-correlation across measures. |
| 5.4 Regional patterns | Confirm/extend Sousa Filho (2023): is South/Southeast more segregated? On all dimensions or only evenness? | Region-level boxplots + a compact table; short narrative. |
| 5.5 Minority share vs segregation | Does segregation vary systematically with the size of the preto+pardo population? | Scatter (city-level) of each measure vs `ppp`, LOESS, no inferential claims. |
| 5.6 Maps | Spatial texture of the results. | (a) National choropleth: cities colored by D and by one spatial measure (dot or municipality polygon). (b) 4–6 illustrative city composition maps — reuse existing `seg_profile_*` for POA/SP/RJ/BH/Floripa; regenerate consistently. |

All descriptive. Language throughout: "cities in region X show higher median
values", never "significantly higher".

---

## 8. Discussion points

- What multidimensionality reveals that D alone hides (concrete examples from 5.2/5.3).
- Which dimensions are structurally coupled in the Brazilian context and why
  (center-periphery legacy, gated enclaves — tie to Barros & Feitosa 2024,
  França 2022, Telles 2004).
- Regional heterogeneity and its drivers (historical settlement, migration,
  housing policy).
- **Limitations:** (a) small-unit upward bias of D and its spatial analogue —
  cities with many small tracts may show inflated evenness measures; no
  correction applied; (b) MAUP — tract boundaries are administrative and changed
  between 2010 and 2022, so this is not directly comparable to Sousa Filho's
  2010 numbers; (c) cross-sectional 2022 only; (d) `preto+pardo` aggregation
  masks preto/pardo differences; (e) any spatial measures dropped for megacities
  (§6.3); (f) `RelativeConcentration`/`RelativeCentralization` can be negative
  and are sensitive to the CBD/areal definition.
- **Future work:** simulation-based inference (single-value and comparative),
  spatial vs compositional decomposition (Rey et al. 2021), temporal change
  2010→2022, street-network-based measures.

---

## 9. Paper metadata & target journal

- **Working title:** "Multidimensional Racial Residential Segregation across
  Brazilian Cities: A Nationwide Assessment with 2022 Census Data"
  (PT: "Segregação residencial racial multidimensional nas cidades brasileiras:
  uma análise nacional com dados do Censo 2022")
- **Primary target:** **REBEP – Revista Brasileira de Estudos de População**
  - Open access, no APC, Qualis A1, SciELO + Scopus, bilingual (PT/EN/ES accepted).
  - Both inspiration papers (Sousa Filho et al. 2023; Barros & Feitosa 2024) are here.
  - Typical length ~8,000 words / ~40,000 characters — **the `draft_v4` intro
    must be cut substantially** regardless.
  - Author-date references (current `natbib`/`plainnat` setup is compatible).
- **Fallback:** Applied Spatial Analysis and Policy (Springer, English) — spatial
  measures + policy framing; single language.
- **Template adaptation is the LAST step** — after prose + figures are final.
  REBEP provides a submission template; do not restructure to it until content
  is locked.
- Confirm with the IntechOpen book editors that repurposing the analysis as a
  journal article (instead of / in addition to the chapter) is acceptable.

---

## 10. Out of scope (this paper)

- Any statistical inference, uncertainty quantification, hypothesis testing.
- Comparative / decomposition analytics.
- Temporal 2010→2022 comparison.
- Income / economic segregation.
- Multi-group segregation indices.
- Street-network-based measures.

---

## 11. Sequencing after spec approval

1. `writing-plans` skill → implementation plan covering:
   a. pipeline refactor (`utils.ipynb` → module) + tests on the 4 known cities
      (reproduce current `draft_v4` numbers as a regression check);
   b. build city universe; acquire/verify all 27 UF geometries;
   c. `run_all` nationwide with checkpointing; resolve §6.3 compute risk;
   d. generate figures + tables (§7);
   e. rewrite prose: Intro (trim), Related Work (+gap para), Methods (no
      inference), Results (new), Discussion (new);
   f. bilingual pass if REBEP;
   g. format to REBEP template (final).
2. Execute plan with review checkpoints.

---

## 12. Open questions

- None blocking. §6.3 (megacity spatial measures) is resolved empirically during
  implementation, with a documented fallback.
