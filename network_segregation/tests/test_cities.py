from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from netseg import cities


def test_load_race_counts_handles_suppressed(tmp_path):
    csv = tmp_path / "race.csv"
    csv.write_text(
        '"CD_SETOR";"V01317";"V01318";"V01319";"V01320";"V01321";"V01322"\n'
        '"431490205000001";"10";"X";"0";"5";"1";"9"\n'
        '"431490205000002";"X";"X";"X";"X";"X";"X"\n'
    )
    df = cities.load_race_counts(csv)
    assert list(df.columns) == ["CD_SETOR", *cities.GROUPS, "pop_total", "pp_total"]
    assert df.loc[0, "preta"] == 0 and df.loc[0, "pop_total"] == 16 and df.loc[0, "pp_total"] == 5
    assert df.loc[1, "pop_total"] == 0
    assert df[cities.GROUPS].isna().sum().sum() == 0


def _write_shp(tmp_path: Path) -> Path:
    d = tmp_path / "RS_setores_CD2022"
    d.mkdir()
    gdf = gpd.GeoDataFrame(
        {
            "CD_SETOR": ["431490205000001", "431490205000002", "431490205000003", "431490205000004", "999999905000001"],
            "SITUACAO": ["Urbana", "Urbana", "Rural", "Urbana", "Urbana"],
            "CD_MUN": ["4314902", "4314902", "4314902", "4314902", "9999999"],
        },
        geometry=[box(-51.20 + k * 0.01, -30.05, -51.19 + k * 0.01, -30.04) for k in range(5)],
        crs="EPSG:4674",
    )
    gdf.to_file(d / "RS_setores_CD2022.shp")
    return tmp_path


def test_load_urban_tracts_filters_and_zero_fills(tmp_path):
    shp_dir = _write_shp(tmp_path)
    race = pd.DataFrame(
        {
            "CD_SETOR": ["431490205000001", "431490205000002", "431490205000003"],
            "branca": [10, 0, 7], "preta": [1, 0, 0], "amarela": [0, 0, 0], "parda": [4, 0, 1], "indigena": [0, 0, 0],
        }
    )
    race["pop_total"] = race[cities.GROUPS].sum(axis=1)
    race["pp_total"] = race["preta"] + race["parda"]
    gdf, stats = cities.load_urban_tracts("4314902", race, shp_dir=shp_dir)
    # tract 2: zero pop; tract 3: rural; tract 4: missing from census -> 0 -> dropped
    assert list(gdf["CD_SETOR"]) == ["431490205000001"]
    assert stats == {"n_tracts_all": 2, "n_tracts_urban": 1, "pop_all": 23, "pop_urban": 15}
    assert gdf.crs.is_projected and "UTM" in gdf.crs.name and "SIRGAS" in gdf.crs.name
    assert list(gdf.index) == [0]


def test_load_urban_tracts_raises_when_no_urban(tmp_path):
    shp_dir = _write_shp(tmp_path)
    race = pd.DataFrame({"CD_SETOR": ["431490205000003"], "branca": [5], "preta": [0], "amarela": [0], "parda": [0], "indigena": [0]})
    race["pop_total"] = 5
    race["pp_total"] = 0
    with pytest.raises(ValueError, match="no populated urban tracts"):
        cities.load_urban_tracts("4314902", race, shp_dir=shp_dir)


def test_select_cities_threshold(tmp_path):
    u = tmp_path / "u.csv"
    u.write_text("COD_MUNICIPIO,COD_UF,UF,pop_total,n_tracts\n1,11,RO,500000,10\n2,11,RO,299999,5\n3,11,RO,300000,5\n")
    n = tmp_path / "n.csv"
    n.write_text("COD_MUNICIPIO,NM_MUN\n1,A\n2,B\n3,C\n")
    out = cities.select_cities(u, n)
    assert list(out["COD_MUNICIPIO"]) == ["1", "3"]
    assert list(out.columns) == ["COD_MUNICIPIO", "NM_MUN", "UF", "pop_total"]


@pytest.mark.realdata
def test_select_cities_real_91_with_capitals():
    capitals = {
        "1100205", "1200401", "1302603", "1400100", "1501402", "1600303", "1721000", "2111300", "2211001",
        "2304400", "2408102", "2507507", "2611606", "2704302", "2800308", "2927408", "3106200", "3205309",
        "3304557", "3550308", "4106902", "4205407", "4314902", "5002704", "5103403", "5208707", "5300108",
    }
    out = cities.select_cities()
    assert len(out) == 91
    assert capitals <= set(out["COD_MUNICIPIO"])
