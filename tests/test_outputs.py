"""Validation of the nationwide segregation-profiling output.

Consumes ``outputs/segregation_profiles_2022.parquet`` (one row per city,
written by ``scripts/run_nationwide.py``). These tests are the hard coverage
guarantee that feeds the manuscript appendix; see ``outputs/coverage_note.md``.
"""

import pathlib

import pandas as pd
import pytest

OUT = pathlib.Path(__file__).resolve().parents[1] / "outputs" / "segregation_profiles_2022.parquet"

MEASURES = ["Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation",
            "DistanceDecayIsolation", "RelativeConcentration",
            "RelativeCentralization", "RelativeClustering"]

# Measures bounded to [0, 1] by construction (small float tolerance allowed).
BOUNDED = ["Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation", "DistanceDecayIsolation"]


@pytest.fixture(scope="module")
def profiles():
    if not OUT.exists():
        pytest.skip("run scripts/run_nationwide.py first")
    return pd.read_parquet(OUT)


def test_one_row_per_city(profiles):
    assert profiles["COD_MUNICIPIO"].is_unique


def test_expected_columns_present(profiles):
    for col in ["COD_MUNICIPIO", "COD_UF", "fatal_error", "n_tracts", *MEASURES]:
        assert col in profiles.columns, col


def test_coverage(profiles):
    ok = profiles[~profiles["fatal_error"].astype(bool)]
    assert len(ok) / len(profiles) > 0.97  # <3% cities lost


def test_no_null_measures(profiles):
    """Hard coverage guarantee: every measure column is fully populated."""
    ok = profiles[~profiles["fatal_error"].astype(bool)]
    nulls = {m: int(ok[m].isna().sum()) for m in MEASURES}
    assert all(v == 0 for v in nulls.values()), nulls


def test_measure_ranges(profiles):
    ok = profiles[~profiles["fatal_error"].astype(bool)]
    for m in BOUNDED:
        vals = ok[m].dropna()
        assert vals.between(0, 1).mean() > 0.99, m
    for m in ["RelativeConcentration", "RelativeCentralization", "RelativeClustering"]:
        assert ok[m].notna().mean() > 0.5, m


def test_bounded_measures_within_unit_interval(profiles):
    """Dissim/Gini/Entropy/Isolation/SpatialDissim/DDxi must all be in [0, 1]."""
    ok = profiles[~profiles["fatal_error"].astype(bool)]
    for m in BOUNDED:
        vals = ok[m].dropna()
        assert vals.between(-1e-4, 1.0001).all(), (m, vals.min(), vals.max())


def test_porto_alegre_values(profiles):
    poa = profiles.set_index("COD_MUNICIPIO").loc["4314902"]
    assert abs(poa["Dissim"] - 0.369) < 0.01
    assert abs(poa["Gini"] - 0.489) < 0.01
