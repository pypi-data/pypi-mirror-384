from pathlib import Path
from breathe_design import api_interface as api
from tests.utils import run_notebooks
import pytest

# ---- Collect all notebooks under docs/examples ----
EXAMPLE_NOTEBOOK_DIR = Path("docs") / "examples"
EXAMPLE_NOTEBOOKS = sorted(p for p in EXAMPLE_NOTEBOOK_DIR.rglob("*.ipynb"))


def test__show_service_version(use_m2m_auth):
    version = api.get_service_version()
    print(f"Service version is {version}")


@pytest.mark.parametrize(
    "notebook_path", EXAMPLE_NOTEBOOKS, ids=[str(s) for s in EXAMPLE_NOTEBOOKS]
)
def test_run_example_notebooks_without_errors(notebook_path, use_m2m_auth):
    run_notebooks(notebook_path, use_m2m_auth)
