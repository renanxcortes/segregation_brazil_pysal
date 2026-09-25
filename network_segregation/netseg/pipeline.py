"""Per-city orchestration with caching and failure capture."""

from __future__ import annotations

import datetime as dt
import json
import traceback
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd

from netseg.cities import load_urban_tracts
from netseg.distances import Pairs, euclidean_pairs, graph_to_csr, network_pairs
from netseg.measures import compute_indices
from netseg.network import clip_graph, download_walk_graph, footprint, prepare_graph, snap_points
from netseg.topology import fragmentation, network_metrics
from netseg.weights import kernel_matrix, matched_kernel_matrix

SPECS = [("main", 2000.0, "linear"), ("b1000", 1000.0, "linear"), ("b3000", 3000.0, "linear"), ("exp2000", 2000.0, "exponential")]
LIMIT = 3000.0
BUFFER_M = 2000.0
SNAP_FLAG_M = 500.0


def run_city(cod, name, race, data_dir, *, loader=load_urban_tracts, downloader=download_walk_graph, frag_kwargs=None) -> dict:
    data_dir = Path(data_dir)
    result_path = data_dir / "results" / f"{cod}.json"
    if result_path.exists():
        return json.loads(result_path.read_text())

    gdf, tract_stats = loader(cod, race)
    pts = gdf.geometry.representative_point()
    xy = np.c_[pts.x, pts.y]
    fp = footprint(gdf)
    poly_wgs84 = gpd.GeoSeries([fp.buffer(BUFFER_M)], crs=gdf.crs).to_crs(4326).iloc[0]

    graph_path = data_dir / "osm" / f"{cod}.graphml"
    G = prepare_graph(downloader(poly_wgs84, graph_path), gdf.crs)
    csr, nodes = graph_to_csr(G)
    node_ids, snap = snap_points(G, xy)
    index = {n: k for k, n in enumerate(nodes)}
    tract_nodes = np.array([index[n] for n in node_ids])

    pairs_path = data_dir / "pairs"
    pe_file, pn_file = pairs_path / f"{cod}_euc.npz", pairs_path / f"{cod}_net.npz"
    if pe_file.exists() and pn_file.exists():
        pe, pn = Pairs.load(pe_file), Pairs.load(pn_file)
    else:
        pe, pn = euclidean_pairs(xy, LIMIT), network_pairs(csr, tract_nodes, snap, LIMIT)
        pe.save(pe_file)
        pn.save(pn_file)

    rows = []
    for spec, bw, decay in SPECS:
        ie = compute_indices(gdf, kernel_matrix(pe, bw, decay))
        inet = compute_indices(gdf, kernel_matrix(pn, bw, decay))
        for k in ie:
            rows.append({"COD_MUNICIPIO": cod, "NM_MUN": name, "spec": spec, "bandwidth": bw, "decay": decay,
                         "index": k, "euc": ie[k], "net": inet[k]})
        if spec == "main":
            inet_main = inet

    # Population-matched robustness (Saporito 2026): shrink each tract's Euclidean radius until its
    # environment holds as many (kernel-weighted) people as its 2-km network environment.
    pop = gdf["pop_total"].to_numpy(float)
    main_bw = SPECS[0][1]
    env_net = kernel_matrix(pn, main_bw) @ pop
    env_euc = kernel_matrix(pe, main_bw) @ pop
    w_match, b_match = matched_kernel_matrix(pe, env_net, pop, b_max=main_bw)
    ipm = compute_indices(gdf, w_match)
    for k in ipm:
        rows.append({"COD_MUNICIPIO": cod, "NM_MUN": name, "spec": "popmatch", "bandwidth": float(np.median(b_match)),
                     "decay": "linear", "index": k, "euc": ipm[k], "net": inet_main[k]})

    area_km2 = fp.area / 1e6
    Gc = clip_graph(G, fp, largest=False)  # all urban nodes; routes may leave the footprint
    city = {
        "COD_MUNICIPIO": cod,
        "NM_MUN": name,
        **tract_stats,
        "area_km2": area_km2,
        "median_snap_m": float(np.median(snap)),
        "n_snap_gt500": int((snap > SNAP_FLAG_M).sum()),
        "env_pop_euc_mean": float(env_euc.mean()),
        "env_pop_net_mean": float(env_net.mean()),
        "env_pop_popmatch_mean": float((w_match @ pop).mean()),
        "popmatch_b_median": float(np.median(b_match)),
        "graph_nodes": int(G.number_of_nodes()),
        "graph_downloaded": (dt.datetime.fromtimestamp(graph_path.stat().st_mtime).date().isoformat()
                             if graph_path.exists() else None),
        "osmnx_version": ox.__version__,
        **network_metrics(Gc, area_km2),
        **fragmentation(G, sample_from=list(Gc.nodes), **(frag_kwargs or {})),
    }
    out = {"indices": rows, "city": city}
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(out, default=float))
    return out


def run_all(cities_df, race, data_dir, out_dir, **kw):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    idx_rows, city_rows, fails = [], [], []
    for rec in cities_df.itertuples(index=False):
        try:
            res = run_city(rec.COD_MUNICIPIO, rec.NM_MUN, race, data_dir, **kw)
            idx_rows += res["indices"]
            city_rows.append(res["city"])
            print(f"ok   {rec.COD_MUNICIPIO} {rec.NM_MUN}", flush=True)
        except Exception as exc:  # one city must not stop the run
            fails.append({"COD_MUNICIPIO": rec.COD_MUNICIPIO, "NM_MUN": rec.NM_MUN, "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAIL {rec.COD_MUNICIPIO} {rec.NM_MUN}\n{traceback.format_exc()}", flush=True)
    idx = pd.DataFrame(idx_rows)
    cty = pd.DataFrame(city_rows)
    idx.to_parquet(out_dir / "indices_long.parquet", index=False)
    cty.to_parquet(out_dir / "cities.parquet", index=False)
    pd.DataFrame(fails, columns=["COD_MUNICIPIO", "NM_MUN", "error"]).to_csv(out_dir / "failures.csv", index=False)
    return idx, cty
