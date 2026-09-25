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


def test_meshedness_uses_all_components():
    two = nx.disjoint_union(grid_graph(3, 3), grid_graph(3, 3))
    out = topology.network_metrics(two, area_km2=1.0)
    v, e, p = 18, 24, 2
    assert out["cyclomatic"] == e - v + p
    assert out["meshedness"] == pytest.approx((e - v + p) / (2 * v - 5))


def test_fragmentation_samples_only_from_given_nodes():
    G = _patchwork()
    patch0 = [n for n in G if n[0] == 0]
    out = topology.fragmentation(G, S=500, N=2000, sample_from=patch0)
    assert out["frag_N"] == 100 and out["frag_S"] == 100
