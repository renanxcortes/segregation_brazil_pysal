import math
import pytest
from segbr.census import load_census
from segbr.cities import build_city_gdf
from segbr.measures import MEASURES, compute_profile

EXPECTED_POA = {
    "Dissim": 0.369,
    "SpatialDissim": 0.29,
    "Gini": 0.489,
    "Entropy": 0.130,
    "Isolation": 0.365,
    "DistanceDecayIsolation": 0.324,
    "RelativeConcentration": -0.107,
    "RelativeCentralization": -0.100,
    "RelativeClustering": 0.596,
}


def test_measures_registry_order_and_dimensions():
    assert list(MEASURES) == [
        "Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation",
        "DistanceDecayIsolation", "RelativeConcentration",
        "RelativeCentralization", "RelativeClustering",
    ]
    dims = {d for _, d in MEASURES.values()}
    assert dims == {"Evenness", "Exposure", "Concentration", "Centralization", "Clustering"}


@pytest.mark.slow
def test_compute_profile_porto_alegre_regression(census_csv, shp_dir):
    df = load_census(census_csv)
    gdf = build_city_gdf("4314902", df, shp_dir)
    prof = compute_profile(gdf)
    assert prof["n_tracts"] == len(gdf)
    # Porto Alegre is one of Brazil's whitest state capitals (~74% branca);
    # its preta+parda share is ~0.26, not the 0.30-0.45 the draft brief assumed.
    assert 0.20 < prof["ppp"] < 0.35
    for name, expected in EXPECTED_POA.items():
        assert name in prof, f"{name} missing (error: {prof.get(name + '_error')})"
        assert math.isclose(prof[name], expected, abs_tol=0.01), (name, prof[name], expected)


def test_compute_profile_subset_and_error_isolation(census_csv, shp_dir):
    df = load_census(census_csv)
    gdf = build_city_gdf("4314902", df, shp_dir)
    prof = compute_profile(gdf, measures=["Dissim", "Entropy"])
    assert set(prof) >= {"Dissim", "Entropy", "n_tracts", "timings"}
    assert "Gini" not in prof
