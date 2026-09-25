"""PySAL segregation indices on spatially weighted local environments."""

from __future__ import annotations

import numpy as np
from segregation.multigroup import MultiInfoTheory
from segregation.singlegroup import Dissim, Entropy, Isolation

from netseg.cities import GROUPS


def local_environment(gdf, cols: list[str], wsp):
    """Spatially lagged counts, as in segregation._base._build_local_environment (rounded to integers)."""
    out = gdf[[gdf.geometry.name]].copy()
    lagged = wsp @ gdf[cols].to_numpy(dtype=float)
    for k, c in enumerate(cols):
        out[c] = np.round(lagged[:, k], 0)
    return out


def compute_indices(gdf, wsp) -> dict[str, float]:
    # a group absent citywide contributes 0 to H (0 log 0 = 0); PySAL would return NaN
    groups = [c for c in GROUPS if gdf[c].sum() > 0]
    env = local_environment(gdf.reset_index(drop=True), [*groups, "pp_total", "pop_total"], wsp)
    return {
        "H": float(MultiInfoTheory(env, groups=groups).statistic),
        "Dissim_pp": float(Dissim(env, "pp_total", "pop_total").statistic),
        "Isolation_pp": float(Isolation(env, "pp_total", "pop_total").statistic),
        "Entropy_pp": float(Entropy(env, "pp_total", "pop_total").statistic),
    }
