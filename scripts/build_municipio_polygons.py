"""Dissolve 2022 tract geometries to municipality and state (UF) polygons.

Builds two cached layers used only by the national maps in ``figures.py``:

* ``outputs/municipio_polygons.gpkg`` - one polygon per universe city (319),
  dissolved from the per-UF tract shapefiles in ``shapefiles_2022/``.
* ``outputs/uf_polygons.gpkg`` - one polygon per state (27), dissolved from
  *all* tracts (not just universe cities); a light background context layer.

Geometries are simplified with a topology-preserving tolerance (default
``0.005`` degrees, ~500 m) before writing: the national maps are drawn at
Brazil scale where tract-boundary precision is invisible, and the raw dissolve
is ~23 MB versus well under 2 MB simplified.

The municipality dissolve is heavy (SP alone is ~27k tracts), so that step is
resumable / idempotent:

* If the GPKG already exists and holds all 319 universe codes, it does nothing.
* Otherwise it processes UFs one at a time; a UF whose codes are all already in
  the GPKG is skipped, and the GPKG is rewritten atomically (temp file +
  ``os.replace``) after each UF, so a kill mid-run leaves a valid partial GPKG
  that the next run resumes from.

The UF layer is small and rebuilt in one pass (skipped if already complete).

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
UF_OUT = ROOT / "outputs" / "uf_polygons.gpkg"

TOLERANCE = 0.005  # degrees (~500 m) - invisible at Brazil scale

# All 27 UF acronyms (shapefile folder prefixes).
UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]

# The shapefiles are already in SIRGAS 2000 geographic coordinates (equivalent
# to EPSG:4674). We keep that native CRS rather than reprojecting: the local
# PROJ database cannot serialise an EPSG code on write, but the native .prj WKT
# round-trips fine. All 27 UF shapefiles share this CRS, so concatenation is
# safe without any transform.


def _simplify(g: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    g = g.copy()
    g["geometry"] = g.geometry.simplify(TOLERANCE, preserve_topology=True)
    return g


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
    return _simplify(g)


def build_municipios() -> None:
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
        size_mb = OUT.stat().st_size / 1e6
        print(f"DONE: {len(present)}/{len(all_codes)} municipality polygons -> "
              f"{OUT} ({size_mb:.2f} MB)")


def build_ufs() -> None:
    """One polygon per state, dissolved from every tract (universe or not)."""
    if UF_OUT.exists():
        try:
            existing = gpd.read_file(UF_OUT)
            if len(existing) == len(UFS):
                print(f"UF GPKG already complete ({len(existing)}/27)")
                return
        except Exception:
            pass

    parts = []
    for uf in UFS:
        shp = SHP_DIR / f"{uf}_setores_CD2022" / f"{uf}_setores_CD2022.shp"
        if not shp.exists():
            raise FileNotFoundError(shp)
        t0 = time.time()
        g = gpd.read_file(shp, columns=["CD_UF"])
        g = g.dissolve(by="CD_UF").reset_index()[["CD_UF", "geometry"]]
        g = _simplify(g)
        parts.append(g)
        print(f"[{uf}] state polygon in {time.time() - t0:5.1f}s")

    ufs = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=parts[0].crs)
    tmp = UF_OUT.with_suffix(".gpkg.tmp")
    if tmp.exists():
        tmp.unlink()
    ufs.to_file(tmp, driver="GPKG")
    os.replace(tmp, UF_OUT)
    size_mb = UF_OUT.stat().st_size / 1e6
    print(f"DONE: {len(ufs)} state polygons -> {UF_OUT} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    build_municipios()
    build_ufs()
