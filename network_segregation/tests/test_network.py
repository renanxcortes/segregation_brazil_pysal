import networkx as nx
import numpy as np
from shapely.geometry import box

from netseg import network
from tests.helpers import grid_graph


def test_snap_points_nearest_node_and_distance():
    G = grid_graph(3, 3)
    ids, d = network.snap_points(G, np.array([[10.0, 0.0], [190.0, 210.0]]))
    assert list(ids) == [(0, 0), (2, 2)]
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


def test_clip_graph_can_keep_all_components():
    G = grid_graph(5, 1)  # nodes x = 0..400
    from shapely.geometry import MultiPolygon

    poly = MultiPolygon([box(-1, -1, 101, 1), box(299, -1, 401, 1)])  # two separate pieces
    assert network.clip_graph(G, poly).number_of_nodes() == 2
    assert network.clip_graph(G, poly, largest=False).number_of_nodes() == 4


def test_download_retries_transient_errors(tmp_path, monkeypatch):
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("overpass timed out")
        return nx.MultiDiGraph(crs="EPSG:4326")

    monkeypatch.setattr(network.ox, "graph_from_polygon", flaky)
    monkeypatch.setattr(network.ox, "save_graphml", lambda G, p: None)
    monkeypatch.setattr(network.time, "sleep", lambda s: None)
    G = network.download_walk_graph(box(0, 0, 1, 1), tmp_path / "g.graphml", attempts=5, wait_s=1)
    assert calls["n"] == 3 and isinstance(G, nx.MultiDiGraph)


def test_download_gives_up_after_attempts(tmp_path, monkeypatch):
    import pytest

    def dead(*a, **k):
        raise ConnectionError("down")

    monkeypatch.setattr(network.ox, "graph_from_polygon", dead)
    monkeypatch.setattr(network.time, "sleep", lambda s: None)
    with pytest.raises(ConnectionError):
        network.download_walk_graph(box(0, 0, 1, 1), tmp_path / "g.graphml", attempts=3, wait_s=1)
