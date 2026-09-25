"""OpenStreetMap walk network: download, projection, component selection, snapping."""

from __future__ import annotations

import time
from pathlib import Path

import networkx as nx
import numpy as np
import osmnx as ox
import shapely
from scipy.spatial import cKDTree
from shapely.ops import unary_union


def footprint(gdf):
    """Union of all tract polygons (in the GeoDataFrame's CRS)."""
    return unary_union(gdf.geometry.values)


def download_walk_graph(polygon_wgs84, cache_path: Path, attempts: int = 6, wait_s: float = 120.0) -> nx.MultiDiGraph:
    """OSM pedestrian graph for a WGS84 polygon; cached as GraphML.

    Overpass timeouts are transient, so failed downloads are retried with linearly growing waits.
    """
    cache_path = Path(cache_path)
    if cache_path.exists():
        return ox.load_graphml(cache_path)
    for k in range(1, attempts + 1):
        try:
            G = ox.graph_from_polygon(polygon_wgs84, network_type="walk", simplify=True, retain_all=False,
                                      truncate_by_edge=True)
            break
        except Exception as exc:  # network errors surface as several requests/urllib3/osmnx types
            if k == attempts:
                raise
            print(f"download attempt {k} failed ({type(exc).__name__}); retrying in {wait_s * k:.0f} s", flush=True)
            time.sleep(wait_s * k)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, cache_path)
    return G


def _largest_component(G: nx.MultiGraph) -> nx.MultiGraph:
    nodes = max(nx.connected_components(G), key=len)
    return G.subgraph(nodes).copy()


def prepare_graph(G: nx.MultiDiGraph, crs) -> nx.MultiGraph:
    """Project to ``crs``, make undirected, keep the largest connected component."""
    Gp = ox.projection.project_graph(G, to_crs=crs)
    return _largest_component(ox.convert.to_undirected(Gp))


def node_xy(G) -> tuple[np.ndarray, np.ndarray]:
    nodes = np.empty(G.number_of_nodes(), dtype=object)
    nodes[:] = list(G.nodes)
    xy = np.array([[G.nodes[n]["x"], G.nodes[n]["y"]] for n in nodes], dtype=float)
    return nodes, xy


def snap_points(G, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Nearest graph node for each point, and the straight-line snap distance."""
    nodes, nxy = node_xy(G)
    d, idx = cKDTree(nxy).query(xy)
    return nodes[idx], d


def clip_graph(G: nx.MultiGraph, polygon, largest: bool = True) -> nx.MultiGraph:
    """Subgraph of nodes inside ``polygon`` (same CRS); only its largest component if ``largest``."""
    nodes, nxy = node_xy(G)
    inside = shapely.contains_xy(polygon, nxy[:, 0], nxy[:, 1])
    sub = G.subgraph(nodes[inside].tolist()).copy()
    return _largest_component(sub) if largest else sub
