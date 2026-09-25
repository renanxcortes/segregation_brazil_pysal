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
