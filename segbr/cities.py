from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

UF_BY_CODE = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def build_city_gdf(cod_municipio: str, census_df: pd.DataFrame, shp_dir: str | Path) -> gpd.GeoDataFrame:
    """Tract GeoDataFrame for one municipality, EPSG:3857, zero-population tracts dropped."""
    uf_code = cod_municipio[:2]
    uf = UF_BY_CODE.get(uf_code)
    if uf is None:
        raise ValueError(f"unknown UF code {uf_code!r} for municipality {cod_municipio!r}")

    shp = Path(shp_dir) / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp"
    if not shp.exists():
        raise FileNotFoundError(shp)

    gdf = gpd.read_file(shp, where=f"CD_MUN = '{cod_municipio}'")
    if len(gdf) == 0:
        raise ValueError(f"no tracts for municipality {cod_municipio!r} in {shp}")

    cols = ["CD_SETOR", "pop_total", "pp_total"]
    merged = gdf[["CD_SETOR", "geometry"]].merge(census_df[cols], on="CD_SETOR", how="left")
    merged[["pop_total", "pp_total"]] = merged[["pop_total", "pp_total"]].fillna(0).astype("int64")
    merged = merged[merged["pop_total"] > 0].copy()
    if len(merged) == 0:
        raise ValueError(f"all tracts have zero population for {cod_municipio!r}")

    return gpd.GeoDataFrame(merged, geometry="geometry", crs=gdf.crs).to_crs(epsg=3857)
