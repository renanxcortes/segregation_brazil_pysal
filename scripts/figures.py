"""Regenerate every table and figure in the paper from outputs/.

Usage:
    python scripts/figures.py <cmd>

where <cmd> is one of the subcommands below (or ``all`` to run them all):
    table1             descriptive Table 1 (cities per macro-region)
    fig_distributions  (Task 11)
    fig_correlation    (Task 12)
    fig_rankings       (Task 13)
    fig_regional       (Task 14)
    fig_minorityshare  (Task 15)
    fig_maps           (Task 16)
"""
import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "outputs" / "segregation_profiles_2022.parquet"
UNIVERSE = ROOT / "outputs" / "city_universe_2022.csv"
TABLES = ROOT / "outputs" / "tables"
FIGDIR = ROOT / "figures"

# The nine segregation measures, in canonical order.
MEASURES = ["Dissim", "SpatialDissim", "Gini", "Entropy", "Isolation",
            "DistanceDecayIsolation", "RelativeConcentration",
            "RelativeCentralization", "RelativeClustering"]

# Two-digit IBGE UF code -> macro-region. Covers all 27 units.
REGION_BY_UF = {
    "11": "Norte", "12": "Norte", "13": "Norte", "14": "Norte", "15": "Norte",
    "16": "Norte", "17": "Norte",
    "21": "Nordeste", "22": "Nordeste", "23": "Nordeste", "24": "Nordeste",
    "25": "Nordeste", "26": "Nordeste", "27": "Nordeste", "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste", "32": "Sudeste", "33": "Sudeste", "35": "Sudeste",
    "41": "Sul", "42": "Sul", "43": "Sul",
    "50": "Centro-Oeste", "51": "Centro-Oeste", "52": "Centro-Oeste",
    "53": "Centro-Oeste",
}

REGION_ORDER = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def load() -> pd.DataFrame:
    """Merge the city universe and the segregation profiles.

    Returns one row per analyzed city with:
      - all universe columns (incl. ``UF``); universe ``n_tracts`` is the
        pre zero-pop-drop count, universe ``pop_total`` -> ``pop_total``.
      - all profile columns; on name clashes the profile copy gets a ``_p``
        suffix (so ``n_tracts_p`` = post zero-pop-drop count = actually
        analyzed, ``COD_UF_p`` = profile's UF code, ``pop_total_p``).
      - ``REGION``: macro-region derived from universe ``COD_UF``.

    fatal_error rows are dropped (there are 0 in the 2022 run).
    """
    prof = pd.read_parquet(PROFILES)
    uni = pd.read_csv(UNIVERSE, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    df = uni.merge(prof, on="COD_MUNICIPIO", suffixes=("", "_p"))
    df = df[~df["fatal_error"].astype(bool)].copy()
    df["REGION"] = df["COD_UF"].map(REGION_BY_UF)
    return df


def table1() -> None:
    """Descriptive Table 1: cities analyzed per macro-region + Brasil total.

    Tract counts use ``n_tracts_p`` (the post zero-pop-drop count from the
    parquet = tracts actually fed to the segregation estimators).
    """
    df = load()
    tracts = "n_tracts_p"  # parquet = post zero-pop-drop = actually analyzed

    g = df.groupby("REGION").agg(
        cities=("COD_MUNICIPIO", "size"),
        tracts_min=(tracts, "min"),
        tracts_med=(tracts, "median"),
        tracts_max=(tracts, "max"),
        ppp_min=("ppp", "min"),
        ppp_med=("ppp", "median"),
        ppp_max=("ppp", "max"),
    ).reindex(REGION_ORDER)

    total = pd.DataFrame({
        "cities": [len(df)],
        "tracts_min": [df[tracts].min()],
        "tracts_med": [df[tracts].median()],
        "tracts_max": [df[tracts].max()],
        "ppp_min": [df["ppp"].min()],
        "ppp_med": [df["ppp"].median()],
        "ppp_max": [df["ppp"].max()],
    }, index=["Brasil"])

    out = pd.concat([g, total])
    out["cities"] = out["cities"].astype(int)
    for c in ("tracts_min", "tracts_med", "tracts_max"):
        out[c] = out[c].astype(int)
    out = out.round({"ppp_min": 3, "ppp_med": 3, "ppp_max": 3})

    # LaTeX-safe display labels (no bare _ % & # so the file \input-s cleanly).
    disp = out.rename(columns={
        "cities": "Cidades",
        "tracts_min": "Setores (mín.)",
        "tracts_med": "Setores (mediana)",
        "tracts_max": "Setores (máx.)",
        "ppp_min": "PPP (mín.)",
        "ppp_med": "PPP (mediana)",
        "ppp_max": "PPP (máx.)",
    })
    disp.index.name = "Região"

    TABLES.mkdir(parents=True, exist_ok=True)
    latex = disp.to_latex(
        caption="Cidades analisadas por macrorregião (Censo 2022).",
        label="tab:descriptive",
        float_format="%.3f",
    )
    with open(TABLES / "table1_descriptive.tex", "w", encoding="utf-8",
              newline="\n") as f:
        f.write(latex)

    print(out.to_string())


def _todo(name: str):
    def fn() -> None:
        raise SystemExit(f"{name}: not implemented yet")
    return fn


# Subcommand registry. Tasks 11-16 replace the _todo placeholders with real
# functions; the `all` dispatch below iterates this dict in order.
DISPATCH = {
    "table1": table1,
    "fig_distributions": _todo("fig_distributions"),
    "fig_correlation": _todo("fig_correlation"),
    "fig_rankings": _todo("fig_rankings"),
    "fig_regional": _todo("fig_regional"),
    "fig_minorityshare": _todo("fig_minorityshare"),
    "fig_maps": _todo("fig_maps"),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=list(DISPATCH) + ["all"])
    args = ap.parse_args()
    if args.cmd == "all":
        for fn in DISPATCH.values():
            fn()
    else:
        DISPATCH[args.cmd]()


if __name__ == "__main__":
    main()
