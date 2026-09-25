"""RQ2: city-level OLS of the Euclidean-network gap on street-network topology."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

FORMULA_KR = ("{dv} ~ log_intersection_density + z_circuity + z_meshedness + log_cyclomatic + z_dead_end"
              " + log_pop_density + z_H_euc + log_cyclomatic:z_circuity")
FORMULA_FULL = FORMULA_KR + " + z_fragmentation"
MAIN_EFFECTS = ["log_intersection_density", "z_circuity", "z_meshedness", "log_cyclomatic", "z_dead_end",
                "log_pop_density", "z_H_euc", "z_fragmentation"]


def _z(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def analysis_frame(indices: pd.DataFrame, cities: pd.DataFrame, spec: str = "main", index: str = "H") -> pd.DataFrame:
    sel = indices[(indices["spec"] == spec) & (indices["index"] == index)][["COD_MUNICIPIO", "euc", "net"]]
    df = cities.merge(sel.rename(columns={"euc": "H_euc", "net": "H_net"}), on="COD_MUNICIPIO", how="inner")
    df["dH"] = df["H_net"] - df["H_euc"]
    df["pdH"] = 100.0 * df["dH"] / df["H_euc"]
    df["z_circuity"] = _z(df["circuity_avg"])
    df["z_meshedness"] = _z(df["meshedness"])
    df["z_dead_end"] = _z(df["prop_dead_end"])
    df["z_fragmentation"] = _z(df["fragmentation"])
    df["z_H_euc"] = _z(df["H_euc"])
    df["log_intersection_density"] = np.log(df["intersection_density_km"])
    df["log_cyclomatic"] = np.log(df["cyclomatic"])
    df["log_pop_density"] = np.log(df["pop_urban"] / df["area_km2"])
    return df.reset_index(drop=True)


def fit(df: pd.DataFrame, dv: str, full: bool):
    formula = (FORMULA_FULL if full else FORMULA_KR).format(dv=dv)
    return smf.ols(formula, data=df).fit(cov_type="HC3")


def vif_table(df: pd.DataFrame) -> pd.DataFrame:
    X = df[MAIN_EFFECTS].assign(const=1.0).to_numpy()
    return pd.DataFrame({"variable": MAIN_EFFECTS,
                         "vif": [variance_inflation_factor(X, k) for k in range(len(MAIN_EFFECTS))]})
