import pandas as pd
from segbr.census import load_census


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
