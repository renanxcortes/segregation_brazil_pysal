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


# Readable panel titles for the nine measures.
MEASURE_LABELS = {
    "Dissim": "Dissimilarity (D)",
    "SpatialDissim": "Spatial Dissimilarity",
    "Gini": "Gini",
    "Entropy": "Entropy (H)",
    "Isolation": "Isolation",
    "DistanceDecayIsolation": "Distance-Decay Isolation",
    "RelativeConcentration": "Relative Concentration",
    "RelativeCentralization": "Relative Centralization",
    "RelativeClustering": "Relative Clustering",
}

# Per-measure x-range for the KDE panels. The six evenness/exposure measures
# live in [0, 1]; Entropy is tiny and right-skewed so we crop hard. The three
# spatial-proximity measures can be negative; RelativeConcentration has a long
# left tail (~9 cities near -2) that we crop for readability.
MEASURE_XLIM = {
    "Dissim": (0.0, 0.5),
    "SpatialDissim": (0.0, 0.4),
    "Gini": (0.0, 0.65),
    "Entropy": (0.0, 0.25),
    "Isolation": (0.0, 1.0),
    "DistanceDecayIsolation": (0.0, 1.0),
    "RelativeConcentration": (-1.0, 0.7),
    "RelativeCentralization": (-0.35, 0.2),
    "RelativeClustering": (-0.45, 1.05),
}


def fig_distributions() -> None:
    """§5.1 - distribution of each of the nine measures across the 319 cities.

    3x3 grid, one panel per measure, with a per-region KDE overlay. Also writes
    the summary-stats table (nine measures x {mean, std, 25%, 50%, 75%, min,
    max}).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import gaussian_kde

    df = load()

    fig, axes = plt.subplots(3, 3, figsize=(13, 11))
    for ax, m in zip(axes.ravel(), MEASURES):
        lo, hi = MEASURE_XLIM[m]
        grid = np.linspace(lo, hi, 400)
        for region in REGION_ORDER:
            vals = df.loc[df["REGION"] == region, m].to_numpy()
            if vals.size < 2 or np.ptp(vals) == 0:
                continue
            kde = gaussian_kde(vals)
            ax.plot(grid, kde(grid), label=region, lw=1.4)
        ax.set_title(MEASURE_LABELS[m])
        ax.set_xlim(lo, hi)
        ax.set_yticks([])
        ax.set_ylabel("")
    axes.ravel()[0].legend(fontsize=7)
    fig.suptitle("Distribution of each segregation measure by macro-region "
                 "(2022, 319 cities)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGDIR / "fig_distributions.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Summary-stats table: nine measures x seven statistics.
    stats = (df[MEASURES]
             .describe(percentiles=[0.25, 0.5, 0.75]).T
             [["mean", "std", "25%", "50%", "75%", "min", "max"]]
             .round(3))
    stats.index = [MEASURE_LABELS[m] for m in stats.index]
    stats.index.name = "Medida"

    # LaTeX-safe display labels (no bare _ % & # so the file \input-s cleanly).
    disp = stats.rename(columns={
        "mean": "Média", "std": "Desvio-padrão",
        "25%": "P25", "50%": "Mediana", "75%": "P75",
        "min": "Mínimo", "max": "Máximo",
    })

    TABLES.mkdir(parents=True, exist_ok=True)
    latex = disp.to_latex(
        caption="Estatísticas descritivas dos nove índices de segregação "
                "(todas as 319 cidades, Censo 2022).",
        label="tab:summary",
        float_format="%.3f",
    )
    with open(TABLES / "table_summary_stats.tex", "w", encoding="utf-8",
              newline="\n") as f:
        f.write(latex)

    print(stats.to_string())


# Compact column codes for the 9x9 LaTeX correlation matrix (a full-label
# header would overflow the page). Row labels keep the readable MEASURE_LABELS.
MEASURE_CODES = {
    "Dissim": "D",
    "SpatialDissim": "SD",
    "Gini": "G",
    "Entropy": "H",
    "Isolation": "Iso",
    "DistanceDecayIsolation": "DDI",
    "RelativeConcentration": "RCo",
    "RelativeCentralization": "RCe",
    "RelativeClustering": "RCl",
}


def fig_correlation() -> None:
    """§5.2 - do the nine dimensions agree?

    Spearman rank-correlation of the nine measures across the analyzed cities.
    Writes a printed-value heatmap (``fig_correlation.png``), the 9x9 matrix as
    LaTeX (``table2_correlation.tex``), and a companion dendrogram +
    scree summary (``fig_measure_clustering.png``) built from 1 - |rho|.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import squareform

    df = load()
    corr = df[MEASURES].corr(method="spearman")
    labels = [MEASURE_LABELS[m] for m in MEASURES]

    # --- Heatmap -----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(corr.to_numpy(), vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(MEASURES)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(len(MEASURES)))
    ax.set_yticklabels(labels)
    for i in range(len(MEASURES)):
        for j in range(len(MEASURES)):
            v = corr.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if abs(v) > 0.6 else "black")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman rho")
    ax.set_title(f"Inter-measure Spearman correlation "
                 f"({len(df)} cities, 2022)", fontsize=12)
    fig.tight_layout()
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGDIR / "fig_correlation.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # --- Hierarchical clustering + PCA scree on 1 - |rho| -----------------
    dist = 1.0 - corr.abs().to_numpy()
    np.fill_diagonal(dist, 0.0)
    dist = (dist + dist.T) / 2.0
    Z = linkage(squareform(dist, checks=False), method="average")

    eigvals = np.linalg.eigvalsh(corr.to_numpy())[::-1]
    explained = eigvals / eigvals.sum()

    fig, (axd, axs) = plt.subplots(1, 2, figsize=(13, 5))
    dendrogram(Z, labels=labels, ax=axd, leaf_rotation=90)
    axd.set_title("Measure clustering (average linkage, 1 - |rho|)")
    axd.set_ylabel("distance")
    axs.bar(range(1, len(explained) + 1), explained, color="#4c72b0")
    axs.plot(range(1, len(explained) + 1), np.cumsum(explained),
             "-o", color="#c44e52")
    axs.set_title("PCA on the correlation matrix")
    axs.set_xlabel("component")
    axs.set_ylabel("variance explained")
    axs.set_xticks(range(1, len(explained) + 1))
    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_measure_clustering.png", dpi=200,
                bbox_inches="tight")
    plt.close(fig)

    # --- LaTeX table -----------------------------------------------------
    disp = corr.round(2).copy()
    disp.index = labels
    disp.index.name = "Medida"
    disp.columns = [MEASURE_CODES[m] for m in MEASURES]

    TABLES.mkdir(parents=True, exist_ok=True)
    latex = disp.to_latex(
        caption="Correlação de Spearman entre os nove índices de segregação "
                "(nível cidade, Censo 2022). Colunas: "
                "D=Dissimilaridade, SD=Dissimilaridade espacial, G=Gini, "
                "H=Entropia, Iso=Isolamento, DDI=Isolamento com decaimento, "
                "RCo=Concentração relativa, RCe=Centralização relativa, "
                "RCl=Agrupamento relativo.",
        label="tab:corr",
        float_format="%.2f",
    )
    with open(TABLES / "table2_correlation.tex", "w", encoding="utf-8",
              newline="\n") as f:
        f.write(latex)

    print(corr.round(2).to_string())
    print()
    print("PCA variance explained:", np.round(explained, 3).tolist())
    print("cumulative:", np.round(np.cumsum(explained), 3).tolist())

    # Redundant (|rho| > 0.9) and distinct (|rho| < 0.5) pairs.
    pairs = []
    for i in range(len(MEASURES)):
        for j in range(i + 1, len(MEASURES)):
            pairs.append((MEASURES[i], MEASURES[j], corr.iloc[i, j]))
    print("\nredundant |rho|>0.9:")
    for a, b, r in sorted(pairs, key=lambda p: -abs(p[2])):
        if abs(r) > 0.9:
            print(f"  {a:24s} {b:24s} {r:+.3f}")
    print("distinct |rho|<0.5:")
    for a, b, r in sorted(pairs, key=lambda p: abs(p[2])):
        if abs(r) < 0.5:
            print(f"  {a:24s} {b:24s} {r:+.3f}")


MUNICIPIO_NAMES = ROOT / "outputs" / "municipio_names.csv"

# The three contrasting dimensions shown as ranked bar charts: an evenness
# measure (spatial sorting), an exposure measure (composition-driven), and a
# spatial-proximity measure (clustering of minority tracts).
RANK_MEASURES = ["Dissim", "Isolation", "RelativeClustering"]


def _municipio_names() -> pd.DataFrame:
    """COD_MUNICIPIO -> NM_MUN, built from the shapefiles and cached to CSV."""
    if not MUNICIPIO_NAMES.exists():
        import build_municipio_names
        build_municipio_names.build()
    return pd.read_csv(MUNICIPIO_NAMES, dtype={"COD_MUNICIPIO": str})


def fig_rankings() -> None:
    """§5.3 - which cities are most segregated, and does it depend on the
    dimension?

    Horizontal bar charts of the top-15 cities for three contrasting measures
    (Dissim, Isolation, RelativeClustering), plus a 9x9 Kendall-tau matrix of
    the city rankings across all nine measures (``table3_rank_correlation.tex``).
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    df = load().merge(_municipio_names(), on="COD_MUNICIPIO", how="left")
    df["label"] = df["NM_MUN"] + " (" + df["UF"] + ")"

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    for ax, m in zip(axes, RANK_MEASURES):
        top = (df.nlargest(15, m)[["label", m]]
               .set_index("label")[m][::-1])
        top.plot.barh(ax=ax, color="#4c72b0")
        ax.set_title(f"Top 15 cities - {MEASURE_LABELS[m]}")
        ax.set_xlabel(MEASURE_LABELS[m])
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=8)
    fig.suptitle(f"Most-segregated cities by dimension ({len(df)} cities, 2022)",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGDIR / "fig_rankings.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # --- Kendall-tau of the city rankings across the nine measures -------
    ranks = df[MEASURES].rank()
    tau = ranks.corr(method="kendall").round(2)

    disp = tau.copy()
    disp.index = [MEASURE_LABELS[m] for m in MEASURES]
    disp.index.name = "Medida"
    disp.columns = [MEASURE_CODES[m] for m in MEASURES]

    TABLES.mkdir(parents=True, exist_ok=True)
    latex = disp.to_latex(
        caption="Correlação de postos de Kendall (tau) entre os "
                "ordenamentos de cidades pelos nove índices de segregação "
                "(nível cidade, Censo 2022). Colunas: "
                "D=Dissimilaridade, SD=Dissimilaridade espacial, G=Gini, "
                "H=Entropia, Iso=Isolamento, DDI=Isolamento com decaimento, "
                "RCo=Concentração relativa, RCe=Centralização relativa, "
                "RCl=Agrupamento relativo.",
        label="tab:rankcorr",
        float_format="%.2f",
    )
    with open(TABLES / "table3_rank_correlation.tex", "w", encoding="utf-8",
              newline="\n") as f:
        f.write(latex)

    # --- Console summary for the Results prose --------------------------
    for m in RANK_MEASURES:
        names = df.nlargest(5, m)["label"].tolist()
        print(f"top 5 {m}: {names}")
    for a, b in [("Dissim", "Isolation"), ("Dissim", "RelativeClustering"),
                 ("Isolation", "RelativeClustering")]:
        sa = set(df.nlargest(5, a)["label"])
        sb = set(df.nlargest(5, b)["label"])
        print(f"top-5 overlap {a} vs {b}: {len(sa & sb)} -> {sorted(sa & sb)}")
    print("\nKendall tau matrix:")
    print(tau.to_string())
    off = tau.to_numpy()[~np.eye(len(MEASURES), dtype=bool)]
    print(f"\ntau range (off-diagonal): {off.min():.2f} - {off.max():.2f}")
    print(f"Dissim-Isolation Kendall tau: "
          f"{tau.loc['Dissim', 'Isolation']:.2f}")


def _todo(name: str):
    def fn() -> None:
        raise SystemExit(f"{name}: not implemented yet")
    return fn


# Subcommand registry. Tasks 11-16 replace the _todo placeholders with real
# functions; the `all` dispatch below iterates this dict in order.
DISPATCH = {
    "table1": table1,
    "fig_distributions": fig_distributions,
    "fig_correlation": fig_correlation,
    "fig_rankings": fig_rankings,
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
