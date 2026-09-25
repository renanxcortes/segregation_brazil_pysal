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
    osm_id = lambda n: n[0] * 1000 + n[1]  # noqa: E731  (osmnx needs scalar node ids, like real OSM)
    G = nx.MultiDiGraph(crs="EPSG:4326")
    for n, d in grid.nodes(data=True):
        lon, lat = to_ll.transform(d["x"], d["y"])
        G.add_node(osm_id(n), x=lon, y=lat)
    for k, (u, v, d) in enumerate(grid.edges(data=True)):
        G.add_edge(osm_id(u), osm_id(v), length=d["length"], osmid=k)  # osmnx.to_undirected compares osmid
        G.add_edge(osm_id(v), osm_id(u), length=d["length"], osmid=k)
    return G


def test_run_city_end_to_end(tmp_path):
    out = pipeline.run_city("4314902", "Toy", None, tmp_path, loader=fake_loader, downloader=fake_downloader,
                            frag_kwargs={"S": 50, "N": 50})
    idx = pd.DataFrame(out["indices"])
    assert set(idx["spec"]) == {"main", "b1000", "b3000", "exp2000", "popmatch"}
    assert set(idx["index"]) == {"H", "Dissim_pp", "Isolation_pp", "Entropy_pp"}
    main_h = idx[(idx.spec == "main") & (idx["index"] == "H")].iloc[0]
    assert main_h.net > main_h.euc > 0  # the barrier makes network segregation higher
    assert out["city"]["meshedness"] > 0 and 0 <= out["city"]["fragmentation"] <= 2
    assert (tmp_path / "results" / "4314902.json").exists()


def test_run_city_population_matched_spec(tmp_path):
    out = pipeline.run_city("4314902", "Toy", None, tmp_path, loader=fake_loader, downloader=fake_downloader,
                            frag_kwargs={"S": 20, "N": 20})
    idx = pd.DataFrame(out["indices"])
    main = idx[idx.spec == "main"].set_index("index")
    pm = idx[idx.spec == "popmatch"].set_index("index")
    assert (pm["net"] == main["net"]).all()          # network side unchanged
    assert (pm["bandwidth"] < 2000).all()            # Euclidean radius shrinks to match population
    c = out["city"]
    assert c["env_pop_net_mean"] < c["env_pop_euc_mean"]
    assert abs(c["env_pop_popmatch_mean"] - c["env_pop_net_mean"]) / c["env_pop_net_mean"] < 1e-3


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
