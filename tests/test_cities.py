import geopandas as gpd
import pytest
from segbr.census import load_census
from segbr.cities import build_city_gdf, UF_BY_CODE


def test_uf_by_code_covers_all_states():
    assert len(UF_BY_CODE) == 27
    assert UF_BY_CODE["43"] == "RS"
    assert UF_BY_CODE["35"] == "SP"
    assert UF_BY_CODE["33"] == "RJ"
    assert UF_BY_CODE["31"] == "MG"


def test_build_city_gdf_porto_alegre(census_csv, shp_dir):
    df = load_census(census_csv)
    gdf = build_city_gdf("4314902", df, shp_dir)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs.to_epsg() == 3857
    assert {"CD_SETOR", "pop_total", "pp_total", "geometry"} <= set(gdf.columns)
    assert (gdf["pop_total"] > 0).all()
    assert 2000 < len(gdf) < 2800
    assert gdf["geometry"].notna().all()


def test_build_city_gdf_missing_city_raises(census_csv, shp_dir):
    df = load_census(census_csv)
    with pytest.raises(ValueError):
        build_city_gdf("9999999", df, shp_dir)
