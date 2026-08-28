# Coverage note -- nationwide segregation profiles, 2022

Source: `outputs/segregation_profiles_2022.parquet`, produced by
`scripts/run_nationwide.py` over the city universe in
`outputs/city_universe_2022.csv` (every Brazilian municipality with a 2022
resident population of at least 100,000). Group studied: `preta + parda`
(`pp_total`) as a share of total colour/race respondents (`pop_total`); `ppp`
is that share per city.

## Coverage

- **319 cities profiled** -- one row per municipality, `COD_MUNICIPIO` unique.
- **0 cities excluded.** Every city returned a complete profile; `fatal_error`
  is empty for all 319 rows. Because `run_all` writes `failures_2022.csv` only
  when at least one fatal error occurs, **no failures file was produced**, and
  its absence is expected, not an error.
- **0 nulls in every one of the nine measure columns** (`Dissim`,
  `SpatialDissim`, `Gini`, `Entropy`, `Isolation`, `DistanceDecayIsolation`,
  `RelativeConcentration`, `RelativeCentralization`, `RelativeClustering`).
  This is the hard coverage guarantee: all 319 x 9 = 2,871 measure values are
  present.
- **No (city, measure) pair was time-skipped.** The run used no time budget, so
  no `*_error` / "skipped: time budget" columns exist in the output.
- Non-fatal rate: **100%** (well above the 97% target).
- Total wall-clock compute across all cities: ~309 s (dominated by
  Sao Paulo's `SpatialDissim`, ~208 s).

## Tract counts

Three distinct tract counts exist for these 319 cities and should not be
conflated:

| Count | Meaning | National total (319 cities) |
|---|---|---:|
| Raw shapefile tracts | Geometry rows in `shapefiles_2022/<UF>_setores_CD2022` for the municipality | **238,449** |
| Census-CSV tracts (`city_universe_2022.csv` `n_tracts`) | `CD_SETOR` row count per municipality in the 2022 colour/race aggregation CSV -- i.e. `municipality_universe`'s `.agg(n_tracts=("CD_SETOR", "size"))`; **not** a shapefile count | **234,148** |
| Analyzed tracts (parquet `n_tracts`) | Tracts actually fed to the estimators | **231,305** |

**Drop mechanism.** `build_city_gdf` starts from the shapefile geometries,
left-merges the census race counts onto them, fills unmatched tracts with 0,
and keeps only tracts with `pop_total > 0`. A shapefile tract is therefore
excluded when it is **either** a genuine zero-population tract **or** absent
from the census file (no race row -> filled with 0 -> dropped). Census rows
with no matching geometry never enter the analysis at all.

- **Raw shapefile -> analyzed: 238,449 -> 231,305, a drop of 7,144 tracts
  (about 3.0%)** nationwide. Of the raw total, 234,148 have a census row
  (the 4,301 gap is overwhelmingly shapefile tracts missing from the census
  file), and of those 2,843 are then dropped for zero population.
- Example: **Sao Paulo -- 27,301 raw shapefile tracts vs 26,679 analyzed**
  (622 dropped, 2.3%; its census-CSV count is 26,889).

## Reference check

Porto Alegre (`COD_MUNICIPIO = 4314902`, 2,695 tracts, `ppp` = 0.260):
`Dissim` = 0.369, `Gini` = 0.489 -- matches the values established in the
single-city pipeline work.

## Data-quality glance

All values were inspected against the expected range of each index. Nothing was
altered; the notes below are documentation only.

### Bounded evenness / exposure measures -- all in range

`Dissim`, `SpatialDissim`, `Gini`, `Entropy`, `Isolation` and
`DistanceDecayIsolation` are bounded to `[0, 1]` by construction. Across all 319
cities every value falls inside `[0, 1]` (observed spans: `Dissim`
0.081-0.458, `SpatialDissim` 0.024-0.343, `Gini` 0.115-0.562, `Entropy`
0.007-0.211, `Isolation` 0.166-0.891, `DistanceDecayIsolation` 0.154-0.939).
No out-of-range values.

### RelativeClustering -- one city slightly above 1

`RelativeClustering` can legitimately exceed 1 by a small margin. Exactly one
city does: **Balneario Camboriu, SC (`COD_MUNICIPIO = 4202008`, 285 analyzed
tracts, `ppp` = 0.206), `RelativeClustering` = 1.0121**. This is within normal
tolerance for the index and is not treated as an error. All other 318 cities
are at or below 1 (range otherwise -0.387 to 0.815).

### RelativeCentralization -- in range

Range -0.304 to 0.163 across the 319 cities; this index is allowed to be
negative and nothing is anomalous.

### RelativeConcentration -- large negative values in majority-Black cities

`RelativeConcentration` (RCO) is the widest-ranging index: mean -0.163,
spanning **-1.999 to 0.571**. Nine cities sit below -1:

| COD_MUNICIPIO | City | Analyzed tracts | ppp | RelativeConcentration |
|---|---|---:|---:|---:|
| 1600600 | Santana (AP) | 198 | 0.787 | -1.9995 |
| 2910800 | Feira de Santana (BA) | 1,094 | 0.829 | -1.9309 |
| 2105302 | Imperatriz (MA) | 453 | 0.721 | -1.6495 |
| 1302504 | Manacapuru (AM) | 205 | 0.868 | -1.6197 |
| 1506807 | Santarem (PA) | 626 | 0.799 | -1.5700 |
| 1501808 | Breves (PA) | 119 | 0.850 | -1.5430 |
| 1600303 | Macapa (AP) | 751 | 0.761 | -1.4655 |
| 1200401 | Rio Branco (AC) | 662 | 0.748 | -1.2909 |
| 2933307 | Vitoria da Conquista (BA) | 659 | 0.702 | -1.1250 |

**The minimum, RCO = -1.9995, is Santana, Amapa** (`COD_MUNICIPIO = 1600600`).
It has **198 analyzed tracts** (211 raw shapefile tracts; 13 dropped -- 8 absent
from the census file, 5 genuinely zero-population), 107,360 colour/race
respondents, and **`ppp` = 0.787** -- preta + parda make up nearly four-fifths
of the population.

This is **not a near-degenerate small city**: Santana has 198 tracts, Feira de
Santana 1,094. The common thread is that the studied group is the overwhelming
local majority: every one of the nine cities has `ppp` between 0.70 and 0.87,
and across all 319 cities RCO is negatively correlated with `ppp`
(r = -0.45). RelativeConcentration compares the physical area occupied by the
studied group with that occupied by the reference group, normalised by the
extreme-packing bounds. When the studied group is most of the population, the
reference group is a thin remainder scattered across the same (often large,
low-density) tracts, the normalisation denominator collapses, and the index is
driven toward its degenerate floor near -2. The values are a known artefact of
applying a minority-concentration index to a majority group in
territorially large, low-density municipalities (Amazonia, interior Bahia,
Amapa) -- they are numerically correct outputs of the estimator, not corrupt
data, and are left untouched. Downstream analysis should either interpret RCO
for these high-`ppp` cities with this caveat or exclude the concentration
dimension there.
