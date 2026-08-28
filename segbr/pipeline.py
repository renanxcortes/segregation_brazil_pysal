"""Checkpointed, resumable nationwide segregation-profiling loop."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from segbr.cities import build_city_gdf
from segbr.measures import compute_profile

FAILURES_CSV_NAME = "failures_2022.csv"


def _load_checkpoint(out_path: Path) -> list[dict]:
    """Return the rows already persisted at ``out_path`` (empty if none)."""
    if out_path.exists():
        return pd.read_parquet(out_path).to_dict("records")
    return []


def run_all(universe_df, census_df, shp_dir, out_path, *, measures=None,
            time_budget_s=None, limit=None) -> pd.DataFrame:
    """Compute segregation profiles for every municipality in ``universe_df``.

    One Parquet row is written per city to ``out_path`` after that city is
    processed, so the call is resumable: municipalities already present in the
    file are skipped and only the missing ones are appended. A per-city
    exception (missing shapefile, bad geometry, unknown code) is caught and
    stored as a row with ``fatal_error`` set -- the loop never aborts. When any
    such row exists, a companion ``failures_2022.csv`` is written next to
    ``out_path``. Returns the full results DataFrame.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Read the checkpoint once; keep completed rows in memory from here on.
    records = _load_checkpoint(out_path)
    done = {r["COD_MUNICIPIO"] for r in records}

    todo = universe_df[~universe_df["COD_MUNICIPIO"].isin(done)]
    if limit is not None:
        todo = todo.head(limit)

    for rec in todo.itertuples(index=False):
        row = {"COD_MUNICIPIO": rec.COD_MUNICIPIO, "COD_UF": rec.COD_UF, "fatal_error": ""}
        try:
            # Everything that could raise stays inside the try -- never-abort is
            # load-bearing, so even the pop_total coercion is guarded.
            row["pop_total_universe"] = int(rec.pop_total)
            gdf = build_city_gdf(rec.COD_MUNICIPIO, census_df, shp_dir)
            prof = compute_profile(gdf, measures=measures, time_budget_s=time_budget_s)
            row["timings"] = str(prof.pop("timings", {}))
            row.update(prof)
        except Exception as exc:  # noqa: BLE001 - isolate per-city failure
            row["fatal_error"] = f"{type(exc).__name__}: {exc}"

        records.append(row)
        # Incremental persist after every city -> resumable across a kill.
        # Write to a temp file on the same filesystem then atomically replace, so
        # a kill mid-write cannot corrupt the existing checkpoint.
        tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        pd.DataFrame(records).to_parquet(tmp, index=False)
        os.replace(tmp, out_path)

    full = pd.DataFrame(records)
    if full.empty:
        return full
    failures = full[full["fatal_error"].astype(bool)]
    if len(failures):
        failures.to_csv(out_path.with_name(FAILURES_CSV_NAME), index=False)
    return full
