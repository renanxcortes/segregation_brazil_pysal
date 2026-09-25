"""Run the Euclidean-vs-network pipeline for the 91 cities (resumable).

Street networks come from one dated Geofabrik extract of Brazil (data/osm_source/brazil-latest.osm.pbf),
clipped per city with osmium; ``--source overpass`` falls back to live Overpass queries.
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from netseg.cities import load_race_counts, select_cities  # noqa: E402
from netseg.network import download_walk_graph  # noqa: E402
from netseg.osm_extract import OSMIUM, filter_highways, make_extract_downloader  # noqa: E402
from netseg.pipeline import run_all  # noqa: E402

SRC = ROOT / "data" / "osm_source" / "brazil-latest.osm.pbf"
HIGHWAYS = ROOT / "data" / "osm_source" / "brazil-highways.osm.pbf"


def extract_downloader():
    if not HIGHWAYS.exists():
        print("filtering national extract to highways (one-off)...", flush=True)
        filter_highways(SRC, HIGHWAYS)
    stamp = subprocess.run([str(OSMIUM), "fileinfo", "-g", "header.option.osmosis_replication_timestamp", str(SRC)],
                           capture_output=True, text=True).stdout.strip()
    (ROOT / "outputs").mkdir(exist_ok=True)
    (ROOT / "outputs" / "osm_snapshot.txt").write_text(
        f"source: Geofabrik brazil-latest.osm.pbf\nreplication_timestamp: {stamp}\n", newline="\n")
    return make_extract_downloader(HIGHWAYS, ROOT / "data" / "osm_clips")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="COD_MUNICIPIO codes to run")
    ap.add_argument("--smallest", type=int, help="run only the N smallest cities (smoke test)")
    ap.add_argument("--source", choices=["extract", "overpass"], default="extract")
    a = ap.parse_args()
    # smallest first: results accumulate quickly and Sao Paulo (by far the largest) runs last
    cities = select_cities().sort_values("pop_total").reset_index(drop=True)
    if a.only:
        cities = cities[cities["COD_MUNICIPIO"].isin(a.only)]
    if a.smallest:
        cities = cities.head(a.smallest)
    downloader = extract_downloader() if a.source == "extract" else download_walk_graph
    run_all(cities, load_race_counts(), ROOT / "data", ROOT / "outputs", downloader=downloader)
