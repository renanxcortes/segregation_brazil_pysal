from __future__ import annotations

from pathlib import Path

import pandas as pd

RACE_VARS = ["V01317", "V01318", "V01319", "V01320", "V01321"]
GROUP_VARS = ["V01318", "V01320"]  # preta + parda


def load_census(csv_path: str | Path) -> pd.DataFrame:
    """Load the 2022 'cor ou raça' tract aggregates, cleaned.

    Returns one row per census tract with integer race counts, derived
    ``pop_total`` and ``pp_total`` (preta + parda), and municipality / UF codes.
    """
    usecols = ["CD_SETOR", *RACE_VARS]
    df = pd.read_csv(
        csv_path,
        sep=";",
        usecols=usecols,
        dtype={"CD_SETOR": str, **{v: str for v in RACE_VARS}},
    )

    df[RACE_VARS] = (
        df[RACE_VARS]
        .replace({"X": None})
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    df["pop_total"] = df[RACE_VARS].sum(axis=1).astype("int64")
    df["pp_total"] = df[GROUP_VARS].sum(axis=1).astype("int64")
    df["COD_MUNICIPIO"] = df["CD_SETOR"].str[:7]
    df["COD_UF"] = df["CD_SETOR"].str[:2]
    return df


def municipality_universe(df: pd.DataFrame, threshold: int = 100_000) -> pd.DataFrame:
    """Municipalities whose total 2022 population exceeds ``threshold``."""
    grp = (
        df.groupby(["COD_MUNICIPIO", "COD_UF"], as_index=False)
        .agg(pop_total=("pop_total", "sum"), n_tracts=("CD_SETOR", "size"))
    )
    grp = grp[grp["pop_total"] > threshold]
    grp = grp.sort_values("pop_total", ascending=False).reset_index(drop=True)
    return grp[["COD_MUNICIPIO", "COD_UF", "pop_total", "n_tracts"]]
