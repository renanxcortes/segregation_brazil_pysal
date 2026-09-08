"""Export the 6 manuscript tables as separate, editable .xlsx files.

REBEP wants complementary tables in an editable format (e.g. Excel),
numbered the same way as in the manuscript, in addition to their being
embedded as native Word tables in manuscript.docx. This script recomputes
each table from the same source data as scripts/figures.py (it does not
hardcode numbers) and writes one workbook per table, with the caption as a
header row above the data.

    draft/rebep/tables_submission/Table1.xlsx  cities by macro-region
    draft/rebep/tables_submission/Table2.xlsx  the nine indices, by dimension
    draft/rebep/tables_submission/Table3.xlsx  descriptive statistics
    draft/rebep/tables_submission/Table4.xlsx  Spearman rank correlation
    draft/rebep/tables_submission/Table5.xlsx  Kendall rank correlation
    draft/rebep/tables_submission/Table6.xlsx  medians by macro-region

Usage:
    python draft/rebep/export_submission_tables.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTDIR = HERE / "tables_submission"

sys.path.insert(0, str(ROOT / "scripts"))
import figures as F  # noqa: E402

import pandas as pd
from openpyxl.styles import Font


def _write(df: pd.DataFrame, path: Path, caption: str, index_label: str = ""):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="Table", startrow=2, index=True,
                     index_label=index_label)
        ws = xw.sheets["Table"]
        ws["A1"] = caption
        ws["A1"].font = Font(bold=True)


def table1_descriptive():
    df = F.load()
    tracts = "n_tracts_p"
    g = df.groupby("REGION").agg(
        Cities=("COD_MUNICIPIO", "size"),
        **{"Tracts (min.)": (tracts, "min")},
        **{"Tracts (median)": (tracts, "median")},
        **{"Tracts (max.)": (tracts, "max")},
        **{"Minority share (min.)": ("ppp", "min")},
        **{"Minority share (median)": ("ppp", "median")},
        **{"Minority share (max.)": ("ppp", "max")},
    ).reindex(F.REGION_ORDER)
    total = pd.DataFrame({
        "Cities": [len(df)],
        "Tracts (min.)": [df[tracts].min()],
        "Tracts (median)": [df[tracts].median()],
        "Tracts (max.)": [df[tracts].max()],
        "Minority share (min.)": [df["ppp"].min()],
        "Minority share (median)": [df["ppp"].median()],
        "Minority share (max.)": [df["ppp"].max()],
    }, index=["Brazil"])
    out = pd.concat([g, total])
    for c in ("Cities", "Tracts (min.)", "Tracts (median)", "Tracts (max.)"):
        out[c] = out[c].astype(int)
    out = out.round({"Minority share (min.)": 3, "Minority share (median)": 3,
                      "Minority share (max.)": 3})
    _write(out, OUTDIR / "Table1.xlsx",
           "Table 1. Cities analysed by macro-region (2022 Census). "
           "Minority share is the tract preta and parda population as a "
           "fraction of the total.", index_label="Region")


def table2_measures():
    rows = [
        ("Dissimilarity (D)", "Evenness", "Aspatial",
         "Unequal spread of the group across tracts"),
        ("Spatial Dissimilarity", "Evenness", "Spatial",
         "Evenness adjusted for tract adjacency"),
        ("Gini", "Evenness", "Aspatial",
         "Inequality of group shares across tracts"),
        ("Entropy (H)", "Evenness", "Aspatial",
         "Departure of tract compositions from the city mix"),
        ("Isolation", "Exposure", "Aspatial",
         "Expected own-group share of a member's tract"),
        ("Distance-Decay Isolation", "Exposure", "Spatial",
         "Isolation weighted by inter-tract distance"),
        ("Relative Concentration", "Concentration", "Spatial",
         "Physical space occupied by the group vs. the reference"),
        ("Relative Centralization", "Centralization", "Spatial",
         "Group settlement near the urban core"),
        ("Relative Clustering", "Clustering", "Spatial",
         "Adjacency of the tracts the group inhabits"),
    ]
    df = pd.DataFrame(rows, columns=["Index", "Dimension", "Type", "Concept"]
                       ).set_index("Index")
    _write(df, OUTDIR / "Table2.xlsx",
           "Table 2. The nine segregation indices, by dimension of Massey "
           "and Denton (1988).")


def table3_summary_stats():
    df = F.load()
    stats = (df[F.MEASURES]
             .describe(percentiles=[0.25, 0.5, 0.75]).T
             [["mean", "std", "25%", "50%", "75%", "min", "max"]]
             .round(3))
    stats.index = [F.MEASURE_LABELS[m] for m in stats.index]
    stats.columns = ["Mean", "SD", "P25", "Median", "P75", "Min.", "Max."]
    _write(stats, OUTDIR / "Table3.xlsx",
           "Table 3. Descriptive statistics of the nine segregation indices "
           "(all 319 cities, 2022 Census).", index_label="Index")


def table4_correlation():
    df = F.load()
    corr = df[F.MEASURES].corr(method="spearman").round(2)
    labels = [F.MEASURE_LABELS[m] for m in F.MEASURES]
    corr.index = labels
    corr.columns = [F.MEASURE_CODES[m] for m in F.MEASURES]
    _write(corr, OUTDIR / "Table4.xlsx",
           "Table 4. Spearman rank correlation between the nine segregation "
           "indices (city level, 2022 Census). Columns: D=Dissimilarity, "
           "SD=Spatial Dissimilarity, G=Gini, H=Entropy, Iso=Isolation, "
           "DDI=Distance-Decay Isolation, RCo=Relative Concentration, "
           "RCe=Relative Centralization, RCl=Relative Clustering.",
           index_label="Index")


def table5_rank_correlation():
    df = F.load().merge(F._municipio_names(), on="COD_MUNICIPIO", how="left")
    ranks = df[F.MEASURES].rank()
    tau = ranks.corr(method="kendall").round(2)
    tau.index = [F.MEASURE_LABELS[m] for m in F.MEASURES]
    tau.columns = [F.MEASURE_CODES[m] for m in F.MEASURES]
    _write(tau, OUTDIR / "Table5.xlsx",
           "Table 5. Kendall rank correlation (tau) between the city "
           "rankings on the nine segregation indices (city level, 2022 "
           "Census). Columns: D=Dissimilarity, SD=Spatial Dissimilarity, "
           "G=Gini, H=Entropy, Iso=Isolation, DDI=Distance-Decay Isolation, "
           "RCo=Relative Concentration, RCe=Relative Centralization, "
           "RCl=Relative Clustering.", index_label="Index")


def table6_regional():
    df = F.load()
    med = df.groupby("REGION")[F.MEASURES].median().reindex(F.REGION_ORDER).round(3)
    med.columns = [F.MEASURE_CODES[m] for m in F.MEASURES]
    _write(med, OUTDIR / "Table6.xlsx",
           "Table 6. Median of each segregation index by macro-region "
           "(city level, 2022 Census). Columns: D=Dissimilarity, "
           "SD=Spatial Dissimilarity, G=Gini, H=Entropy, Iso=Isolation, "
           "DDI=Distance-Decay Isolation, RCo=Relative Concentration, "
           "RCe=Relative Centralization, RCl=Relative Clustering.",
           index_label="Region")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    table1_descriptive()
    print("wrote Table1.xlsx (cities by macro-region)")
    table2_measures()
    print("wrote Table2.xlsx (the nine indices)")
    table3_summary_stats()
    print("wrote Table3.xlsx (descriptive statistics)")
    table4_correlation()
    print("wrote Table4.xlsx (Spearman correlation)")
    table5_rank_correlation()
    print("wrote Table5.xlsx (Kendall rank correlation)")
    table6_regional()
    print("wrote Table6.xlsx (medians by macro-region)")


if __name__ == "__main__":
    main()
