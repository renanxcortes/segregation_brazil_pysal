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


def matched_kernel_matrix(pairs: Pairs, target_env_pop: np.ndarray, pop: np.ndarray, b_max: float = 2000.0,
                          iters: int = 50):
    """Row-adaptive linear kernel whose per-tract environment population matches ``target_env_pop``.

    For each tract i, bisection finds b_i in (0, b_max] with
    pop_i + sum_j max(0, 1 - d_ij / b_i) pop_j = target_i (monotone in b_i). Used to hold local-environment
    population constant between Euclidean and network environments (Saporito 2026).
    Returns the sparse matrix (diagonal 1, rows not symmetric) and the bandwidths b_i.
    """
    p = pairs.within(b_max)
    n = pairs.n
    popj = pop[p.j]
    lo, hi = np.zeros(n), np.full(n, float(b_max))

    def env(b: np.ndarray) -> np.ndarray:
        bi = b[p.i]
        w = np.where(bi > 0, np.clip(1.0 - p.d / np.where(bi > 0, bi, 1.0), 0.0, None), 0.0)
        return pop + np.bincount(p.i, weights=w * popj, minlength=n)

    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        too_big = env(mid) > target_env_pop
        hi = np.where(too_big, mid, hi)
        lo = np.where(too_big, lo, mid)
    b = 0.5 * (lo + hi)
    w = np.clip(1.0 - p.d / b[p.i], 0.0, None)
    keep = w > 0
    diag = np.arange(n)
    rows = np.concatenate([p.i[keep], diag])
    cols = np.concatenate([p.j[keep], diag])
    vals = np.concatenate([w[keep], np.ones(n)])
    return coo_matrix((vals, (rows, cols)), shape=(n, n)).tocsr(), b


def to_libpysal(wsp):
    """libpysal W with ids 0..n-1 (for cross-validation against segregation's w= path)."""
    return WSP(wsp).to_W(silence_warnings=True)
