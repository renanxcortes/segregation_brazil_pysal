import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def census_csv(repo_root) -> pathlib.Path:
    p = repo_root / "Agregados_por_setores_cor_ou_raca_BR_csv" / "Agregados_por_setores_cor_ou_raca_BR.csv"
    if not p.exists():
        pytest.skip(f"census CSV not present at {p}")
    return p


@pytest.fixture(scope="session")
def shp_dir(repo_root) -> pathlib.Path:
    p = repo_root / "shapefiles_2022"
    if not p.exists():
        pytest.skip(f"shapefiles_2022 not present at {p}")
    return p
