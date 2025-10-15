import importlib
import pathlib

import pytest


def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def test_pyproject_declares_distribution_name() -> None:
    pyproject_path = project_root() / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.fail("pyproject.toml not found; run `Milestone 0` scaffolding")

    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover
        pytest.skip("tomllib not available")

    with pyproject_path.open("rb") as fp:
        data = tomllib.load(fp)

    project = data.get("project")
    assert project, "pyproject.toml missing [project] section"
    assert project.get("name") == "spaps", "distribution name must be 'spaps'"
    assert "version" in project, "project version must be declared"


def test_package_exports_version_attribute() -> None:
    module = importlib.import_module("spaps_client")
    assert hasattr(module, "__version__"), "__version__ attribute must be exposed"
