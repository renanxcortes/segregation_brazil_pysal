"""Export the 5 REBEP illustrations as separate, editable, >=300dpi PDF files.

REBEP wants each illustration as its own file (EPS/WMF/editable PDF, >=300dpi),
numbered the same way as in the manuscript. The project's main figure
pipeline (scripts/figures.py) writes 200dpi PNGs meant for LaTeX inclusion;
this script does not touch that pipeline. It reuses the same data loader
(``figures.load``) and re-draws the 5 figures kept in the REBEP version,
saving true vector PDFs (matplotlib's PDF backend is vector-native; only
the ``imshow`` heatmap and scatter markers are rasterised, at 300dpi) at:

    draft/rebep/figures_submission/Figure1.pdf  distributions
    draft/rebep/figures_submission/Figure2.pdf  correlation + clustering (2 panels)
    draft/rebep/figures_submission/Figure3.pdf  rankings
    draft/rebep/figures_submission/Figure4.pdf  minority share
    draft/rebep/figures_submission/Figure5.pdf  national maps (2 panels)

Usage (from anywhere; paths are resolved from this file's location):
    python draft/rebep/export_submission_figures.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTDIR = HERE / "figures_submission"

sys.path.insert(0, str(ROOT / "scripts"))
import figures as F  # noqa: E402  (project's figure/data module)

DPI = 300


def export_distributions():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import gaussian_kde

    df = F.load()
    fig, axes = plt.subplots(3, 3, figsize=(13, 11))
    for ax, m in zip(axes.ravel(), F.MEASURES):
        lo, hi = F.MEASURE_XLIM[m]
        grid = np.linspace(lo, hi, 400)
        for region in F.REGION_ORDER:
            vals = df.loc[df["REGION"] == region, m].to_numpy()
            if vals.size < 2 or np.ptp(vals) == 0:
                continue
            kde = gaussian_kde(vals)
            ax.plot(grid, kde(grid), label=region, lw=1.4)
        ax.set_title(F.MEASURE_LABELS[m])
        ax.set_xlim(lo, hi)
        ax.set_yticks([])
        ax.set_ylabel("")
    axes.ravel()[0].legend(fontsize=7)
    fig.suptitle("Distribution of each segregation measure by macro-region "
                 "(2022, 319 cities)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUTDIR / "Figure1.pdf", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def export_correlation_and_clustering():
    """Figure 2: (a) Spearman correlation heatmap, (b) hierarchical
    clustering dendrogram -- one combined file, matching the merged
    subfigure in manuscript.tex."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import squareform

    df = F.load()
    corr = df[F.MEASURES].corr(method="spearman")
    labels = [F.MEASURE_LABELS[m] for m in F.MEASURES]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(17, 8))

    # (a) heatmap
    im = ax_a.imshow(corr.to_numpy(), vmin=-1, vmax=1, cmap="RdBu_r")
    ax_a.set_xticks(range(len(F.MEASURES)))
    ax_a.set_xticklabels(labels, rotation=45, ha="right")
    ax_a.set_yticks(range(len(F.MEASURES)))
    ax_a.set_yticklabels(labels)
    for i in range(len(F.MEASURES)):
        for j in range(len(F.MEASURES)):
            v = corr.iloc[i, j]
            ax_a.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                      color="white" if abs(v) > 0.6 else "black")
    fig.colorbar(im, ax=ax_a, shrink=0.8, label="Spearman rho")
    ax_a.set_title("(a) Spearman rank correlation", fontsize=12)

    # (b) dendrogram
    dist = 1.0 - corr.abs().to_numpy()
    np.fill_diagonal(dist, 0.0)
    dist = (dist + dist.T) / 2.0
    Z = linkage(squareform(dist, checks=False), method="average")
    dendrogram(Z, labels=labels, ax=ax_b, leaf_rotation=90)
    ax_b.set_title("(b) Hierarchical clustering", fontsize=12)
    ax_b.set_ylabel("distance")

    fig.tight_layout()
    fig.savefig(OUTDIR / "Figure2.pdf", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def export_rankings():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = F.load().merge(F._municipio_names(), on="COD_MUNICIPIO", how="left")
    df["label"] = df["NM_MUN"] + " (" + df["UF"] + ")"

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    for ax, m in zip(axes, F.RANK_MEASURES):
        top = (df.nlargest(15, m)[["label", m]]
               .set_index("label")[m][::-1])
        top.plot.barh(ax=ax, color="#4c72b0")
        ax.set_title(f"Top 15 cities - {F.MEASURE_LABELS[m]}")
        ax.set_xlabel(F.MEASURE_LABELS[m])
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=8)
    fig.suptitle(f"Most-segregated cities by dimension ({len(df)} cities, 2022)",
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUTDIR / "Figure3.pdf", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def export_minorityshare():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
    except Exception:
        lowess = None

    df = F.load()
    cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    region_colors = {r: cycle[i % len(cycle)]
                     for i, r in enumerate(F.REGION_ORDER)}
    ylim_crop = {"RelativeConcentration": (-1.05, 0.75)}

    fig, axes = plt.subplots(3, 3, figsize=(14, 12))
    for ax, m in zip(axes.ravel(), F.MEASURES):
        for region in F.REGION_ORDER:
            sub = df[df["REGION"] == region]
            ax.scatter(sub["ppp"], sub[m], s=12, alpha=0.55,
                       color=region_colors[region], label=region,
                       edgecolors="none")
        if lowess is not None:
            fit = df[["ppp", m]].dropna().sort_values("ppp")
            sm = lowess(fit[m], fit["ppp"], frac=0.5)
            ax.plot(sm[:, 0], sm[:, 1], color="black", lw=1.8)
        ax.set_title(F.MEASURE_LABELS[m])
        ax.set_xlabel("share preta+parda")
        if m in ylim_crop:
            lo, hi = ylim_crop[m]
            n_hidden = int((df[m] < lo).sum())
            ax.set_ylim(lo, hi)
            ax.text(0.02, 0.03,
                    f"y-axis cropped at {lo:g}; {n_hidden} cities below "
                    f"(min {df[m].min():.2f}) not shown",
                    transform=ax.transAxes, fontsize=7, color="firebrick",
                    va="bottom")
    axes.ravel()[0].legend(fontsize=7)
    fig.suptitle(f"Each segregation measure vs preta+parda population share "
                 f"({len(df)} cities, 2022)", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUTDIR / "Figure4.pdf", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def export_national_maps():
    """Figure 5: (a) Dissimilarity, (b) Spatial Dissimilarity -- one combined
    file, matching the merged subfigure in manuscript.tex."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import geopandas as gpd

    if not F.MUNICIPIO_POLYGONS.exists():
        raise SystemExit(
            f"{F.MUNICIPIO_POLYGONS} not found - run "
            f"'python scripts/build_municipio_polygons.py' first")

    df = F.load()[["COD_MUNICIPIO", "Dissim", "SpatialDissim"]]
    poly = gpd.read_file(F.MUNICIPIO_POLYGONS).rename(
        columns={"CD_MUN": "COD_MUNICIPIO"})
    poly["COD_MUNICIPIO"] = poly["COD_MUNICIPIO"].astype(str)
    poly = poly.merge(df, on="COD_MUNICIPIO", how="left")

    pts = poly.copy()
    pts["geometry"] = pts.geometry.representative_point()
    ufs = gpd.read_file(F.UF_POLYGONS) if F.UF_POLYGONS.exists() else None

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(17, 10))
    panels = [("Dissim", ax_a, "(a) Dissimilarity index"),
              ("SpatialDissim", ax_b, "(b) Spatial Dissimilarity index")]
    for col, ax, title in panels:
        if ufs is not None:
            ufs.plot(ax=ax, color="#eeeeee", edgecolor="#bcbcbc",
                     linewidth=0.5)
        miss = pts[pts[col].isna()]
        if len(miss):
            miss.plot(ax=ax, color="lightgrey", markersize=16,
                      edgecolor="white", linewidth=0.3)
        pts[pts[col].notna()].plot(
            column=col, ax=ax, cmap="YlOrRd", markersize=28,
            edgecolor="white", linewidth=0.3, legend=True,
            legend_kwds={"shrink": 0.6, "label": F.MEASURE_LABELS[col]})
        ax.set_axis_off()
        ax.set_title(title, fontsize=12)
    fig.suptitle("Racial residential segregation across the 319 "
                 "municipalities: one point per city, over state boundaries.",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(OUTDIR / "Figure5.pdf", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    export_distributions()
    print("wrote Figure1.pdf (distributions)")
    export_correlation_and_clustering()
    print("wrote Figure2.pdf (correlation + clustering)")
    export_rankings()
    print("wrote Figure3.pdf (rankings)")
    export_minorityshare()
    print("wrote Figure4.pdf (minority share)")
    export_national_maps()
    print("wrote Figure5.pdf (national maps)")


if __name__ == "__main__":
    main()
