import pytest
from click.testing import CliRunner

from imsi.tools.ensemble.ensemble_cli import ensemble


@pytest.fixture
def dummy_config(tmp_path):
    """Creates a dummy config.yaml file that won't be parsed but will bypass file existence checks."""
    config = tmp_path / "config.yaml"
    config.write_text(
        """
        ensemble_level:
          user: dummy
          run_directory: .
        member_level: {}
        """)  # Content isn't used
    return config


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize(
    ("command", "expected_message"),
    [
        (None, "Attempting to use configuration file"),
        ("--help", "Commands to manage ensemble runs"),
    ],
    ids=["no_command", "help_command"]
)
def test_ensemble_base_help(runner, dummy_config, command, expected_message):
    """Test base CLI group with no subcommand or --help."""
    args = ["--config-path", str(dummy_config)]
    if command:
        args.append(command)
    result = runner.invoke(ensemble, args)
    assert result.exit_code == 0
    assert expected_message in result.output


@pytest.mark.parametrize("subcommand", ["setup", "config", "save-restarts", "build", "submit", "status"])
def test_subcommands_help(runner, dummy_config, subcommand):
    """Each subcommand should show help and be callable."""
    result = runner.invoke(ensemble, ["--config-path", str(dummy_config), subcommand, "--help"])
    assert result.exit_code == 0
    assert subcommand in result.output
