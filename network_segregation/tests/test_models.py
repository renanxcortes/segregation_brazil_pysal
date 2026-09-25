import numpy as np
import pandas as pd
import pytest

from netseg import models


def _fake(n=91, seed=0):
    rng = np.random.default_rng(seed)
    cities = pd.DataFrame({
        "COD_MUNICIPIO": [str(k) for k in range(n)],
        "intersection_density_km": rng.lognormal(4, 0.4, n),
        "circuity_avg": rng.normal(1.08, 0.03, n),
        "meshedness": rng.normal(0.2, 0.05, n),
        "cyclomatic": rng.lognormal(9, 1, n),
        "prop_dead_end": rng.normal(0.15, 0.04, n),
        "fragmentation": rng.normal(0.5, 0.1, n),
        "pop_urban": rng.lognormal(13, 0.7, n),
        "area_km2": rng.lognormal(5, 0.6, n),
    })
    euc = rng.uniform(0.05, 0.2, n)
    z = (cities["fragmentation"] - cities["fragmentation"].mean()) / cities["fragmentation"].std()
    net = euc + 0.02 + 0.01 * z + rng.normal(0, 0.002, n)
    idx = pd.DataFrame({"COD_MUNICIPIO": cities["COD_MUNICIPIO"], "spec": "main", "index": "H", "euc": euc, "net": net})
    return idx, cities


def test_analysis_frame_columns_and_gap():
    idx, cities = _fake()
    df = models.analysis_frame(idx, cities)
    assert len(df) == 91
    np.testing.assert_allclose(df["dH"], df["H_net"] - df["H_euc"])
    np.testing.assert_allclose(df["pdH"], 100 * df["dH"] / df["H_euc"])
    assert abs(df["z_fragmentation"].mean()) < 1e-12 and df["z_fragmentation"].std() == pytest.approx(1)


def test_fit_recovers_fragmentation_effect():
    idx, cities = _fake()
    res = models.fit(models.analysis_frame(idx, cities), "dH", full=True)
    assert res.cov_type == "HC3"
    assert res.params["z_fragmentation"] == pytest.approx(0.01, abs=0.002)
    assert res.pvalues["z_fragmentation"] < 0.01
    kr = models.fit(models.analysis_frame(idx, cities), "dH", full=False)
    assert "z_fragmentation" not in kr.params


def test_vif_table():
    idx, cities = _fake()
    v = models.vif_table(models.analysis_frame(idx, cities))
    assert set(v.columns) == {"variable", "vif"} and (v["vif"] >= 1).all()
