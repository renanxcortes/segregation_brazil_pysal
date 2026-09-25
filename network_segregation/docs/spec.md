# Segregated by design in Brazil? Street-network topology and the measurement of racial segregation — design spec

Date: 2026-09-24 · Status: draft for author review · Not committed (per author instruction)

## 1. Purpose

Draft an English, venue-neutral journal article that adapts Knaap & Rey (2023),
*Segregated by Design? Street Network Topological Structure and the Measurement
of Urban Segregation*, to Brazil using the PySAL `segregation` package. The paper
asks whether measured racial segregation in large Brazilian cities changes when
the "local environment" is defined by walking distance along the street network
instead of straight-line (Euclidean) distance, and which properties of the
street network explain that gap.

Success = a reproducible pipeline that produces all tables/figures for 91
cities, plus a complete LaTeX manuscript draft (all sections written, verified
bibliography) that the author can take to a journal template.

## 2. Constraints (from the author)

- All work lives in a **new, self-contained folder** `network_segregation/`.
  **No pre-existing file in the repository is modified.** Existing data/outputs
  (census CSV, tract shapefiles, `outputs/city_universe_2022.csv`) are **read
  only**.
- **Nothing is committed** to git.
- **No statistical inference on the segregation indices** (no random-labelling
  / permutation tests, no CIs). Knaap & Rey's RQ2 is dropped. The OLS in RQ3
  reports conventional (robust) standard errors; this is the only inferential
  element, and it concerns city-level associations, not the indices.
- Manuscript: English, plain `article` LaTeX + BibTeX, journal-agnostic.
- The PySAL `segregation` software is cited as Cortes, Knaap & Rey (2026),
  JOSS 11(125):11126, doi:10.21105/joss.11126, alongside Cortes et al. (2020)
  and Rey et al. (2021).
- The Brazilian literature review centres on **street-network topology and
  configuration** of Brazilian cities (§9, strand 2.3). IPEA's *Acesso a
  Oportunidades* accessibility work is engaged as a secondary strand.

## 3. Research questions

- **RQ1 (gap).** How different are spatial segregation indices computed with
  Euclidean vs street-network distance in Brazilian cities, in levels and in
  city rankings?
- **RQ2 (topology).** Which street-network topology characteristics are
  associated with the size of that gap?

(Knaap & Rey's inferential RQ is intentionally out of scope; mentioned as
future work.)

## 4. Data and units

| Item | Choice |
|---|---|
| Cities | The 91 municipalities with 2022 population ≥ 300,000 in `outputs/city_universe_2022.csv` (all 27 state capitals are already included). |
| Spatial unit | 2022 census tracts (setores censitários), **urban tracts only**: `SITUACAO == "Urbana"` (`CD_SIT` ∈ {1, 2, 3}), `pop_total > 0`. |
| Population | `Agregados_por_setores_cor_ou_raca_BR.csv`: V01317 branca, V01318 preta, V01319 amarela, V01320 parda, V01321 indígena. |
| Geometry | `shapefiles_2022/<UF>_setores_CD2022/*.shp`, projected to the city's UTM zone (SIRGAS 2000, EPSG 31978–31985) for metric distances. |
| Street network | OpenStreetMap pedestrian network for the union of the city's urban tracts buffered by 2 km (so paths leaving the tract footprint are allowed). **Changed 2026-09-24:** built from one Geofabrik extract of Brazil (replication 2026-09-23T20:22:04Z) clipped per city with `osmium`, keeping ways with OSMnx's exact `walk` filter, instead of Overpass queries (throttled after ~5 cities). Validated on Palmas: identical tract-pair network distances to the Overpass version. Cached as GraphML in `network_segregation/data/osm/` (git-ignored). |

**Why urban tracts only:** Brazilian municipalities include very large rural
tracts (e.g. Porto Velho, ~34,000 km²) whose centroids lie kilometres from the
street network; including them would inflate the network–Euclidean gap for
reasons unrelated to urban design. The restriction and the number of dropped
tracts/people are reported per city.

## 5. Methods

### 5.1 Local environments and weights (Approach A)

For each city, tract centroids (representative points, guaranteed inside the
polygon) are snapped to the nearest network node; the snap distance is
recorded as a diagnostic (cities with a median snap > 250 m are flagged).

Two distance matrices over tract pairs:

- `D_euc`: Euclidean distance between centroids.
- `D_net`: shortest-path walking distance between snapped nodes, plus the
  two snap distances, from `scipy.sparse.csgraph.dijkstra` with
  `limit = bandwidth` (only pairs within the bandwidth are needed).

Both are converted to spatial weights with **the same kernel**, so distance
metric is the only difference (Knaap & Rey, Eq. 8):

`w_ij = 1 − d_ij / b` if `d_ij ≤ b`, else 0; diagonal `w_ii = 1`; `b = 2,000 m`.

Weights are built as `libpysal.weights.W` objects (sparse) and passed as `w=`
to the `segregation` estimators.

### 5.2 Segregation measures

- **Primary:** multigroup spatial information theory index `H` —
  `segregation.multigroup.MultiInfoTheory(data, groups=[5 groups], w=W)`,
  giving `H_euc`, `H_net`, `ΔH = H_net − H_euc`, `%ΔH = ΔH / H_euc`.
- **Secondary (link to the author's nationwide paper):** single-group
  preta+parda vs total, spatialized through the same two `W` via the
  estimators' local-environment `w=` argument: `Dissim`, `Isolation`,
  `Entropy` (singlegroup, segregation 2.5.3). `DistanceDecayIsolation` is
  not used because it takes no `w` (its own decay would confound the
  comparison).
- **Cross-check (not in the main results):** for 3 cities (Porto Alegre,
  Curitiba, Salvador) also compute `H` via `segregation`'s native
  `network=` (pandana) path and report agreement in an appendix. Runs in a
  separate conda env; if pandana cannot be installed on Windows, the
  cross-check is dropped and this is stated in the paper.

### 5.3 Street-network topology metrics (per city, on the walk graph clipped to the urban-tract footprint)

From `osmnx.stats.basic_stats` and `momepy`/direct computation: street
segment count, intersection count, intersection density (per km²), street
density (km per km²), mean street-segment length, mean streets per node,
average circuity, proportion of dead-ends / 3-way / 4-way nodes, self-loop
proportion, cyclomatic number (`e − v + p`), meshedness
(`(e − v + 1)/(2v − 5)`), gamma (`e / 3(v − 2)`).

**Configurational fragmentation (Brazil-specific addition).** Medeiros (2013)
diagnoses Brazilian cities as "patchworks" where local and global
configuration are poorly articulated, operationalized in space syntax as low
*synergy* — the correlation between local (radius-3) and global integration.
We compute a metric analogue on the OSM walk graph (not axial maps, which are
unavailable at this scale):

- *Local reach* `L_i` = street length reachable from node `i` within 800 m
  of network distance.
- *Global closeness* `G_i` = 1 / mean network distance from `i` to a fixed
  random sample of `S = 500` nodes (seeded; exact all-pairs closeness is
  infeasible for São Paulo-scale graphs). Computed on a random sample of
  `N = 2,000` nodes `i` per city (seeded).
- **Synergy** `σ = corr_Pearson(log L_i, G_i)` over the sampled nodes;
  **fragmentation** `F = 1 − σ`.

Hypothesis: higher `F` (patchwork) → larger `ΔH`. `F` enters the RQ2
predictor set; the sample sizes `S`, `N` are checked for stability on 3
cities (F changes < 0.02 when S, N are doubled) and reported. This is
labelled explicitly in the paper as a metric-distance approximation of the
space-syntax synergy measure, not a replication of it. City controls: population,
urban land area, population density, share preta+parda, `H_euc`.

### 5.4 Analyses

RQ1:
1. Descriptive table of `H_euc`, `H_net`, `ΔH`, `%ΔH` (analogue of K&R Table 1).
2. Pearson and Spearman correlation between `H_euc` and `H_net`; number of
   cities where `ΔH < 0`.
3. Rank-change ("slope") chart of the top-15 most segregated cities under
   each metric (analogue of K&R Fig. 2).
4. Map of `%ΔH` across Brazil; 2–3 city vignettes comparing 2-km Euclidean
   buffers vs 2-km network isochrones (analogue of K&R Fig. 1), chosen to
   contrast grid-like vs dendritic/hilly fabrics (e.g. a planned grid such as
   Goiânia or Brasília vs a hillside city such as Rio de Janeiro or Salvador).

RQ2:
5. Correlation clustermap of topology metrics (analogue of K&R Fig. 4).
6. OLS of `ΔH` and of `%ΔH` on a parsimonious predictor set (N = 91, target
   ≤ 8 predictors): intersection density, circuity, meshedness, cyclomatic
   number (logged), dead-end share, fragmentation `F`, population density,
   `H_euc`, plus the K&R cyclomatic × circuity interaction. A K&R-only model
   (without `F`) is reported alongside, so the added value of `F` is visible
   (ΔR², coefficient). Normal-ish regressors z-scored,
   power-law regressors logged; HC3 robust SEs; VIF reported; collinear
   metrics (gamma, k-avg) excluded a priori.

Robustness (reported in an appendix table): bandwidth `b` ∈ {1,000, 3,000 m};
exponential instead of linear decay; secondary single-group indices.

**Population-matched comparison (added 2026-09-24 at the author's request).**
Saporito (2026, *Urban Science* 10(9):506) shows that 2-km network
environments contain fewer people than 2-km Euclidean ones, so part of the
network–Euclidean gap may be a population-size (scale) effect rather than a
barrier effect. For each tract we shrink the Euclidean linear-kernel radius
`b_i ≤ 2,000 m` (bisection) until its kernel-weighted environment population
equals that of its 2-km network environment, recompute `H` (and the secondary
indices) and compare with the main network value (spec label `popmatch`).
This is reported in the main Results as a robustness check on RQ1, not just
in an appendix.

### 5.5 Brazil-specific discussion points (manuscript, not extra analyses)

Informal settlements (favelas) that are under-mapped in OSM (walk paths/
stairways) and their likely effect on `D_net`; steep topography; gated
condominiums (condomínios fechados) as network barriers; the link between
network segregation and accessibility inequalities documented by IPEA.

## 6. Folder layout (all new)

```
network_segregation/
  .gitignore                 # data/osm/, data/cache/, *.aux etc.
  README.md                  # how to reproduce
  environment.yml            # separate conda env: geopandas, libpysal, segregation, osmnx, momepy, statsmodels, scipy, matplotlib, seaborn
  docs/spec.md               # this file
  docs/plan.md               # implementation plan (next step)
  netseg/                    # small package, one purpose per module
    cities.py                # select the 91 cities; load urban tracts + race counts (read-only inputs)
    network.py               # download/cache OSM walk graph; clip; snap centroids
    distances.py             # D_euc and bandwidth-limited D_net
    weights.py               # kernel → libpysal W
    measures.py              # H (and secondary indices) for a given W
    topology.py              # per-city network metrics
    pipeline.py              # per-city orchestration, resumable, per-city error capture
  scripts/
    run_all.py               # loop over cities → outputs/city_results.parquet
    run_robustness.py
    run_crosscheck_pandana.py
    make_figures.py, make_tables.py, fit_models.py
  tests/                     # pytest: toy grids with known distances/weights/H
  outputs/                   # parquet/csv results, figures/, tables/
  manuscript/
    manuscript.tex, references.bib, figures/ (copied from outputs), tables/
```

Existing repo code (`segbr/`) is not imported (to avoid coupling); needed
logic (reading tracts/race counts) is re-implemented in `netseg/cities.py`.

## 7. Error handling and reproducibility

- Per-city failures (OSM download, disconnected graph, snapping) are caught,
  logged to `outputs/failures.csv`, and do not stop the run; runs resume from
  cached per-city results.
- The largest connected component of each walk graph is used, and every tract
  snaps to it; the snap distance is added to the network distance, and tracts
  with snap > 500 m (typically on islands or unmapped areas) are counted and
  reported per city.
- Distances are computed once per city up to the largest bandwidth (3 km) and
  cached; all bandwidth/decay variants are derived from that cache, so the
  main and robustness results come from a single pass.
- OSM download date and `osmnx` version are recorded (OSM is a moving
  target).
- Memory: `D_net` is computed only within the bandwidth and stored sparse, so
  São Paulo (~26k urban tracts) fits in memory.

## 8. Testing

- Unit tests on synthetic inputs: a toy lattice graph where network and
  Euclidean distances are known analytically; kernel weights; that equal
  distance matrices give `H_net == H_euc`; that adding a barrier (removing
  edges) raises `D_net` and weakly raises `H_net` on a segregated toy layout.
- Smoke test on one real small city (e.g. a ~300k municipality) end to end.
- Output checks: 91 rows (or documented failures), no NaN in `H_euc`/`H_net`.

## 9. Manuscript outline

1. Introduction — Euclidean abstraction; Brazilian urban form (favelas,
   hills, condomínios, planned grids); contribution.
2. Background, in four strands, with **Brazilian street-network topology as
   the centrepiece** (strand 2.3):
   - 2.1 Spatial segregation measurement (White 1983; Wong 1993; Reardon &
     O'Sullivan 2004; Reardon et al. 2008; Feitosa et al. 2007).
   - 2.2 Street networks, topology and social interaction, international
     (Grannis 1998, 2005; Roberto 2018; Knaap & Rey 2023; Boeing 2017, 2019,
     2022; Fleischmann 2019).
   - 2.3 **Street-network topology and configuration of Brazilian cities**:
     Medeiros (2013) *Urbis Brasiliae* (27 capitals among 164 world cities;
     Brazilian grids the most fragmented, "patchwork" labyrinths — the key
     motivating fact for this paper); Holanda (2002) on Brasília's
     configuration and segregation; Netto, Pinheiro & Paschoalino (2015)
     segregation as restricted interaction through street networks; Saboya &
     Peres (2025) CHASM, a street-grid-based segregation measure (closest
     methodological neighbour); Gonçalves, Maffini & Maraschin (2024) network
     accessibility index and racial/income segregation in Pelotas; Carvalho &
     Netto (2023) segregation inside favelas; Spadon, Gimenes &
     Rodrigues-Jr (2018) OSM topological features for 645 São Paulo-state
     cities; Coy (2006) condomínios fechados and fragmentation. This strand
     motivates the hypotheses: fragmented, cul-de-sac-rich and gated fabrics
     should widen ΔH; planned grids (Brasília's superquadras aside, Goiânia,
     Belo Horizonte's core) should narrow it.
   - 2.4 Racial segregation in Brazil (Telles; Sousa Filho et al. 2023;
     Marques; França) and, briefly, IPEA network-based accessibility
     inequalities by race (Pereira et al. 2019 TD 2535; Tomasiello et al.
     2024; Bittencourt, Giannotti & Marques 2021) as evidence that network
     position has racialized consequences.
3. Data and methods (§4–5).
4. Results — RQ1 then RQ2.
5. Discussion — Brazilian specifics, OSM completeness, planning implications,
   limitations (no inference; walk network only; tract centroids; MAUP).
6. Conclusion and future work (inferential test of the gap, time-varying
   networks, public-transport networks via r5r).
Appendix — robustness, pandana cross-check, per-city table.

## 10. Verified key references (collected so far)

- Knaap, E., & Rey, S. (2023). Segregated by design? Street network topological structure and the measurement of urban segregation. (Local PDF provided by author.)
- Cortes, R. X., Knaap, E., & Rey, S. J. (2026). segregation: Segregation analysis, inference, and decomposition in Python. *JOSS*, 11(125), 11126. doi:10.21105/joss.11126
- Roberto, E. (2018). The spatial proximity and connectivity method for measuring and analyzing residential segregation. *Sociological Methodology*, 48, 182–224. doi:10.1177/0081175018796871
- Feitosa, F. F., Câmara, G., Monteiro, A. M. V., Koschitzki, T., & Silva, M. P. S. (2007). Global and local spatial indices of urban segregation. *IJGIS*, 21(3), 299–323. doi:10.1080/13658810600911903
- Boeing, G. (2019). Urban spatial order: street network orientation, configuration, and entropy. *Applied Network Science*, 4, 67.
- Boeing, G. (2022). Street network models and indicators for every urban area in the world. *Geographical Analysis*, 54(3), 519–535.
Brazilian street-network topology / configuration (core strand 2.3):

- Medeiros, V. (2013). *Urbis Brasiliae: o labirinto das cidades brasileiras*. Brasília: EdUnB. (From PhD thesis, UnB, 2006.)
- Holanda, F. de (2002). *O espaço de exceção*. Brasília: EdUnB.
- Netto, V. M., Pinheiro, M. S., & Paschoalino, R. (2015). Segregated networks in the city. *IJURR*, 39(6), 1084–1102. doi:10.1111/1468-2427.12346
- Saboya, R. T. de, & Peres, O. M. (2025). CHASM: a configurational measure of socio-spatial residential segregation. *EPB: Urban Analytics and City Science*, 52(6), 1464–1481. doi:10.1177/23998083241287701
- Gonçalves, G. M., Maffini, A. L., & Maraschin, C. (2024). Uncovering income and racial spatial inequalities and segregation patterns with a potential accessibility network index. *urbe*, 16, e20230163. doi:10.1590/2175-3369.016.e20230163
- Carvalho, C., & Netto, V. M. (2023). Segregation within segregation: informal settlements beyond socially homogenous areas. *Cities*, 134, 104152.
- Spadon, G., Gimenes, G., & Rodrigues-Jr, J. F. (2018). Topological street-network characterization through feature-vector and cluster analysis. *ICCS 2018*, LNCS 10860, 274–287.
- Coy, M. (2006). Gated communities and urban fragmentation in Latin America: the Brazilian experience. *GeoJournal*, 66, 121–132. doi:10.1007/s10708-006-9011-6

Racial segregation and accessibility in Brazil (strand 2.4):

- Sousa Filho, J. F. de, et al. (2023). Segregação racial e econômica no Brasil. *REBEP*, 40, 1–24.
- Pereira, R. H. M., Braga, C. K. V., Serra, B., & Nadalin, V. (2019). *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras, 2019*. IPEA, TD 2535.
- Pereira, R. H. M., Braga, C. K. V., Herszenhut, D., Saraiva, M., & Tomasiello, D. B. (2022). *Estimativas de acessibilidade a empregos e serviços públicos … 2017, 2018, 2019*. IPEA, TD 2800.
- Pereira, R. H. M. (2019). Future accessibility impacts of transport policy scenarios. *J. Transport Geography*, 74, 321–332.
- Pereira, R. H. M., Banister, D., Schwanen, T., & Wessel, N. (2019). Distributional effects of transport policies on inequalities in access to opportunities in Rio de Janeiro. *JTLU*, 12(1), 741–764.
- Pereira, R. H. M., Saraiva, M., Herszenhut, D., Braga, C. K. V., & Conway, M. W. (2021). r5r: Rapid realistic routing on multimodal transport networks with R5 in R. *Findings*. doi:10.32866/001c.21262
- Pereira, R. H. M., & Herszenhut, D. (2023). *Introduction to urban accessibility: a practical guide with R*. IPEA.
- Tomasiello, D. B., Vieira, J. P. B., Parga, J. P. F. A., Servo, L. M. S., & Pereira, R. H. M. (2024). Racial and income inequalities in access to healthcare in Brazilian cities. *J. Transport & Health*, 34, 101722.
- Boisjoly, G., Serra, B., Oliveira, G. T., & El-Geneidy, A. (2020). Accessibility measurements in São Paulo, Rio de Janeiro, Curitiba and Recife, Brazil. *J. Transport Geography*, 82, 102551.
- Bittencourt, T. A., Giannotti, M., & Marques, E. (2021). Cumulative (and self-reinforcing) spatial inequalities: interactions between accessibility and segregation in four Brazilian metropolises. *EPB: Urban Analytics and City Science*, 48(7), 1989–2005.

The remaining classics (White 1983; Wong 1993; Reardon & O'Sullivan 2004;
Reardon et al. 2008; Grannis 1998/2005; Boeing 2017 OSMnx; Fleischmann 2019
momepy; Cortes et al. 2020; Rey et al. 2021; Telles 2004) are taken from Knaap &
Rey's reference list and the existing `draft/references.bib` (read-only), and
re-verified when `references.bib` is assembled.

## 11. Out of scope

Permutation/random-labelling inference; 2010 vs 2022 comparison; income
segregation; public-transport or car travel times; metropolitan
(agglomeration) units; modifying any existing repository file.
