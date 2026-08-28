import pandas as pd
import pytest
import segbr.pipeline as pipeline
from segbr.census import load_census, municipality_universe
from segbr.pipeline import run_all


@pytest.mark.slow
def test_run_all_two_cities_and_resume(tmp_path, census_csv, shp_dir, monkeypatch):
    df = load_census(census_csv)
    uni = municipality_universe(df).head(0).copy()
    # hand-pick two small-ish cities: Porto Alegre and Florianópolis
    uni = pd.DataFrame(
        {"COD_MUNICIPIO": ["4314902", "4205407"], "COD_UF": ["43", "42"],
         "pop_total": [1, 1], "n_tracts": [1, 1]}
    )
    out = tmp_path / "profiles.parquet"

    res1 = run_all(uni.head(1), df, shp_dir, out, measures=["Dissim", "Entropy"])
    assert len(res1) == 1
    assert out.exists()

    poa_row_1 = res1.set_index("COD_MUNICIPIO").loc["4314902"].to_dict()

    # resume: full universe, first city already done → only the second is computed.
    # Guard build_city_gdf so it EXPLODES if run_all tries to recompute Porto Alegre,
    # proving the checkpoint is actually loaded (not silently discarded).
    real_build = pipeline.build_city_gdf

    def guarded_build(cod, *args, **kwargs):
        assert cod != "4314902", "Porto Alegre must NOT be recomputed on resume"
        return real_build(cod, *args, **kwargs)

    monkeypatch.setattr(pipeline, "build_city_gdf", guarded_build)

    res2 = run_all(uni, df, shp_dir, out, measures=["Dissim", "Entropy"])
    assert set(res2["COD_MUNICIPIO"]) == {"4314902", "4205407"}
    assert len(res2) == 2
    assert res2.set_index("COD_MUNICIPIO").loc["4314902", "Dissim"] == pytest.approx(0.369, abs=0.01)
    # POA's row is the byte-for-byte original from the first run.
    poa_row_2 = res2.set_index("COD_MUNICIPIO").loc["4314902"].to_dict()
    assert poa_row_2 == poa_row_1


def test_run_all_records_missing_city(tmp_path, census_csv, shp_dir):
    df = load_census(census_csv)
    uni = pd.DataFrame(
        {"COD_MUNICIPIO": ["9999999"], "COD_UF": ["99"], "pop_total": [1], "n_tracts": [1]}
    )
    out = tmp_path / "p.parquet"
    res = run_all(uni, df, shp_dir, out, measures=["Dissim"])
    assert res.iloc[0]["fatal_error"]
    assert (out.with_name("failures_2022.csv")).exists()
