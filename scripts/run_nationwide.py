"""Compute nine segregation measures for every city in the universe. Resumable."""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from segbr.census import load_census  # noqa: E402
from segbr.pipeline import run_all  # noqa: E402
CSV = ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
SHP = ROOT / "shapefiles_2022"
UNIVERSE = ROOT / "outputs" / "city_universe_2022.csv"
OUT = ROOT / "outputs" / "segregation_profiles_2022.parquet"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="process at most N remaining cities")
    ap.add_argument("--time-budget", type=float, default=None,
                    help="per-city seconds budget; remaining measures skipped past it")
    ap.add_argument("--out", type=Path, default=OUT, help=argparse.SUPPRESS)
    ap.add_argument("--universe", type=Path, default=UNIVERSE, help=argparse.SUPPRESS)
    args = ap.parse_args()

    universe = pd.read_csv(args.universe, dtype={"COD_MUNICIPIO": str, "COD_UF": str})
    census = load_census(CSV)
    res = run_all(universe, census, SHP, args.out, time_budget_s=args.time_budget, limit=args.limit)

    if res.empty:
        print("0 cities processed (nothing to do)")
        return

    done = res[~res["fatal_error"].astype(bool)]
    print(f"{len(done)}/{len(universe)} cities profiled; {len(res) - len(done)} fatal errors")
    err_cols = [c for c in res.columns if c.endswith("_error")]
    if err_cols:
        per_measure = {c: int(res[c].astype(bool).sum()) for c in err_cols}
        per_measure = {k: v for k, v in per_measure.items() if v}
        if per_measure:
            print("per-measure errors:", per_measure)


if __name__ == "__main__":
    main()
