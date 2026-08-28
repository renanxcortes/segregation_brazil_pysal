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
    df = pd.read_csv(csv_path, sep=";", usecols=usecols, dtype={"CD_SETOR": str})

    df[RACE_VARS] = (
        df[RACE_VARS].replace("X", 0).apply(pd.to_numeric, errors="coerce").fillna(0).astype("int64")
    )

    df["pop_total"] = df[RACE_VARS].sum(axis=1).astype("int64")
    df["pp_total"] = df[GROUP_VARS].sum(axis=1).astype("int64")
    df["COD_MUNICIPIO"] = df["CD_SETOR"].str[:7]
    df["COD_UF"] = df["CD_SETOR"].str[:2]
    return df
