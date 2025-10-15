import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore[import]


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def package_version() -> str:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as fp:
        data = tomllib.load(fp)
    return data["project"]["version"]


@pytest.fixture()
def dist_dir(tmp_path: Path) -> Path:
    return tmp_path / "dist"


def test_python_package_builds(dist_dir: Path) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
        cwd=PROJECT_ROOT,
    )

    wheels = list(dist_dir.glob("spaps-*.whl"))
    sdists = list(dist_dir.glob("spaps-*.tar.gz"))
    assert wheels, "Wheel file was not produced"
    assert sdists, "Source distribution was not produced"


def test_built_wheel_installs_in_clean_environment(dist_dir: Path) -> None:
    subprocess.check_call(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
        cwd=PROJECT_ROOT,
    )

    wheel = next(dist_dir.glob("spaps-*.whl"))

    with tempfile.TemporaryDirectory() as venv_dir:
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        python_bin = Path(venv_dir) / "bin" / "python"
        pip_bin = Path(venv_dir) / "bin" / "pip"

        subprocess.check_call([pip_bin, "install", str(wheel)])
        code = "import spaps_client; print(spaps_client.__version__)"
        captured = subprocess.check_output([python_bin, "-c", code], text=True).strip()
        assert captured == package_version()
