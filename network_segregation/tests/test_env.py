import importlib

import pytest


@pytest.mark.parametrize(
    "mod", ["geopandas", "libpysal", "segregation", "osmnx", "networkx", "scipy", "statsmodels", "momepy", "seaborn"]
)
def test_import(mod):
    importlib.import_module(mod)


def test_segregation_version():
    import segregation

    assert segregation.__version__ == "2.5.3"
