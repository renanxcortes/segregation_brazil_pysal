"""The nine Massey-dimension segregation measures for a single city GeoDataFrame."""

from __future__ import annotations

import time

from segregation.singlegroup import (
    Dissim, SpatialDissim, Gini, Entropy, Isolation, DistanceDecayIsolation,
    RelativeConcentration, RelativeCentralization, RelativeClustering,
)

MEASURES: dict[str, tuple[type, str]] = {
    "Dissim": (Dissim, "Evenness"),
    "SpatialDissim": (SpatialDissim, "Evenness"),
    "Gini": (Gini, "Evenness"),
    "Entropy": (Entropy, "Evenness"),
    "Isolation": (Isolation, "Exposure"),
    "DistanceDecayIsolation": (DistanceDecayIsolation, "Exposure"),
    "RelativeConcentration": (RelativeConcentration, "Concentration"),
    "RelativeCentralization": (RelativeCentralization, "Centralization"),
    "RelativeClustering": (RelativeClustering, "Clustering"),
}


def compute_profile(gdf, *, measures=None, time_budget_s=None) -> dict:
    """Compute selected segregation measures for one city GeoDataFrame.

    A failure in one measure is recorded under ``<name>_error`` and does not
    abort the rest. ``time_budget_s`` (if set) skips remaining measures once the
    elapsed wall-clock exceeds it, recording ``<name>_error='skipped: time budget'``.
    """
    names = list(measures) if measures is not None else list(MEASURES)
    pop_total = int(gdf["pop_total"].sum())
    pp_total = int(gdf["pp_total"].sum())
    out: dict = {
        "n_tracts": int(len(gdf)),
        "pop_total": pop_total,
        "pp_total": pp_total,
        "ppp": (pp_total / pop_total) if pop_total else float("nan"),
        "timings": {},
    }
    start = time.perf_counter()
    for name in names:
        cls, _dim = MEASURES[name]
        if time_budget_s is not None and time.perf_counter() - start > time_budget_s:
            out[f"{name}_error"] = "skipped: time budget"
            continue
        t0 = time.perf_counter()
        try:
            out[name] = float(
                cls(gdf, group_pop_var="pp_total", total_pop_var="pop_total").statistic
            )
        except Exception as exc:  # noqa: BLE001 - deliberate: isolate per-measure failure
            out[f"{name}_error"] = f"{type(exc).__name__}: {exc}"
        finally:
            out["timings"][name] = round(time.perf_counter() - t0, 2)
    out["seconds"] = round(time.perf_counter() - start, 2)
    return out
