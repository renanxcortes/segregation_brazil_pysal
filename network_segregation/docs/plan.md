# Segregated by Design in Brazil — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible pipeline that measures, for the 91 Brazilian municipalities with ≥300k inhabitants, racial segregation under Euclidean vs street-network (walking) distance, relates the gap to street-network topology (incl. a configurational fragmentation index), and drafts the English LaTeX manuscript.

**Architecture:** A small package `netseg/` with one module per responsibility (inputs → OSM graph → pairwise distances → kernel weights → PySAL indices; topology in parallel), orchestrated per city with on-disk caching and per-city error capture. Distances are computed once per city up to 3 km and every bandwidth/decay variant is derived from that cache. Scripts turn cached results into tables, figures, models and LaTeX macros that the manuscript `\input`s.

**Tech Stack:** Python 3.12, geopandas, libpysal, segregation 2.5.3 (PySAL), osmnx ≥2.0, networkx, scipy (csgraph Dijkstra, cKDTree), statsmodels, matplotlib/seaborn, pytest; LaTeX (TinyTeX `latexmk`) + BibTeX.

**Spec:** `network_segregation/docs/spec.md` (read it first; this plan implements it).

## Global Constraints

- Everything is created under `network_segregation/`. **No pre-existing file in the repository may be modified.** Existing data are read-only inputs: `Agregados_por_setores_cor_ou_raca_BR_csv/Agregados_por_setores_cor_ou_raca_BR.csv`, `shapefiles_2022/<UF>_setores_CD2022/<UF>_setores_CD2022.shp`, `outputs/city_universe_2022.csv`, `outputs/municipio_names.csv`, `outputs/municipio_polygons.gpkg`, `outputs/uf_polygons.gpkg`.
- **Never run `git add` / `git commit`.** Every task ends with a "no-commit check" instead: `git status --porcelain` must list only paths under `network_segregation/` (new, untracked).
- Python: a new conda env `netseg` (never modify the Anaconda `base` env). Interpreter: `C:/Users/renan/anaconda3/envs/netseg/python.exe` (abbreviated `$PY` below). conda: `C:/Users/renan/anaconda3/Scripts/conda.exe`.
- All commands run from `network_segregation/` (it has its own `pytest.ini`, so the repo-root `pytest.ini` is not used).
- Cities: municipalities with `pop_total >= 300_000` in `outputs/city_universe_2022.csv` → exactly 91 (includes all 27 capitals).
- Tracts: `SITUACAO == "Urbana"` and `pop_total > 0`. Groups: `branca` V01317, `preta` V01318, `amarela` V01319, `parda` V01320, `indigena` V01321; `"X"` (suppressed) → 0.
- Main specification: triangular kernel `w = 1 − d/b` for `d ≤ b`, `b = 2000` m, diagonal = 1. Robustness: `b ∈ {1000, 3000}` linear; `b = 2000` exponential `w = exp(−3d/b)` for `d ≤ b`.
- OSM network: `osmnx.graph_from_polygon(..., network_type="walk")`, polygon = union of urban tracts buffered by 2,000 m.
- No permutation / random-labelling inference anywhere. RQ2 OLS uses HC3 robust SEs.
- Fragmentation: `S = 500` targets, `N = 2000` sampled origins, local radius 800 m, seed 0; `F = 1 − corr(log L_i, G_i)`.
- `segregation` software citation: Cortes, Knaap & Rey (2026), JOSS 11(125):11126, doi:10.21105/joss.11126 — always cited together with Cortes et al. (2020) and Rey et al. (2021).

## Review Focus

1. **Tract far from any mapped street** (island, unmapped favela, large urban-fringe tract): must still get a network distance = snap_i + path + snap_j, and be counted in `n_snap_gt500`. Pinned by `test_network_pairs_adds_snap_distances` (Task 4) and `test_run_city_reports_snap_diagnostics` (Task 7).
2. **One city fails** (Overpass timeout, empty graph, no urban tracts): the run must continue, write the failure to `outputs/failures.csv`, and a re-run must skip already-finished cities. Pinned by `test_run_all_records_failure_and_continues` and `test_run_city_uses_cached_result` (Task 7).
3. **Suppressed/missing census counts** (`"X"`, tracts absent from the CSV, zero-population tracts): treated as 0 and dropped when `pop_total == 0`, never NaN. Pinned by `test_load_race_counts_handles_suppressed` and `test_load_urban_tracts_filters_and_zero_fills` (Task 2).
4. **Row order vs weights order**: indices must not change if the tract rows are permuted consistently with the weights. Pinned by `test_indices_invariant_to_row_permutation` (Task 5).
5. **Parallel / zero-length / self-loop OSM edges**: parallel edges use the shortest length, zero-length edges remain traversable, self-loops ignored for routing. Pinned by `test_graph_to_csr_min_parallel_and_zero_length` (Task 4).

---

### Task 1: Scaffold folder and conda environment

**Files:**
- Create: `network_segregation/.gitignore`, `network_segregation/environment.yml`, `network_segregation/environment-crosscheck.yml`, `network_segregation/pytest.ini`, `network_segregation/README.md`, `network_segregation/netseg/__init__.py`, `network_segregation/tests/__init__.py`, `network_segregation/tests/test_env.py`

**Interfaces:**
- Produces: importable package `netseg`; env `netseg` with the libraries below.

- [ ] **Step 1: Create files**

`network_segregation/.gitignore`:
```
data/
outputs/cache/
__pycache__/
.pytest_cache/
manuscript/*.aux
manuscript/*.bbl
manuscript/*.blg
manuscript/*.log
manuscript/*.out
manuscript/*.fdb_latexmk
manuscript/*.fls
manuscript/*.synctex.gz
```

`network_segregation/environment.yml`:
```yaml
name: netseg
channels: [conda-forge]
dependencies:
  - python=3.12
  - geopandas>=1.0
  - libpysal>=4.12
  - osmnx>=2.0
  - networkx>=3.3
  - scipy>=1.13
  - numpy>=2.0
  - pandas>=2.2
  - pyogrio
  - pyarrow
  - shapely>=2.0
  - statsmodels>=0.14
  - matplotlib
  - seaborn
  - momepy>=0.8
  - pytest
  - pip
  - pip:
    - segregation==2.5.3
```

`network_segregation/environment-crosscheck.yml` (optional env, Task 9 only):
```yaml
name: netseg-pandana
channels: [conda-forge]
dependencies:
  - python=3.11
  - geopandas
  - osmnx>=2.0
  - pandana
  - pyogrio
  - pip
  - pip:
    - segregation==2.5.3
```

`network_segregation/pytest.ini`:
```ini
[pytest]
testpaths = tests
addopts = -q
markers =
    realdata: needs the repository's census/shapefile inputs
    slow: long-running
filterwarnings =
    ignore::FutureWarning
    ignore::UserWarning
    ignore::RuntimeWarning
```

`network_segregation/netseg/__init__.py`:
```python
"""Euclidean vs street-network segregation for Brazilian cities."""
```

`network_segregation/tests/__init__.py`: empty file.

`network_segregation/README.md`:
```markdown
# Segregated by design in Brazil?

Self-contained companion code for the paper. Reads the repository's 2022 census
inputs read-only; writes only inside this folder.

    conda env create -f environment.yml          # env "netseg"
    conda activate netseg
    pytest                                        # unit tests
    python scripts/run_all.py                     # 91 cities -> outputs/
    python scripts/check_fragmentation_stability.py
    python scripts/fit_models.py
    python scripts/make_tables.py
    python scripts/make_figures.py
    cd manuscript && latexmk -pdf manuscript.tex

OSM graphs are cached in `data/osm/`; per-city results in `data/results/`.
```

`network_segregation/tests/test_env.py`:
```python
import importlib

import pytest


@pytest.mark.parametrize(
    "mod", ["geopandas", "libpysal", "segregation", "osmnx", "networkx", "scipy", "statsmodels", "momepy", "seaborn"]
)
def test_import(mod):
    importlib.import_module(mod)


def test_segregation_version():
    import segregation

    assert segregation.__version__ == "2.5.3"
```

- [ ] **Step 2: Create the env**

Run: `C:/Users/renan/anaconda3/Scripts/conda.exe env create -f environment.yml`
Expected: env `netseg` created (takes several minutes).

- [ ] **Step 3: Run tests**

Run: `$PY -m pytest tests/test_env.py -v`
Expected: 10 passed.

- [ ] **Step 4: No-commit check**

Run: `git status --porcelain` (from repo root)
Expected: only `?? network_segregation/...` lines.

---

### Task 2: City selection and urban-tract loading (`netseg/cities.py`)

**Files:**
- Create: `network_segregation/netseg/cities.py`
- Test: `network_segregation/tests/test_cities.py`

**Interfaces:**
- Produces:
  - `GROUPS: list[str] = ["branca", "preta", "amarela", "parda", "indigena"]`
  - `select_cities(universe_csv=UNIVERSE_CSV, names_csv=NAMES_CSV, min_pop=300_000) -> pd.DataFrame` with columns `COD_MUNICIPIO` (str), `NM_MUN`, `UF`, `pop_total`, sorted by `pop_total` desc.
  - `load_race_counts(csv_path=CENSUS_CSV) -> pd.DataFrame` columns `CD_SETOR` (str), the five `GROUPS` (int64), `pop_total`, `pp_total`.
  - `load_urban_tracts(cod: str, race: pd.DataFrame, shp_dir=SHP_DIR) -> tuple[gpd.GeoDataFrame, dict]`; GeoDataFrame in the city's SIRGAS 2000 / UTM CRS, index `0..n-1`, columns `CD_SETOR`, `GROUPS`, `pop_total`, `pp_total`, `geometry`; dict keys `n_tracts_all`, `n_tracts_urban`, `pop_all`, `pop_urban`.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_cities.py`:
```python
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from netseg import cities


def test_load_race_counts_handles_suppressed(tmp_path):
    csv = tmp_path / "race.csv"
    csv.write_text(
        '"CD_SETOR";"V01317";"V01318";"V01319";"V01320";"V01321";"V01322"\n'
        '"431490205000001";"10";"X";"0";"5";"1";"9"\n'
        '"431490205000002";"X";"X";"X";"X";"X";"X"\n'
    )
    df = cities.load_race_counts(csv)
    assert list(df.columns) == ["CD_SETOR", *cities.GROUPS, "pop_total", "pp_total"]
    assert df.loc[0, "preta"] == 0 and df.loc[0, "pop_total"] == 16 and df.loc[0, "pp_total"] == 5
    assert df.loc[1, "pop_total"] == 0
    assert df[cities.GROUPS].isna().sum().sum() == 0


def _write_shp(tmp_path: Path) -> Path:
    d = tmp_path / "RS_setores_CD2022"
    d.mkdir()
    gdf = gpd.GeoDataFrame(
        {
            "CD_SETOR": ["431490205000001", "431490205000002", "431490205000003", "431490205000004", "999999905000001"],
            "SITUACAO": ["Urbana", "Urbana", "Rural", "Urbana", "Urbana"],
            "CD_MUN": ["4314902", "4314902", "4314902", "4314902", "9999999"],
        },
        geometry=[box(-51.20 + k * 0.01, -30.05, -51.19 + k * 0.01, -30.04) for k in range(5)],
        crs="EPSG:4674",
    )
    gdf.to_file(d / "RS_setores_CD2022.shp")
    return tmp_path


def test_load_urban_tracts_filters_and_zero_fills(tmp_path):
    shp_dir = _write_shp(tmp_path)
    race = pd.DataFrame(
        {
            "CD_SETOR": ["431490205000001", "431490205000002", "431490205000003"],
            "branca": [10, 0, 7], "preta": [1, 0, 0], "amarela": [0, 0, 0], "parda": [4, 0, 1], "indigena": [0, 0, 0],
        }
    )
    race["pop_total"] = race[cities.GROUPS].sum(axis=1)
    race["pp_total"] = race["preta"] + race["parda"]
    gdf, stats = cities.load_urban_tracts("4314902", race, shp_dir=shp_dir)
    # tract 2: zero pop; tract 3: rural; tract 4: missing from census -> 0 -> dropped
    assert list(gdf["CD_SETOR"]) == ["431490205000001"]
    assert stats == {"n_tracts_all": 2, "n_tracts_urban": 1, "pop_all": 23, "pop_urban": 15}
    assert gdf.crs.is_projected and "UTM" in gdf.crs.name and "SIRGAS" in gdf.crs.name
    assert list(gdf.index) == [0]


def test_load_urban_tracts_raises_when_no_urban(tmp_path):
    shp_dir = _write_shp(tmp_path)
    race = pd.DataFrame({"CD_SETOR": ["431490205000003"], "branca": [5], "preta": [0], "amarela": [0], "parda": [0], "indigena": [0]})
    race["pop_total"] = 5
    race["pp_total"] = 0
    with pytest.raises(ValueError, match="no populated urban tracts"):
        cities.load_urban_tracts("4314902", race, shp_dir=shp_dir)


def test_select_cities_threshold(tmp_path):
    u = tmp_path / "u.csv"
    u.write_text("COD_MUNICIPIO,COD_UF,UF,pop_total,n_tracts\n1,11,RO,500000,10\n2,11,RO,299999,5\n3,11,RO,300000,5\n")
    n = tmp_path / "n.csv"
    n.write_text("COD_MUNICIPIO,NM_MUN\n1,A\n2,B\n3,C\n")
    out = cities.select_cities(u, n)
    assert list(out["COD_MUNICIPIO"]) == ["1", "3"]
    assert list(out.columns) == ["COD_MUNICIPIO", "NM_MUN", "UF", "pop_total"]


@pytest.mark.realdata
def test_select_cities_real_91_with_capitals():
    capitals = {
        "1100205", "1200401", "1302603", "1400100", "1501402", "1600303", "1721000", "2111300", "2211001",
        "2304400", "2408102", "2507507", "2611606", "2704302", "2800308", "2927408", "3106200", "3205309",
        "3304557", "3550308", "4106902", "4205407", "4314902", "5002704", "5103403", "5208707", "5300108",
    }
    out = cities.select_cities()
    assert len(out) == 91
    assert capitals <= set(out["COD_MUNICIPIO"])
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_cities.py -v`
Expected: FAIL / ERROR — `ImportError: cannot import name 'cities'`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/cities.py`:
```python
"""Read-only access to the repository's 2022 census inputs."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CENSUS_CSV = REPO_ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
SHP_DIR = REPO_ROOT / "shapefiles_2022"
UNIVERSE_CSV = REPO_ROOT / "outputs" / "city_universe_2022.csv"
NAMES_CSV = REPO_ROOT / "outputs" / "municipio_names.csv"

RACE_VARS = {"V01317": "branca", "V01318": "preta", "V01319": "amarela", "V01320": "parda", "V01321": "indigena"}
GROUPS = list(RACE_VARS.values())
COUNT_COLS = [*GROUPS, "pop_total", "pp_total"]

UF_BY_CODE = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def select_cities(universe_csv=UNIVERSE_CSV, names_csv=NAMES_CSV, min_pop: int = 300_000) -> pd.DataFrame:
    """Municipalities with 2022 population >= ``min_pop``, largest first."""
    u = pd.read_csv(universe_csv, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    names = pd.read_csv(names_csv, dtype={"COD_MUNICIPIO": str})
    out = u[u["pop_total"] >= min_pop].merge(names, on="COD_MUNICIPIO", how="left")
    out = out.sort_values("pop_total", ascending=False).reset_index(drop=True)
    return out[["COD_MUNICIPIO", "NM_MUN", "UF", "pop_total"]]


def load_race_counts(csv_path=CENSUS_CSV) -> pd.DataFrame:
    """Five colour/race counts per tract; suppressed cells ("X") become 0."""
    df = pd.read_csv(csv_path, sep=";", usecols=["CD_SETOR", *RACE_VARS], dtype=str)
    counts = (
        df[list(RACE_VARS)]
        .replace({"X": None})
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype("int64")
        .rename(columns=RACE_VARS)
    )
    counts.insert(0, "CD_SETOR", df["CD_SETOR"])
    counts["pop_total"] = counts[GROUPS].sum(axis=1).astype("int64")
    counts["pp_total"] = (counts["preta"] + counts["parda"]).astype("int64")
    return counts


def load_urban_tracts(cod: str, race: pd.DataFrame, shp_dir=SHP_DIR) -> tuple[gpd.GeoDataFrame, dict]:
    """Populated urban tracts of one municipality, projected to SIRGAS 2000 / UTM."""
    uf = UF_BY_CODE[cod[:2]]
    shp = Path(shp_dir) / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp"
    raw = gpd.read_file(shp, where=f"CD_MUN = '{cod}'", columns=["CD_SETOR", "SITUACAO"])
    merged = raw.merge(race[["CD_SETOR", *COUNT_COLS]], on="CD_SETOR", how="left")
    merged[COUNT_COLS] = merged[COUNT_COLS].fillna(0).astype("int64")
    populated = merged[merged["pop_total"] > 0]
    urban = populated[populated["SITUACAO"] == "Urbana"]
    if urban.empty:
        raise ValueError(f"no populated urban tracts for municipality {cod!r}")
    stats = {
        "n_tracts_all": int(len(populated)),
        "n_tracts_urban": int(len(urban)),
        "pop_all": int(populated["pop_total"].sum()),
        "pop_urban": int(urban["pop_total"].sum()),
    }
    gdf = gpd.GeoDataFrame(urban.drop(columns="SITUACAO"), geometry="geometry", crs=raw.crs)
    utm = gdf.estimate_utm_crs(datum_name="SIRGAS 2000")
    return gdf.to_crs(utm).reset_index(drop=True), stats
```

- [ ] **Step 4: Run tests**

Run: `$PY -m pytest tests/test_cities.py -v`
Expected: 5 passed.

- [ ] **Step 5: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 3: OSM walk graph download, preparation and snapping (`netseg/network.py`)

**Files:**
- Create: `network_segregation/netseg/network.py`
- Test: `network_segregation/tests/test_network.py`, `network_segregation/tests/helpers.py`

**Interfaces:**
- Consumes: GeoDataFrame from `load_urban_tracts`.
- Produces:
  - `footprint(gdf) -> shapely Polygon|MultiPolygon` (union of tracts, in `gdf.crs`).
  - `download_walk_graph(polygon_wgs84, cache_path: Path) -> nx.MultiDiGraph` (osmnx, cached GraphML).
  - `prepare_graph(G: nx.MultiDiGraph, crs) -> nx.MultiGraph` (projected, undirected, largest connected component; edges carry `length` in metres; nodes `x`, `y` in `crs`).
  - `snap_points(G: nx.MultiGraph, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (node ids, snap distances in metres).
  - `clip_graph(G: nx.MultiGraph, polygon) -> nx.MultiGraph` (nodes inside polygon, largest connected component).
- Test helper (used by Tasks 4, 6, 7): `tests/helpers.py::grid_graph(nx_, ny, spacing=100.0, origin=(0.0, 0.0)) -> nx.MultiGraph` with `x`, `y`, `length`, `graph["crs"] = "EPSG:31982"`.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/helpers.py`:
```python
import networkx as nx


def grid_graph(nx_: int, ny: int, spacing: float = 100.0, origin=(0.0, 0.0)) -> nx.MultiGraph:
    """Projected lattice street graph: nodes (i, j) at origin + spacing*(i, j)."""
    base = nx.grid_2d_graph(nx_, ny)
    G = nx.MultiGraph()
    G.graph["crs"] = "EPSG:31982"
    for (i, j) in base.nodes:
        G.add_node((i, j), x=origin[0] + i * spacing, y=origin[1] + j * spacing)
    for u, v in base.edges:
        G.add_edge(u, v, length=spacing)
    return G
```

`network_segregation/tests/test_network.py`:
```python
import networkx as nx
import numpy as np
from shapely.geometry import box

from netseg import network
from tests.helpers import grid_graph


def test_snap_points_nearest_node_and_distance():
    G = grid_graph(3, 3)
    ids, d = network.snap_points(G, np.array([[10.0, 0.0], [190.0, 210.0]]))
    assert list(map(tuple, ids)) == [(0, 0), (2, 2)] or list(ids) == [(0, 0), (2, 2)]
    np.testing.assert_allclose(d, [10.0, np.hypot(10, 10)])


def test_prepare_graph_keeps_largest_component():
    G = nx.MultiDiGraph(crs="EPSG:4326")
    # a 3-node path near Porto Alegre and an isolated 2-node island far away
    for n, (lon, lat) in {1: (-51.20, -30.03), 2: (-51.199, -30.03), 3: (-51.198, -30.03), 8: (-51.0, -30.0), 9: (-51.0001, -30.0)}.items():
        G.add_node(n, x=lon, y=lat)
    for k, (u, v) in enumerate([(1, 2), (2, 3), (8, 9)]):
        G.add_edge(u, v, length=96.3, osmid=k)  # osmnx.to_undirected compares osmid
        G.add_edge(v, u, length=96.3, osmid=k)
    out = network.prepare_graph(G, "EPSG:31982")
    assert set(out.nodes) == {1, 2, 3}
    assert not out.is_directed()
    assert out.nodes[1]["x"] > 1000  # projected metres, not degrees


def test_clip_graph_inside_polygon():
    G = grid_graph(5, 5)
    out = network.clip_graph(G, box(-1, -1, 201, 201))
    assert out.number_of_nodes() == 9


def test_footprint_union(tmp_path):
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)], crs="EPSG:31982")
    assert abs(network.footprint(gdf).area - 2.0) < 1e-9
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_network.py -v`
Expected: FAIL — `ImportError: cannot import name 'network'`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/network.py`:
```python
"""OpenStreetMap walk network: download, projection, component selection, snapping."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import osmnx as ox
import shapely
from scipy.spatial import cKDTree
from shapely.ops import unary_union


def footprint(gdf):
    """Union of all tract polygons (in the GeoDataFrame's CRS)."""
    return unary_union(gdf.geometry.values)


def download_walk_graph(polygon_wgs84, cache_path: Path) -> nx.MultiDiGraph:
    """OSM pedestrian graph for a WGS84 polygon; cached as GraphML."""
    cache_path = Path(cache_path)
    if cache_path.exists():
        return ox.load_graphml(cache_path)
    G = ox.graph_from_polygon(polygon_wgs84, network_type="walk", simplify=True, retain_all=False, truncate_by_edge=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, cache_path)
    return G


def _largest_component(G: nx.MultiGraph) -> nx.MultiGraph:
    nodes = max(nx.connected_components(G), key=len)
    return G.subgraph(nodes).copy()


def prepare_graph(G: nx.MultiDiGraph, crs) -> nx.MultiGraph:
    """Project to ``crs``, make undirected, keep the largest connected component."""
    Gp = ox.projection.project_graph(G, to_crs=crs)
    return _largest_component(ox.convert.to_undirected(Gp))


def node_xy(G) -> tuple[np.ndarray, np.ndarray]:
    nodes = np.empty(G.number_of_nodes(), dtype=object)
    nodes[:] = list(G.nodes)
    xy = np.array([[G.nodes[n]["x"], G.nodes[n]["y"]] for n in nodes], dtype=float)
    return nodes, xy


def snap_points(G, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Nearest graph node for each point, and the straight-line snap distance."""
    nodes, nxy = node_xy(G)
    d, idx = cKDTree(nxy).query(xy)
    return nodes[idx], d


def clip_graph(G: nx.MultiGraph, polygon) -> nx.MultiGraph:
    """Subgraph of nodes inside ``polygon`` (same CRS), largest component."""
    nodes, nxy = node_xy(G)
    inside = shapely.contains_xy(polygon, nxy[:, 0], nxy[:, 1])
    return _largest_component(G.subgraph(nodes[inside].tolist()).copy())
```

- [ ] **Step 4: Run tests**

Run: `$PY -m pytest tests/test_network.py -v`
Expected: 4 passed. (If `test_snap_points…` fails only on the tuple comparison form, keep the assertion that matches numpy object arrays of tuples — the first branch.)

- [ ] **Step 5: Live smoke (network access)**

Run:
```bash
$PY -c "
import geopandas as gpd; from shapely.geometry import box; from pathlib import Path
from netseg import network
p = box(-51.235, -30.04, -51.225, -30.03)
G = network.download_walk_graph(p, Path('data/osm/_smoke.graphml'))
Gu = network.prepare_graph(G, 'EPSG:31982'); print(Gu.number_of_nodes(), Gu.number_of_edges())
"
```
Expected: two positive integers (downtown Porto Alegre). Delete `data/osm/_smoke.graphml` afterwards.

- [ ] **Step 6: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 4: Euclidean and network pairwise distances (`netseg/distances.py`)

**Files:**
- Create: `network_segregation/netseg/distances.py`
- Test: `network_segregation/tests/test_distances.py`

**Interfaces:**
- Consumes: `nx.MultiGraph` from `prepare_graph`; node ids + snap distances from `snap_points`.
- Produces:
  - `@dataclass(frozen=True) class Pairs: i: np.ndarray; j: np.ndarray; d: np.ndarray; n: int` — symmetric off-diagonal pairs (both (i,j) and (j,i)), with methods `within(bandwidth) -> Pairs`, `save(path)`, `Pairs.load(path) -> Pairs`.
  - `euclidean_pairs(xy: np.ndarray, limit: float) -> Pairs`
  - `graph_to_csr(G) -> tuple[scipy.sparse.csr_matrix, np.ndarray]` (symmetric edge-length matrix, node array aligned with rows)
  - `network_pairs(csr, tract_node_idx: np.ndarray, snap_d: np.ndarray, limit: float, batch: int = 16) -> Pairs` where `d = snap_i + path(node_i, node_j) + snap_j`, kept if `≤ limit`.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_distances.py`:
```python
import networkx as nx
import numpy as np

from netseg import distances
from tests.helpers import grid_graph


def _as_dict(p):
    return {(int(a), int(b)): float(c) for a, b, c in zip(p.i, p.j, p.d)}


def test_euclidean_pairs_symmetric_within_limit():
    xy = np.array([[0, 0], [300, 400], [5000, 0]], dtype=float)
    p = distances.euclidean_pairs(xy, limit=1000)
    assert _as_dict(p) == {(0, 1): 500.0, (1, 0): 500.0}
    assert p.n == 3


def test_graph_to_csr_min_parallel_and_zero_length():
    G = nx.MultiGraph()
    for n, x in [("a", 0), ("b", 1), ("c", 2)]:
        G.add_node(n, x=float(x), y=0.0)
    G.add_edge("a", "b", length=50.0)
    G.add_edge("a", "b", length=30.0)   # parallel: shorter wins
    G.add_edge("b", "c", length=0.0)    # zero length must stay traversable
    G.add_edge("c", "c", length=10.0)   # self-loop ignored
    csr, nodes = distances.graph_to_csr(G)
    k = {n: i for i, n in enumerate(nodes)}
    from scipy.sparse.csgraph import dijkstra

    dist = dijkstra(csr, directed=False, indices=k["a"])
    assert abs(dist[k["b"]] - 30.0) < 1e-6
    assert np.isfinite(dist[k["c"]]) and abs(dist[k["c"]] - 30.0) < 0.01


def test_network_pairs_on_grid_matches_manhattan():
    G = grid_graph(5, 5)  # spacing 100
    csr, nodes = distances.graph_to_csr(G)
    k = {n: i for i, n in enumerate(nodes)}
    tract_nodes = np.array([k[(0, 0)], k[(2, 1)], k[(4, 4)]])
    p = distances.network_pairs(csr, tract_nodes, np.zeros(3), limit=550)
    got = _as_dict(p)
    assert got[(0, 1)] == 300.0 and got[(1, 0)] == 300.0
    assert got[(1, 2)] == 500.0
    assert (0, 2) not in got  # 800 m > limit


def test_network_pairs_adds_snap_distances():
    G = grid_graph(3, 1)
    csr, nodes = distances.graph_to_csr(G)
    k = {n: i for i, n in enumerate(nodes)}
    tract_nodes = np.array([k[(0, 0)], k[(2, 0)], k[(2, 0)]])
    snap = np.array([400.0, 10.0, 20.0])
    p = distances.network_pairs(csr, tract_nodes, snap, limit=1000)
    got = _as_dict(p)
    assert got[(0, 1)] == 400 + 200 + 10
    assert got[(1, 2)] == 30.0  # same node: only snaps
    assert (0, 0) not in got and (1, 1) not in got


def test_network_ge_euclidean_on_grid():
    G = grid_graph(6, 6)
    csr, nodes = distances.graph_to_csr(G)
    k = {n: i for i, n in enumerate(nodes)}
    ids = [(0, 0), (3, 2), (5, 5), (1, 4)]
    xy = np.array([[i * 100.0, j * 100.0] for i, j in ids])
    pn = _as_dict(distances.network_pairs(csr, np.array([k[n] for n in ids]), np.zeros(4), 2000))
    pe = _as_dict(distances.euclidean_pairs(xy, 2000))
    for key, de in pe.items():
        assert pn[key] >= de - 1e-9


def test_pairs_roundtrip_and_within(tmp_path):
    p = distances.Pairs(np.array([0, 1]), np.array([1, 0]), np.array([1500.0, 1500.0]), 2)
    p.save(tmp_path / "p.npz")
    q = distances.Pairs.load(tmp_path / "p.npz")
    assert _as_dict(q) == _as_dict(p) and q.n == 2
    assert len(p.within(1000).d) == 0
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_distances.py -v`
Expected: FAIL — `ImportError: cannot import name 'distances'`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/distances.py`:
```python
"""Tract-to-tract distances within a limit: Euclidean and along the walk network."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ZERO_LENGTH = 1e-3  # metres; keeps zero-length OSM edges as edges in the sparse graph


@dataclass(frozen=True)
class Pairs:
    """Symmetric, off-diagonal tract pairs (i, j) with distance d (metres)."""

    i: np.ndarray
    j: np.ndarray
    d: np.ndarray
    n: int

    def within(self, bandwidth: float) -> "Pairs":
        m = self.d <= bandwidth
        return Pairs(self.i[m], self.j[m], self.d[m], self.n)

    def save(self, path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, i=self.i, j=self.j, d=self.d, n=self.n)

    @classmethod
    def load(cls, path) -> "Pairs":
        z = np.load(path)
        return cls(z["i"], z["j"], z["d"], int(z["n"]))


def euclidean_pairs(xy: np.ndarray, limit: float) -> Pairs:
    ij = cKDTree(xy).query_pairs(limit, output_type="ndarray")
    d = np.linalg.norm(xy[ij[:, 0]] - xy[ij[:, 1]], axis=1)
    return Pairs(
        np.concatenate([ij[:, 0], ij[:, 1]]),
        np.concatenate([ij[:, 1], ij[:, 0]]),
        np.concatenate([d, d]),
        len(xy),
    )


def graph_to_csr(G) -> tuple[csr_matrix, np.ndarray]:
    """Symmetric sparse matrix of edge lengths (shortest parallel edge; no self-loops)."""
    nodes = np.empty(G.number_of_nodes(), dtype=object)
    nodes[:] = list(G.nodes)
    index = {n: k for k, n in enumerate(nodes)}
    best: dict[tuple[int, int], float] = {}
    for u, v, data in G.edges(data=True):
        a, b = index[u], index[v]
        if a == b:
            continue
        key = (a, b) if a < b else (b, a)
        length = max(float(data["length"]), ZERO_LENGTH)
        if length < best.get(key, np.inf):
            best[key] = length
    keys = np.array(list(best.keys()), dtype=np.int64).reshape(-1, 2)
    vals = np.array(list(best.values()), dtype=float)
    rows = np.concatenate([keys[:, 0], keys[:, 1]])
    cols = np.concatenate([keys[:, 1], keys[:, 0]])
    n = len(nodes)
    return csr_matrix((np.concatenate([vals, vals]), (rows, cols)), shape=(n, n)), nodes


def network_pairs(csr, tract_node_idx: np.ndarray, snap_d: np.ndarray, limit: float, batch: int = 16) -> Pairs:
    """d_ij = snap_i + shortest path(node_i, node_j) + snap_j, kept when <= limit."""
    uniq, inv = np.unique(tract_node_idx, return_inverse=True)
    counts = np.bincount(inv, minlength=len(uniq))
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]])
    by_node = np.argsort(inv, kind="stable")

    def tracts_at(ks: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        c = counts[ks]
        rep = np.repeat(np.arange(len(ks)), c)
        offs = np.arange(c.sum()) - np.repeat(np.cumsum(c) - c, c)
        return by_node[starts[ks][rep] + offs], rep

    I, J, D = [], [], []
    for s in range(0, len(uniq), batch):
        src = uniq[s : s + batch]
        dist = dijkstra(csr, directed=False, indices=src, limit=limit)[:, uniq]
        for a in range(len(src)):
            ks = np.flatnonzero(np.isfinite(dist[a]))
            tj, rep = tracts_at(ks)
            path = dist[a, ks][rep]
            for ti in by_node[starts[s + a] : starts[s + a] + counts[s + a]]:
                d = snap_d[ti] + path + snap_d[tj]
                keep = (d <= limit) & (tj != ti)
                I.append(np.full(keep.sum(), ti))
                J.append(tj[keep])
                D.append(d[keep])
    cat = lambda xs, dt: np.concatenate(xs).astype(dt) if xs else np.empty(0, dt)  # noqa: E731
    return Pairs(cat(I, np.int64), cat(J, np.int64), cat(D, float), len(tract_node_idx))
```

- [ ] **Step 4: Run tests**

Run: `$PY -m pytest tests/test_distances.py -v`
Expected: 6 passed.

- [ ] **Step 5: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 5: Kernel weights and PySAL segregation indices (`netseg/weights.py`, `netseg/measures.py`)

**Files:**
- Create: `network_segregation/netseg/weights.py`, `network_segregation/netseg/measures.py`
- Test: `network_segregation/tests/test_measures.py`

**Interfaces:**
- Consumes: `Pairs` (Task 4), `GROUPS` (Task 2).
- Produces:
  - `kernel_matrix(pairs: Pairs, bandwidth: float, decay: str = "linear") -> scipy.sparse.csr_matrix` (n×n, diagonal 1; `decay ∈ {"linear", "exponential"}`).
  - `to_libpysal(wsp) -> libpysal.weights.W` (only used for tests / cross-validation).
  - `local_environment(gdf, cols, wsp) -> gpd.GeoDataFrame` — replicates `segregation._base._build_local_environment` (`wsp @ counts`, rounded to integers).
  - `compute_indices(gdf, wsp) -> dict[str, float]` with keys `H`, `Dissim_pp`, `Isolation_pp`, `Entropy_pp`.

**Why a local-environment function instead of passing `w=`:** for São Paulo the kernel has ~10⁷ non-zeros; building a dict-based `libpysal.W` (and `segregation` re-building it in `fill_diagonal`) is slow and memory-heavy. We apply the same sparse product segregation applies internally and then call the PySAL estimators on the spatialized counts. `test_matches_segregation_w_path` proves the two routes give identical results.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_measures.py`:
```python
import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

from netseg import distances, measures, weights
from netseg.cities import GROUPS


def _toy(n=8, seed=1):
    rng = np.random.default_rng(seed)
    cells = [(i, j) for i in range(n) for j in range(n)]
    g = gpd.GeoDataFrame(geometry=[box(i * 250, j * 250, (i + 1) * 250, (j + 1) * 250) for i, j in cells], crs="EPSG:31982")
    west = np.array([i < n / 2 for i, _ in cells])
    g["branca"] = np.where(west, rng.integers(200, 300, len(cells)), rng.integers(10, 40, len(cells)))
    g["parda"] = np.where(west, rng.integers(10, 40, len(cells)), rng.integers(150, 250, len(cells)))
    g["preta"] = np.where(west, rng.integers(0, 10, len(cells)), rng.integers(30, 60, len(cells)))
    g["amarela"] = rng.integers(0, 3, len(cells))
    g["indigena"] = rng.integers(0, 2, len(cells))
    g["pop_total"] = g[GROUPS].sum(axis=1)
    g["pp_total"] = g["preta"] + g["parda"]
    pts = g.geometry.centroid
    return g, np.c_[pts.x, pts.y]


def test_kernel_matrix_linear_and_exponential():
    p = distances.Pairs(np.array([0, 1]), np.array([1, 0]), np.array([500.0, 500.0]), 3)
    w = weights.kernel_matrix(p, 2000, "linear").toarray()
    np.testing.assert_allclose(np.diag(w), 1.0)
    assert w[0, 1] == pytest.approx(0.75) and w[0, 2] == 0
    we = weights.kernel_matrix(p, 2000, "exponential").toarray()
    assert we[0, 1] == pytest.approx(np.exp(-0.75))
    with pytest.raises(ValueError):
        weights.kernel_matrix(p, 2000, "gaussian")


def test_matches_segregation_w_path():
    from segregation.multigroup import MultiInfoTheory
    from segregation.singlegroup import Dissim, Entropy, Isolation

    g, xy = _toy()
    wsp = weights.kernel_matrix(distances.euclidean_pairs(xy, 1000), 1000)
    ours = measures.compute_indices(g, wsp)
    W = weights.to_libpysal(wsp)
    assert ours["H"] == pytest.approx(MultiInfoTheory(g, groups=GROUPS, w=W).statistic, abs=1e-12)
    assert ours["Dissim_pp"] == pytest.approx(Dissim(g, "pp_total", "pop_total", w=W).statistic, abs=1e-12)
    assert ours["Isolation_pp"] == pytest.approx(Isolation(g, "pp_total", "pop_total", w=W).statistic, abs=1e-12)
    assert ours["Entropy_pp"] == pytest.approx(Entropy(g, "pp_total", "pop_total", w=W).statistic, abs=1e-12)


def test_identical_weights_identical_indices():
    g, xy = _toy()
    p = distances.euclidean_pairs(xy, 2000)
    a = measures.compute_indices(g, weights.kernel_matrix(p, 2000))
    b = measures.compute_indices(g, weights.kernel_matrix(p, 2000))
    assert a == b


def test_segregated_layout_positive_and_smoothing_lowers_H():
    g, xy = _toy()
    p = distances.euclidean_pairs(xy, 3000)
    h_small = measures.compute_indices(g, weights.kernel_matrix(p, 500))["H"]
    h_big = measures.compute_indices(g, weights.kernel_matrix(p, 3000))["H"]
    assert 0 < h_big < h_small


def test_indices_invariant_to_row_permutation():
    g, xy = _toy()
    perm = np.random.default_rng(0).permutation(len(g))
    g2 = g.iloc[perm].reset_index(drop=True)
    a = measures.compute_indices(g, weights.kernel_matrix(distances.euclidean_pairs(xy, 1500), 1500))
    b = measures.compute_indices(g2, weights.kernel_matrix(distances.euclidean_pairs(xy[perm], 1500), 1500))
    for k in a:
        assert a[k] == pytest.approx(b[k], abs=1e-12)
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_measures.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/weights.py`:
```python
"""Distance-decay kernel weights (same kernel for Euclidean and network distance)."""

from __future__ import annotations

import numpy as np
from libpysal.weights import WSP
from scipy.sparse import coo_matrix

from netseg.distances import Pairs


def kernel_matrix(pairs: Pairs, bandwidth: float, decay: str = "linear"):
    """Sparse n x n weights: linear w = 1 - d/b or exponential w = exp(-3d/b), d <= b; diagonal 1."""
    p = pairs.within(bandwidth)
    if decay == "linear":
        w = 1.0 - p.d / bandwidth
    elif decay == "exponential":
        w = np.exp(-3.0 * p.d / bandwidth)
    else:
        raise ValueError(f"unknown decay {decay!r}")
    keep = w > 0
    diag = np.arange(pairs.n)
    rows = np.concatenate([p.i[keep], diag])
    cols = np.concatenate([p.j[keep], diag])
    vals = np.concatenate([w[keep], np.ones(pairs.n)])
    return coo_matrix((vals, (rows, cols)), shape=(pairs.n, pairs.n)).tocsr()


def to_libpysal(wsp):
    """libpysal W with ids 0..n-1 (for cross-validation against segregation's w= path)."""
    return WSP(wsp).to_W(silence_warnings=True)
```

`network_segregation/netseg/measures.py`:
```python
"""PySAL segregation indices on spatially weighted local environments."""

from __future__ import annotations

import numpy as np
from segregation.multigroup import MultiInfoTheory
from segregation.singlegroup import Dissim, Entropy, Isolation

from netseg.cities import GROUPS


def local_environment(gdf, cols: list[str], wsp):
    """Spatially lagged counts, as in segregation._base._build_local_environment (rounded to integers)."""
    out = gdf[[gdf.geometry.name]].copy()
    lagged = wsp @ gdf[cols].to_numpy(dtype=float)
    for k, c in enumerate(cols):
        out[c] = np.round(lagged[:, k], 0)
    return out


def compute_indices(gdf, wsp) -> dict[str, float]:
    env = local_environment(gdf.reset_index(drop=True), [*GROUPS, "pp_total", "pop_total"], wsp)
    return {
        "H": float(MultiInfoTheory(env, groups=GROUPS).statistic),
        "Dissim_pp": float(Dissim(env, "pp_total", "pop_total").statistic),
        "Isolation_pp": float(Isolation(env, "pp_total", "pop_total").statistic),
        "Entropy_pp": float(Entropy(env, "pp_total", "pop_total").statistic),
    }
```

- [ ] **Step 4: Run tests**

Run: `$PY -m pytest tests/test_measures.py -v`
Expected: 5 passed. If `test_matches_segregation_w_path` fails for a single-group index, check whether that estimator lags only `[group, total]` (it does in 2.5.3) — the rounding must be applied per column exactly as above; do not relax the tolerance.

- [ ] **Step 5: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 6: Street-network topology and configurational fragmentation (`netseg/topology.py`)

**Files:**
- Create: `network_segregation/netseg/topology.py`
- Test: `network_segregation/tests/test_topology.py`

**Interfaces:**
- Consumes: `nx.MultiGraph` (projected, undirected, connected) from `clip_graph`; `graph_to_csr` (Task 4).
- Produces:
  - `network_metrics(G, area_km2: float) -> dict` keys: `n_nodes`, `n_edges`, `intersection_count`, `intersection_density_km`, `street_length_total_km`, `street_density_km`, `street_length_avg`, `streets_per_node_avg`, `prop_dead_end`, `prop_3way`, `prop_4way`, `self_loop_proportion`, `circuity_avg`, `cyclomatic`, `meshedness`, `gamma`.
  - `fragmentation(G, S=500, N=2000, radius=800.0, seed=0, batch=25) -> dict` keys `synergy`, `fragmentation`, `frag_S`, `frag_N`.

Definitions (document in docstrings; they go in the paper's Table 2): intersections = nodes of degree ≥ 3; degree counts parallel edges (osmnx "streets per node" analogue on the undirected graph); circuity = Σ edge length / Σ straight-line endpoint distance (self-loops excluded); cyclomatic = e − v + p; meshedness = (e − v + 1)/(2v − 5); gamma = e / (3(v − 2)); densities per km² of urban footprint.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_topology.py`:
```python
import networkx as nx
import pytest

from netseg import topology
from tests.helpers import grid_graph


def test_grid_metrics_match_closed_form():
    m = 5
    G = grid_graph(m, m)
    out = topology.network_metrics(G, area_km2=0.16)
    v, e = m * m, 2 * m * (m - 1)
    assert out["n_nodes"] == v and out["n_edges"] == e
    assert out["cyclomatic"] == e - v + 1
    assert out["meshedness"] == pytest.approx((e - v + 1) / (2 * v - 5))
    assert out["gamma"] == pytest.approx(e / (3 * (v - 2)))
    assert out["circuity_avg"] == pytest.approx(1.0)
    assert out["prop_4way"] == pytest.approx(9 / 25) and out["prop_3way"] == pytest.approx(12 / 25)
    assert out["prop_dead_end"] == 0
    assert out["intersection_count"] == 21
    assert out["street_length_total_km"] == pytest.approx(4.0)
    assert out["street_density_km"] == pytest.approx(4.0 / 0.16)


def test_tree_has_zero_meshedness_and_dead_ends():
    G = grid_graph(5, 1)
    out = topology.network_metrics(G, area_km2=1.0)
    assert out["meshedness"] == pytest.approx(0.0)
    assert out["prop_dead_end"] == pytest.approx(2 / 5)


def test_meshedness_matches_momepy():
    momepy = pytest.importorskip("momepy")
    G = grid_graph(6, 4)
    ours = topology.network_metrics(G, area_km2=1.0)["meshedness"]
    theirs = momepy.meshedness(nx.Graph(G), radius=None)
    assert ours == pytest.approx(theirs)


def _patchwork():
    """Three 10x10 grids in a row joined by single 1500 m links (same node count as a 30x10 grid)."""
    G = nx.MultiGraph(crs="EPSG:31982")
    for p in range(3):
        part = grid_graph(10, 10, origin=(p * 2400.0, 0.0))
        G.add_nodes_from(((p, n), d) for n, d in part.nodes(data=True))
        G.add_edges_from(((p, u), (p, v), d) for u, v, d in part.edges(data=True))
    G.add_edge((0, (9, 0)), (1, (0, 0)), length=1500.0)
    G.add_edge((1, (9, 0)), (2, (0, 0)), length=1500.0)
    return G


def test_patchwork_more_fragmented_than_grid():
    grid = grid_graph(30, 10)
    patch = _patchwork()
    fg = topology.fragmentation(grid, S=300, N=300, seed=0)
    fp = topology.fragmentation(patch, S=300, N=300, seed=0)
    assert fp["fragmentation"] > fg["fragmentation"]
    assert -1 <= fg["synergy"] <= 1


def test_fragmentation_seeded_reproducible():
    G = grid_graph(12, 12)
    assert topology.fragmentation(G, S=50, N=60, seed=3) == topology.fragmentation(G, S=50, N=60, seed=3)
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_topology.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/topology.py`:
```python
"""Street-network topology metrics (Knaap & Rey 2023, Table 2) and configurational fragmentation."""

from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.sparse import triu
from scipy.sparse.csgraph import dijkstra

from netseg.distances import graph_to_csr


def network_metrics(G: nx.MultiGraph, area_km2: float) -> dict:
    """Size, density, node-type, circuity and cycle-based metrics of an undirected street graph."""
    v, e = G.number_of_nodes(), G.number_of_edges()
    p = nx.number_connected_components(G)
    deg = np.array([d for _, d in G.degree()])
    lengths, straight, loops = [], [], 0
    for a, b, data in G.edges(data=True):
        lengths.append(float(data["length"]))
        if a == b:
            loops += 1
            continue
        straight.append(np.hypot(G.nodes[a]["x"] - G.nodes[b]["x"], G.nodes[a]["y"] - G.nodes[b]["y"]))
    lengths = np.asarray(lengths)
    nonloop_len = sum(float(d["length"]) for a, b, d in G.edges(data=True) if a != b)
    inter = int((deg >= 3).sum())
    total_km = lengths.sum() / 1000.0
    return {
        "n_nodes": v,
        "n_edges": e,
        "intersection_count": inter,
        "intersection_density_km": inter / area_km2,
        "street_length_total_km": total_km,
        "street_density_km": total_km / area_km2,
        "street_length_avg": float(lengths.mean()),
        "streets_per_node_avg": float(deg.mean()),
        "prop_dead_end": float((deg == 1).mean()),
        "prop_3way": float((deg == 3).mean()),
        "prop_4way": float((deg == 4).mean()),
        "self_loop_proportion": loops / e,
        "circuity_avg": nonloop_len / float(np.sum(straight)),
        "cyclomatic": e - v + p,
        "meshedness": (e - v + 1) / (2 * v - 5),
        "gamma": e / (3 * (v - 2)),
    }


def fragmentation(G: nx.MultiGraph, S: int = 500, N: int = 2000, radius: float = 800.0, seed: int = 0, batch: int = 25) -> dict:
    """Metric analogue of space-syntax synergy (Medeiros 2013).

    L_i: street length with both endpoints within ``radius`` of node i (local reach).
    G_i: 1 / mean network distance from i to S random target nodes (global closeness).
    synergy = Pearson corr(log L_i, G_i) over N random origin nodes; fragmentation = 1 - synergy.
    """
    csr, _ = graph_to_csr(G)
    n = csr.shape[0]
    rng = np.random.default_rng(seed)
    origins = np.sort(rng.choice(n, size=min(N, n), replace=False))
    targets = np.sort(rng.choice(n, size=min(S, n), replace=False))

    up = triu(csr, k=1).tocoo()
    eu, ev, el = up.row, up.col, up.data

    local = np.empty(len(origins))
    for s in range(0, len(origins), batch):
        dist = dijkstra(csr, directed=False, indices=origins[s : s + batch], limit=radius)
        for a in range(dist.shape[0]):
            inside = np.isfinite(dist[a])
            local[s + a] = el[inside[eu] & inside[ev]].sum()

    total = np.zeros(len(origins))
    for s in range(0, len(targets), batch):
        dist = dijkstra(csr, directed=False, indices=targets[s : s + batch])
        total += dist[:, origins].sum(axis=0)
    closeness = len(targets) / total

    synergy = float(np.corrcoef(np.log(local + 1.0), closeness)[0, 1])
    return {"synergy": synergy, "fragmentation": 1.0 - synergy, "frag_S": int(len(targets)), "frag_N": int(len(origins))}
```

- [ ] **Step 4: Run tests**

Run: `$PY -m pytest tests/test_topology.py -v`
Expected: 6 passed. If `test_patchwork_more_fragmented_than_grid` fails, print both `synergy` values and inspect before changing anything: the expected mechanism is that local reach is similar across the three patches while closeness differs by patch; do not tune the test to pass without understanding why.

- [ ] **Step 5: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 7: Per-city pipeline and the 91-city run (`netseg/pipeline.py`, `scripts/run_all.py`)

**Files:**
- Create: `network_segregation/netseg/pipeline.py`, `network_segregation/scripts/run_all.py`
- Test: `network_segregation/tests/test_pipeline.py`

**Interfaces:**
- Consumes: everything from Tasks 2–6.
- Produces:
  - `SPECS: list[tuple[str, float, str]] = [("main", 2000, "linear"), ("b1000", 1000, "linear"), ("b3000", 3000, "linear"), ("exp2000", 2000, "exponential")]`, `LIMIT = 3000.0`, `BUFFER_M = 2000.0`.
  - `run_city(cod: str, name: str, race, data_dir: Path, *, loader=load_urban_tracts, downloader=download_walk_graph, frag_kwargs=None) -> dict` with keys `"indices"` (list of row dicts: `COD_MUNICIPIO, NM_MUN, spec, bandwidth, decay, index, euc, net`) and `"city"` (dict: `COD_MUNICIPIO, NM_MUN`, tract stats, `area_km2`, `median_snap_m`, `n_snap_gt500`, `graph_nodes`, `graph_downloaded`, `osmnx_version`, all `network_metrics` + `fragmentation` keys). Cached at `data_dir/results/<cod>.json`.
  - `run_all(cities_df, race, data_dir, out_dir, **kw) -> tuple[pd.DataFrame, pd.DataFrame]` → writes `out_dir/indices_long.parquet`, `out_dir/cities.parquet`, and `out_dir/failures.csv` (columns `COD_MUNICIPIO, NM_MUN, error`; always written, possibly empty).

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_pipeline.py`:
```python
import json

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import box

from netseg import pipeline
from netseg.cities import GROUPS
from tests.helpers import grid_graph

CRS = "EPSG:31982"
X0, Y0 = 480_000.0, 6_676_000.0  # near Porto Alegre, UTM 22S


def fake_loader(cod, race, **_):
    cells = [(i, j) for i in range(6) for j in range(6)]
    g = gpd.GeoDataFrame(
        {"CD_SETOR": [f"{cod}{k:08d}" for k in range(len(cells))]},
        geometry=[box(X0 + i * 300, Y0 + j * 300, X0 + (i + 1) * 300, Y0 + (j + 1) * 300) for i, j in cells],
        crs=CRS,
    )
    west = np.array([i < 3 for i, _ in cells])
    g["branca"] = np.where(west, 250, 20)
    g["parda"] = np.where(west, 20, 200)
    g["preta"] = np.where(west, 5, 40)
    g["amarela"] = 1
    g["indigena"] = 0
    g["pop_total"] = g[GROUPS].sum(axis=1)
    g["pp_total"] = g["preta"] + g["parda"]
    return g, {"n_tracts_all": 36, "n_tracts_urban": 36, "pop_all": int(g.pop_total.sum()), "pop_urban": int(g.pop_total.sum())}


def fake_downloader(polygon_wgs84, cache_path):
    """Lat/lon lattice covering the fake city, 100 m spacing, with a 'wall' of removed edges."""
    grid = grid_graph(22, 22, spacing=100.0, origin=(X0 - 150, Y0 - 150))
    for j in range(0, 18):  # barrier between west and east halves except a gap at the top
        grid.remove_edges_from([((10, j), (11, j))])
    to_ll = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
    G = nx.MultiDiGraph(crs="EPSG:4326")
    for n, d in grid.nodes(data=True):
        lon, lat = to_ll.transform(d["x"], d["y"])
        G.add_node(n, x=lon, y=lat)
    for k, (u, v, d) in enumerate(grid.edges(data=True)):
        G.add_edge(u, v, length=d["length"], osmid=k)  # osmnx.to_undirected compares osmid
        G.add_edge(v, u, length=d["length"], osmid=k)
    return G


def test_run_city_end_to_end(tmp_path):
    out = pipeline.run_city("4314902", "Toy", None, tmp_path, loader=fake_loader, downloader=fake_downloader,
                            frag_kwargs={"S": 50, "N": 50})
    idx = pd.DataFrame(out["indices"])
    assert set(idx["spec"]) == {"main", "b1000", "b3000", "exp2000"}
    assert set(idx["index"]) == {"H", "Dissim_pp", "Isolation_pp", "Entropy_pp"}
    main_h = idx[(idx.spec == "main") & (idx["index"] == "H")].iloc[0]
    assert main_h.net > main_h.euc > 0  # the barrier makes network segregation higher
    assert out["city"]["meshedness"] > 0 and 0 <= out["city"]["fragmentation"] <= 2
    assert (tmp_path / "results" / "4314902.json").exists()


def test_run_city_reports_snap_diagnostics(tmp_path):
    out = pipeline.run_city("4314902", "Toy", None, tmp_path, loader=fake_loader, downloader=fake_downloader,
                            frag_kwargs={"S": 20, "N": 20})
    assert out["city"]["median_snap_m"] < 100
    assert out["city"]["n_snap_gt500"] == 0


def test_run_city_uses_cached_result(tmp_path):
    (tmp_path / "results").mkdir()
    cached = {"indices": [{"x": 1}], "city": {"COD_MUNICIPIO": "1"}}
    (tmp_path / "results" / "1.json").write_text(json.dumps(cached))

    def boom(*a, **k):
        raise AssertionError("must not be called")

    assert pipeline.run_city("1", "C", None, tmp_path, loader=boom, downloader=boom) == cached


def test_run_all_records_failure_and_continues(tmp_path):
    cities = pd.DataFrame({"COD_MUNICIPIO": ["4314902", "9999999"], "NM_MUN": ["Toy", "Bad"], "UF": ["RS", "XX"], "pop_total": [1, 1]})

    def loader(cod, race, **kw):
        if cod == "9999999":
            raise ValueError("no populated urban tracts for municipality '9999999'")
        return fake_loader(cod, race)

    idx, cty = pipeline.run_all(cities, None, tmp_path / "data", tmp_path / "out", loader=loader,
                                downloader=fake_downloader, frag_kwargs={"S": 20, "N": 20})
    fails = pd.read_csv(tmp_path / "out" / "failures.csv", dtype=str)
    assert list(fails["COD_MUNICIPIO"]) == ["9999999"] and "no populated" in fails.loc[0, "error"]
    assert list(cty["COD_MUNICIPIO"]) == ["4314902"]
    assert (tmp_path / "out" / "indices_long.parquet").exists()
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_pipeline.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/pipeline.py`:
```python
"""Per-city orchestration with caching and failure capture."""

from __future__ import annotations

import datetime as dt
import json
import traceback
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd

from netseg.cities import load_urban_tracts
from netseg.distances import Pairs, euclidean_pairs, graph_to_csr, network_pairs
from netseg.measures import compute_indices
from netseg.network import clip_graph, download_walk_graph, footprint, prepare_graph, snap_points
from netseg.topology import fragmentation, network_metrics
from netseg.weights import kernel_matrix

SPECS = [("main", 2000.0, "linear"), ("b1000", 1000.0, "linear"), ("b3000", 3000.0, "linear"), ("exp2000", 2000.0, "exponential")]
LIMIT = 3000.0
BUFFER_M = 2000.0
SNAP_FLAG_M = 500.0


def run_city(cod, name, race, data_dir, *, loader=load_urban_tracts, downloader=download_walk_graph, frag_kwargs=None) -> dict:
    data_dir = Path(data_dir)
    result_path = data_dir / "results" / f"{cod}.json"
    if result_path.exists():
        return json.loads(result_path.read_text())

    gdf, tract_stats = loader(cod, race)
    pts = gdf.geometry.representative_point()
    xy = np.c_[pts.x, pts.y]
    fp = footprint(gdf)
    poly_wgs84 = gpd.GeoSeries([fp.buffer(BUFFER_M)], crs=gdf.crs).to_crs(4326).iloc[0]

    graph_path = data_dir / "osm" / f"{cod}.graphml"
    G = prepare_graph(downloader(poly_wgs84, graph_path), gdf.crs)
    csr, nodes = graph_to_csr(G)
    node_ids, snap = snap_points(G, xy)
    index = {n: k for k, n in enumerate(nodes)}
    tract_nodes = np.array([index[n] for n in node_ids])

    pairs_path = data_dir / "pairs"
    pe_file, pn_file = pairs_path / f"{cod}_euc.npz", pairs_path / f"{cod}_net.npz"
    if pe_file.exists() and pn_file.exists():
        pe, pn = Pairs.load(pe_file), Pairs.load(pn_file)
    else:
        pe, pn = euclidean_pairs(xy, LIMIT), network_pairs(csr, tract_nodes, snap, LIMIT)
        pe.save(pe_file)
        pn.save(pn_file)

    rows = []
    for spec, bw, decay in SPECS:
        ie = compute_indices(gdf, kernel_matrix(pe, bw, decay))
        inet = compute_indices(gdf, kernel_matrix(pn, bw, decay))
        for k in ie:
            rows.append({"COD_MUNICIPIO": cod, "NM_MUN": name, "spec": spec, "bandwidth": bw, "decay": decay,
                         "index": k, "euc": ie[k], "net": inet[k]})

    area_km2 = fp.area / 1e6
    Gc = clip_graph(G, fp)
    city = {
        "COD_MUNICIPIO": cod,
        "NM_MUN": name,
        **tract_stats,
        "area_km2": area_km2,
        "median_snap_m": float(np.median(snap)),
        "n_snap_gt500": int((snap > SNAP_FLAG_M).sum()),
        "graph_nodes": int(G.number_of_nodes()),
        "graph_downloaded": (dt.datetime.fromtimestamp(graph_path.stat().st_mtime).date().isoformat()
                             if graph_path.exists() else None),
        "osmnx_version": ox.__version__,
        **network_metrics(Gc, area_km2),
        **fragmentation(Gc, **(frag_kwargs or {})),
    }
    out = {"indices": rows, "city": city}
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(out, default=float))
    return out


def run_all(cities_df, race, data_dir, out_dir, **kw):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    idx_rows, city_rows, fails = [], [], []
    for rec in cities_df.itertuples(index=False):
        try:
            res = run_city(rec.COD_MUNICIPIO, rec.NM_MUN, race, data_dir, **kw)
            idx_rows += res["indices"]
            city_rows.append(res["city"])
            print(f"ok   {rec.COD_MUNICIPIO} {rec.NM_MUN}", flush=True)
        except Exception as exc:  # one city must not stop the run
            fails.append({"COD_MUNICIPIO": rec.COD_MUNICIPIO, "NM_MUN": rec.NM_MUN, "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAIL {rec.COD_MUNICIPIO} {rec.NM_MUN}\n{traceback.format_exc()}", flush=True)
    idx = pd.DataFrame(idx_rows)
    cty = pd.DataFrame(city_rows)
    idx.to_parquet(out_dir / "indices_long.parquet", index=False)
    cty.to_parquet(out_dir / "cities.parquet", index=False)
    pd.DataFrame(fails, columns=["COD_MUNICIPIO", "NM_MUN", "error"]).to_csv(out_dir / "failures.csv", index=False)
    return idx, cty
```

`network_segregation/scripts/run_all.py`:
```python
"""Run the Euclidean-vs-network pipeline for the 91 cities (resumable)."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from netseg.cities import load_race_counts, select_cities  # noqa: E402
from netseg.pipeline import run_all  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="COD_MUNICIPIO codes to run")
    ap.add_argument("--smallest", type=int, help="run only the N smallest cities (smoke test)")
    a = ap.parse_args()
    cities = select_cities()
    if a.only:
        cities = cities[cities["COD_MUNICIPIO"].isin(a.only)]
    if a.smallest:
        cities = cities.tail(a.smallest)
    run_all(cities, load_race_counts(), ROOT / "data", ROOT / "outputs")
```

- [ ] **Step 4: Run tests**

Run: `$PY -m pytest tests/test_pipeline.py -v`
Expected: 4 passed.

- [ ] **Step 5: Real smoke test on the smallest city**

Run: `$PY scripts/run_all.py --smallest 1`
Expected: `ok <cod> <name>`; `outputs/failures.csv` has only a header; `outputs/indices_long.parquet` has 16 rows (4 specs × 4 indices). Inspect: `H` main `net` ≥ `euc` is expected but not required; report the values.

- [ ] **Step 6: Full run (long; run in background)**

Run: `$PY scripts/run_all.py` (background; resumable — re-running skips finished cities).
Expected: 91 `ok` lines or documented failures. Then check:
```bash
$PY -c "
import pandas as pd
c = pd.read_parquet('outputs/cities.parquet'); i = pd.read_parquet('outputs/indices_long.parquet')
f = pd.read_csv('outputs/failures.csv'); print(len(c), 'cities;', len(f), 'failures'); print(f)
m = i[(i.spec=='main') & (i['index']=='H')]; print(m[['euc','net']].describe()); assert m[['euc','net']].notna().all().all()
"
```
Re-run failed cities with `--only <cod>` after diagnosing (e.g. Overpass timeouts → re-run; persistent failures stay in `failures.csv` and are reported in the paper).

- [ ] **Step 7: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths (`data/` is git-ignored by the folder's `.gitignore`).

---

### Task 8: Fragmentation stability check (`scripts/check_fragmentation_stability.py`)

**Files:**
- Create: `network_segregation/scripts/check_fragmentation_stability.py`

**Interfaces:**
- Consumes: cached graphs `data/osm/<cod>.graphml`, `load_urban_tracts`, `prepare_graph`, `clip_graph`, `footprint`, `fragmentation`.
- Produces: `outputs/tables/fragmentation_stability.csv` (columns `COD_MUNICIPIO, S, N, fragmentation`).

- [ ] **Step 1: Implement**

```python
"""Is F stable when S and N are doubled? (spec §5.3: |ΔF| < 0.02)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import osmnx as ox  # noqa: E402
import pandas as pd  # noqa: E402

from netseg.cities import load_race_counts, load_urban_tracts  # noqa: E402
from netseg.network import clip_graph, footprint, prepare_graph  # noqa: E402
from netseg.topology import fragmentation  # noqa: E402

CITIES = {"4314902": "Porto Alegre", "4106902": "Curitiba", "2927408": "Salvador"}

if __name__ == "__main__":
    race = load_race_counts()
    rows = []
    for cod in CITIES:
        gdf, _ = load_urban_tracts(cod, race)
        G = prepare_graph(ox.load_graphml(ROOT / "data" / "osm" / f"{cod}.graphml"), gdf.crs)
        Gc = clip_graph(G, footprint(gdf))
        for S, N in [(500, 2000), (1000, 4000)]:
            rows.append({"COD_MUNICIPIO": cod, "S": S, "N": N, **fragmentation(Gc, S=S, N=N, seed=0)})
    df = pd.DataFrame(rows)
    (ROOT / "outputs" / "tables").mkdir(parents=True, exist_ok=True)
    df[["COD_MUNICIPIO", "S", "N", "fragmentation"]].to_csv(ROOT / "outputs" / "tables" / "fragmentation_stability.csv", index=False)
    spread = df.groupby("COD_MUNICIPIO")["fragmentation"].agg(lambda s: s.max() - s.min())
    print(spread)
    print("STABLE" if (spread < 0.02).all() else "UNSTABLE: raise S/N defaults in netseg/topology.py and pipeline, then re-run")
```

- [ ] **Step 2: Run**

Run: `$PY scripts/check_fragmentation_stability.py`
Expected: `STABLE`. If `UNSTABLE`, stop and report to the author (changing S/N requires recomputing all cities: delete `data/results/*.json` only — pairs caches stay valid).

- [ ] **Step 3: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 9: PySAL native network cross-check (`scripts/run_crosscheck_pandana.py`)

**Files:**
- Create: `network_segregation/scripts/run_crosscheck_pandana.py`

**Interfaces:**
- Consumes: cached graphs; `load_urban_tracts`; `segregation.multigroup.MultiInfoTheory(..., network=, distance=2000, decay="linear")`.
- Produces: `outputs/tables/crosscheck_pandana.csv` (`COD_MUNICIPIO, H_net_ours, H_net_pandana`).

Note for the paper: segregation's `network=` route aggregates population at the nearest network node (pandana) and ignores snap distance, so values are expected to be close, not identical.

- [ ] **Step 1: Create the optional env**

Run: `C:/Users/renan/anaconda3/Scripts/conda.exe env create -f environment-crosscheck.yml`
If this fails (pandana has no working Windows build for the solver), **skip the rest of this task** and write `outputs/tables/crosscheck_pandana.csv` with a single line `status\npandana unavailable on this platform` — the manuscript then states the cross-check was not run (spec §5.2).

- [ ] **Step 2: Implement**

```python
"""Cross-check H_net against segregation's native pandana route (3 cities)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import osmnx as ox  # noqa: E402
import pandana  # noqa: E402
import pandas as pd  # noqa: E402
from segregation.multigroup import MultiInfoTheory  # noqa: E402

from netseg.cities import GROUPS, load_race_counts, load_urban_tracts  # noqa: E402
from netseg.network import prepare_graph  # noqa: E402

CITIES = ["4314902", "4106902", "2927408"]

if __name__ == "__main__":
    race = load_race_counts()
    main = pd.read_parquet(ROOT / "outputs" / "indices_long.parquet")
    main = main[(main.spec == "main") & (main["index"] == "H")].set_index("COD_MUNICIPIO")
    rows = []
    for cod in CITIES:
        gdf, _ = load_urban_tracts(cod, race)
        G = prepare_graph(ox.load_graphml(ROOT / "data" / "osm" / f"{cod}.graphml"), gdf.crs)
        nodes, edges = ox.convert.graph_to_gdfs(G)
        edges = edges.reset_index()
        net = pandana.Network(nodes["x"], nodes["y"], edges["u"], edges["v"], edges[["length"]], twoway=True)
        h = MultiInfoTheory(gdf, groups=GROUPS, network=net, distance=2000, decay="linear").statistic
        rows.append({"COD_MUNICIPIO": cod, "H_net_ours": main.loc[cod, "net"], "H_net_pandana": h})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "outputs" / "tables" / "crosscheck_pandana.csv", index=False)
    print(df)
```

- [ ] **Step 3: Run**

Run: `C:/Users/renan/anaconda3/envs/netseg-pandana/python.exe scripts/run_crosscheck_pandana.py`
Expected: three rows; report the absolute differences to the author (no pass/fail threshold — this is descriptive).

- [ ] **Step 4: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 10: RQ2 regression models (`netseg/models.py`, `scripts/fit_models.py`)

**Files:**
- Create: `network_segregation/netseg/models.py`, `network_segregation/scripts/fit_models.py`
- Test: `network_segregation/tests/test_models.py`

**Interfaces:**
- Consumes: `outputs/indices_long.parquet`, `outputs/cities.parquet`.
- Produces:
  - `analysis_frame(indices: pd.DataFrame, cities: pd.DataFrame, spec="main", index="H") -> pd.DataFrame` — one row per city with `H_euc`, `H_net`, `dH`, `pdH` (percent), and transformed regressors `z_circuity`, `z_meshedness`, `z_dead_end`, `z_fragmentation`, `z_H_euc`, `log_intersection_density`, `log_cyclomatic`, `log_pop_density`.
  - `FORMULA_KR = "{dv} ~ log_intersection_density + z_circuity + z_meshedness + log_cyclomatic + z_dead_end + log_pop_density + z_H_euc + log_cyclomatic:z_circuity"`, `FORMULA_FULL = FORMULA_KR + " + z_fragmentation"`.
  - `fit(df, dv: str, full: bool) -> statsmodels RegressionResults` (OLS, `cov_type="HC3"`).
  - `vif_table(df) -> pd.DataFrame` (`variable`, `vif`) for the full model's main-effect regressors.
- Script writes `outputs/tables/models.tex` (4 columns: dH K&R, dH +F, pdH K&R, pdH +F), `outputs/tables/models_coefs.csv`, `outputs/tables/vif.csv`, `outputs/analysis_frame.parquet`.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_models.py`:
```python
import numpy as np
import pandas as pd
import pytest

from netseg import models


def _fake(n=91, seed=0):
    rng = np.random.default_rng(seed)
    cities = pd.DataFrame({
        "COD_MUNICIPIO": [str(k) for k in range(n)],
        "intersection_density_km": rng.lognormal(4, 0.4, n),
        "circuity_avg": rng.normal(1.08, 0.03, n),
        "meshedness": rng.normal(0.2, 0.05, n),
        "cyclomatic": rng.lognormal(9, 1, n),
        "prop_dead_end": rng.normal(0.15, 0.04, n),
        "fragmentation": rng.normal(0.5, 0.1, n),
        "pop_urban": rng.lognormal(13, 0.7, n),
        "area_km2": rng.lognormal(5, 0.6, n),
    })
    euc = rng.uniform(0.05, 0.2, n)
    z = (cities["fragmentation"] - cities["fragmentation"].mean()) / cities["fragmentation"].std()
    net = euc + 0.02 + 0.01 * z + rng.normal(0, 0.002, n)
    idx = pd.DataFrame({"COD_MUNICIPIO": cities["COD_MUNICIPIO"], "spec": "main", "index": "H", "euc": euc, "net": net})
    return idx, cities


def test_analysis_frame_columns_and_gap():
    idx, cities = _fake()
    df = models.analysis_frame(idx, cities)
    assert len(df) == 91
    np.testing.assert_allclose(df["dH"], df["H_net"] - df["H_euc"])
    np.testing.assert_allclose(df["pdH"], 100 * df["dH"] / df["H_euc"])
    assert abs(df["z_fragmentation"].mean()) < 1e-12 and df["z_fragmentation"].std() == pytest.approx(1)


def test_fit_recovers_fragmentation_effect():
    idx, cities = _fake()
    res = models.fit(models.analysis_frame(idx, cities), "dH", full=True)
    assert res.cov_type == "HC3"
    assert res.params["z_fragmentation"] == pytest.approx(0.01, abs=0.002)
    assert res.pvalues["z_fragmentation"] < 0.01
    kr = models.fit(models.analysis_frame(idx, cities), "dH", full=False)
    assert "z_fragmentation" not in kr.params


def test_vif_table():
    idx, cities = _fake()
    v = models.vif_table(models.analysis_frame(idx, cities))
    assert set(v.columns) == {"variable", "vif"} and (v["vif"] >= 1).all()
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_models.py -v`
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/models.py`:
```python
"""RQ2: city-level OLS of the Euclidean-network gap on street-network topology."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

FORMULA_KR = ("{dv} ~ log_intersection_density + z_circuity + z_meshedness + log_cyclomatic + z_dead_end"
              " + log_pop_density + z_H_euc + log_cyclomatic:z_circuity")
FORMULA_FULL = FORMULA_KR + " + z_fragmentation"
MAIN_EFFECTS = ["log_intersection_density", "z_circuity", "z_meshedness", "log_cyclomatic", "z_dead_end",
                "log_pop_density", "z_H_euc", "z_fragmentation"]


def _z(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def analysis_frame(indices: pd.DataFrame, cities: pd.DataFrame, spec: str = "main", index: str = "H") -> pd.DataFrame:
    sel = indices[(indices["spec"] == spec) & (indices["index"] == index)][["COD_MUNICIPIO", "euc", "net"]]
    df = cities.merge(sel.rename(columns={"euc": "H_euc", "net": "H_net"}), on="COD_MUNICIPIO", how="inner")
    df["dH"] = df["H_net"] - df["H_euc"]
    df["pdH"] = 100.0 * df["dH"] / df["H_euc"]
    df["z_circuity"] = _z(df["circuity_avg"])
    df["z_meshedness"] = _z(df["meshedness"])
    df["z_dead_end"] = _z(df["prop_dead_end"])
    df["z_fragmentation"] = _z(df["fragmentation"])
    df["z_H_euc"] = _z(df["H_euc"])
    df["log_intersection_density"] = np.log(df["intersection_density_km"])
    df["log_cyclomatic"] = np.log(df["cyclomatic"])
    df["log_pop_density"] = np.log(df["pop_urban"] / df["area_km2"])
    return df.reset_index(drop=True)


def fit(df: pd.DataFrame, dv: str, full: bool):
    formula = (FORMULA_FULL if full else FORMULA_KR).format(dv=dv)
    return smf.ols(formula, data=df).fit(cov_type="HC3")


def vif_table(df: pd.DataFrame) -> pd.DataFrame:
    X = df[MAIN_EFFECTS].assign(const=1.0).to_numpy()
    return pd.DataFrame({"variable": MAIN_EFFECTS,
                         "vif": [variance_inflation_factor(X, k) for k in range(len(MAIN_EFFECTS))]})
```

`network_segregation/scripts/fit_models.py`:
```python
"""Fit the four RQ2 models and write LaTeX/CSV tables."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from statsmodels.iolib.summary2 import summary_col  # noqa: E402

from netseg.models import analysis_frame, fit, vif_table  # noqa: E402

if __name__ == "__main__":
    out = ROOT / "outputs"
    (out / "tables").mkdir(parents=True, exist_ok=True)
    df = analysis_frame(pd.read_parquet(out / "indices_long.parquet"), pd.read_parquet(out / "cities.parquet"))
    df.to_parquet(out / "analysis_frame.parquet", index=False)
    fits = {"$\\Delta H$ (K\\&R)": fit(df, "dH", False), "$\\Delta H$ (+F)": fit(df, "dH", True),
            "\\%$\\Delta H$ (K\\&R)": fit(df, "pdH", False), "\\%$\\Delta H$ (+F)": fit(df, "pdH", True)}
    table = summary_col(list(fits.values()), model_names=list(fits.keys()), stars=True,
                        info_dict={"N": lambda r: f"{int(r.nobs)}", "Adj. R2": lambda r: f"{r.rsquared_adj:.3f}"})
    (out / "tables" / "models.tex").write_text(table.as_latex())
    pd.concat({k: pd.DataFrame({"coef": r.params, "se": r.bse, "p": r.pvalues}) for k, r in fits.items()}).to_csv(
        out / "tables" / "models_coefs.csv")
    vif_table(df).to_csv(out / "tables" / "vif.csv", index=False)
    print(table)
```

- [ ] **Step 4: Run tests, then the script**

Run: `$PY -m pytest tests/test_models.py -v` → Expected: 3 passed.
Run: `$PY scripts/fit_models.py` → Expected: a 4-column table printed; `outputs/tables/models.tex` exists. Report any VIF > 10 to the author before writing the Results section.

- [ ] **Step 5: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 11: Tables and LaTeX number macros (`netseg/report.py`, `scripts/make_tables.py`)

**Files:**
- Create: `network_segregation/netseg/report.py`, `network_segregation/scripts/make_tables.py`
- Test: `network_segregation/tests/test_report.py`

**Interfaces:**
- Consumes: `outputs/indices_long.parquet`, `outputs/cities.parquet`, `outputs/failures.csv`.
- Produces:
  - `gap_table(indices, spec="main", index="H") -> pd.DataFrame` — rows `H_euc`, `H_net`, `dH`, `pdH`; columns `count, mean, std, min, 25%, 50%, 75%, max` (K&R Table 1 analogue).
  - `rank_comparison(indices, spec="main", index="H", top=15) -> pd.DataFrame` — `NM_MUN, rank_euc, rank_net, rank_change`, sorted by `rank_euc`, first `top` rows by either ranking (union).
  - `robustness_table(indices) -> pd.DataFrame` — one row per `(spec, index)`: `mean_dH`, `mean_pdH`, `share_positive`, `pearson`, `spearman`.
  - `write_macros(values: dict[str, float|int|str], path)` — writes `\newcommand{\<name>}{<value>}` lines (names letters only).
- Script writes `outputs/tables/{gap,ranks,robustness,topology_desc}.tex` and `outputs/tables/numbers.tex`.

- [ ] **Step 1: Write failing tests**

`network_segregation/tests/test_report.py`:
```python
import numpy as np
import pandas as pd
import pytest

from netseg import report


def _idx():
    rows = []
    for k, (e, n) in enumerate([(0.10, 0.12), (0.20, 0.21), (0.15, 0.20), (0.05, 0.049)]):
        rows.append({"COD_MUNICIPIO": str(k), "NM_MUN": f"C{k}", "spec": "main", "index": "H", "euc": e, "net": n})
        rows.append({"COD_MUNICIPIO": str(k), "NM_MUN": f"C{k}", "spec": "b1000", "index": "H", "euc": e, "net": n})
    return pd.DataFrame(rows)


def test_gap_table():
    t = report.gap_table(_idx())
    assert list(t.index) == ["H_euc", "H_net", "dH", "pdH"]
    assert t.loc["dH", "count"] == 4
    assert t.loc["dH", "min"] == pytest.approx(-0.001)


def test_rank_comparison():
    r = report.rank_comparison(_idx(), top=2)
    c2 = r.set_index("NM_MUN").loc["C2"]
    assert c2.rank_euc == 2 and c2.rank_net == 2
    assert set(r["NM_MUN"]) == {"C1", "C2"}


def test_robustness_table():
    t = report.robustness_table(_idx())
    row = t.set_index(["spec", "index"]).loc[("main", "H")]
    assert row.share_positive == pytest.approx(0.75)
    assert -1 <= row.spearman <= 1


def test_write_macros(tmp_path):
    p = tmp_path / "n.tex"
    report.write_macros({"nCities": 91, "meanPdH": "12.3"}, p)
    assert p.read_text() == "\\newcommand{\\nCities}{91}\n\\newcommand{\\meanPdH}{12.3}\n"
    with pytest.raises(ValueError):
        report.write_macros({"bad_name1": 1}, p)
```

- [ ] **Step 2: Run to verify failure**

Run: `$PY -m pytest tests/test_report.py -v` → Expected: FAIL — `ImportError`.

- [ ] **Step 3: Implement**

`network_segregation/netseg/report.py`:
```python
"""Descriptive tables for RQ1 and LaTeX macros for numbers quoted in the text."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def _sel(indices, spec, index):
    d = indices[(indices["spec"] == spec) & (indices["index"] == index)].copy()
    d["dH"] = d["net"] - d["euc"]
    d["pdH"] = 100.0 * d["dH"] / d["euc"]
    return d


def gap_table(indices, spec="main", index="H") -> pd.DataFrame:
    d = _sel(indices, spec, index).rename(columns={"euc": "H_euc", "net": "H_net"})
    return d[["H_euc", "H_net", "dH", "pdH"]].describe().T


def rank_comparison(indices, spec="main", index="H", top=15) -> pd.DataFrame:
    d = _sel(indices, spec, index)
    d["rank_euc"] = d["euc"].rank(ascending=False, method="min").astype(int)
    d["rank_net"] = d["net"].rank(ascending=False, method="min").astype(int)
    d["rank_change"] = d["rank_euc"] - d["rank_net"]
    keep = (d["rank_euc"] <= top) | (d["rank_net"] <= top)
    return d.loc[keep, ["NM_MUN", "rank_euc", "rank_net", "rank_change"]].sort_values("rank_euc").reset_index(drop=True)


def robustness_table(indices) -> pd.DataFrame:
    rows = []
    for (spec, index), g in indices.groupby(["spec", "index"], sort=False):
        d = _sel(g, spec, index)
        rows.append({"spec": spec, "index": index, "mean_dH": d["dH"].mean(), "mean_pdH": d["pdH"].mean(),
                     "share_positive": (d["dH"] > 0).mean(), "pearson": d["euc"].corr(d["net"]),
                     "spearman": d["euc"].corr(d["net"], method="spearman")})
    return pd.DataFrame(rows)


def write_macros(values: dict, path) -> None:
    lines = []
    for name, val in values.items():
        if not re.fullmatch(r"[A-Za-z]+", name):
            raise ValueError(f"LaTeX macro names must be letters only: {name!r}")
        lines.append(f"\\newcommand{{\\{name}}}{{{val}}}\n")
    Path(path).write_text("".join(lines))
```

`network_segregation/scripts/make_tables.py`:
```python
"""Write RQ1 tables and numbers.tex (every number quoted in the manuscript comes from here)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from netseg.report import gap_table, rank_comparison, robustness_table, write_macros  # noqa: E402

TOPO_COLS = ["intersection_density_km", "street_density_km", "street_length_avg", "streets_per_node_avg",
             "circuity_avg", "prop_dead_end", "prop_3way", "prop_4way", "cyclomatic", "meshedness", "gamma",
             "fragmentation"]

if __name__ == "__main__":
    out = ROOT / "outputs"
    t = out / "tables"
    t.mkdir(parents=True, exist_ok=True)
    idx = pd.read_parquet(out / "indices_long.parquet")
    cty = pd.read_parquet(out / "cities.parquet")
    fails = pd.read_csv(out / "failures.csv")

    gap = gap_table(idx)
    gap.to_latex(t / "gap.tex", float_format="%.3f")
    ranks = rank_comparison(idx)
    ranks.to_latex(t / "ranks.tex", index=False)
    rob = robustness_table(idx)
    rob.to_latex(t / "robustness.tex", index=False, float_format="%.3f")
    cty[TOPO_COLS].describe().T.to_latex(t / "topology_desc.tex", float_format="%.3f")

    main = rob.set_index(["spec", "index"]).loc[("main", "H")]
    write_macros({
        "nCities": len(cty),
        "nFailed": len(fails),
        "nTractsUrban": f"{int(cty['n_tracts_urban'].sum()):,}",
        "sharePopUrban": f"{100 * cty['pop_urban'].sum() / cty['pop_all'].sum():.1f}",
        "meanHeuc": f"{gap.loc['H_euc', 'mean']:.3f}",
        "meanHnet": f"{gap.loc['H_net', 'mean']:.3f}",
        "meanDH": f"{gap.loc['dH', 'mean']:.3f}",
        "meanPdH": f"{gap.loc['pdH', 'mean']:.1f}",
        "maxPdH": f"{gap.loc['pdH', 'max']:.1f}",
        "sharePositive": f"{100 * main['share_positive']:.1f}",
        "pearsonMain": f"{main['pearson']:.3f}",
        "spearmanMain": f"{main['spearman']:.3f}",
        "nRankChangeTop": int((ranks["rank_change"] != 0).sum()),
    }, t / "numbers.tex")
    print(gap, ranks, rob, sep="\n\n")
```

- [ ] **Step 4: Run tests, then the script**

Run: `$PY -m pytest tests/test_report.py -v` → Expected: 4 passed.
Run: `$PY scripts/make_tables.py` → Expected: tables printed; five `.tex` files in `outputs/tables/`.

- [ ] **Step 5: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 12: Figures (`netseg/vignette.py`, `scripts/make_figures.py`)

**Files:**
- Create: `network_segregation/netseg/vignette.py`, `network_segregation/scripts/make_figures.py`
- Test: `network_segregation/tests/test_vignette.py`

Before writing chart code, **invoke the `dataviz` skill** and follow its palette/mark guidance; use it for colours and typography in every figure below.

**Interfaces:**
- Consumes: outputs of Tasks 7, 10, 11; `outputs/municipio_polygons.gpkg` (read-only).
- Produces:
  - `reach_edges(G, origin, bandwidth=2000.0) -> list[tuple]` — edges `(u, v, key)` whose both endpoints are within `bandwidth` network distance of `origin`.
  - Figures in `outputs/figures/`: `fig1_vignettes.pdf` (3 panels: 2-km Euclidean circle vs reachable walk edges for Goiânia 5208707, Rio de Janeiro 3304557, Salvador 2927408; origin = graph node nearest the population-weighted centroid of urban tracts), `fig2_rank_slope.pdf` (top-15, `rank_comparison`), `fig3_scatter.pdf` (`H_euc` vs `H_net`, 45° line, capitals labelled), `fig4_map_pdH.pdf` (Brazil, points at municipality centroids coloured by `pdH`, UF outlines), `fig5_clustermap.pdf` (Spearman correlations of topology metrics + `pdH`), `fig6_fragmentation.pdf` (`fragmentation` vs `pdH`).

- [ ] **Step 1: Write failing test**

`network_segregation/tests/test_vignette.py`:
```python
from netseg import vignette
from tests.helpers import grid_graph


def test_reach_edges_within_bandwidth():
    G = grid_graph(5, 1)  # path 0-1-2-3-4, spacing 100
    got = {tuple(sorted((u[0], v[0]))) for u, v, _ in vignette.reach_edges(G, (0, 0), bandwidth=250)}
    assert got == {(0, 1), (1, 2)}
```

- [ ] **Step 2: Run to verify failure** — `$PY -m pytest tests/test_vignette.py -v` → FAIL (`ImportError`).

- [ ] **Step 3: Implement `netseg/vignette.py`**

```python
"""Edges reachable within a network distance (K&R Fig. 1 analogue)."""

from __future__ import annotations

import networkx as nx


def reach_edges(G, origin, bandwidth: float = 2000.0) -> list[tuple]:
    dist = nx.single_source_dijkstra_path_length(G, origin, cutoff=bandwidth, weight="length")
    return [(u, v, k) for u, v, k in G.edges(keys=True) if u in dist and v in dist]
```

- [ ] **Step 4: Implement `scripts/make_figures.py`**

```python
"""All manuscript figures (PDF, vector)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import geopandas as gpd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import osmnx as ox  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from shapely.geometry import Point  # noqa: E402

from netseg.cities import REPO_ROOT, load_race_counts, load_urban_tracts  # noqa: E402
from netseg.network import prepare_graph, snap_points  # noqa: E402
from netseg.report import rank_comparison  # noqa: E402
from netseg.vignette import reach_edges  # noqa: E402

OUT = ROOT / "outputs"
FIG = OUT / "figures"
VIGNETTES = {"5208707": "Goiânia", "3304557": "Rio de Janeiro", "2927408": "Salvador"}
CAPITALS = {"1100205", "1200401", "1302603", "1400100", "1501402", "1600303", "1721000", "2111300", "2211001",
            "2304400", "2408102", "2507507", "2611606", "2704302", "2800308", "2927408", "3106200", "3205309",
            "3304557", "3550308", "4106902", "4205407", "4314902", "5002704", "5103403", "5208707", "5300108"}


def fig_vignettes():
    race = load_race_counts()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    for ax, (cod, name) in zip(axes, VIGNETTES.items()):
        gdf, _ = load_urban_tracts(cod, race)
        G = prepare_graph(ox.load_graphml(ROOT / "data" / "osm" / f"{cod}.graphml"), gdf.crs)
        c = gdf.geometry.representative_point()
        w = gdf["pop_total"].to_numpy()
        centre = np.array([[np.average(c.x, weights=w), np.average(c.y, weights=w)]])
        origin = snap_points(G, centre)[0][0]
        ox0, oy0 = G.nodes[origin]["x"], G.nodes[origin]["y"]
        edges = ox.convert.graph_to_gdfs(G, nodes=False)
        near = edges.cx[ox0 - 2600: ox0 + 2600, oy0 - 2600: oy0 + 2600]
        near.plot(ax=ax, color="0.85", linewidth=0.4)
        reach = set(reach_edges(G, origin, 2000.0))
        near[near.index.isin(reach)].plot(ax=ax, color="C0", linewidth=0.7)
        gpd.GeoSeries([Point(ox0, oy0).buffer(2000)], crs=gdf.crs).boundary.plot(ax=ax, color="C3", linewidth=1)
        ax.plot(ox0, oy0, "kx")
        ax.set_title(name)
        ax.set_axis_off()
    fig.savefig(FIG / "fig1_vignettes.pdf", bbox_inches="tight")


def fig_rank_slope(idx):
    r = rank_comparison(idx, top=15)
    fig, ax = plt.subplots(figsize=(6, 7))
    for row in r.itertuples():
        ax.plot([0, 1], [row.rank_euc, row.rank_net], color="C0" if row.rank_change == 0 else "C1", marker="o")
        ax.text(-0.03, row.rank_euc, row.NM_MUN, ha="right", va="center", fontsize=8)
        ax.text(1.03, row.rank_net, row.NM_MUN, ha="left", va="center", fontsize=8)
    ax.set_xticks([0, 1], ["Euclidean", "Network"])
    ax.invert_yaxis()
    ax.set_ylabel("Rank (1 = most segregated)")
    ax.set_xlim(-0.6, 1.6)
    fig.savefig(FIG / "fig2_rank_slope.pdf", bbox_inches="tight")


def fig_scatter(af):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(af["H_euc"], af["H_net"], s=14, color="C0")
    lim = [0, max(af["H_euc"].max(), af["H_net"].max()) * 1.05]
    ax.plot(lim, lim, color="0.5", linestyle="--", linewidth=0.8)
    for row in af[af["COD_MUNICIPIO"].isin(CAPITALS)].itertuples():
        ax.annotate(row.NM_MUN, (row.H_euc, row.H_net), fontsize=6, xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel("$H$ (Euclidean distance)")
    ax.set_ylabel("$H$ (network distance)")
    fig.savefig(FIG / "fig3_scatter.pdf", bbox_inches="tight")


def fig_map(af):
    mun = gpd.read_file(REPO_ROOT / "outputs" / "municipio_polygons.gpkg")
    mun["COD_MUNICIPIO"] = mun[[c for c in mun.columns if c.upper().startswith("CD_MUN") or c == "COD_MUNICIPIO"][0]].astype(str)
    pts = mun.merge(af[["COD_MUNICIPIO", "pdH"]], on="COD_MUNICIPIO")
    pts = pts.set_geometry(pts.to_crs(5880).representative_point())
    uf = gpd.read_file(REPO_ROOT / "outputs" / "uf_polygons.gpkg").to_crs(5880)
    fig, ax = plt.subplots(figsize=(7, 7))
    uf.boundary.plot(ax=ax, color="0.6", linewidth=0.4)
    pts.plot(ax=ax, column="pdH", cmap="viridis", markersize=18, legend=True, legend_kwds={"label": "% difference in $H$"})
    ax.set_axis_off()
    fig.savefig(FIG / "fig4_map_pdH.pdf", bbox_inches="tight")


def fig_clustermap(af):
    cols = ["intersection_density_km", "street_density_km", "street_length_avg", "streets_per_node_avg",
            "circuity_avg", "prop_dead_end", "prop_3way", "prop_4way", "self_loop_proportion", "cyclomatic",
            "meshedness", "gamma", "fragmentation", "pop_urban", "area_km2", "pdH"]
    g = sns.clustermap(af[cols].corr(method="spearman"), cmap="PRGn", vmin=-1, vmax=1, figsize=(9, 9))
    g.savefig(FIG / "fig5_clustermap.pdf")


def fig_fragmentation(af):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(af["fragmentation"], af["pdH"], s=14, color="C0")
    b = np.polyfit(af["fragmentation"], af["pdH"], 1)
    xs = np.linspace(af["fragmentation"].min(), af["fragmentation"].max(), 50)
    ax.plot(xs, np.polyval(b, xs), color="C3")
    ax.set_xlabel("Configurational fragmentation $F$")
    ax.set_ylabel("% difference in $H$ (network vs Euclidean)")
    fig.savefig(FIG / "fig6_fragmentation.pdf", bbox_inches="tight")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    idx = pd.read_parquet(OUT / "indices_long.parquet")
    af = pd.read_parquet(OUT / "analysis_frame.parquet")
    fig_vignettes()
    fig_rank_slope(idx)
    fig_scatter(af)
    fig_map(af)
    fig_clustermap(af)
    fig_fragmentation(af)
    print(sorted(p.name for p in FIG.glob("*.pdf")))
```

Before running `fig_map`, check the code column name: `$PY -c "import geopandas as g; print(g.read_file('../outputs/municipio_polygons.gpkg', rows=1).columns.tolist())"`. If none matches the selector above, replace the selector with the actual column name (e.g. `mun["COD_MUNICIPIO"] = mun["CD_MUN"].astype(str)`).

- [ ] **Step 5: Run test and script**

Run: `$PY -m pytest tests/test_vignette.py -v` → Expected: 1 passed.
Run: `$PY scripts/make_figures.py` → Expected: six PDF names printed. Open each PDF and check it visually (labels readable, no overlapping titles); fix and re-run as needed.

- [ ] **Step 6: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 13: Bibliography (`manuscript/references.bib`)

**Files:**
- Create: `network_segregation/manuscript/references.bib`

**Interfaces:**
- Produces: BibTeX keys used by Task 14 (exact keys below).

- [ ] **Step 1: Write the verified entries**

These were verified during design (spec §10) — copy verbatim:
```bibtex
@article{cortes2026segregation,
  title={segregation: Segregation Analysis, Inference, and Decomposition in {Python}},
  author={Cortes, Renan X. and Knaap, Elijah and Rey, Sergio J.},
  journal={Journal of Open Source Software}, year={2026}, volume={11}, number={125}, pages={11126},
  doi={10.21105/joss.11126}}
@article{roberto2018spatial,
  title={The Spatial Proximity and Connectivity Method for Measuring and Analyzing Residential Segregation},
  author={Roberto, Elizabeth}, journal={Sociological Methodology}, year={2018}, volume={48}, number={1},
  pages={182--224}, doi={10.1177/0081175018796871}}
@article{feitosa2007global,
  title={Global and Local Spatial Indices of Urban Segregation},
  author={Feitosa, Fl{\'a}via F. and C{\^a}mara, Gilberto and Monteiro, Ant{\^o}nio M. V. and Koschitzki, Thomas and Silva, Marcelino P. S.},
  journal={International Journal of Geographical Information Science}, year={2007}, volume={21}, number={3},
  pages={299--323}, doi={10.1080/13658810600911903}}
@article{boeing2019urban,
  title={Urban Spatial Order: Street Network Orientation, Configuration, and Entropy},
  author={Boeing, Geoff}, journal={Applied Network Science}, year={2019}, volume={4}, pages={67},
  doi={10.1007/s41109-019-0189-1}}
@article{boeing2022street,
  title={Street Network Models and Indicators for Every Urban Area in the World},
  author={Boeing, Geoff}, journal={Geographical Analysis}, year={2022}, volume={54}, number={3}, pages={519--535},
  doi={10.1111/gean.12281}}
@book{medeiros2013urbis,
  title={Urbis Brasiliae: o labirinto das cidades brasileiras}, author={Medeiros, Val{\'e}rio},
  publisher={Editora Universidade de Bras{\'i}lia}, address={Bras{\'i}lia}, year={2013}}
@book{holanda2002espaco,
  title={O espa{\c{c}}o de exce{\c{c}}{\~a}o}, author={Holanda, Frederico de},
  publisher={Editora Universidade de Bras{\'i}lia}, address={Bras{\'i}lia}, year={2002}}
@article{netto2015segregated,
  title={Segregated Networks in the City}, author={Netto, Vinicius M. and Pinheiro, Ma{\'i}ra Soares and Paschoalino, Roberto},
  journal={International Journal of Urban and Regional Research}, year={2015}, volume={39}, number={6},
  pages={1084--1102}, doi={10.1111/1468-2427.12346}}
@article{saboya2025chasm,
  title={{CHASM}: A Configurational Measure of Socio-Spatial Residential Segregation},
  author={Saboya, Renato Tibiri{\c{c}}{\'a} de and Peres, Otavio Martins},
  journal={Environment and Planning B: Urban Analytics and City Science}, year={2025}, volume={52}, number={6},
  pages={1464--1481}, doi={10.1177/23998083241287701}}
@article{goncalves2024uncovering,
  title={Uncovering Income and Racial Spatial Inequalities and Segregation Patterns with a Potential Accessibility Network Index},
  author={Gon{\c{c}}alves, G. M. and Maffini, A. L. and Maraschin, C.},
  journal={urbe. Revista Brasileira de Gest{\~a}o Urbana}, year={2024}, volume={16}, pages={e20230163},
  doi={10.1590/2175-3369.016.e20230163}}
@article{carvalho2023segregation,
  title={Segregation within Segregation: Informal Settlements beyond Socially Homogenous Areas},
  author={Carvalho, C. and Netto, Vinicius M.}, journal={Cities}, year={2023}, volume={134}, pages={104152}}
@inproceedings{spadon2018topological,
  title={Topological Street-Network Characterization through Feature-Vector and Cluster Analysis},
  author={Spadon, Gabriel and Gimenes, Gabriel and Rodrigues-Jr, Jose F.},
  booktitle={Computational Science -- ICCS 2018}, series={Lecture Notes in Computer Science}, volume={10860},
  pages={274--287}, year={2018}, publisher={Springer}}
@article{coy2006gated,
  title={Gated Communities and Urban Fragmentation in {Latin America}: The {Brazilian} Experience},
  author={Coy, Martin}, journal={GeoJournal}, year={2006}, volume={66}, pages={121--132}, doi={10.1007/s10708-006-9011-6}}
@article{sousafilho2023segregacao,
  title={Segrega{\c{c}}{\~a}o racial e econ{\^o}mica no {Brasil}: uma an{\'a}lise nacional das desigualdades socioecon{\^o}micas e socioespaciais},
  author={Sousa Filho, Jos{\'e} Firmino de and others}, journal={Revista Brasileira de Estudos de Popula{\c{c}}{\~a}o},
  year={2023}, volume={40}, pages={1--24}}
@techreport{pereira2019desigualdades,
  title={Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras, 2019},
  author={Pereira, Rafael H. M. and Braga, Carlos Kau{\^e} Vieira and Serra, Bernardo and Nadalin, Vanessa},
  institution={Instituto de Pesquisa Econ{\^o}mica Aplicada (IPEA)}, type={Texto para Discuss{\~a}o}, number={2535},
  address={Bras{\'i}lia}, year={2019}}
@article{tomasiello2024racial,
  title={Racial and Income Inequalities in Access to Healthcare in {Brazilian} Cities},
  author={Tomasiello, Diego B. and Vieira, Jo{\~a}o Pedro B. and Parga, Jo{\~a}o Pedro F. A. and Servo, Luciana M. S. and Pereira, Rafael H. M.},
  journal={Journal of Transport \& Health}, year={2024}, volume={34}, pages={101722}}
@article{bittencourt2021cumulative,
  title={Cumulative (and Self-Reinforcing) Spatial Inequalities: Interactions between Accessibility and Segregation in Four {Brazilian} Metropolises},
  author={Bittencourt, Tain{\'a} A. and Giannotti, Mariana and Marques, Eduardo},
  journal={Environment and Planning B: Urban Analytics and City Science}, year={2021}, volume={48}, number={7},
  pages={1989--2005}, doi={10.1177/2399808320958426}}
@article{boisjoly2020accessibility,
  title={Accessibility Measurements in {S}{\~a}o {P}aulo, {R}io de {J}aneiro, {C}uritiba and {R}ecife, {Brazil}},
  author={Boisjoly, Genevi{\`e}ve and Serra, Bernardo and Oliveira, Gustavo T. and El-Geneidy, Ahmed},
  journal={Journal of Transport Geography}, year={2020}, volume={82}, pages={102551}}
@article{pereira2021r5r,
  title={r5r: Rapid Realistic Routing on Multimodal Transport Networks with {R}$^5$ in {R}},
  author={Pereira, Rafael H. M. and Saraiva, Marcus and Herszenhut, Daniel and Braga, Carlos Kau{\^e} Vieira and Conway, Matthew Wigginton},
  journal={Findings}, year={2021}, doi={10.32866/001c.21262}}
```

- [ ] **Step 2: Add the classics — each verified by a web search before adding**

Add entries with these keys; for each, run a web search for the title and confirm journal, volume, pages and DOI before writing it. If a detail cannot be confirmed, omit that field rather than guess:
`knaap2023segregated` (Knaap & Rey, "Segregated by Design? Street Network Topological Structure and the Measurement of Urban Segregation" — confirm venue/year: journal article or preprint), `white1983measurement` (White 1983, AJS 88(5)), `wong1993spatial` (Wong 1993, Urban Studies 30(3)), `reardon2004measures` (Reardon & O'Sullivan 2004, Sociological Methodology 34), `reardon2008geographic` (Reardon et al. 2008, Demography 45(3)), `grannis1998importance` (Grannis 1998, AJS 103(6)), `grannis2005tcommunities` (Grannis 2005, City & Community 4(3)), `boeing2017osmnx` (Boeing 2017, CEUS 65), `fleischmann2019momepy` (Fleischmann 2019, JOSS 4(43)), `cortes2020open` (Cortes, Rey, Knaap, Wolf 2020, J. Geographical Systems 22), `rey2021comparative` (Rey, Cortes, Knaap 2021, Spatial Demography 9), `rey2022pysal` (Rey et al. 2022, Geographical Analysis 54(3)), `telles2004race` (Telles 2004, *Race in Another America*, Princeton UP), `pereira2019distributional` (Pereira, Banister, Schwanen & Wessel 2019, JTLU 12(1):741–764, doi:10.5198/jtlu.2019.1523). The existing `../draft/references.bib` may be *read* for candidate entries (never edited).

- [ ] **Step 3: Validate**

Run: `$PY -c "import re,collections; t=open('manuscript/references.bib',encoding='utf-8').read(); k=re.findall(r'@\w+\{([^,]+),',t); d=[x for x,c in collections.Counter(k).items() if c>1]; print(len(k),'entries; duplicates:',d)"`
Expected: ≥ 33 entries; `duplicates: []`.

- [ ] **Step 4: No-commit check** — `git status --porcelain` lists only `network_segregation/` paths.

---

### Task 14: Manuscript draft (`manuscript/manuscript.tex`) and build

**Files:**
- Create: `network_segregation/manuscript/manuscript.tex`, `network_segregation/scripts/sync_manuscript_assets.py`
- Produces: `network_segregation/manuscript/manuscript.pdf`.

- [ ] **Step 1: Asset sync script**

`network_segregation/scripts/sync_manuscript_assets.py`:
```python
"""Copy figures and tables from outputs/ into manuscript/ (the manuscript never reads outputs/ directly)."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ["figures", "tables"]:
    dst = ROOT / "manuscript" / sub
    dst.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "outputs" / sub).glob("*"):
        if f.suffix in {".pdf", ".tex"}:
            shutil.copy2(f, dst / f.name)
print("synced")
```
Run: `$PY scripts/sync_manuscript_assets.py` → Expected: `synced`.

- [ ] **Step 2: Write the LaTeX skeleton**

```latex
\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,microtype,amsmath,booktabs,graphicx,siunitx,natbib,hyperref}
\usepackage[margin=1in]{geometry}
\bibliographystyle{apalike}
\input{tables/numbers.tex}

\title{Segregated by Design in Brazil? Street-Network Topology and the Measurement of Racial Segregation}
\author{Renan Xavier Cortes}
\date{\today}

\begin{document}
\maketitle
\begin{abstract}
% 200–250 words: motivation (Euclidean abstraction; fragmented Brazilian grids), data (\nCities{} municipalities, 2022 census urban tracts, OSM walk networks),
% method (multigroup spatial information theory index H, identical 2-km kernel, Euclidean vs network distance; topology incl. configurational fragmentation),
% findings using \meanPdH, \spearmanMain, \nRankChangeTop and the sign/significance of fragmentation from models.tex, implication.
\end{abstract}
\noindent\textbf{Keywords:} segregation; street networks; spatial weights; configurational analysis; Brazil; PySAL

\section{Introduction}
\section{Background}
\subsection{Measuring segregation in space}
\subsection{Street networks and social interaction}
\subsection{The configuration of Brazilian street networks}
\subsection{Race, space and access in Brazilian cities}
\section{Data and methods}
\subsection{Cities, tracts and population groups}
\subsection{Street networks}
\subsection{Local environments and the segregation index}
\subsection{Network topology and configurational fragmentation}
\subsection{Analytical strategy}
\section{Results}
\subsection{How much does the distance metric matter?}
\subsection{Which network characteristics explain the gap?}
\section{Discussion}
\section{Conclusion}
\section*{Code and data availability}
\bibliography{references}
\appendix
\section{Robustness}
\section{Cross-check against the native PySAL network route}
\section{City-level results}
\end{document}
```

- [ ] **Step 3: Write each section (prose), using only verified sources and generated numbers**

Rules: every number in the text is either a `\macro` from `numbers.tex` or read from a generated table file; never type a result by hand. Cite with `\citet`/`\citep` using the keys from Task 13 only.

Content per section:
- **Introduction** (≈700 words): Euclidean distance as the "spherical cow" of spatial analysis \citep{knaap2023segregated}; Brazilian cities as "labyrinths" \citep{medeiros2013urbis} — hills, favelas reached by stairways, *condomínios fechados* \citep{coy2006gated}, planned grids (Goiânia, Brasília \citep{holanda2002espaco}); RQ1 and RQ2; contributions: first nationwide Euclidean-vs-network segregation comparison for a Global South country; a configurational fragmentation predictor; open, reproducible PySAL workflow \citep{cortes2026segregation,cortes2020open,rey2021comparative}; explicitly state that inference on the gap is left for future work.
- **2.1** White 1983; Wong 1993; Reardon & O'Sullivan 2004; Reardon et al. 2008; Feitosa et al. 2007 (Brazilian kernel-based indices).
- **2.2** Grannis 1998, 2005; Roberto 2018; Knaap & Rey 2023 (summarise their US results: network-based H higher almost everywhere, ~20\% relative difference, rank correlation 0.90); Boeing 2017, 2019, 2022; Fleischmann 2019.
- **2.3 (core)** Medeiros 2013 (27 capitals among 164 cities; Brazilian grids most fragmented, "patchwork"; synergy/intelligibility); Holanda 2002; Netto, Pinheiro & Paschoalino 2015 (segregation as restricted interaction); Saboya & Peres 2025 (CHASM: street-grid-based exposure); Gonçalves, Maffini & Maraschin 2024 (network accessibility and racial segregation, Pelotas); Carvalho & Netto 2023 (favelas); Spadon et al. 2018 (OSM topology of 645 SP-state cities); Coy 2006 (gated communities). End with hypotheses H1 (network H > Euclidean H), H2 (gap larger where circuity, dead-end share and fragmentation are higher), H3 (gap smaller where intersection density and meshedness are higher).
- **2.4** Telles 2004; Sousa Filho et al. 2023; IPEA accessibility evidence \citep{pereira2019desigualdades,tomasiello2024racial,bittencourt2021cumulative,boisjoly2020accessibility,pereira2019distributional,pereira2021r5r} — network position has racialised consequences.
- **3 Data and methods**: follow spec §4–5 exactly; equations for $W$ (triangular kernel, diagonal 1), local proportions, entropy, $H$ (K&R eqs. 1–7 in standard notation); Table 2 of topology definitions (write as a `tabular` from the definitions in Task 6); fragmentation definition and its status as a metric approximation of synergy; model equation; note that the local environment is computed as in \citet{cortes2026segregation} (same sparse lag, identical results — cite `test_matches_segregation_w_path` in the code availability section only). Report urban-tract restriction with `\nTractsUrban` and `\sharePopUrban`.
- **4.1**: `\input{tables/gap.tex}` (Table 3), Fig. 3 scatter, Fig. 2 rank slope, Fig. 4 map, Fig. 1 vignettes; quote `\meanHeuc`, `\meanHnet`, `\meanDH`, `\meanPdH`, `\maxPdH`, `\sharePositive`, `\pearsonMain`, `\spearmanMain`, `\nRankChangeTop`. Compare with K&R's US numbers qualitatively.
- **4.2**: Fig. 5 clustermap, `\input{tables/models.tex}`, Fig. 6; interpret coefficients from `models_coefs.csv` (signs, magnitudes, ΔR² between K&R and +F columns), VIFs from `vif.csv`. Describe as associations; no causal language.
- **Discussion**: OSM completeness in favelas (under-mapped stairways/alleys bias `D_net` upward → gap is an upper bound there); gated condominiums as barriers that are *mapped* as private ways; topography; planning implications (connectivity, permeability of *loteamentos*); limitations: no inference on the gap, walk network only, tract representative points, MAUP, municipal (not metropolitan) units.
- **Conclusion + future work**: random-labelling inference on the gap \citep{rey2021comparative}; multiscalar profiles; public-transport networks via r5r \citep{pereira2021r5r}; 2010–2022 change.
- **Code and data availability**: all code in the companion folder; OSM © OpenStreetMap contributors (ODbL), download dates in `cities.parquet`; census from IBGE; URL withheld during review.
- **Appendices**: `\input{tables/robustness.tex}`; cross-check table from `crosscheck_pandana.csv` (or the "not run" statement); per-city longtable generated from `analysis_frame.parquet` — add to `make_tables.py` a `city_results.tex` (`NM_MUN, UF, H_euc, H_net, pdH, fragmentation`), re-run it and the sync script.

- [ ] **Step 4: Build**

Run (from `network_segregation/manuscript/`): `latexmk -pdf -interaction=nonstopmode manuscript.tex`
Expected: `manuscript.pdf` produced; then check the log:
`grep -E "undefined|Citation .* undefined|multiply defined" manuscript.log` → Expected: no output.

- [ ] **Step 5: Consistency pass**

Check: every `\cite` key exists in `references.bib`; every figure/table referenced in the text exists and is referenced at least once; abstract numbers use macros; no hard-coded result numbers (`grep -nE "[0-9]\.[0-9]{2,}" manuscript.tex` → review each hit; only method constants such as 2,000 m may appear literally).

- [ ] **Step 6: Final no-commit check**

Run from repo root: `git status --porcelain`
Expected: only `?? network_segregation/` (untracked); **no modified (`M`) pre-existing files**. Also run `$PY -m pytest` from `network_segregation/` → all tests pass (the `realdata` test included).
