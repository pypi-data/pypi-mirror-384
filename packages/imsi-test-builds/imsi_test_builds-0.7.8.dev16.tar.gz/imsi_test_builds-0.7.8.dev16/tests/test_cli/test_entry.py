from imsi.cli.entry import cli
import pytest
from pathlib import Path
from click.testing import CliRunner
import os

# append new tools here
TOOL_LIST = ["setup", "chunk-manager"]


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize("command", ["--help", "-h"])
def test_cli_initialization(runner, command):
    result = runner.invoke(cli, [command])
    assert result.exit_code == 0


@pytest.mark.parametrize("command_name", TOOL_LIST)
def test_cli_subcommands_added(runner, command_name):
    # Ensure each sub-command is present and can be invoked without errors
    result = runner.invoke(cli, [command_name, "--help"])
    assert result.exit_code == 0
    assert f"Usage: cli {command_name}" in result.output


@pytest.mark.parametrize(
    "command_name",
    ["config", "submit", "reload", "set", "list", "status"],
)
def test_cli_subcommands_requiring_repo(runner, command_name):
    with runner.isolated_filesystem() as tmp_dir:
        (Path(tmp_dir) / "src").mkdir()
        result = runner.invoke(cli, [command_name, "--help"])

        assert result.exit_code == 0
        assert f"Usage: cli {command_name}" in result.output


# test that error is raised with wrong WRK_DIR
def test_cli_wrk_dir(runner):
    with runner.isolated_filesystem() as tmp_dir:
        os.environ["WRK_DIR"] = "bad_dir"
        result = runner.invoke(
            cli,
            [
                "config",
            ],
        )
        del os.environ["WRK_DIR"]
        assert result.exit_code == 1
        assert result.exception


# test that warning is raised if both WRK_DIR and src directory found
def test_cli_both_directories(runner):
    with runner.isolated_filesystem() as tmp_dir:
        # make a spoof setup directory parent
        Path(tmp_dir, "test_dir").mkdir(parents=True, exist_ok=True)

        # spoof a setup directory by making src
        (Path(tmp_dir, "test_dir").resolve() / "src").mkdir()
        os.environ["WRK_DIR"] = str(Path(tmp_dir, "test_dir").resolve())

        # spoof a setup directory by making src in the cwd
        (Path(tmp_dir).resolve() / "src").mkdir()

        with pytest.warns(UserWarning):
            runner.invoke(cli, ["config"])
        del os.environ["WRK_DIR"]


# test that error is raised in src or WRK_DIR not set
def test_cli_no_directories(runner):
    with runner.isolated_filesystem() as tmp_dir:
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 1
        assert result.exception
