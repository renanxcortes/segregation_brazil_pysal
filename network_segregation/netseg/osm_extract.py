"""Walk networks from a local OpenStreetMap extract (Geofabrik PBF) instead of the Overpass API.

The public Overpass server throttles large downloads, so each city is clipped from one dated national
extract with ``osmium`` and turned into an OSMnx graph. Ways are kept with exactly the tag rules of
OSMnx's ``network_type="walk"`` filter (parsed from OSMnx itself, with Overpass semantics).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import networkx as nx
import osmnx as ox
from shapely.geometry import mapping

OSMIUM = Path(sys.prefix) / "Library" / "bin" / "osmium.exe"
if not OSMIUM.exists() and shutil.which("osmium"):
    OSMIUM = Path(shutil.which("osmium"))

_RULE = re.compile(r'\["([^"]+)"(?:(!~|~)"([^"]*)")?\]')
_EXTRA_TAGS = ["highway", "area", "access", "foot", "service", "sidewalk", "sidewalk:both", "sidewalk:left",
               "sidewalk:right"]


def parse_overpass_filter(flt: str) -> list[tuple[str, str, str | None]]:
    """``["k"]`` -> (k, "exists", None); ``["k"!~"re"]`` -> (k, "not_match", re); ``["k"~"re"]`` -> (k, "match", re)."""
    rules = []
    for key, op, rx in _RULE.findall(flt):
        rules.append((key, {"": "exists", "!~": "not_match", "~": "match"}[op], rx or None))
    return rules


WALK_RULES = parse_overpass_filter(ox._overpass._get_network_filter("walk"))


def is_walkable(tags: dict, rules=WALK_RULES) -> bool:
    """Overpass semantics: regexes are unanchored; ``!~`` also passes when the key is absent."""
    for key, op, rx in rules:
        val = tags.get(key)
        if op == "exists" and val is None:
            return False
        if op == "not_match" and val is not None and re.search(rx, str(val)):
            return False
        if op == "match" and (val is None or not re.search(rx, str(val))):
            return False
    return True


def extract_city_osm(src_pbf, polygon_wgs84, out_osm) -> None:
    """Clip ``src_pbf`` to a WGS84 polygon (complete ways) and write OSM XML."""
    out_osm = Path(out_osm)
    out_osm.parent.mkdir(parents=True, exist_ok=True)
    poly_file = out_osm.with_suffix(".geojson")
    poly_file.write_text(json.dumps({"type": "Feature", "properties": {}, "geometry": mapping(polygon_wgs84)}))
    subprocess.run([str(OSMIUM), "extract", "-p", str(poly_file), "--strategy", "complete_ways", "--overwrite",
                    "-o", str(out_osm), str(src_pbf)], check=True, capture_output=True)


def filter_highways(src_pbf, out_pbf) -> None:
    """One-off national pre-filter to ways tagged highway (keeps the per-city clips small and fast)."""
    subprocess.run([str(OSMIUM), "tags-filter", "--overwrite", "-o", str(out_pbf), str(src_pbf), "w/highway"],
                   check=True, capture_output=True)


def graph_from_osm_xml(osm_path, polygon_wgs84) -> nx.MultiDiGraph:
    """Walk graph from an OSM XML clip: walk filter, truncation by edge, simplification (as graph_from_polygon)."""
    saved = list(ox.settings.useful_tags_way)
    ox.settings.useful_tags_way = sorted(set(saved) | set(_EXTRA_TAGS))
    try:
        G = ox.graph_from_xml(osm_path, bidirectional=True, simplify=False, retain_all=True)
    finally:
        ox.settings.useful_tags_way = saved
    G.remove_edges_from([(u, v, k) for u, v, k, d in G.edges(keys=True, data=True) if not is_walkable(d)])
    G.remove_nodes_from(list(nx.isolates(G)))
    G = ox.truncate.truncate_graph_polygon(G, polygon_wgs84, truncate_by_edge=True)
    G.remove_nodes_from(list(nx.isolates(G)))
    return ox.simplification.simplify_graph(G)


def make_extract_downloader(src_pbf, work_dir):
    """A drop-in for ``network.download_walk_graph``: same signature, GraphML cache at ``cache_path``."""
    src_pbf, work_dir = Path(src_pbf), Path(work_dir)

    def download(polygon_wgs84, cache_path) -> nx.MultiDiGraph:
        cache_path = Path(cache_path)
        if cache_path.exists():
            return ox.load_graphml(cache_path)
        work_dir.mkdir(parents=True, exist_ok=True)
        clip = work_dir / f"{cache_path.stem}.osm"
        extract_city_osm(src_pbf, polygon_wgs84, clip)
        G = graph_from_osm_xml(clip, polygon_wgs84)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(G, cache_path)
        clip.unlink(missing_ok=True)
        return G

    return download
