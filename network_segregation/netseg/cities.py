"""Read-only access to the repository's 2022 census inputs."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CENSUS_CSV = REPO_ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
SHP_DIR = REPO_ROOT / "shapefiles_2022"
UNIVERSE_CSV = REPO_ROOT / "outputs" / "city_universe_2022.csv"
NAMES_CSV = REPO_ROOT / "outputs" / "municipio_names.csv"

RACE_VARS = {"V01317": "branca", "V01318": "preta", "V01319": "amarela", "V01320": "parda", "V01321": "indigena"}
GROUPS = list(RACE_VARS.values())
COUNT_COLS = [*GROUPS, "pop_total", "pp_total"]

UF_BY_CODE = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def select_cities(universe_csv=UNIVERSE_CSV, names_csv=NAMES_CSV, min_pop: int = 300_000) -> pd.DataFrame:
    """Municipalities with 2022 population >= ``min_pop``, largest first."""
    u = pd.read_csv(universe_csv, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    names = pd.read_csv(names_csv, dtype={"COD_MUNICIPIO": str})
    out = u[u["pop_total"] >= min_pop].merge(names, on="COD_MUNICIPIO", how="left")
    out = out.sort_values("pop_total", ascending=False).reset_index(drop=True)
    return out[["COD_MUNICIPIO", "NM_MUN", "UF", "pop_total"]]


def load_race_counts(csv_path=CENSUS_CSV) -> pd.DataFrame:
    """Five colour/race counts per tract; suppressed cells ("X") become 0."""
    df = pd.read_csv(csv_path, sep=";", usecols=["CD_SETOR", *RACE_VARS], dtype=str)
    counts = (
        df[list(RACE_VARS)]
        .replace({"X": None})
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype("int64")
        .rename(columns=RACE_VARS)
    )
    counts.insert(0, "CD_SETOR", df["CD_SETOR"])
    counts["pop_total"] = counts[GROUPS].sum(axis=1).astype("int64")
    counts["pp_total"] = (counts["preta"] + counts["parda"]).astype("int64")
    return counts


def load_urban_tracts(cod: str, race: pd.DataFrame, shp_dir=SHP_DIR) -> tuple[gpd.GeoDataFrame, dict]:
    """Populated urban tracts of one municipality, projected to SIRGAS 2000 / UTM."""
    uf = UF_BY_CODE[cod[:2]]
    shp = Path(shp_dir) / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp"
    # the where-clause field must be among the selected columns, or pyogrio returns nothing
    raw = gpd.read_file(shp, where=f"CD_MUN = '{cod}'", columns=["CD_SETOR", "SITUACAO", "CD_MUN"])
    raw = raw.drop(columns="CD_MUN")
    merged = raw.merge(race[["CD_SETOR", *COUNT_COLS]], on="CD_SETOR", how="left")
    merged[COUNT_COLS] = merged[COUNT_COLS].fillna(0).astype("int64")
    populated = merged[merged["pop_total"] > 0]
    urban = populated[populated["SITUACAO"] == "Urbana"]
    if urban.empty:
        raise ValueError(f"no populated urban tracts for municipality {cod!r}")
    stats = {
        "n_tracts_all": int(len(populated)),
        "n_tracts_urban": int(len(urban)),
        "pop_all": int(populated["pop_total"].sum()),
        "pop_urban": int(urban["pop_total"].sum()),
    }
    gdf = gpd.GeoDataFrame(urban.drop(columns="SITUACAO"), geometry="geometry", crs=raw.crs)
    utm = gdf.estimate_utm_crs(datum_name="SIRGAS 2000")
    return gdf.to_crs(utm).reset_index(drop=True), stats
