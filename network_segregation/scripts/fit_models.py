"""Fit the four RQ2 models and write LaTeX/CSV tables."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from netseg.models import analysis_frame, fit, vif_table  # noqa: E402

TERMS = [("log_intersection_density", "Intersection density (log)"), ("z_circuity", "Circuity"),
         ("z_meshedness", "Meshedness"), ("log_cyclomatic", "Cyclomatic number (log)"),
         ("z_dead_end", "Dead-end share"), ("log_pop_density", "Population density (log)"),
         ("z_H_euc", "$H$, Euclidean"), ("log_cyclomatic:z_circuity", "Cyclomatic (log) $\\times$ circuity"),
         ("z_fragmentation", "Fragmentation $F$"), ("Intercept", "Intercept")]


def _stars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""


def latex_table(fits: dict) -> str:
    """Coefficients with HC3 standard errors in parentheses; our own LaTeX (no double escaping)."""
    cols = list(fits)
    lines = ["\\begin{tabular}{l" + "r" * len(cols) + "}", "\\toprule", " & " + " & ".join(cols) + " \\\\", "\\midrule"]
    for term, label in TERMS:
        coef, se = [], []
        for r in fits.values():
            if term in r.params:
                digits = 4 if abs(r.params[term]) < 1 and "pdH" not in r.model.formula.split("~")[0] else 2
                coef.append(f"{r.params[term]:.{digits}f}{_stars(r.pvalues[term])}")
                se.append(f"({r.bse[term]:.{digits}f})")
            else:
                coef.append("")
                se.append("")
        lines += [f"{label} & " + " & ".join(coef) + " \\\\", " & " + " & ".join(se) + " \\\\"]
    lines += ["\\midrule",
              "$N$ & " + " & ".join(f"{int(r.nobs)}" for r in fits.values()) + " \\\\",
              "Adj. $R^2$ & " + " & ".join(f"{r.rsquared_adj:.3f}" for r in fits.values()) + " \\\\",
              "\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = ROOT / "outputs"
    (out / "tables").mkdir(parents=True, exist_ok=True)
    df = analysis_frame(pd.read_parquet(out / "indices_long.parquet"), pd.read_parquet(out / "cities.parquet"))
    df.to_parquet(out / "analysis_frame.parquet", index=False)
    fits = {"$\\Delta H$ (K\\&R)": fit(df, "dH", False), "$\\Delta H$ (+$F$)": fit(df, "dH", True),
            "\\%$\\Delta H$ (K\\&R)": fit(df, "pdH", False), "\\%$\\Delta H$ (+$F$)": fit(df, "pdH", True)}
    (out / "tables" / "models.tex").write_text(latex_table(fits), encoding="utf-8", newline="\n")
    pd.concat({k: pd.DataFrame({"coef": r.params, "se": r.bse, "p": r.pvalues}) for k, r in fits.items()}).to_csv(
        out / "tables" / "models_coefs.csv")
    vif_table(df).to_csv(out / "tables" / "vif.csv", index=False)
    print(latex_table(fits))
