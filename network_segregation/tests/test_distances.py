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
