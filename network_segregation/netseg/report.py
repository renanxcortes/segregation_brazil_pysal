"""Descriptive tables for RQ1 and LaTeX macros for numbers quoted in the text."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def _sel(indices, spec, index):
    d = indices[(indices["spec"] == spec) & (indices["index"] == index)].copy()
    d["dH"] = d["net"] - d["euc"]
    d["pdH"] = 100.0 * d["dH"] / d["euc"]
    return d


def gap_table(indices, spec="main", index="H") -> pd.DataFrame:
    d = _sel(indices, spec, index).rename(columns={"euc": "H_euc", "net": "H_net"})
    return d[["H_euc", "H_net", "dH", "pdH"]].describe().T


def rank_comparison(indices, spec="main", index="H", top=15) -> pd.DataFrame:
    d = _sel(indices, spec, index)
    d["rank_euc"] = d["euc"].rank(ascending=False, method="min").astype(int)
    d["rank_net"] = d["net"].rank(ascending=False, method="min").astype(int)
    d["rank_change"] = d["rank_euc"] - d["rank_net"]
    keep = (d["rank_euc"] <= top) | (d["rank_net"] <= top)
    return d.loc[keep, ["NM_MUN", "rank_euc", "rank_net", "rank_change"]].sort_values("rank_euc").reset_index(drop=True)


def robustness_table(indices) -> pd.DataFrame:
    rows = []
    for (spec, index), g in indices.groupby(["spec", "index"], sort=False):
        d = _sel(g, spec, index)
        rows.append({"spec": spec, "index": index, "mean_dH": d["dH"].mean(), "mean_pdH": d["pdH"].mean(),
                     "share_positive": (d["dH"] > 0).mean(), "pearson": d["euc"].corr(d["net"]),
                     "spearman": d["euc"].corr(d["net"], method="spearman")})
    return pd.DataFrame(rows)


def write_macros(values: dict, path) -> None:
    lines = []
    for name, val in values.items():
        if not re.fullmatch(r"[A-Za-z]+", name):
            raise ValueError(f"LaTeX macro names must be letters only: {name!r}")
        lines.append(f"\\newcommand{{\\{name}}}{{{val}}}\n")
    Path(path).write_text("".join(lines), encoding="utf-8", newline="\n")  # UTF-8, LF on every platform
