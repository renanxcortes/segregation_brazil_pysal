"""Is F stable when S and N are doubled? (spec §5.3: |ΔF| < 0.02)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import osmnx as ox  # noqa: E402
import pandas as pd  # noqa: E402

from netseg.cities import load_race_counts, load_urban_tracts  # noqa: E402
from netseg.network import clip_graph, footprint, prepare_graph  # noqa: E402
from netseg.topology import fragmentation  # noqa: E402

CITIES = {"4314902": "Porto Alegre", "4106902": "Curitiba", "2927408": "Salvador"}

if __name__ == "__main__":
    race = load_race_counts()
    rows = []
    for cod in CITIES:
        gdf, _ = load_urban_tracts(cod, race)
        G = prepare_graph(ox.load_graphml(ROOT / "data" / "osm" / f"{cod}.graphml"), gdf.crs)
        urban = list(clip_graph(G, footprint(gdf), largest=False).nodes)
        for S, N in [(500, 2000), (1000, 4000)]:
            rows.append({"COD_MUNICIPIO": cod, "S": S, "N": N, **fragmentation(G, S=S, N=N, seed=0, sample_from=urban)})
    df = pd.DataFrame(rows)
    (ROOT / "outputs" / "tables").mkdir(parents=True, exist_ok=True)
    df[["COD_MUNICIPIO", "S", "N", "fragmentation"]].to_csv(ROOT / "outputs" / "tables" / "fragmentation_stability.csv", index=False)
    spread = df.groupby("COD_MUNICIPIO")["fragmentation"].agg(lambda s: s.max() - s.min())
    print(spread)
    print("STABLE" if (spread < 0.02).all() else "UNSTABLE: raise S/N defaults in netseg/topology.py and pipeline, then re-run")
