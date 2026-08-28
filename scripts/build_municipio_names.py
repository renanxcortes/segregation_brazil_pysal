"""Build outputs/municipio_names.csv: COD_MUNICIPIO -> NM_MUN.

Reads NM_MUN from the 2022 census-tract shapefiles (one per UF), keeps one
row per municipality, and restricts to the analyzed city universe. Run once;
the CSV is committed so figures.py never needs geopandas.

Usage:
    python scripts/build_municipio_names.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "outputs" / "city_universe_2022.csv"
SHP_DIR = ROOT / "shapefiles_2022"
OUT = ROOT / "outputs" / "municipio_names.csv"


def build() -> pd.DataFrame:
    import geopandas as gpd

    uni = pd.read_csv(UNIVERSE, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    wanted = set(uni["COD_MUNICIPIO"])

    frames = []
    for shp in sorted(SHP_DIR.glob("*_setores_CD2022/*_setores_CD2022.shp")):
        g = gpd.read_file(shp, columns=["CD_MUN", "NM_MUN"], ignore_geometry=True)
        g = g[["CD_MUN", "NM_MUN"]].drop_duplicates()
        frames.append(g)

    names = (pd.concat(frames, ignore_index=True)
             .drop_duplicates(subset="CD_MUN")
             .rename(columns={"CD_MUN": "COD_MUNICIPIO"}))
    names = names[names["COD_MUNICIPIO"].isin(wanted)].copy()
    names = names.sort_values("COD_MUNICIPIO").reset_index(drop=True)

    missing = wanted - set(names["COD_MUNICIPIO"])
    if missing:
        raise SystemExit(f"no NM_MUN for {len(missing)} codes: {sorted(missing)}")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        names.to_csv(f, index=False, lineterminator="\n")
    print(f"wrote {OUT} ({len(names)} municipalities)")
    return names


if __name__ == "__main__":
    build()
