"""Write the >100k-population municipality universe to outputs/city_universe_2022.csv."""
from pathlib import Path

from segbr.census import load_census, municipality_universe
from segbr.cities import UF_BY_CODE

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
OUT = ROOT / "outputs" / "city_universe_2022.csv"


def main() -> None:
    df = load_census(CSV)
    uni = municipality_universe(df, threshold=100_000)
    uni["UF"] = uni["COD_UF"].map(UF_BY_CODE)
    uni = uni[["COD_MUNICIPIO", "COD_UF", "UF", "pop_total", "n_tracts"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    uni.to_csv(OUT, index=False)
    print(f"{len(uni)} municipalities > 100k written to {OUT}")
    print(uni.head(10).to_string(index=False))
    print("tract totals:", uni["n_tracts"].sum())


if __name__ == "__main__":
    main()
