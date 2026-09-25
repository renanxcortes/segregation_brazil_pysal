"""Write RQ1 tables and numbers.tex (every number quoted in the manuscript comes from here)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from netseg.report import gap_table, rank_comparison, robustness_table, write_macros  # noqa: E402

TOPO_COLS = ["intersection_density_km", "street_density_km", "street_length_avg", "streets_per_node_avg",
             "circuity_avg", "prop_dead_end", "prop_3way", "prop_4way", "cyclomatic", "meshedness", "gamma",
             "fragmentation"]


SPEC = {"main": "2 km, linear", "b1000": "1 km, linear", "b3000": "3 km, linear", "exp2000": "2 km, exponential",
        "popmatch": "Population-matched"}
INDEX = {"H": "H (five groups)", "Dissim_pp": "Dissimilarity (PP)", "Isolation_pp": "Isolation (PP)",
         "Entropy_pp": "Entropy (PP)"}
LABELS = {"H_euc": "H, Euclidean", "H_net": "H, network", "dH": "Gap", "pdH": "Gap (%)", "NM_MUN": "City",
          "rank_euc": "Rank, Euclidean", "rank_net": "Rank, network", "rank_change": "Change", "spec": "Specification",
          "index": "Index", "mean_dH": "Mean gap", "mean_pdH": "Mean gap (%)", "share_positive": "Share gap > 0",
          "pearson": "Pearson", "spearman": "Spearman", "fragmentation": "F",
          "intersection_density_km": "Intersection density (per km2)", "street_density_km": "Street density (km/km2)",
          "street_length_avg": "Mean street length (m)", "streets_per_node_avg": "Streets per node",
          "circuity_avg": "Circuity", "prop_dead_end": "Dead-end share", "prop_3way": "3-way share",
          "prop_4way": "4-way share", "cyclomatic": "Cyclomatic number", "meshedness": "Meshedness", "gamma": "Gamma"}


def _tex(df, path, **kw):
    """Readable labels, LaTeX-escaped text, UTF-8 with LF line endings."""
    df = df.rename(index=LABELS, columns=LABELS)
    for col in ("Specification", "Index"):
        if col in df.columns:
            df[col] = df[col].replace({**SPEC, **INDEX})
    Path(path).write_text(df.to_latex(escape=True, **kw), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    out = ROOT / "outputs"
    t = out / "tables"
    t.mkdir(parents=True, exist_ok=True)
    idx = pd.read_parquet(out / "indices_long.parquet")
    cty = pd.read_parquet(out / "cities.parquet")
    fails = pd.read_csv(out / "failures.csv")
    af = pd.read_parquet(out / "analysis_frame.parquet")

    gap = gap_table(idx)
    _tex(gap, t / "gap.tex", float_format="%.3f")
    ranks = rank_comparison(idx)
    _tex(ranks, t / "ranks.tex", index=False)
    rob = robustness_table(idx)
    _tex(rob, t / "robustness.tex", index=False, float_format="%.3f")
    _tex(cty[TOPO_COLS].describe().T, t / "topology_desc.tex", float_format="%.3f")
    cc = t / "crosscheck_pandana.csv"
    if cc.exists():
        x = pd.read_csv(cc, dtype={"COD_MUNICIPIO": str}).drop(columns="COD_MUNICIPIO")
        x.columns = ["City", "H, Euclidean", "H, network (ours)", "H, network (pandana)"]
        _tex(x, t / "crosscheck.tex", index=False, float_format="%.4f")
    city_tab = af[["NM_MUN", "H_euc", "H_net", "pdH", "fragmentation"]].sort_values("pdH", ascending=False)
    _tex(city_tab, t / "city_results.tex", index=False, float_format="%.3f", longtable=True)

    main = rob.set_index(["spec", "index"]).loc[("main", "H")]
    pm = rob.set_index(["spec", "index"]).loc[("popmatch", "H")]
    gap_pm = gap_table(idx, spec="popmatch")
    ratio = af["env_pop_net_mean"] / af["env_pop_euc_mean"]
    rho = lambda a, b: f"{a.corr(b, method='spearman'):.2f}"  # noqa: E731
    write_macros({
        "nSnapFar": f"{int(cty['n_snap_gt500'].sum()):,}",
        "ratioMin": f"{100 * ratio.min():.0f}",
        "ratioMax": f"{100 * ratio.max():.0f}",
        "rhoRatioPdH": rho(ratio, af["pdH"]),
        "rhoDeadEndRatio": rho(af["prop_dead_end"], ratio),
        "rhoCircuityRatio": rho(af["circuity_avg"], ratio),
        "rhoMeshRatio": rho(af["meshedness"], ratio),
        "rhoFragRatio": rho(af["fragmentation"], ratio),
        "rhoDeadEndPdH": rho(af["prop_dead_end"], af["pdH"]),
        "rhoFragPdH": rho(af["fragmentation"], af["pdH"]),
        "meanPdHPopmatch": f"{gap_pm.loc['pdH', 'mean']:.1f}",
        "meanDHPopmatch": f"{gap_pm.loc['dH', 'mean']:.4f}",
        "sharePositivePopmatch": f"{100 * pm['share_positive']:.1f}",
        "spearmanPopmatch": f"{pm['spearman']:.3f}",
        "envPopRatio": f"{100 * (cty['env_pop_net_mean'] / cty['env_pop_euc_mean']).median():.0f}",
        "medianPopmatchB": f"{cty['popmatch_b_median'].median():,.0f}",
        "maxDH": f"{gap.loc['dH', 'max']:.3f}",
        "minPdH": f"{gap.loc['pdH', 'min']:.1f}",
        "nCities": len(cty),
        "nFailed": len(fails),
        "nTractsUrban": f"{int(cty['n_tracts_urban'].sum()):,}",
        "sharePopUrban": f"{100 * cty['pop_urban'].sum() / cty['pop_all'].sum():.1f}",
        "meanHeuc": f"{gap.loc['H_euc', 'mean']:.3f}",
        "meanHnet": f"{gap.loc['H_net', 'mean']:.3f}",
        "meanDH": f"{gap.loc['dH', 'mean']:.3f}",
        "meanPdH": f"{gap.loc['pdH', 'mean']:.1f}",
        "maxPdH": f"{gap.loc['pdH', 'max']:.1f}",
        "sharePositive": f"{100 * main['share_positive']:.1f}",
        "pearsonMain": f"{main['pearson']:.3f}",
        "spearmanMain": f"{main['spearman']:.3f}",
        "nRankChangeTop": int((ranks["rank_change"] != 0).sum()),
    }, t / "numbers.tex")
    print(gap, ranks, rob, sep="\n\n")
