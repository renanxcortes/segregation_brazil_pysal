"""All manuscript figures (PDF, vector). Colours follow the dataviz reference palette."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import geopandas as gpd  # noqa: E402
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import osmnx as ox  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from shapely.geometry import Point  # noqa: E402

from netseg.cities import REPO_ROOT, load_race_counts, load_urban_tracts  # noqa: E402
from netseg.network import prepare_graph, snap_points  # noqa: E402
from netseg.report import rank_comparison  # noqa: E402
from netseg.vignette import reach_edges  # noqa: E402

OUT = ROOT / "outputs"
FIG = OUT / "figures"
VIGNETTES = {"5208707": "Goiânia", "3304557": "Rio de Janeiro", "2927408": "Salvador"}
CAPITALS = {"1100205", "1200401", "1302603", "1400100", "1501402", "1600303", "1721000", "2111300", "2211001",
            "2304400", "2408102", "2507507", "2611606", "2704302", "2800308", "2927408", "3106200", "3205309",
            "3304557", "3550308", "4106902", "4205407", "4314902", "5002704", "5103403", "5208707", "5300108"}

# reference palette (dataviz skill, light mode)
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#dbe9f9", "#2a78d6", "#0d3a73"])
DIV = LinearSegmentedColormap.from_list("div", ["#eb6834", "#f1f0ec", "#2a78d6"])

mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
    "axes.edgecolor": MUTED, "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 300,
})


def fig_vignettes():
    race = load_race_counts()
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    for ax, (cod, name) in zip(axes, VIGNETTES.items()):
        gdf, _ = load_urban_tracts(cod, race)
        G = prepare_graph(ox.load_graphml(ROOT / "data" / "osm" / f"{cod}.graphml"), gdf.crs)
        c = gdf.geometry.representative_point()
        w = gdf["pop_total"].to_numpy()
        centre = np.array([[np.average(c.x, weights=w), np.average(c.y, weights=w)]])
        origin = snap_points(G, centre)[0][0]
        ox0, oy0 = G.nodes[origin]["x"], G.nodes[origin]["y"]
        edges = ox.convert.graph_to_gdfs(G, nodes=False)
        near = edges.cx[ox0 - 2600: ox0 + 2600, oy0 - 2600: oy0 + 2600]
        near.plot(ax=ax, color="#cfcec9", linewidth=0.4)
        reach = set(reach_edges(G, origin, 2000.0))
        near[near.index.isin(reach)].plot(ax=ax, color=BLUE, linewidth=0.7)
        gpd.GeoSeries([Point(ox0, oy0).buffer(2000)], crs=gdf.crs).boundary.plot(ax=ax, color=ORANGE, linewidth=1.2)
        ax.plot(ox0, oy0, marker="x", color=INK, markersize=8)
        ax.set_xlim(ox0 - 2600, ox0 + 2600)
        ax.set_ylim(oy0 - 2600, oy0 + 2600)
        ax.set_aspect("equal")
        ax.set_title(name, color=INK)
        ax.set_axis_off()
    fig.legend(handles=[mpl.lines.Line2D([], [], color=BLUE, lw=2, label="Reachable within 2 km on foot"),
                        mpl.lines.Line2D([], [], color=ORANGE, lw=2, label="2 km straight-line radius")],
               loc="lower center", ncol=2, frameon=False)
    fig.savefig(FIG / "fig1_vignettes.pdf", bbox_inches="tight")


def fig_rank_slope(idx):
    r = rank_comparison(idx, top=15)
    fig, ax = plt.subplots(figsize=(6.2, 9.5))
    ax.grid(False)
    for row in r.itertuples():
        moved = row.rank_change != 0
        ax.plot([0, 1], [row.rank_euc, row.rank_net], color=ORANGE if moved else BLUE, lw=2, marker="o", ms=8,
                markeredgecolor="white", markeredgewidth=1.5)
        ax.text(-0.04, row.rank_euc, row.NM_MUN, ha="right", va="center", fontsize=8, color=INK)
        ax.text(1.04, row.rank_net, row.NM_MUN, ha="left", va="center", fontsize=8, color=INK)
    ax.set_xticks([0, 1], ["Euclidean", "Network"])
    ax.invert_yaxis()
    ax.set_ylabel("Rank by $H$ (1 = most segregated)")
    ax.set_xlim(-0.7, 1.7)
    ax.spines["bottom"].set_visible(False)
    fig.legend(handles=[mpl.lines.Line2D([], [], color=BLUE, lw=2, label="Same rank"),
                        mpl.lines.Line2D([], [], color=ORANGE, lw=2, label="Rank changes")],
               loc="upper center", ncol=2, frameon=False)
    fig.savefig(FIG / "fig2_rank_slope.pdf", bbox_inches="tight")


def fig_scatter(af):
    fig, ax = plt.subplots(figsize=(5, 5))
    lim = [0, max(af["H_euc"].max(), af["H_net"].max()) * 1.08]
    ax.plot(lim, lim, color=MUTED, linestyle="--", linewidth=0.8, label="Equal values")
    ax.scatter(af["H_euc"], af["H_net"], s=22, color=BLUE, edgecolor="white", linewidth=0.8, label="Municipality")
    # selective direct labels: the largest relative gaps and the most segregated cities
    lab = pd.concat([af.nlargest(5, "pdH"), af.nlargest(3, "H_net")]).drop_duplicates("COD_MUNICIPIO")
    for row in lab.itertuples():
        left = row.H_euc < 0.5 * lim[1]  # label away from the nearest axis
        ax.annotate(row.NM_MUN, (row.H_euc, row.H_net), fontsize=7, color=INK2, xytext=(5, 2) if left else (-5, 3),
                    textcoords="offset points", ha="left" if left else "right")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("$H$ with Euclidean distance")
    ax.set_ylabel("$H$ with network distance")
    ax.legend(frameon=False, loc="upper left")
    fig.savefig(FIG / "fig3_scatter.pdf", bbox_inches="tight")


def fig_map(af):
    mun = gpd.read_file(REPO_ROOT / "outputs" / "municipio_polygons.gpkg")
    code_col = next(c for c in mun.columns if c.upper() in {"COD_MUNICIPIO", "CD_MUN", "CD_MUNICIPIO", "CODE_MUNI"})
    mun["COD_MUNICIPIO"] = mun[code_col].astype(str).str[:7]
    pts = mun.merge(af[["COD_MUNICIPIO", "pdH"]], on="COD_MUNICIPIO")
    pts = pts.set_geometry(pts.to_crs(5880).representative_point())
    uf = gpd.read_file(REPO_ROOT / "outputs" / "uf_polygons.gpkg").to_crs(5880)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.grid(False)
    uf.boundary.plot(ax=ax, color="#bdbcb6", linewidth=0.4)
    if pts["pdH"].min() < 0:
        cmap, norm = DIV, TwoSlopeNorm(vcenter=0, vmin=pts["pdH"].min(), vmax=pts["pdH"].max())
    else:
        cmap, norm = SEQ, None
    pts.plot(ax=ax, column="pdH", cmap=cmap, norm=norm, markersize=28, edgecolor="white", linewidth=0.6,
             legend=True, legend_kwds={"label": "% difference in $H$ (network vs Euclidean)", "shrink": 0.6})
    ax.set_axis_off()
    fig.savefig(FIG / "fig4_map_pdH.pdf", bbox_inches="tight")


def fig_clustermap(af):
    cols = ["intersection_density_km", "street_density_km", "street_length_avg", "streets_per_node_avg",
            "circuity_avg", "prop_dead_end", "prop_3way", "prop_4way", "self_loop_proportion", "cyclomatic",
            "meshedness", "gamma", "fragmentation", "pop_urban", "area_km2", "pdH"]
    names = {"intersection_density_km": "Intersection density", "street_density_km": "Street density",
             "street_length_avg": "Mean street length", "streets_per_node_avg": "Streets per node",
             "circuity_avg": "Circuity", "prop_dead_end": "Dead-end share", "prop_3way": "3-way share",
             "prop_4way": "4-way share", "self_loop_proportion": "Self-loop share", "cyclomatic": "Cyclomatic number",
             "meshedness": "Meshedness", "gamma": "Gamma", "fragmentation": "Fragmentation F",
             "pop_urban": "Urban population", "area_km2": "Urban area", "pdH": "% difference in H"}
    corr = af[cols].corr(method="spearman").rename(index=names, columns=names)
    g = sns.clustermap(corr, cmap=DIV, vmin=-1, vmax=1, figsize=(9, 9), linewidths=1, linecolor="white",
                       cbar_pos=(1.02, 0.3, 0.025, 0.4), cbar_kws={"label": "Spearman correlation"})
    g.savefig(FIG / "fig5_clustermap.pdf")


def fig_fragmentation(af):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(af["fragmentation"], af["pdH"], s=22, color=BLUE, edgecolor="white", linewidth=0.8)
    b = np.polyfit(af["fragmentation"], af["pdH"], 1)
    xs = np.linspace(af["fragmentation"].min(), af["fragmentation"].max(), 50)
    ax.plot(xs, np.polyval(b, xs), color=ORANGE, lw=2, label="Least-squares line")
    ax.set_xlabel("Configurational fragmentation $F$")
    ax.set_ylabel("% difference in $H$ (network vs Euclidean)")
    ax.legend(frameon=False)
    fig.savefig(FIG / "fig6_fragmentation.pdf", bbox_inches="tight")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    idx = pd.read_parquet(OUT / "indices_long.parquet")
    af = pd.read_parquet(OUT / "analysis_frame.parquet")
    fig_vignettes()
    fig_rank_slope(idx)
    fig_scatter(af)
    fig_map(af)
    fig_clustermap(af)
    fig_fragmentation(af)
    print(sorted(p.name for p in FIG.glob("*.pdf")))
