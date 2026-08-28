import tempfile
from pathlib import Path

from segbr.census import load_census, municipality_universe


def test_load_census_cleaning_logic():
    """Test that X and NaN/missing values are cleaned to 0."""
    # Create a minimal 3-row CSV with X and missing values in race columns
    csv_content = """CD_SETOR;V01317;V01318;V01319;V01320;V01321
1234567890123;100;X;50;;200
1234567890124;75;;150;25;100
1234567890125;X;X;X;X;X
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        df = load_census(temp_path)

        # Verify shape
        assert len(df) == 3

        # Row 0: 100, 0 (X), 50, 0 (missing), 200 -> pop_total=350, pp_total=0
        assert df.loc[0, "V01317"] == 100
        assert df.loc[0, "V01318"] == 0  # X -> 0
        assert df.loc[0, "V01319"] == 50
        assert df.loc[0, "V01320"] == 0  # missing -> 0
        assert df.loc[0, "V01321"] == 200
        assert df.loc[0, "pop_total"] == 350
        assert df.loc[0, "pp_total"] == 0  # V01318 + V01320 = 0 + 0

        # Row 1: 75, 0 (missing), 150, 25, 100 -> pop_total=350, pp_total=25
        assert df.loc[1, "V01317"] == 75
        assert df.loc[1, "V01318"] == 0  # missing -> 0
        assert df.loc[1, "V01319"] == 150
        assert df.loc[1, "V01320"] == 25
        assert df.loc[1, "V01321"] == 100
        assert df.loc[1, "pop_total"] == 350
        assert df.loc[1, "pp_total"] == 25  # V01318 + V01320 = 0 + 25

        # Row 2: all X -> all 0 -> pop_total=0, pp_total=0
        assert df.loc[2, "V01317"] == 0
        assert df.loc[2, "V01318"] == 0
        assert df.loc[2, "V01319"] == 0
        assert df.loc[2, "V01320"] == 0
        assert df.loc[2, "V01321"] == 0
        assert df.loc[2, "pop_total"] == 0
        assert df.loc[2, "pp_total"] == 0

        # Verify municipality codes are extracted
        assert df["COD_MUNICIPIO"].str.len().eq(7).all()
        assert df["COD_UF"].str.len().eq(2).all()
    finally:
        Path(temp_path).unlink()


def test_load_census_shape_and_types(census_csv):
    df = load_census(census_csv)
    assert {"CD_SETOR", "pop_total", "pp_total", "COD_MUNICIPIO", "COD_UF"} <= set(df.columns)
    assert df["CD_SETOR"].map(type).eq(str).all()
    assert str(df["pop_total"].dtype).startswith("int")
    assert (df["pp_total"] <= df["pop_total"]).all()
    assert (df[["V01317", "V01318", "V01319", "V01320", "V01321"]] >= 0).all().all()


def test_load_census_municipio_codes(census_csv):
    df = load_census(census_csv)
    assert df["COD_MUNICIPIO"].str.len().eq(7).all()
    assert df["COD_UF"].str.len().eq(2).all()
    # Porto Alegre must be present with nonzero population
    poa = df[df["COD_MUNICIPIO"] == "4314902"]
    assert len(poa) > 2000
    assert poa["pop_total"].sum() > 1_000_000


def test_municipality_universe(census_csv):
    df = load_census(census_csv)
    uni = municipality_universe(df, threshold=100_000)
    assert list(uni.columns) == ["COD_MUNICIPIO", "COD_UF", "pop_total", "n_tracts"]
    assert (uni["pop_total"] > 100_000).all()
    assert uni["pop_total"].is_monotonic_decreasing
    assert uni["COD_MUNICIPIO"].is_unique
    # Brazil has on the order of 300-340 municipalities above 100k
    assert 280 <= len(uni) <= 360
    # São Paulo is the largest
    assert uni.iloc[0]["COD_MUNICIPIO"] == "3550308"
    # Porto Alegre is in the set
    assert "4314902" in set(uni["COD_MUNICIPIO"])


def test_municipality_universe_threshold_monotone(census_csv):
    df = load_census(census_csv)
    assert len(municipality_universe(df, 200_000)) < len(municipality_universe(df, 100_000))
