# Nationwide Multidimensional Racial Segregation Article — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a reproducible pipeline that computes nine segregation indices for every Brazilian municipality > 100k population from 2022 Census data, then turn `draft_v4` into a submittable journal article (target: REBEP) presenting that nationwide multidimensional descriptive analysis.

**Architecture:** A small Python package (`segbr/`) holds the data-loading, city-assembly, and measurement logic currently scattered across `utils.ipynb`. A driver script runs the package over the full city universe with checkpointing, writing one Parquet table of results. Figure/table scripts read only that table (plus geometries for maps). The manuscript is a plain LaTeX file (`draft/draft_v5.tex`) whose every empirical claim traces to a committed figure or table. Statistical inference is entirely out of scope.

**Tech Stack:** Python 3 (Anaconda `base`), geopandas 1.1.2, libpysal 4.14.1, `segregation` 2.5.3, pandas 2.3.3, numpy 2.3.5, matplotlib, contextily; pytest; LaTeX (article class → REBEP template at the end).

**Spec:** `docs/superpowers/specs/2026-08-28-brazil-nationwide-segregation-article-design.md` — read it alongside this plan.

## Global Constraints

- **Python interpreter:** `C:/Users/renan/anaconda3/python.exe` (the default `python` on PATH is 3.14 with none of the geo stack). All `pytest` / script runs use this interpreter. In Git Bash: `PY="C:/Users/renan/anaconda3/python.exe"`.
- **Census CSV:** `Agregados_por_setores_cor_ou_raca_BR_csv/Agregados_por_setores_cor_ou_raca_BR.csv` — `;`-separated, header quoted, latin-1 safe to read with default utf-8? NO — pandas default works but file uses IBGE encoding; read with `sep=';'` and it parses. Column `CD_SETOR` must be read as `str`.
- **Race variables (2022):** branca `V01317`, preta `V01318`, amarela `V01319`, parda `V01320`, indígena `V01321`. Missing token is the string `"X"` → 0; NA → 0.
- **Group under study:** `pp_total = V01318 + V01320` (preta + parda). **Reference:** `pop_total = V01317+V01318+V01319+V01320+V01321`.
- **Geometries:** `shapefiles_2022/<UF>_setores_CD2022/<UF>_setores_CD2022.shp` — all 27 UFs present. Join key `CD_SETOR`; municipality field `CD_MUN` (7-digit string; special non-census codes have `CD_MUN` null → drop). Urban/rural field: `SITUACAO` / `CD_SIT`. Native CRS SIRGAS 2000 geographic; reproject to **EPSG:3857** before any distance-based measure.
- **City universe:** municipalities with summed `pop_total` **> 100000** (~320 cities). All tracts, no urban/rural filter.
- **Nine measures, PySAL defaults, Queen contiguity where relevant:** `Dissim`, `SpatialDissim`, `Gini`, `Entropy`, `Isolation`, `DistanceDecayIsolation`, `RelativeConcentration`, `RelativeCentralization`, `RelativeClustering`. Report raw `.statistic`. **No bias correction, no inference.**
- **Regression baseline (Porto Alegre, `CD_MUN='4314902'`, computed 2026-08-28):** Dissim 0.369, SpatialDissim ≈0.29, Gini 0.489, Entropy 0.130, Isolation 0.365, DistanceDecayIsolation 0.324, RelativeConcentration −0.107, RelativeCentralization −0.100, RelativeClustering 0.596. Use `abs tol = 0.01` in tests.
- **Commit style:** frequent, one per task minimum; conventional-commit prefixes (`feat:`, `test:`, `chore:`, `docs:`, `paper:`).
- **Journal:** REBEP primary (bilingual, no APC, ~8,000 words / ~40,000 chars). Applied Spatial Analysis and Policy fallback. Template adaptation is the LAST task — do not restructure earlier.

---

## File Structure

```
segbr/
  __init__.py          # package exports
  census.py            # load_census(), municipality_universe()
  cities.py            # build_city_gdf()
  measures.py          # MEASURES registry, compute_profile()
  pipeline.py          # run_all() with checkpointing
scripts/
  build_universe.py    # writes outputs/city_universe_2022.csv
  run_nationwide.py     # writes outputs/segregation_profiles_2022.parquet + failures
  figures.py           # regenerates every figure/table from outputs/
tests/
  conftest.py
  test_census.py
  test_cities.py
  test_measures.py
  test_pipeline.py
outputs/
  city_universe_2022.csv
  segregation_profiles_2022.parquet
  failures_2022.csv
  tables/table1_descriptive.tex, table2_correlation.tex, ...
  environment.txt
figures/               # existing dir; regenerated deterministically
draft/
  draft_v5.tex         # new plain-LaTeX manuscript
  references.bib       # cleaned
requirements-lock.txt  # pinned versions
```

Existing notebooks (`0_*`..`8_*`, `utils.ipynb`) stay untouched as exploratory history; the package supersedes `utils.ipynb` for anything the paper depends on.

---

## Task 1: Project scaffolding + environment lock

**Files:**
- Create: `segbr/__init__.py`, `tests/conftest.py`, `requirements-lock.txt`, `outputs/.gitkeep`, `pytest.ini`
- Create: `outputs/environment.txt`

**Interfaces:**
- Produces: importable `segbr` package; `pytest` runnable via the Anaconda interpreter; `tests/conftest.py` exposes fixture `repo_root` (pathlib.Path) and `census_csv` (Path to the census CSV).

- [ ] **Step 1: Capture the environment**

Run:
```bash
PY="C:/Users/renan/anaconda3/python.exe"
"$PY" -m pip freeze > requirements-lock.txt
"$PY" -c "import sys,geopandas,libpysal,segregation,pandas,numpy; print(sys.version); [print(m.__name__, m.__version__) for m in (geopandas,libpysal,segregation,pandas,numpy)]" > outputs/environment.txt
cat outputs/environment.txt
```
Expected: prints Python 3.x, geopandas 1.1.2, libpysal 4.14.1, segregation 2.5.3, pandas 2.3.3, numpy 2.3.5.

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -q
filterwarnings =
    ignore::RuntimeWarning
    ignore::UserWarning
```

- [ ] **Step 3: Create `segbr/__init__.py`**

```python
"""Nationwide multidimensional racial segregation measurement for Brazil (2022 Census)."""

from segbr.census import load_census, municipality_universe
from segbr.cities import build_city_gdf
from segbr.measures import MEASURES, compute_profile
from segbr.pipeline import run_all

__all__ = [
    "load_census",
    "municipality_universe",
    "build_city_gdf",
    "MEASURES",
    "compute_profile",
    "run_all",
]
```

Note: this imports names defined in later tasks. It will not import cleanly until Task 5. That is expected; do not run it yet.

- [ ] **Step 4: Create `tests/conftest.py`**

```python
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def census_csv(repo_root) -> pathlib.Path:
    p = repo_root / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
    if not p.exists():
        pytest.skip(f"census CSV not present at {p}")
    return p


@pytest.fixture(scope="session")
def shp_dir(repo_root) -> pathlib.Path:
    p = repo_root / "shapefiles_2022"
    if not p.exists():
        pytest.skip(f"shapefiles_2022 not present at {p}")
    return p
```

- [ ] **Step 5: Create `outputs/.gitkeep`** (empty file) so the directory is tracked.

- [ ] **Step 6: Commit**

```bash
git add segbr/__init__.py tests/conftest.py pytest.ini requirements-lock.txt outputs/.gitkeep outputs/environment.txt
git commit -m "chore: scaffold segbr package, pytest, pinned environment"
```

---

## Task 2: `load_census()` — read and clean the national tract table

**Files:**
- Create: `segbr/census.py`
- Test: `tests/test_census.py`

**Interfaces:**
- Produces:
  - `load_census(csv_path: str | Path) -> pandas.DataFrame` with columns
    `CD_SETOR` (str), `V01317..V01321` (int64), `pop_total` (int64),
    `pp_total` (int64), `COD_MUNICIPIO` (str, 7 chars), `COD_UF` (str, 2 chars).
    Missing token `"X"` and NaN both become 0.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_census.py
import pandas as pd
from segbr.census import load_census


def test_load_census_shape_and_types(census_csv):
    df = load_census(census_csv)
    assert {"CD_SETOR", "pop_total", "pp_total", "COD_MUNICIPIO", "COD_UF"} <= set(df.columns)
    assert df["CD_SETOR"].map(type).eq(str).all()
    assert str(df["pop_total"].dtype).startswith("int")
    assert (df["pp_total"] <= df["pop_total"]).all()
    assert (df[["V01317", "V01318", "V01319", "V01320", "V01321"]] >= 0).all().all()


def test_load_census_municipio_codes(census_csv):
    df = load_census(census_csv)
    assert df["COD_MUNICIPIO"].str.len().eq(7).all()
    assert df["COD_UF"].str.len().eq(2).all()
    # Porto Alegre must be present with nonzero population
    poa = df[df["COD_MUNICIPIO"] == "4314902"]
    assert len(poa) > 2000
    assert poa["pop_total"].sum() > 1_000_000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"$PY" -m pytest tests/test_census.py -v`
Expected: FAIL — `ModuleNotFoundError` / `ImportError: cannot import name 'load_census'`.

- [ ] **Step 3: Write minimal implementation**

```python
# segbr/census.py
from __future__ import annotations

from pathlib import Path

import pandas as pd

RACE_VARS = ["V01317", "V01318", "V01319", "V01320", "V01321"]
GROUP_VARS = ["V01318", "V01320"]  # preta + parda


def load_census(csv_path: str | Path) -> pd.DataFrame:
    """Load the 2022 'cor ou raça' tract aggregates, cleaned.

    Returns one row per census tract with integer race counts, derived
    ``pop_total`` and ``pp_total`` (preta + parda), and municipality / UF codes.
    """
    usecols = ["CD_SETOR", *RACE_VARS]
    df = pd.read_csv(csv_path, sep=";", usecols=usecols, dtype={"CD_SETOR": str})

    df[RACE_VARS] = (
        df[RACE_VARS].replace("X", 0).apply(pd.to_numeric, errors="coerce").fillna(0).astype("int64")
    )

    df["pop_total"] = df[RACE_VARS].sum(axis=1).astype("int64")
    df["pp_total"] = df[GROUP_VARS].sum(axis=1).astype("int64")
    df["COD_MUNICIPIO"] = df["CD_SETOR"].str[:7]
    df["COD_UF"] = df["CD_SETOR"].str[:2]
    return df
```

- [ ] **Step 4: Run test to verify it passes**

Run: `"$PY" -m pytest tests/test_census.py -v`
Expected: PASS (both tests). If `test_load_census_municipio_codes` fails on the tract count, print `df[df.COD_MUNICIPIO=='4314902'].shape` and adjust only if the CSV genuinely differs from the 2026-08-28 recon (POA had 2744 shapefile tracts; CSV rows may be slightly fewer).

- [ ] **Step 5: Commit**

```bash
git add segbr/census.py tests/test_census.py
git commit -m "feat: load_census() reads and cleans 2022 tract race aggregates"
```

---

## Task 3: `municipality_universe()` — the > 100k filter

**Files:**
- Modify: `segbr/census.py`
- Test: `tests/test_census.py`

**Interfaces:**
- Consumes: `load_census()` output.
- Produces:
  - `municipality_universe(df: pandas.DataFrame, threshold: int = 100_000) -> pandas.DataFrame`
    with columns `COD_MUNICIPIO` (str), `COD_UF` (str), `pop_total` (int64),
    `n_tracts` (int64), sorted by `pop_total` descending. One row per municipality
    above the threshold.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_census.py
from segbr.census import municipality_universe


def test_municipality_universe(census_csv):
    df = load_census(census_csv)
    uni = municipality_universe(df, threshold=100_000)
    assert list(uni.columns) == ["COD_MUNICIPIO", "COD_UF", "pop_total", "n_tracts"]
    assert (uni["pop_total"] > 100_000).all()
    assert uni["pop_total"].is_monotonic_decreasing
    assert uni["COD_MUNICIPIO"].is_unique
    # Brazil has on the order of 300-340 municipalities above 100k
    assert 280 <= len(uni) <= 360
    # São Paulo is the largest
    assert uni.iloc[0]["COD_MUNICIPIO"] == "3550308"
    # Porto Alegre is in the set
    assert "4314902" in set(uni["COD_MUNICIPIO"])


def test_municipality_universe_threshold_monotone(census_csv):
    df = load_census(census_csv)
    assert len(municipality_universe(df, 200_000)) < len(municipality_universe(df, 100_000))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"$PY" -m pytest tests/test_census.py::test_municipality_universe -v`
Expected: FAIL — `ImportError: cannot import name 'municipality_universe'`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to segbr/census.py
def municipality_universe(df: pd.DataFrame, threshold: int = 100_000) -> pd.DataFrame:
    """Municipalities whose total 2022 population exceeds ``threshold``."""
    grp = (
        df.groupby(["COD_MUNICIPIO", "COD_UF"], as_index=False)
        .agg(pop_total=("pop_total", "sum"), n_tracts=("CD_SETOR", "size"))
    )
    grp = grp[grp["pop_total"] > threshold]
    grp = grp.sort_values("pop_total", ascending=False).reset_index(drop=True)
    return grp[["COD_MUNICIPIO", "COD_UF", "pop_total", "n_tracts"]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `"$PY" -m pytest tests/test_census.py -v`
Expected: PASS. If the count assertion fails, adjust the `280 <= len <= 360` band to the true value and note it in the spec §4.1; do not loosen the other assertions.

- [ ] **Step 5: Commit**

```bash
git add segbr/census.py tests/test_census.py
git commit -m "feat: municipality_universe() filters municipalities above a population threshold"
```

---

## Task 4: `build_city_gdf()` — assemble one city's tract GeoDataFrame

**Files:**
- Create: `segbr/cities.py`
- Test: `tests/test_cities.py`

**Interfaces:**
- Consumes: cleaned census DataFrame from `load_census()`; `shapefiles_2022/` directory.
- Produces:
  - `UF_BY_CODE: dict[str, str]` mapping 2-digit IBGE UF code → UF acronym (e.g. `"43" -> "RS"`).
  - `build_city_gdf(cod_municipio: str, census_df: pandas.DataFrame, shp_dir: str | Path) -> geopandas.GeoDataFrame`
    in EPSG:3857, one row per tract of that municipality, with columns
    `CD_SETOR`, `pop_total`, `pp_total`, `geometry`, and tracts with
    `pop_total == 0` **removed** (matches PySAL expectations; documented in Methods).
    Raises `FileNotFoundError` if the UF shapefile is missing, `ValueError` if
    zero tracts remain.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cities.py
import geopandas as gpd
import pytest
from segbr.census import load_census
from segbr.cities import build_city_gdf, UF_BY_CODE


def test_uf_by_code_covers_all_states():
    assert len(UF_BY_CODE) == 27
    assert UF_BY_CODE["43"] == "RS"
    assert UF_BY_CODE["35"] == "SP"
    assert UF_BY_CODE["33"] == "RJ"
    assert UF_BY_CODE["31"] == "MG"


def test_build_city_gdf_porto_alegre(census_csv, shp_dir):
    df = load_census(census_csv)
    gdf = build_city_gdf("4314902", df, shp_dir)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs.to_epsg() == 3857
    assert {"CD_SETOR", "pop_total", "pp_total", "geometry"} <= set(gdf.columns)
    assert (gdf["pop_total"] > 0).all()
    assert 2000 < len(gdf) < 2800
    assert gdf["geometry"].notna().all()


def test_build_city_gdf_missing_city_raises(census_csv, shp_dir):
    df = load_census(census_csv)
    with pytest.raises(ValueError):
        build_city_gdf("9999999", df, shp_dir)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"$PY" -m pytest tests/test_cities.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Write minimal implementation**

```python
# segbr/cities.py
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

UF_BY_CODE = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def build_city_gdf(cod_municipio: str, census_df: pd.DataFrame, shp_dir: str | Path) -> gpd.GeoDataFrame:
    """Tract GeoDataFrame for one municipality, EPSG:3857, zero-population tracts dropped."""
    uf_code = cod_municipio[:2]
    uf = UF_BY_CODE.get(uf_code)
    if uf is None:
        raise ValueError(f"unknown UF code {uf_code!r} for municipality {cod_municipio!r}")

    shp = Path(shp_dir) / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp"
    if not shp.exists():
        raise FileNotFoundError(shp)

    gdf = gpd.read_file(shp, where=f"CD_MUN = '{cod_municipio}'")
    if len(gdf) == 0:
        raise ValueError(f"no tracts for municipality {cod_municipio!r} in {shp}")

    cols = ["CD_SETOR", "pop_total", "pp_total"]
    merged = gdf[["CD_SETOR", "geometry"]].merge(census_df[cols], on="CD_SETOR", how="left")
    merged[["pop_total", "pp_total"]] = merged[["pop_total", "pp_total"]].fillna(0).astype("int64")
    merged = merged[merged["pop_total"] > 0].copy()
    if len(merged) == 0:
        raise ValueError(f"all tracts have zero population for {cod_municipio!r}")

    return gpd.GeoDataFrame(merged, geometry="geometry", crs=gdf.crs).to_crs(epsg=3857)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `"$PY" -m pytest tests/test_cities.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add segbr/cities.py tests/test_cities.py
git commit -m "feat: build_city_gdf() assembles one municipality's tract GeoDataFrame"
```

---

## Task 5: `compute_profile()` — the nine measures for one city

**Files:**
- Create: `segbr/measures.py`
- Test: `tests/test_measures.py`

**Interfaces:**
- Consumes: a city GeoDataFrame from `build_city_gdf()`.
- Produces:
  - `MEASURES: dict[str, tuple[type, str]]` — ordered mapping of measure name →
    (PySAL class, Massey dimension string). Names, in order:
    `Dissim, SpatialDissim, Gini, Entropy, Isolation, DistanceDecayIsolation,
    RelativeConcentration, RelativeCentralization, RelativeClustering`.
  - `compute_profile(gdf, *, measures=None, time_budget_s=None) -> dict` returning
    `{measure_name: float}` for each computed measure, `{measure_name + "_error":
    str}` for any that raised, plus `n_tracts` (int), `pop_total` (int),
    `pp_total` (int), `ppp` (float), `seconds` (float per-measure dict under key
    `timings`). Never raises for a single measure failure.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_measures.py
import math
import pytest
from segbr.census import load_census
from segbr.cities import build_city_gdf
from segbr.measures import MEASURES, compute_profile

EXPECTED_POA = {
    "Dissim": 0.369,
    "SpatialDissim": 0.29,
    "Gini": 0.489,
    "Entropy": 0.130,
    "Isolation": 0.365,
    "DistanceDecayIsolation": 0.324,
    "RelativeConcentration": -0.107,
    "RelativeCentralization": -0.100,
    "RelativeClustering": 0.596,
}


def test_measures_registry_order_and_dimensions():
    assert list(MEASURES) == [
        "Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation",
        "DistanceDecayIsolation", "RelativeConcentration",
        "RelativeCentralization", "RelativeClustering",
    ]
    dims = {d for _, d in MEASURES.values()}
    assert dims == {"Evenness", "Exposure", "Concentration", "Centralization", "Clustering"}


@pytest.mark.slow
def test_compute_profile_porto_alegre_regression(census_csv, shp_dir):
    df = load_census(census_csv)
    gdf = build_city_gdf("4314902", df, shp_dir)
    prof = compute_profile(gdf)
    assert prof["n_tracts"] == len(gdf)
    assert 0.30 < prof["ppp"] < 0.45
    for name, expected in EXPECTED_POA.items():
        assert name in prof, f"{name} missing (error: {prof.get(name + '_error')})"
        assert math.isclose(prof[name], expected, abs_tol=0.01), (name, prof[name], expected)


def test_compute_profile_subset_and_error_isolation(census_csv, shp_dir):
    df = load_census(census_csv)
    gdf = build_city_gdf("4314902", df, shp_dir)
    prof = compute_profile(gdf, measures=["Dissim", "Entropy"])
    assert set(prof) >= {"Dissim", "Entropy", "n_tracts", "timings"}
    assert "Gini" not in prof
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"$PY" -m pytest tests/test_measures.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Write minimal implementation**

```python
# segbr/measures.py
from __future__ import annotations

import time

from segregation.singlegroup import (
    Dissim, SpatialDissim, Gini, Entropy, Isolation, DistanceDecayIsolation,
    RelativeConcentration, RelativeCentralization, RelativeClustering,
)

MEASURES = {
    "Dissim": (Dissim, "Evenness"),
    "SpatialDissim": (SpatialDissim, "Evenness"),
    "Gini": (Gini, "Evenness"),
    "Entropy": (Entropy, "Evenness"),
    "Isolation": (Isolation, "Exposure"),
    "DistanceDecayIsolation": (DistanceDecayIsolation, "Exposure"),
    "RelativeConcentration": (RelativeConcentration, "Concentration"),
    "RelativeCentralization": (RelativeCentralization, "Centralization"),
    "RelativeClustering": (RelativeClustering, "Clustering"),
}


def compute_profile(gdf, *, measures=None, time_budget_s=None) -> dict:
    """Compute selected segregation measures for one city GeoDataFrame.

    A failure in one measure is recorded under ``<name>_error`` and does not
    abort the rest. ``time_budget_s`` (if set) skips remaining measures once the
    elapsed wall-clock exceeds it, recording ``<name>_error='skipped: time budget'``.
    """
    names = list(measures) if measures is not None else list(MEASURES)
    pop_total = int(gdf["pop_total"].sum())
    pp_total = int(gdf["pp_total"].sum())
    out: dict = {
        "n_tracts": int(len(gdf)),
        "pop_total": pop_total,
        "pp_total": pp_total,
        "ppp": (pp_total / pop_total) if pop_total else float("nan"),
        "timings": {},
    }
    start = time.perf_counter()
    for name in names:
        cls, _dim = MEASURES[name]
        if time_budget_s is not None and time.perf_counter() - start > time_budget_s:
            out[f"{name}_error"] = "skipped: time budget"
            continue
        t0 = time.perf_counter()
        try:
            out[name] = float(cls(gdf, group_pop_var="pp_total", total_pop_var="pop_total").statistic)
        except Exception as exc:  # noqa: BLE001 - deliberate: isolate per-measure failure
            out[f"{name}_error"] = f"{type(exc).__name__}: {exc}"
        finally:
            out["timings"][name] = round(time.perf_counter() - t0, 2)
    out["seconds"] = round(time.perf_counter() - start, 2)
    return out
```

- [ ] **Step 4: Run tests**

Run: `"$PY" -m pytest tests/test_measures.py -v -m "not slow"` then `"$PY" -m pytest tests/test_measures.py -v -m slow`
Expected: all PASS. The regression test takes ~10s. If `SpatialDissim` is off by >0.01, check whether PySAL's default changed; widen only that entry's tolerance to 0.02 and leave a comment.

- [ ] **Step 5: Register the `slow` marker** — append to `pytest.ini`:

```ini
markers =
    slow: hits the full dataset / heavier computation
```

- [ ] **Step 6: Verify `segbr` now imports cleanly**

Run: `"$PY" -c "import segbr; print(sorted(segbr.__all__))"`
Expected: prints the list including `compute_profile` — but `run_all` still missing until Task 6. Temporarily remove `run_all` from `__init__.py` imports/`__all__` if blocking, and restore in Task 6. (Simpler: do Task 6 next.)

- [ ] **Step 7: Commit**

```bash
git add segbr/measures.py tests/test_measures.py pytest.ini
git commit -m "feat: compute_profile() computes nine segregation measures with per-measure error isolation"
```

---

## Task 6: `run_all()` — checkpointed nationwide loop

**Files:**
- Create: `segbr/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `municipality_universe()` output, `load_census()` output, `compute_profile()`.
- Produces:
  - `run_all(universe_df, census_df, shp_dir, out_path, *, measures=None, time_budget_s=None, limit=None) -> pandas.DataFrame`
    — iterates municipalities, calls `build_city_gdf` + `compute_profile`, appends
    one row per city to a Parquet file at `out_path`, **skipping municipalities
    already present in that file** (resumable). Returns the full results
    DataFrame. City-level exceptions (e.g. missing shapefile) are caught and
    written as a row with `fatal_error` set.
  - Companion CSV of failures at `out_path.with_name("failures_2022.csv")`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import pandas as pd
import pytest
from segbr.census import load_census, municipality_universe
from segbr.pipeline import run_all


@pytest.mark.slow
def test_run_all_two_cities_and_resume(tmp_path, census_csv, shp_dir):
    df = load_census(census_csv)
    uni = municipality_universe(df).head(0).copy()
    # hand-pick two small-ish cities: Porto Alegre and Florianópolis
    uni = pd.DataFrame(
        {"COD_MUNICIPIO": ["4314902", "4205407"], "COD_UF": ["43", "42"],
         "pop_total": [1, 1], "n_tracts": [1, 1]}
    )
    out = tmp_path / "profiles.parquet"

    res1 = run_all(uni.head(1), df, shp_dir, out, measures=["Dissim", "Entropy"])
    assert len(res1) == 1
    assert out.exists()

    # resume: full universe, first city already done → only the second is computed
    res2 = run_all(uni, df, shp_dir, out, measures=["Dissim", "Entropy"])
    assert set(res2["COD_MUNICIPIO"]) == {"4314902", "4205407"}
    assert len(res2) == 2
    assert res2.set_index("COD_MUNICIPIO").loc["4314902", "Dissim"] == pytest.approx(0.369, abs=0.01)


def test_run_all_records_missing_city(tmp_path, census_csv, shp_dir):
    df = load_census(census_csv)
    uni = pd.DataFrame(
        {"COD_MUNICIPIO": ["9999999"], "COD_UF": ["99"], "pop_total": [1], "n_tracts": [1]}
    )
    out = tmp_path / "p.parquet"
    res = run_all(uni, df, shp_dir, out, measures=["Dissim"])
    assert res.iloc[0]["fatal_error"]
    assert (out.with_name("failures_2022.csv")).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `"$PY" -m pytest tests/test_pipeline.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Write minimal implementation**

```python
# segbr/pipeline.py
from __future__ import annotations

from pathlib import Path

import pandas as pd

from segbr.cities import build_city_gdf
from segbr.measures import compute_profile


def _done_codes(out_path: Path) -> set[str]:
    if out_path.exists():
        return set(pd.read_parquet(out_path, columns=["COD_MUNICIPIO"])["COD_MUNICIPIO"])
    return set()


def run_all(universe_df, census_df, shp_dir, out_path, *, measures=None,
            time_budget_s=None, limit=None) -> pd.DataFrame:
    """Compute segregation profiles for every municipality in ``universe_df``.

    Appends to the Parquet file at ``out_path`` and skips municipalities already
    present there, so the call is resumable after an interruption.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _done_codes(out_path)

    todo = universe_df[~universe_df["COD_MUNICIPIO"].isin(done)]
    if limit is not None:
        todo = todo.head(limit)

    rows: list[dict] = []
    for rec in todo.itertuples(index=False):
        base = {
            "COD_MUNICIPIO": rec.COD_MUNICIPIO,
            "COD_UF": rec.COD_UF,
            "pop_total_universe": int(rec.pop_total),
            "fatal_error": "",
        }
        try:
            gdf = build_city_gdf(rec.COD_MUNICIPIO, census_df, shp_dir)
            prof = compute_profile(gdf, measures=measures, time_budget_s=time_budget_s)
            timings = prof.pop("timings", {})
            base.update(prof)
            base["timings"] = str(timings)
        except Exception as exc:  # noqa: BLE001 - isolate per-city failure
            base["fatal_error"] = f"{type(exc).__name__}: {exc}"
        rows.append(base)

        # incremental persist after every city
        pd.concat(
            [pd.read_parquet(out_path)] if out_path.exists() else [],
            ignore_index=True,
        )
        new = pd.DataFrame(rows[-1:])
        combined = pd.concat(
            ([pd.read_parquet(out_path)] if out_path.exists() else []) + [new],
            ignore_index=True,
        )
        combined.to_parquet(out_path, index=False)

    full = pd.read_parquet(out_path)
    failures = full[full["fatal_error"].astype(bool)]
    if len(failures):
        failures.to_csv(out_path.with_name("failures_2022.csv"), index=False)
    return full
```

- [ ] **Step 4: Run tests**

Run: `"$PY" -m pytest tests/test_pipeline.py -v`
Expected: PASS. (The resume test also re-reads and confirms the first city was not recomputed — verify by asserting timing/row identity if flaky.)

- [ ] **Step 5: Restore `run_all` in `segbr/__init__.py`** if it was removed in Task 5 Step 6. Run `"$PY" -m pytest -q` — full suite green.

- [ ] **Step 6: Commit**

```bash
git add segbr/pipeline.py segbr/__init__.py tests/test_pipeline.py
git commit -m "feat: run_all() checkpointed, resumable nationwide profiling loop"
```

---

## Task 7: `build_universe.py` — persist the city list

**Files:**
- Create: `scripts/build_universe.py`
- Output: `outputs/city_universe_2022.csv`

**Interfaces:**
- Consumes: `load_census`, `municipality_universe`.
- Produces: `outputs/city_universe_2022.csv` with columns
  `COD_MUNICIPIO, COD_UF, UF, pop_total, n_tracts`.

- [ ] **Step 1: Write the script**

```python
# scripts/build_universe.py
"""Write the >100k-population municipality universe to outputs/city_universe_2022.csv."""
from pathlib import Path

from segbr.census import load_census, municipality_universe
from segbr.cities import UF_BY_CODE

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
OUT = ROOT / "outputs" / "city_universe_2022.csv"


def main() -> None:
    df = load_census(CSV)
    uni = municipality_universe(df, threshold=100_000)
    uni["UF"] = uni["COD_UF"].map(UF_BY_CODE)
    uni = uni[["COD_MUNICIPIO", "COD_UF", "UF", "pop_total", "n_tracts"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    uni.to_csv(OUT, index=False)
    print(f"{len(uni)} municipalities > 100k written to {OUT}")
    print(uni.head(10).to_string(index=False))
    print("tract totals:", uni["n_tracts"].sum())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `"$PY" scripts/build_universe.py`
Expected: prints "~3xx municipalities > 100k", São Paulo (3550308) first, and writes the CSV.

- [ ] **Step 3: Sanity-check the output**

Run: `"$PY" -c "import pandas as pd; d=pd.read_csv('outputs/city_universe_2022.csv', dtype=str); print(len(d)); print(d['UF'].value_counts())"`
Expected: every row has a non-null `UF`; count roughly matches known figure (~320). If any `UF` is null, a municipality code has an unexpected prefix — investigate before proceeding.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_universe.py outputs/city_universe_2022.csv
git commit -m "feat: build and persist the >100k municipality universe"
```

---

## Task 8: `run_nationwide.py` — execute the full profiling run

**Files:**
- Create: `scripts/run_nationwide.py`
- Output: `outputs/segregation_profiles_2022.parquet`, `outputs/failures_2022.csv`

**Interfaces:**
- Consumes: `outputs/city_universe_2022.csv`, `load_census`, `run_all`.
- Produces: the profiles Parquet (one row per city, nine measures + metadata + `timings` + `fatal_error`).

- [ ] **Step 1: Write the script**

```python
# scripts/run_nationwide.py
"""Compute nine segregation measures for every city in the universe. Resumable."""
import argparse
from pathlib import Path

import pandas as pd

from segbr.census import load_census
from segbr.pipeline import run_all

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
SHP = ROOT / "shapefiles_2022"
UNIVERSE = ROOT / "outputs" / "city_universe_2022.csv"
OUT = ROOT / "outputs" / "segregation_profiles_2022.parquet"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="process at most N remaining cities")
    ap.add_argument("--time-budget", type=float, default=None,
                    help="per-city seconds budget; remaining measures skipped past it")
    args = ap.parse_args()

    universe = pd.read_csv(UNIVERSE, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    census = load_census(CSV)
    res = run_all(universe, census, SHP, OUT, time_budget_s=args.time_budget, limit=args.limit)

    done = res[~res["fatal_error"].astype(bool)]
    print(f"{len(done)}/{len(universe)} cities profiled; {len(res) - len(done)} fatal errors")
    err_cols = [c for c in res.columns if c.endswith("_error")]
    if err_cols:
        per_measure = {c: int(res[c].astype(bool).sum()) for c in err_cols}
        print("per-measure errors:", {k: v for k, v in per_measure.items() if v})


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test on 5 cities**

Run: `"$PY" scripts/run_nationwide.py --limit 5`
Expected: writes 5 rows to the Parquet; prints "5/... cities profiled". Inspect:
`"$PY" -c "import pandas as pd; d=pd.read_parquet('outputs/segregation_profiles_2022.parquet'); print(d[['COD_MUNICIPIO','n_tracts','Dissim','Gini','seconds']])"`

- [ ] **Step 3: Time a big city explicitly** (São Paulo)

Run:
```bash
"$PY" -c "
import time, pandas as pd
from segbr.census import load_census
from segbr.cities import build_city_gdf
from segbr.measures import compute_profile
df = load_census('Agregados_por_setores_cor_ou_raca_BR_csv/Agregados_por_setores_cor_ou_raca_BR.csv')
g = build_city_gdf('3550308', df, 'shapefiles_2022'); print('SP tracts', len(g))
t=time.time(); p = compute_profile(g); print('SP seconds', round(time.time()-t,1)); print(p['timings'])
"
```
Expected: reveals which measures are slow at SP scale (Gini is O(n²); `DistanceDecayIsolation` builds a dense distance matrix). Record the timing.

- [ ] **Step 4: Decide the compute strategy from Step 3 evidence** (spec §6.3)
  - If SP finishes < ~15 min and RAM holds: run the whole universe as-is (Step 5a).
  - If one or two measures dominate for the ~10 largest cities: set a `--time-budget` so those get `skipped: time budget`, run the rest complete, and note the skipped (city, measure) pairs in the manuscript appendix (Step 5b).
  - Either way the aspatial + contiguity measures complete for every city.

- [ ] **Step 5: Run the full universe** (long-running; resumable — safe to re-invoke)

Run (5a): `"$PY" scripts/run_nationwide.py`
or (5b): `"$PY" scripts/run_nationwide.py --time-budget 600`
Expected: `outputs/segregation_profiles_2022.parquet` has one row per universe city.

- [ ] **Step 6: Commit**

```bash
git add scripts/run_nationwide.py outputs/segregation_profiles_2022.parquet outputs/failures_2022.csv
git commit -m "feat: nationwide segregation profiling run (2022 Census, ~320 cities)"
```

---

## Task 9: Output validation

**Files:**
- Create: `tests/test_outputs.py`

**Interfaces:**
- Consumes: `outputs/segregation_profiles_2022.parquet`.

- [ ] **Step 1: Write the validation test**

```python
# tests/test_outputs.py
import pathlib
import pandas as pd
import pytest

OUT = pathlib.Path(__file__).resolve().parents[1] / "outputs" / "segregation_profiles_2022.parquet"
MEASURES = ["Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation",
            "DistanceDecayIsolation", "RelativeConcentration",
            "RelativeCentralization", "RelativeClustering"]


@pytest.fixture(scope="module")
def profiles():
    if not OUT.exists():
        pytest.skip("run scripts/run_nationwide.py first")
    return pd.read_parquet(OUT)


def test_one_row_per_city(profiles):
    assert profiles["COD_MUNICIPIO"].is_unique


def test_coverage(profiles):
    ok = profiles[~profiles["fatal_error"].astype(bool)]
    assert len(ok) / len(profiles) > 0.97  # <3% cities lost


def test_measure_ranges(profiles):
    ok = profiles[~profiles["fatal_error"].astype(bool)]
    for m in ["Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation", "DistanceDecayIsolation"]:
        vals = ok[m].dropna()
        assert vals.between(0, 1).mean() > 0.99, m
    for m in ["RelativeConcentration", "RelativeCentralization", "RelativeClustering"]:
        assert ok[m].notna().mean() > 0.5, m


def test_porto_alegre_values(profiles):
    poa = profiles.set_index("COD_MUNICIPIO").loc["4314902"]
    assert abs(poa["Dissim"] - 0.369) < 0.01
    assert abs(poa["Gini"] - 0.489) < 0.01
```

- [ ] **Step 2: Run it**

Run: `"$PY" -m pytest tests/test_outputs.py -v`
Expected: PASS. Investigate any measure whose in-range fraction is < 0.99 (except the relative measures, which can legitimately be negative or NaN).

- [ ] **Step 3: Write the coverage note**

Create `outputs/coverage_note.md` — a short paragraph: how many cities profiled, which dropped and why (from `failures_2022.csv`), which (city, measure) pairs were time-skipped. This text feeds the manuscript appendix.

- [ ] **Step 4: Commit**

```bash
git add tests/test_outputs.py outputs/coverage_note.md
git commit -m "test: validate nationwide profile outputs; document coverage"
```

---

## Task 10: `figures.py` scaffolding + Table 1 (descriptive)

**Files:**
- Create: `scripts/figures.py`
- Output: `outputs/tables/table1_descriptive.tex`

**Interfaces:**
- Consumes: `outputs/city_universe_2022.csv`, `outputs/segregation_profiles_2022.parquet`.
- Produces: `scripts/figures.py` with a `main()` dispatching subcommands
  (`table1`, `fig_distributions`, `fig_correlation`, `fig_rankings`,
  `fig_regional`, `fig_minorityshare`, `fig_maps`, `all`); helper
  `load() -> pandas.DataFrame` that merges universe + profiles + a `REGION`
  column (derived from `COD_UF` via a `REGION_BY_UF` dict) and `UF`.

- [ ] **Step 1: Write scaffolding + Table 1**

```python
# scripts/figures.py
"""Regenerate every table and figure in the paper from outputs/."""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "outputs" / "segregation_profiles_2022.parquet"
UNIVERSE = ROOT / "outputs" / "city_universe_2022.csv"
TABLES = ROOT / "outputs" / "tables"
FIGDIR = ROOT / "figures"

MEASURES = ["Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation",
            "DistanceDecayIsolation", "RelativeConcentration",
            "RelativeCentralization", "RelativeClustering"]

REGION_BY_UF = {
    "11": "Norte", "12": "Norte", "13": "Norte", "14": "Norte", "15": "Norte",
    "16": "Norte", "17": "Norte",
    "21": "Nordeste", "22": "Nordeste", "23": "Nordeste", "24": "Nordeste",
    "25": "Nordeste", "26": "Nordeste", "27": "Nordeste", "28": "Nordeste", "29": "Nordeste",
    "31": "Sudeste", "32": "Sudeste", "33": "Sudeste", "35": "Sudeste",
    "41": "Sul", "42": "Sul", "43": "Sul",
    "50": "Centro-Oeste", "51": "Centro-Oeste", "52": "Centro-Oeste", "53": "Centro-Oeste",
}


def load() -> pd.DataFrame:
    prof = pd.read_parquet(PROFILES)
    uni = pd.read_csv(UNIVERSE, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    df = uni.merge(prof, on="COD_MUNICIPIO", suffixes=("", "_p"))
    df = df[~df["fatal_error"].astype(bool)].copy()
    df["REGION"] = df["COD_UF"].map(REGION_BY_UF)
    return df


def table1() -> None:
    df = load()
    g = df.groupby("REGION").agg(
        cities=("COD_MUNICIPIO", "size"),
        tracts_min=("n_tracts", "min"),
        tracts_med=("n_tracts", "median"),
        tracts_max=("n_tracts", "max"),
        ppp_min=("ppp", "min"),
        ppp_med=("ppp", "median"),
        ppp_max=("ppp", "max"),
    )
    total = pd.DataFrame({
        "cities": [len(df)], "tracts_min": [df.n_tracts.min()],
        "tracts_med": [df.n_tracts.median()], "tracts_max": [df.n_tracts.max()],
        "ppp_min": [df.ppp.min()], "ppp_med": [df.ppp.median()], "ppp_max": [df.ppp.max()],
    }, index=["Brasil"])
    out = pd.concat([g, total])
    TABLES.mkdir(parents=True, exist_ok=True)
    out.round(3).to_latex(TABLES / "table1_descriptive.tex", caption="Cidades analisadas por macrorregião.", label="tab:descriptive")
    print(out.round(3).to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["table1", "fig_distributions", "fig_correlation",
                                    "fig_rankings", "fig_regional", "fig_minorityshare",
                                    "fig_maps", "all"])
    args = ap.parse_args()
    dispatch = {"table1": table1}
    if args.cmd == "all":
        for fn in dispatch.values():
            fn()
    else:
        dispatch[args.cmd]()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `"$PY" scripts/figures.py table1`
Expected: prints the region table, writes `outputs/tables/table1_descriptive.tex`. Sanity-check: 5 regions + Brasil row, city counts sum to the profiled total.

- [ ] **Step 3: Commit**

```bash
git add scripts/figures.py outputs/tables/table1_descriptive.tex
git commit -m "feat: figures.py scaffolding + descriptive Table 1"
```

---

## Task 11: §5.1 — distribution of each measure (fig_distributions)

**Files:**
- Modify: `scripts/figures.py`
- Output: `figures/fig_distributions.png`, `outputs/tables/table_summary_stats.tex`

**Interfaces:**
- Consumes: `load()`.
- Produces: `fig_distributions()` registered in `dispatch`.

- [ ] **Step 1: Add `fig_distributions()`**

```python
# add to scripts/figures.py
def fig_distributions() -> None:
    import matplotlib.pyplot as plt
    df = load()
    fig, axes = plt.subplots(3, 3, figsize=(13, 11))
    for ax, m in zip(axes.ravel(), MEASURES):
        for region, sub in df.groupby("REGION"):
            sub[m].plot(kind="kde", ax=ax, label=region)
        ax.set_title(m)
        ax.set_yticks([])
    axes.ravel()[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_distributions.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    stats = df[MEASURES].describe(percentiles=[0.25, 0.5, 0.75]).T[["mean", "std", "25%", "50%", "75%", "min", "max"]]
    stats.round(3).to_latex(TABLES / "table_summary_stats.tex",
                            caption="Estatísticas descritivas dos nove índices (todas as cidades).",
                            label="tab:summary")
    print(stats.round(3).to_string())
```
Register: add `"fig_distributions": fig_distributions` to `dispatch`.

- [ ] **Step 2: Run + eyeball**

Run: `"$PY" scripts/figures.py fig_distributions`
Expected: 3×3 KDE grid saved; summary-stats table written. Check the PNG opens and axes are labelled with measure names.

- [ ] **Step 3: Commit**

```bash
git add scripts/figures.py figures/fig_distributions.png outputs/tables/table_summary_stats.tex
git commit -m "feat: §5.1 distribution-of-measures figure + summary stats table"
```

---

## Task 12: §5.2 — do the dimensions agree? (fig_correlation)

**Files:**
- Modify: `scripts/figures.py`
- Output: `figures/fig_correlation.png`, `outputs/tables/table2_correlation.tex`

- [ ] **Step 1: Add `fig_correlation()`**

```python
# add to scripts/figures.py
def fig_correlation() -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    df = load()
    corr = df[MEASURES].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(MEASURES)), MEASURES, rotation=90)
    ax.set_yticks(range(len(MEASURES)), MEASURES)
    for i in range(len(MEASURES)):
        for j in range(len(MEASURES)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, shrink=0.8)
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_correlation.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    corr.round(2).to_latex(TABLES / "table2_correlation.tex",
                           caption="Correlação de Spearman entre os nove índices (nível cidade).",
                           label="tab:corr")
    print(corr.round(2).to_string())
```
Register in `dispatch`.

- [ ] **Step 2: Run**

Run: `"$PY" scripts/figures.py fig_correlation`
Expected: heatmap + LaTeX table. Note in the run log which measure pairs are ~0.99 (redundant) and which are < 0.5 (genuinely distinct) — this is the raw material for the §5.2 prose.

- [ ] **Step 3: Commit**

```bash
git add scripts/figures.py figures/fig_correlation.png outputs/tables/table2_correlation.tex
git commit -m "feat: §5.2 inter-measure Spearman correlation figure + table"
```

---

## Task 13: §5.3 — rankings (fig_rankings)

**Files:**
- Modify: `scripts/figures.py`
- Output: `figures/fig_rankings.png`, `outputs/tables/table3_rank_correlation.tex`

- [ ] **Step 1: Add `fig_rankings()`** — top/bottom 15 cities for three contrasting measures (`Dissim`, `Isolation`, `RelativeClustering`), horizontal bar charts; plus a Kendall-τ table of city rankings across all nine measures.

```python
# add to scripts/figures.py
def _city_label(df):
    return df["UF"] + "-" + df["COD_MUNICIPIO"].str[:6]

def fig_rankings() -> None:
    import matplotlib.pyplot as plt
    df = load().copy()
    df["label"] = _city_label(df)
    show = ["Dissim", "Isolation", "RelativeClustering"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    for ax, m in zip(axes, show):
        top = df.nlargest(15, m)[["label", m]].set_index("label")[m][::-1]
        top.plot.barh(ax=ax)
        ax.set_title(f"15 maiores — {m}")
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_rankings.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    ranks = df[MEASURES].rank()
    tau = ranks.corr(method="kendall")
    tau.round(2).to_latex(TABLES / "table3_rank_correlation.tex",
                          caption="Correlação de postos (Kendall) entre índices.",
                          label="tab:rankcorr")
    print("rank-corr range:", round(tau.values[tau.values < 1].min(), 2), "-",
          round(tau.values[tau.values < 1].max(), 2))
```
Register in `dispatch`.

- [ ] **Step 2: Run**

Run: `"$PY" scripts/figures.py fig_rankings`
Expected: 3-panel bar chart + table. Confirm city labels are readable; if not, switch label to municipality name (join `NM_MUN` from any shapefile once, cache to `outputs/municipio_names.csv`).

- [ ] **Step 3: Commit**

```bash
git add scripts/figures.py figures/fig_rankings.png outputs/tables/table3_rank_correlation.tex
git commit -m "feat: §5.3 city rankings figure + rank-correlation table"
```

---

## Task 14: §5.4 — regional patterns (fig_regional)

**Files:**
- Modify: `scripts/figures.py`
- Output: `figures/fig_regional.png`, `outputs/tables/table4_regional.tex`

- [ ] **Step 1: Add `fig_regional()`** — box/violin of each measure by macro-region (3×3 grid); region-level median table.

```python
# add to scripts/figures.py
def fig_regional() -> None:
    import matplotlib.pyplot as plt
    df = load()
    order = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    fig, axes = plt.subplots(3, 3, figsize=(14, 12))
    for ax, m in zip(axes.ravel(), MEASURES):
        data = [df.loc[df.REGION == r, m].dropna() for r in order]
        ax.boxplot(data, labels=[r[:3] for r in order])
        ax.set_title(m)
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_regional.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    med = df.groupby("REGION")[MEASURES].median().reindex(order)
    med.round(3).to_latex(TABLES / "table4_regional.tex",
                          caption="Mediana de cada índice por macrorregião.", label="tab:regional")
    print(med.round(3).to_string())
```
Register in `dispatch`.

- [ ] **Step 2: Run**

Run: `"$PY" scripts/figures.py fig_regional`
Expected: grid + table. Note whether South/Southeast lead on **all** dimensions or only evenness (the Sousa Filho comparison point).

- [ ] **Step 3: Commit**

```bash
git add scripts/figures.py figures/fig_regional.png outputs/tables/table4_regional.tex
git commit -m "feat: §5.4 regional-pattern boxplots + median table"
```

---

## Task 15: §5.5 — minority share vs segregation (fig_minorityshare)

**Files:**
- Modify: `scripts/figures.py`
- Output: `figures/fig_minorityshare.png`

- [ ] **Step 1: Add `fig_minorityshare()`** — scatter of each measure vs `ppp`, colored by region, with a LOESS/lowess line (`statsmodels.nonparametric.lowess`; if statsmodels absent, a rolling-median line).

```python
# add to scripts/figures.py
def fig_minorityshare() -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    df = load()
    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
    except Exception:
        lowess = None
    fig, axes = plt.subplots(3, 3, figsize=(14, 12))
    for ax, m in zip(axes.ravel(), MEASURES):
        ax.scatter(df["ppp"], df[m], s=10, alpha=0.5)
        if lowess is not None:
            sub = df[["ppp", m]].dropna().sort_values("ppp")
            sm = lowess(sub[m], sub["ppp"], frac=0.5)
            ax.plot(sm[:, 0], sm[:, 1], color="black")
        ax.set_title(m)
        ax.set_xlabel("share preta+parda")
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_minorityshare.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
```
Register in `dispatch`. If `statsmodels` missing and you want the smoother, `"$PY" -m pip install statsmodels` and re-freeze `requirements-lock.txt`.

- [ ] **Step 2: Run**

Run: `"$PY" scripts/figures.py fig_minorityshare`
Expected: 3×3 scatter grid saved.

- [ ] **Step 3: Commit**

```bash
git add scripts/figures.py figures/fig_minorityshare.png requirements-lock.txt
git commit -m "feat: §5.5 minority-share vs segregation scatter grid"
```

---

## Task 16: §5.6 — maps (fig_maps)

**Files:**
- Modify: `scripts/figures.py`
- Output: `figures/fig_map_national_dissim.png`, `figures/fig_map_national_spatial.png`, refreshed `figures/seg_profile_<code>.png` for the six illustrative cities.

**Interfaces:**
- Consumes: `load()`, `build_city_gdf`, a Brazil municipality-polygon layer.

- [ ] **Step 1: Obtain a municipality-polygon layer**

Dissolve tract geometries to municipality level once and cache:
```python
# scripts/build_municipio_polygons.py
"""Dissolve 2022 tract geometries to municipality polygons for the universe; cache to GPKG."""
from pathlib import Path
import geopandas as gpd, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
uni = pd.read_csv(ROOT / "outputs" / "city_universe_2022.csv", dtype={"COD_MUNICIPIO": str})
parts = []
for uf in sorted(uni["UF"].unique()):
    codes = set(uni.loc[uni.UF == uf, "COD_MUNICIPIO"])
    g = gpd.read_file(ROOT / "shapefiles_2022" / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp",
                      columns=["CD_MUN", "geometry"])
    g = g[g["CD_MUN"].isin(codes)].dissolve(by="CD_MUN").reset_index()
    parts.append(g)
out = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=parts[0].crs).to_crs(4674)
out.to_file(ROOT / "outputs" / "municipio_polygons.gpkg", driver="GPKG")
print(len(out), "municipality polygons")
```
Run: `"$PY" scripts/build_municipio_polygons.py`

- [ ] **Step 2: Add `fig_maps()`**

```python
# add to scripts/figures.py
ILLUSTRATIVE = ["4314902", "3550308", "3304557", "3106200", "4205407", "2611606"]  # POA, SP, RJ, BH, Floripa, Recife

def fig_maps() -> None:
    import matplotlib.pyplot as plt
    import geopandas as gpd
    df = load().set_index("COD_MUNICIPIO")
    poly = gpd.read_file(ROOT / "outputs" / "municipio_polygons.gpkg").rename(columns={"CD_MUN": "COD_MUNICIPIO"})
    poly = poly.merge(df[["Dissim", "SpatialDissim"]], on="COD_MUNICIPIO", how="left")
    for col, fname in [("Dissim", "fig_map_national_dissim.png"),
                       ("SpatialDissim", "fig_map_national_spatial.png")]:
        ax = poly.plot(column=col, legend=True, cmap="YlOrRd", markersize=8, figsize=(9, 10),
                       missing_kwds={"color": "lightgrey"})
        ax.set_axis_off(); ax.set_title(f"{col} — cidades > 100 mil hab., Censo 2022")
        ax.figure.savefig(FIGDIR / fname, dpi=200, bbox_inches="tight"); plt.close(ax.figure)

    from segbr.census import load_census
    from segbr.cities import build_city_gdf
    census = load_census(ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv")
    for code in ILLUSTRATIVE:
        g = build_city_gdf(code, census, ROOT / "shapefiles_2022")
        g["ppp"] = g["pp_total"] / g["pop_total"]
        ax = g.plot(column="ppp", cmap="YlOrRd", legend=True, vmin=0, vmax=1, figsize=(8, 8))
        try:
            import contextily as cx
            cx.add_basemap(ax)
        except Exception:
            pass
        ax.set_axis_off()
        ax.figure.savefig(FIGDIR / f"seg_profile_{code}.png", dpi=250, bbox_inches="tight")
        plt.close(ax.figure)
```
Register in `dispatch`.

- [ ] **Step 3: Run**

Run: `"$PY" scripts/figures.py fig_maps`
Expected: two national maps + six city composition maps. If `contextily` basemap fails offline, the maps still render without the basemap — acceptable.

- [ ] **Step 4: Run everything once**

Run: `"$PY" scripts/figures.py all` (add `fig_maps` and the earlier fns to the `all` loop)
Expected: every figure/table regenerates without error.

- [ ] **Step 5: Commit**

```bash
git add scripts/figures.py scripts/build_municipio_polygons.py figures/ outputs/municipio_polygons.gpkg outputs/tables/
git commit -m "feat: §5.6 national choropleths + illustrative city composition maps"
```

---

## Task 17: Manuscript skeleton — `draft_v5.tex`

**Files:**
- Create: `draft/draft_v5.tex`
- Reference: `draft/draft_v4.tex` (source text to salvage)

**Interfaces:**
- Produces: a compiling plain-LaTeX article with all section headers, figure/table
  includes pointing at the real files in `figures/` and `outputs/tables/`, and
  `\input`/prose marked `% TODO(taskN)` where later tasks fill it.

- [ ] **Step 1: Create the skeleton**

Plain `article` class (no Sweave/knitr — figures are pre-generated PNGs). Structure per spec §2:

```latex
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern,graphicx,amsmath,amssymb,booktabs,natbib,geometry,hyperref}
\usepackage{caption,subcaption,float}
\geometry{margin=2.5cm}
\graphicspath{{../figures/}}
\title{Multidimensional Racial Residential Segregation across Brazilian Cities:
A Nationwide Assessment with 2022 Census Data}
\author{Renan Xavier Cortes\\ Department of Statistics, UFRGS \\ \texttt{renan.cortes@ufrgs.br}}
\date{\today}
\begin{document}
\maketitle
\begin{abstract}
% TODO(task23)
\end{abstract}
\noindent\textbf{Keywords:} residential segregation; race; Brazil; spatial demography; 2022 Census

\section{Introduction}\label{sec:intro}      % TODO(task18)
\section{Racial segregation in Brazil}\label{sec:brazil}  % TODO(task19)
\section{Data and methods}\label{sec:methods}  % TODO(task20)
\section{Results}\label{sec:results}          % TODO(task21)
\subsection{How segregated are Brazilian cities?}\label{sec:dist}
\subsection{Do the dimensions agree?}\label{sec:agree}
\subsection{Which cities are most segregated?}\label{sec:rank}
\subsection{Regional patterns}\label{sec:region}
\subsection{Minority share and segregation}\label{sec:share}
\subsection{The spatial texture of segregation}\label{sec:maps}
\section{Discussion}\label{sec:discussion}    % TODO(task22)
\section{Reproducibility}\label{sec:repro}
\section{Conclusion}\label{sec:conclusion}
\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
```

- [ ] **Step 2: Wire in the figures and tables** with real `\includegraphics`/`\input` for: `fig_distributions`, `table_summary_stats`, `fig_correlation`, `table2_correlation`, `fig_rankings`, `fig_regional`, `table4_regional`, `fig_minorityshare`, `fig_map_national_dissim`, `fig_map_national_spatial`, the six `seg_profile_*`, `table1_descriptive`. Each in its section with a `\caption` and `\label`; prose still `% TODO`.

- [ ] **Step 3: Compile**

Run: `cd draft && pdflatex -interaction=nonstopmode draft_v5.tex && bibtex draft_v5 && pdflatex -interaction=nonstopmode draft_v5.tex && pdflatex -interaction=nonstopmode draft_v5.tex`
Expected: `draft_v5.pdf` builds; only "undefined references" warnings for empty prose are acceptable. All figures appear.

- [ ] **Step 4: Commit**

```bash
git add draft/draft_v5.tex
git commit -m "paper: draft_v5 skeleton with real figure/table includes"
```

---

## Task 18: Write the Introduction

**Files:**
- Modify: `draft/draft_v5.tex` (§Introduction)

- [ ] **Step 1: Draft ~700–900 words** covering, in order:
  1. Residential segregation as a durable axis of urban inequality; measurement matters for policy.
  2. Massey & Denton (1988): five dimensions (evenness, exposure, concentration, centralization, clustering); one index cannot capture all five.
  3. Aspatial vs spatial measures; why spatial measures matter (checkerboard problem; Reardon & O'Sullivan).
  4. One short paragraph: small-unit upward bias of D (Cortese 1976; Carrington & Troske 1997; Allen et al. 2015) — framed strictly as a **measurement caveat** for cross-city comparison, not a segue into inference.
  5. Brazil: segregation studied mostly via D, on 2010-or-older data, rarely multidimensional, rarely nationwide with spatial measures. Sousa Filho et al. (2023) is the nationwide reference — D only, 2010.
  6. This paper: nationwide (~320 cities > 100k), 2022 Census, nine measures across all five dimensions, reproducible pipeline. State the three questions (levels? do dimensions agree? regional structure?).

- [ ] **Step 2: Salvage** the Massey and spatial-measure sentences from `draft_v4.tex` lines 54–57, 115–118. **Do not** carry over the Ransom/Lee/Rey/`cortes2020`/reviewer-2 paragraphs (lines 58–78).

- [ ] **Step 3: Compile** (Task 17 Step 3 command). Check word count: `\input` the file into `texcount` or `"$PY" -c "..."` word count of the section — target ≤ 900.

- [ ] **Step 4: Commit**

```bash
git add draft/draft_v5.tex && git commit -m "paper: write Introduction"
```

---

## Task 19: Write "Racial segregation in Brazil" + explicit gap

**Files:**
- Modify: `draft/draft_v5.tex` (§Racial segregation in Brazil)

- [ ] **Step 1: Adapt** `draft_v4.tex` lines 82–100 (already drafted and solid). Keep: Telles; Sousa Filho et al. 2023 nationwide; Barros & Feitosa 2018/2024 (SP–London); França 2022; Gonçalves & Strauch 2026 (BH temporal); Barber et al. 2018 (health). Trim the health/SUS paragraph (lines 92–94) to 3–4 sentences.
- [ ] **Step 2: Add a closing gap paragraph** (~120 words): Brazilian quantitative work is (a) D-dominated → evenness only; (b) mostly 2010 census; (c) rarely nationwide *and* multidimensional *and* spatial at once. This paper fills that intersection. No mention of inference beyond one clause ("formal uncertainty quantification remains for future work").
- [ ] **Step 3: Compile.**
- [ ] **Step 4: Commit** — `git commit -m "paper: write Racial segregation in Brazil section + research gap"`

---

## Task 20: Write Data and methods

**Files:**
- Modify: `draft/draft_v5.tex` (§Data and methods)

- [ ] **Step 1: Data subsection** — 2022 Census tract aggregates; variables `V01317–V01321`; group = preta + parda vs total; `"X"`→0; join to IBGE 2022 tract geometries; reproject EPSG:3857; drop zero-population tracts; city universe = municipalities > 100k (state the final N from `outputs/city_universe_2022.csv`); reference Table 1.
- [ ] **Step 2: Measures subsection** — a table: measure → dimension → aspatial/spatial → one-line definition (adapt `draft_v4` lines 115–118). State PySAL `segregation` version (from `outputs/environment.txt`), Queen contiguity default, raw statistics reported.
- [ ] **Step 3: Computation subsection** — hardware; total runtime; note that Gini and distance-decay measures are O(n²) and, for the N largest cities, [either completed in X or were time-budgeted — pull the truth from `outputs/coverage_note.md`]. Point to the public repo + `requirements-lock.txt`.
- [ ] **Step 4: Bias/limitation flag** — 2–3 sentences: D and its spatial analogue carry upward bias when tracts are small; no correction applied; consequences discussed in §Discussion. **No H0/H1, no Monte Carlo.**
- [ ] **Step 5: Compile + commit** — `git commit -m "paper: write Data and methods"`

---

## Task 21: Write Results prose

**Files:**
- Modify: `draft/draft_v5.tex` (§Results and six subsections)

- [ ] **Step 1:** For each subsection, write 120–250 words that state only what the committed figure/table shows. Pull actual numbers from the printed output of each `figures.py` subcommand (re-run and copy values — do not invent):
  - §5.1 ← `fig_distributions` + `table_summary_stats`
  - §5.2 ← `fig_correlation` + `table2_correlation` (name the redundant pairs and the distinct ones)
  - §5.3 ← `fig_rankings` + `table3_rank_correlation` (does the "most segregated" list change with the dimension?)
  - §5.4 ← `fig_regional` + `table4_regional` (South/Southeast vs North/Northeast — on which dimensions; compare to Sousa Filho 2023)
  - §5.5 ← `fig_minorityshare` (describe direction/shape only; "no formal test is performed")
  - §5.6 ← the three map figures (spatial texture; core–periphery; enclaves)
- [ ] **Step 2:** Language audit — grep the section for "significant", "significantly", "p ", "confidence", "credible"; replace with descriptive phrasing.
- [ ] **Step 3: Compile + commit** — `git commit -m "paper: write Results"`

---

## Task 22: Write Discussion, limitations, future work; Reproducibility; Conclusion

**Files:**
- Modify: `draft/draft_v5.tex` (§Discussion, §Reproducibility, §Conclusion)

- [ ] **Step 1: Discussion** (~600 words) — what multidimensionality reveals that D hides (cite the §5.2/§5.3 findings); which dimensions are structurally coupled in Brazil and why (center–periphery, enclaves — Barros & Feitosa 2024, França 2022, Telles 2004); regional heterogeneity and candidate drivers.
- [ ] **Step 2: Limitations** — spec §8 list verbatim in prose: small-unit bias; MAUP + 2010/2022 tract boundary changes (so *not* directly comparable to Sousa Filho's numbers); cross-sectional 2022; preta+parda aggregation; any time-skipped spatial measures (cite `coverage_note.md`); RelativeConcentration/Centralization sign & CBD sensitivity.
- [ ] **Step 3: Future work** — inference (single + comparative), spatial vs compositional decomposition (Rey et al. 2021), temporal 2010→2022, street-network measures.
- [ ] **Step 4: Reproducibility** — repo URL, `segbr/` package, `scripts/` run order, pinned env, data manifest.
- [ ] **Step 5: Conclusion** (~150 words).
- [ ] **Step 6: Compile + commit** — `git commit -m "paper: write Discussion, Reproducibility, Conclusion"`

---

## Task 23: Abstract, title, keywords

**Files:**
- Modify: `draft/draft_v5.tex`

- [ ] **Step 1:** Structured abstract ≤ 200 words: objective / data / methods / main results (3–4 concrete findings with numbers) / conclusion. Mirror the abstract shape of Sousa Filho et al. (2023) and Barros & Feitosa (2024).
- [ ] **Step 2:** Finalise title; 5 keywords.
- [ ] **Step 3: Compile + commit** — `git commit -m "paper: abstract, title, keywords"`

---

## Task 24: Bibliography cleanup

**Files:**
- Modify: `draft/references.bib`

- [ ] **Step 1: Remove duplicate keys** — `references.bib` has `curtiss1942note` (lines 10, 85), `massey2015research` (316, 535), and three overlapping Sousa Filho entries (`sousa2023nacional`, `deSouza2023nationwide_english`, `deSousaFilho2022nationwide` — the first two are the *same* REBEP article, the third is a different SN Social Sciences paper). Keep one REBEP entry (`deSouza2023nationwide_english`), keep `deSousaFilho2022nationwide`, delete `sousa2023nacional`.
- [ ] **Step 2: Prune** entries never cited by `draft_v5.tex` (the probability-theory textbooks from the chapter's stats appendix: `barryjames2023`, `curtiss1942note`, `magalhaes2006probabilidade`, `degroot2012probability`, `johnson2007applied`, `Kolmogorov1933`, `axler2020measure`, `mood1974introduction`, `morettin1999estatística`, `rolla*`, `dantas2013probabilidade`, `meyer2006probabilidade`, `rollalima2025prob`).
- [ ] **Step 3:** `pdflatex … && bibtex draft_v5 …` — zero "I didn't find a database entry" and zero "empty" warnings; check `draft_v5.blg`.
- [ ] **Step 4: Commit** — `git commit -m "paper: dedupe and prune references.bib"`

---

## Task 25: Full compile + consistency pass

**Files:**
- Modify: `draft/draft_v5.tex` as needed

- [ ] **Step 1: Clean build**

Run: `cd draft && rm -f draft_v5.aux draft_v5.bbl && pdflatex -interaction=nonstopmode draft_v5.tex && bibtex draft_v5 && pdflatex -interaction=nonstopmode draft_v5.tex && pdflatex -interaction=nonstopmode draft_v5.tex`
Expected: no undefined references, no missing figures, no overfull-hbox errors > 20pt.

- [ ] **Step 2: Cross-check** every `\ref`/`\cite` resolves; every figure in `figures/` used by the paper is the freshly regenerated one (`scripts/figures.py all` then diff mtimes); every number in Results prose appears in the corresponding table/figure.

- [ ] **Step 3: Word count** — `texcount -inc -sum draft_v5.tex`. Target ≤ 8,000 words (REBEP). If over, trim Introduction and Discussion first.

- [ ] **Step 4: Read the PDF end to end.** Fix flow, undefined acronyms, figure placement.

- [ ] **Step 5: Commit** — `git add draft/draft_v5.* && git commit -m "paper: full compile, consistency and length pass"`

---

## Task 26: REBEP formatting (FINAL — do not start earlier)

**Files:**
- Create: `draft/rebep/` (journal template + adapted manuscript)

**Interfaces:**
- Consumes: finalized `draft/draft_v5.tex` content.

- [ ] **Step 1:** Download the REBEP submission template/guidelines (https://rebep.org.br → "Diretrizes para Autores"). Note: title page, abstract length, reference style (ABNT author-date), figure/table placement rules, word/character cap, ORCID, section-numbering convention.
- [ ] **Step 2:** Create `draft/rebep/manuscript.tex` from the template; move `draft_v5` prose into it section by section; adapt references to the journal's required `.bst` (or ABNTeX). Keep figures at journal-required resolution/format.
- [ ] **Step 3:** Compile in the template; fix template-specific errors.
- [ ] **Step 4:** Produce the submission checklist file `draft/rebep/SUBMISSION.md` — files to upload, cover letter points (novelty vs Sousa Filho 2023), suggested reviewers, data/code availability statement pointing at the repo.
- [ ] **Step 5: Commit** — `git commit -m "paper: adapt manuscript to REBEP template"`

---

## Task 27: Bilingual pass (REBEP accepts PT/EN/ES; EN submission is fine, but prepare PT title/abstract/keywords)

**Files:**
- Modify: `draft/rebep/manuscript.tex`

- [ ] **Step 1:** Add Portuguese `título`, `resumo` (≤ 200 words), `palavras-chave` alongside the English ones (REBEP requires both regardless of body language).
- [ ] **Step 2:** If choosing to submit in Portuguese: translate the body; keep the English version as `draft/rebep/manuscript_en.tex`. If submitting in English: skip the body translation (REBEP will handle it post-acceptance).
- [ ] **Step 3: Compile + commit** — `git commit -m "paper: bilingual title/abstract/keywords for REBEP"`

---

## Self-Review

**1. Spec coverage:**
- §2 contribution (2022, all 5 dims, nationwide, reproducible) → Tasks 8, 11–16, 22 (Reproducibility).
- §3 draft_v4 disposition (cut §3.3, §4.2, trim intro) → Tasks 17, 18 (Step 2 explicitly excludes lines 58–78), 24.
- §4 data (variables, cleaning, geometries, universe, Table 1) → Tasks 2, 4, 7, 10, 20.
- §5 nine measures, PySAL defaults, raw statistics → Task 5, 20.
- §6.1 pipeline refactor → Tasks 1–6. §6.2 artifacts → Tasks 7–9. §6.3 O(n²) risk → Task 8 Steps 3–5. §6.4 reproducibility → Tasks 1, 9, 22.
- §7 six result subsections → Tasks 11–16 (figures) + 21 (prose). Every row of the §7 table maps to one task.
- §8 discussion + limitations + future work → Task 22.
- §9 title/journal/template-last → Tasks 23, 26, 27; template deferred to final tasks per constraint.
- §10 out of scope → enforced in Tasks 18 Step 2, 20 Step 4, 21 Step 2 (language audit).
- §11 sequencing → this plan's task order.

**2. Placeholder scan:** Prose tasks (18–23) specify word budgets, ordered content points, exact source lines to salvage, and "pull numbers from the printed script output" rather than "write about the results". Figure tasks contain runnable code. No "TBD"/"handle edge cases"/"similar to Task N". `compute_profile` error handling is shown in full. The one genuine unknown — whether megacities need time-budgeting — is a documented decision point (Task 8 Step 4) with both branches specified, not a placeholder.

**3. Type consistency:** `load_census` → DataFrame with `COD_MUNICIPIO`/`COD_UF` (used by `municipality_universe`, `build_city_gdf`, `build_universe.py`, `figures.load()`). `municipality_universe` → columns `[COD_MUNICIPIO, COD_UF, pop_total, n_tracts]` (consumed by `run_all` via `.itertuples`, and `build_universe.py` adds `UF`). `build_city_gdf(cod_municipio, census_df, shp_dir)` signature identical in Tasks 4, 8, 16. `compute_profile(gdf, *, measures, time_budget_s)` identical in Tasks 5, 6. `run_all(universe_df, census_df, shp_dir, out_path, *, measures, time_budget_s, limit)` identical in Tasks 6, 8. `MEASURES` keys (nine names) identical across Tasks 5, 9, 10 (`figures.py` `MEASURES` list), 11–16. Parquet columns (`COD_MUNICIPIO`, `fatal_error`, `ppp`, `n_tracts`, nine measure columns, `<name>_error`) consistent Tasks 6, 8, 9, 10.

No gaps found.
