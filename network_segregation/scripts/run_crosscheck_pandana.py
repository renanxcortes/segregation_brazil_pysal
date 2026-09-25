"""Cross-check H_net against segregation's native pandana route (3 cities).

segregation's ``network=`` path aggregates population at the nearest network node (pandana) and ignores snap
distance, so values are expected to be close to ours, not identical. Run with the netseg-pandana env.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import osmnx as ox  # noqa: E402
import pandana  # noqa: E402
import pandas as pd  # noqa: E402
from segregation.multigroup import MultiInfoTheory  # noqa: E402

from netseg.cities import GROUPS, load_race_counts, load_urban_tracts  # noqa: E402
from netseg.network import prepare_graph  # noqa: E402

CITIES = ["4314902", "4106902", "2927408"]

if __name__ == "__main__":
    race = load_race_counts()
    main = pd.read_parquet(ROOT / "outputs" / "indices_long.parquet")
    main = main[(main.spec == "main") & (main["index"] == "H")].set_index("COD_MUNICIPIO")
    rows = []
    for cod in CITIES:
        gdf, _ = load_urban_tracts(cod, race)
        G = prepare_graph(ox.load_graphml(ROOT / "data" / "osm" / f"{cod}.graphml"), gdf.crs)
        nodes, edges = ox.convert.graph_to_gdfs(G)
        edges = edges.reset_index()
        net = pandana.Network(nodes["x"], nodes["y"], edges["u"], edges["v"], edges[["length"]], twoway=True)
        h = MultiInfoTheory(gdf, groups=GROUPS, network=net, distance=2000, decay="linear").statistic
        rows.append({"COD_MUNICIPIO": cod, "NM_MUN": main.loc[cod, "NM_MUN"], "H_euc_ours": main.loc[cod, "euc"],
                     "H_net_ours": main.loc[cod, "net"], "H_net_pandana": h})
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    (ROOT / "outputs" / "tables").mkdir(parents=True, exist_ok=True)
    df.to_csv(ROOT / "outputs" / "tables" / "crosscheck_pandana.csv", index=False)
    print(df)
