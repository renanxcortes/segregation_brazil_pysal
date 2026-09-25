"""Edges reachable within a network distance (K&R Fig. 1 analogue)."""

from __future__ import annotations

import networkx as nx


def reach_edges(G, origin, bandwidth: float = 2000.0) -> list[tuple]:
    dist = nx.single_source_dijkstra_path_length(G, origin, cutoff=bandwidth, weight="length")
    return [(u, v, k) for u, v, k in G.edges(keys=True) if u in dist and v in dist]
