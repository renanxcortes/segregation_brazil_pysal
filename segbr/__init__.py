"""Nationwide multidimensional racial segregation measurement for Brazil (2022 Census)."""

from segbr.census import load_census, municipality_universe
from segbr.cities import build_city_gdf

__all__ = ["load_census", "municipality_universe", "build_city_gdf"]
