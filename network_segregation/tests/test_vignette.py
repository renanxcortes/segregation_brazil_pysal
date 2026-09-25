from netseg import vignette
from tests.helpers import grid_graph


def test_reach_edges_within_bandwidth():
    G = grid_graph(5, 1)  # path 0-1-2-3-4, spacing 100
    got = {tuple(sorted((u[0], v[0]))) for u, v, _ in vignette.reach_edges(G, (0, 0), bandwidth=250)}
    assert got == {(0, 1), (1, 2)}
