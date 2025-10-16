import click
from pathlib import Path
from dotenv import dotenv_values
import os
from importlib.resources import files


def load_rc(variable=None, default=None):
    """
    Load environment variables from the site and user-specific .env files.
    This function is called at the start of the CLI to ensure that all necessary
    environment variables are available for the commands.
    """

    config_site = dotenv_values(dotenv_path=files("imsi").joinpath("imsi.site.rc"))
    config_user = dotenv_values(dotenv_path=f"{os.getenv('HOME')}/imsi.user.rc")
    config_env = os.environ

    var_list = []
    for config, source in zip(
        (config_site, config_user, config_env),
        ("imsi.site.rc", "imsi.user.rc", "$IMSI_DEFAULT_CONFIG_REPOS"),
    ):
        value = config.get(variable, None)
        if value is None:
            continue

        # Always split on colon
        # if nones exist (give [value])
        for v in str(value).split(":"):
            if v:  # ignore empty parts from "::"
                var_list.append((v, source))

    return var_list or None


def get_repo_paths(repo_path: str | None) -> tuple[list[Path], Path]:
    """
    Resolves and validates repository paths containing 'imsi-config' directories.

    Depending on the provided `repo_path` argument and the current working directory,
    this function determines which repositories to use, validates their configuration
    requirements, and returns a list of valid repository paths along with the relative
    path to the 'imsi-config' directory.

    Args:
        repo_path (str | None): Optional path to a specific repository. If None, the function
            will attempt to use the current working directory or load default repositories
            from the runtime configuration.

    Returns:
        tuple[list[Path], Path]: A tuple containing:
            - A list of Path objects, each representing a repository containing an 'imsi-config' directory.
            - A Path object representing the relative path to the 'imsi-config' directory.

    Raises:
        ValueError: If no valid repositories with an 'imsi-config' directory are found,
            or if any provided path is not a directory.
    """
    from imsi.user_interface.ui_manager import validate_version_reqs

    run_dir_config = Path.cwd() / "src" / "imsi-config"

    if not repo_path and run_dir_config.exists():
        validate_version_reqs(run_dir_config)
        return [Path.cwd()], ["pwd"], Path("src", "imsi-config")

    if repo_path:
        base_paths = [(Path(repo_path), "CLI args")]
    else:
        rc_paths = load_rc("IMSI_DEFAULT_CONFIG_REPOS")
        if not rc_paths:
            raise ValueError("No repositories provided via --repo-path or IMSI_DEFAULT_CONFIG_REPOS in user or site rc file.")
        base_paths = [(Path(p), source) for p, source in rc_paths]

    paths, sources = [], []
    for base, source in base_paths:
        if not base.is_dir():
            raise ValueError(f"Path '{base}' is not a directory.")

        if (base / "imsi-config").is_dir():
            matches = [base]
        else:
            matches = [p for p in base.iterdir() if p.is_dir() and (p / "imsi-config").is_dir()]

        paths.extend(matches)
        sources.extend([source] * len(matches))

    if not paths:
        raise ValueError(f"No repositories with 'imsi-config' found in: {base_paths}")

    for path in paths:
        validate_version_reqs(path / "imsi-config")

    return paths, sources, Path("imsi-config")


@click.command(name="list", short_help="List available IMSI configurations.")
@click.option('--repo-path', default=None, help="Path to either a single repo or a directory of repos.")
@click.option('--filter-model', default=None, type=str, help="Filter by model name.")
@click.option('--filter-experiment', default=None, type=str, help="Filter by experiment name.")
def list(repo_path, filter_model, filter_experiment):
    """List available IMSI configurations."""

    from imsi.tools.list.list_manager import list_all_choices
    paths, sources, config_path = get_repo_paths(repo_path)

    list_all_choices(
        repo_paths=paths,
        repo_sources=sources,
        relative_imsi_config_path=config_path,
        filter_model=filter_model,
        filter_experiment=filter_experiment
    )
