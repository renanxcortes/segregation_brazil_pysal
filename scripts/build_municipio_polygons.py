"""Dissolve 2022 tract geometries to municipality polygons for the universe.

Builds ``outputs/municipio_polygons.gpkg`` with one polygon per universe city
(319 of them), dissolved from the per-UF tract shapefiles in
``shapefiles_2022/<UF>_setores_CD2022/``.

The dissolve is heavy (SP alone is ~27k tracts). The script is therefore
resumable / idempotent:

* If the GPKG already exists and holds all 319 universe codes, it does nothing.
* Otherwise it processes UFs one at a time. A UF whose codes are all already in
  the GPKG is skipped. For every other UF the polygons are (re)built and the
  GPKG is rewritten atomically (temp file + ``os.replace``), so a kill mid-run
  always leaves a valid partial GPKG that the next run resumes from.

Run: ``"C:/Users/renan/anaconda3/python.exe" scripts/build_municipio_polygons.py``
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "outputs" / "city_universe_2022.csv"
SHP_DIR = ROOT / "shapefiles_2022"
OUT = ROOT / "outputs" / "municipio_polygons.gpkg"

# The shapefiles are already in SIRGAS 2000 geographic coordinates (equivalent
# to EPSG:4674). We keep that native CRS rather than reprojecting: the local
# PROJ database cannot serialise an EPSG code on write, but the native .prj WKT
# round-trips fine. All 27 UF shapefiles share this CRS, so concatenation is
# safe without any transform.


def _read_existing() -> gpd.GeoDataFrame | None:
    if not OUT.exists():
        return None
    try:
        g = gpd.read_file(OUT)
    except Exception as exc:  # corrupt / half-written -> start over
        print(f"  ! could not read existing {OUT.name} ({exc!r}); rebuilding")
        return None
    return g


def _build_uf(uf: str, codes: set[str]) -> gpd.GeoDataFrame:
    shp = SHP_DIR / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp"
    if not shp.exists():
        raise FileNotFoundError(shp)
    g = gpd.read_file(shp, columns=["CD_MUN"])
    g = g[g["CD_MUN"].isin(codes)]
    g = g.dissolve(by="CD_MUN").reset_index()[["CD_MUN", "geometry"]]
    return g


def build() -> None:
    uni = pd.read_csv(UNIVERSE, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    all_codes = set(uni["COD_MUNICIPIO"])

    existing = _read_existing()
    if existing is not None:
        present = set(existing["CD_MUN"].astype(str))
        print(f"existing GPKG: {len(present)}/{len(all_codes)} municipalities")
        if all_codes <= present:
            print("nothing to do -- all universe municipalities present")
            return
    else:
        present = set()

    for uf in sorted(uni["UF"].unique()):
        uf_codes = set(uni.loc[uni["UF"] == uf, "COD_MUNICIPIO"])
        if uf_codes <= present:
            print(f"[{uf}] skip ({len(uf_codes)} already present)")
            continue

        t0 = time.time()
        g = _build_uf(uf, uf_codes)
        dt = time.time() - t0

        if existing is not None and len(existing):
            keep = existing[~existing["CD_MUN"].astype(str).isin(uf_codes)]
            combined = gpd.GeoDataFrame(
                pd.concat([keep, g], ignore_index=True), crs=g.crs
            )
        else:
            combined = g

        tmp = OUT.with_suffix(".gpkg.tmp")
        if tmp.exists():
            tmp.unlink()
        combined.to_file(tmp, driver="GPKG")
        os.replace(tmp, OUT)

        existing = combined
        present |= set(g["CD_MUN"].astype(str))
        got = len(g)
        want = len(uf_codes)
        flag = "" if got == want else f"  (!! {want - got} missing)"
        print(f"[{uf}] {got}/{want} dissolved in {dt:5.1f}s -> "
              f"total {len(present)}/{len(all_codes)}{flag}")

    missing = sorted(all_codes - present)
    if missing:
        print(f"DONE (partial): {len(present)}/{len(all_codes)}; "
              f"missing {missing}")
    else:
        print(f"DONE: {len(present)}/{len(all_codes)} municipality polygons -> "
              f"{OUT}")


if __name__ == "__main__":
    build()
