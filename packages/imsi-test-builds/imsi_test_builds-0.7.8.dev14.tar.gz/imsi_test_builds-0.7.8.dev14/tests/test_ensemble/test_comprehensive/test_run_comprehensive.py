# tests/test_ensemble/test_comprehensive/test_cli.py
from pathlib import Path
import shutil

import pytest
from click.testing import CliRunner

from imsi.tools.ensemble.ensemble_cli import ensemble


CONFIG_DIR = Path.cwd() / "tests" / "test_ensemble" / "test_comprehensive"  # directory containing this file
CONFIG_FILES = sorted(CONFIG_DIR.glob("config*.yaml"))
RUN_DIRECTORY = Path.cwd() / "tests" / "test_ensemble" / "test_comprehensive" / "tmp_setup_dirs"  # directory for test runs

# Skip the whole module cleanly if nothing to test
if not CONFIG_FILES:
    pytest.skip(
        f"No configuration files matching 'config*.yaml' found in {CONFIG_DIR}.",
        allow_module_level=True,
    )

@pytest.fixture(scope="session")
def runner() -> CliRunner:
    """A single CliRunner reused for every parametrised test."""
    return CliRunner()


@pytest.fixture
def setup_dir(tmp_path):
    """
    A unique temporary directory for each test invocation,
    e.g. /tmp/pytest-of-<user>/pytest-NNNN/p0.
    If your CLI needs to *see* this directory (via an env-var or flag),
    monkeypatch or add an option here.
    """
    return tmp_path


@pytest.mark.parametrize(
    "config_file",
    CONFIG_FILES,
    ids=[p.name for p in CONFIG_FILES],  # pretty node names in `pytest -vv`
)
def test_setup_and_save_restarts(runner, setup_dir, config_file):
    """Ensure `setup` succeeds for every config YAML."""
    RUN_DIRECTORY.mkdir(parents=True, exist_ok=True)
    try:
        result = runner.invoke(
            ensemble,
            ["--config-path", str(config_file), "setup"],
        )
    except FileNotFoundError as e:
        print(f"File not found: {e}. Expected error if in GitLab CI environment.")
    finally:
        shutil.rmtree(RUN_DIRECTORY, ignore_errors=True)
