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


def test_group_absent_citywide_is_ignored_not_nan():
    g, xy = _toy()
    g["indigena"] = 0
    g["pop_total"] = g[GROUPS].sum(axis=1)
    wsp = weights.kernel_matrix(distances.euclidean_pairs(xy, 1000), 1000)
    h = measures.compute_indices(g, wsp)["H"]
    from segregation.multigroup import MultiInfoTheory

    present = [c for c in GROUPS if c != "indigena"]
    ref = MultiInfoTheory(measures.local_environment(g, present, wsp), groups=present).statistic
    assert np.isfinite(h) and h == pytest.approx(ref, abs=1e-12)


def test_matched_kernel_recovers_known_bandwidth():
    g, xy = _toy()
    pop = g["pop_total"].to_numpy(float)
    pe = distances.euclidean_pairs(xy, 3000)
    target = weights.kernel_matrix(pe, 1000) @ pop
    wm, b = weights.matched_kernel_matrix(pe, target, pop, b_max=2000)
    np.testing.assert_allclose(b, 1000, rtol=1e-3)
    np.testing.assert_allclose(wm @ pop, target, rtol=1e-6)


def test_matched_kernel_row_adaptive_matches_each_target():
    g, xy = _toy()
    pop = g["pop_total"].to_numpy(float)
    pe = distances.euclidean_pairs(xy, 3000)
    rng = np.random.default_rng(0)
    b_true = rng.uniform(300, 1800, len(pop))
    lo = weights.kernel_matrix(pe, 300) @ pop
    hi = weights.kernel_matrix(pe, 1800) @ pop
    target = lo + rng.uniform(0, 1, len(pop)) * (hi - lo)
    wm, b = weights.matched_kernel_matrix(pe, target, pop, b_max=2000)
    np.testing.assert_allclose(wm @ pop, target, rtol=1e-4)
    np.testing.assert_allclose(wm.diagonal(), 1.0)
    assert (b > 0).all() and (b <= 2000).all()


def test_matched_kernel_self_only_target():
    g, xy = _toy()
    pop = g["pop_total"].to_numpy(float)
    pe = distances.euclidean_pairs(xy, 3000)
    wm, b = weights.matched_kernel_matrix(pe, pop.copy(), pop, b_max=2000)
    np.testing.assert_allclose((wm @ pop), pop, rtol=1e-6)
