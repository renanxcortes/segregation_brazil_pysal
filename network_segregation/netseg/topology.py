"""Street-network topology metrics (Knaap & Rey 2023, Table 2) and configurational fragmentation.

Definitions: intersections are nodes of degree >= 3; degree counts parallel edges (the
"streets per node" analogue on the undirected graph); circuity is total edge length over
total straight-line endpoint distance (self-loops excluded); cyclomatic = e - v + p;
meshedness = (e - v + p) / (2v - 5)
(p = number of components; e - v + 1 for a connected graph); gamma = e / (3(v - 2)); densities are per km^2 of
the urban footprint.
"""

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
    lengths, straight, nonloop_len, loops = [], [], 0.0, 0
    for a, b, data in G.edges(data=True):
        length = float(data["length"])
        lengths.append(length)
        if a == b:
            loops += 1
            continue
        nonloop_len += length
        straight.append(np.hypot(G.nodes[a]["x"] - G.nodes[b]["x"], G.nodes[a]["y"] - G.nodes[b]["y"]))
    lengths = np.asarray(lengths)
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
        "meshedness": (e - v + p) / (2 * v - 5),
        "gamma": e / (3 * (v - 2)),
    }


def fragmentation(G: nx.MultiGraph, S: int = 500, N: int = 2000, radius: float = 800.0, seed: int = 0, batch: int = 25,
                  sample_from=None) -> dict:
    """Metric analogue of space-syntax synergy (Medeiros 2013).

    L_i: street length with both endpoints within ``radius`` of node i (local reach).
    G_i: 1 / mean network distance from i to S random target nodes (global closeness).
    synergy = Pearson corr(log L_i, G_i) over N random origin nodes; fragmentation = 1 - synergy.
    Routing uses all of ``G``; origins and targets are drawn from ``sample_from`` (default: all nodes).
    """
    csr, nodes = graph_to_csr(G)
    index = {n: k for k, n in enumerate(nodes)}
    pool = np.arange(len(nodes)) if sample_from is None else np.array(sorted(index[n] for n in sample_from))
    rng = np.random.default_rng(seed)
    origins = np.sort(rng.choice(pool, size=min(N, len(pool)), replace=False))
    targets = np.sort(rng.choice(pool, size=min(S, len(pool)), replace=False))

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
