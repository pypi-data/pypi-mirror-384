from imsi.tools.ensemble.table_utils.table_utils import convert_to_bracket_notation, colour
from imsi.cli.core_cli import setup, config, build, submit, save_restarts, status
from imsi.user_interface.setup_manager import InvalidSetupConfig, change_dir


import click
import re
from omegaconf import OmegaConf, DictConfig
from typing import Any, Generator
from pathlib import Path
import warnings


def loop_click_command_on_table(command: callable, run_path: Path, tables) -> None:
    """Calls a click cli command for each member in the table."""
    for member in tables:
        member = OmegaConf.create(member)
        runid_path = Path(run_path, member.setup.runid)
        with change_dir(runid_path):
            ctx = click.Context(command, obj={"FORCE": True})
            try:
                ctx.invoke(command)
            except Exception as e:
                click.echo(
                    f"Error while running {command.name} for {member.setup.runid}: {e}"
                )
                raise e


def save_restarts_ensemble(ensemble_config: DictConfig, tables: list) -> None:
    """Save restarts for each member in the ensemble."""
    run_path = Path(ensemble_config.ensemble_level.run_directory).resolve()
    loop_click_command_on_table(save_restarts, run_path, tables)


def compile_ensemble(ensemble_config: DictConfig, tables: list) -> None:
    """Compile each member in the ensemble."""
    run_path = Path(ensemble_config.ensemble_level.run_directory).resolve()
    loop_click_command_on_table(build, run_path, tables)


def submit_ensemble(ensemble_config: DictConfig, tables: list) -> None:
    """Submit each member in the ensemble."""
    run_path = Path(ensemble_config.ensemble_level.run_directory).resolve()
    loop_click_command_on_table(submit, run_path, tables)


def status_ensemble(ensemble_config: DictConfig, tables: list) -> None:
    run_path = Path(ensemble_config.ensemble_level.run_directory).resolve()
    loop_click_command_on_table(status, run_path, tables)


def setup_ensemble_members(run_path: Path, tables: list) -> None:
    """Run setup command for each run in the ensemble.
    Extracts the setup arguments from the table and runs the setup command.
    """
    print(f"Setting up ensemble members in {run_path}")
    with change_dir(run_path.resolve()):  # TODO: Rethink/refactor
        for member in tables:
            member = OmegaConf.create(member)
            setup_args = get_command_args(member.setup, setup)
            ctx = click.Context(setup, obj={"FORCE": True})
            try:
                ctx.invoke(setup, **setup_args)
            except InvalidSetupConfig as e:
                raise InvalidSetupConfig(
                    f"Error while running setup for {setup_args['runid']}: {e}"
                )


def check_versions_not_unique(tables: list) -> None:
    """If share_repo is True, all runs must have the same version."""
    versions = {member.setup["ver"] for member in tables if "ver" in member.setup}
    if len(versions) > 1:
        raise ValueError("All runs must have the same version if share_repo is True")


def override_table_values_for_shared_repo(run_path: Path, tables: list) -> None:
    """Override these setup args table values for shared repo."""
    for member in tables[1:]:
        setup_config = OmegaConf.create({
                "setup": {
                    "fetch_method": "link",
                    "repo": str(run_path / tables[0]["setup"]["runid"] / "src"),
                }
            })
        # Remove ver. It will use the linked version from the first run.
        member.setup.pop("ver", None)
        # Update the member's setup with the shared repo values in place
        member.setup.merge_with(setup_config.setup)


def run_setup_and_config(ensemble_config: DictConfig, tables: list) -> None:
    """Setup the ensemble run directories and run the config command."""
    run_path = Path(ensemble_config.ensemble_level.run_directory).resolve()
    run_path.mkdir(parents=True, exist_ok=True)
    if ensemble_config.ensemble_level.share_repo:
        check_versions_not_unique(tables)
        # start with first table as template
        setup_ensemble_members(run_path, [tables[0]])
        # link, set src, and ver None for remaining runs
        override_table_values_for_shared_repo(run_path, tables)
        # proceed with the rest of the runs
        setup_ensemble_members(run_path, tables[1:])
    else:
        setup_ensemble_members(run_path, tables)

    config_ensemble_members(run_path, tables)


def update_state_at_keypath(
    run_path: Path, member: DictConfig, setup_args: DictConfig
) -> None:
    """Update member resolved user config file"""
    runid = member.setup.runid
    path_to_imsi_config = Path(
        run_path, runid, f"imsi_configuration_{runid}.yaml"
    )
    imsi_config = OmegaConf.load(path_to_imsi_config)

    # isolate keys that aren't in setup to update
    for full_key_path, value in get_keys_not_in_setup_args(member, setup_args):
        update_config_at_keypath(imsi_config, full_key_path, value)

    config_yamlable = OmegaConf.to_container(imsi_config)
    with open(path_to_imsi_config, "w") as f:
        OmegaConf.save(config_yamlable, f)


def run_config(ensemble_config: DictConfig, tables: list) -> None:
    """Run the config command for each member in the ensemble."""
    run_path = Path(ensemble_config.ensemble_level.run_directory).resolve()
    config_ensemble_members(run_path, tables)


def config_ensemble_members(run_path: Path, tables: list) -> None:
    """Loop through table members and run the config command."""
    with change_dir(run_path.resolve()):  # TODO: Rethink/refactor
        for member in tables:
            member = OmegaConf.create(member)
            setup_args = get_command_args(member.setup, setup)
            update_state_at_keypath(run_path, member, setup_args)

            with change_dir(run_path / member.setup.runid):  # TODO: Rethink/refactor
                ctx = click.Context(config, obj={"FORCE": True})
                try:
                    ctx.invoke(config)
                except AttributeError as e:
                    click.echo(
                        f"Error while running config for {setup_args['runid']}."
                        "Check that the full keypaths are compatible with the configuration.\n"
                        "A common cause of this error is a missing level or key in the configuration."
                    )
                    raise e


def get_keys_not_in_setup_args(
    member: DictConfig, setup_args: DictConfig, parent_key: str = ""
) -> Generator[tuple[str, Any], None, None]:
    """
    Recursively yield key paths and values from member dictionaries
    where keys are not in `setup_args`.
    """

    for key, value in member.items():
        if key == "setup":
            # Skip the setup key itself
            continue

        full_key = f"{parent_key}:{key}" if parent_key else key
        full_key = convert_to_bracket_notation(full_key)
        if isinstance(value, (dict, DictConfig)):
            # Recursively check nested dictionaries
            yield from get_keys_not_in_setup_args(value, setup_args, full_key)
        else:
            # Yield the key path if the key is not in setup_args
            if full_key not in setup_args:
                yield full_key, value


def get_command_args(run: DictConfig, command: click.Command) -> DictConfig[str, Any]:
    """Get the command arguments from the table for the given command."""
    expected_args = {param.name: param for param in command.params}
    command_args = {k: v for k, v in run.items() if k in expected_args}
    return OmegaConf.create(command_args)


def parse_bracket_key_path(key_path: str):
    """Parse bracketed key paths like 'components[CanAM][input_files][GHG_SCENARIO]' into a list of keys."""
    pattern = r'([^\[\]]+)|\[([^\[\]]+)\]'
    matches = re.findall(pattern, key_path)
    return [m[0] or m[1] for m in matches]


def get_value_by_key_path(obj: dict, key_path: str):
    keys = parse_bracket_key_path(key_path)
    for key in keys:
        if isinstance(obj, dict):
            if key in obj:
                obj = obj[key]
            else:
                return None
        else:
            return None
    return obj


def key_exists(config: DictConfig, key_path: str) -> bool:
    keys = parse_bracket_key_path(key_path)
    parent_keys = keys[:-1]
    last_key = keys[-1]

    raw_dict = OmegaConf.to_container(config, resolve=False)
    parent = get_value_by_key_path(raw_dict, "".join(f"[{k}]" for k in parent_keys)) if parent_keys else raw_dict

    return isinstance(parent, dict) and last_key in parent


def update_config_at_keypath(config: DictConfig, key_path: str, value: Any) -> None:
    """Update the configuration dict at a nested key path."""

    if not key_exists(config, key_path):
        warnings.warn(
            colour(
                f"\n  Key path '{key_path}' is specified in the configuration but is not an existing key in the resolved imsi configuration. Please ignore this warning if this is intended.",
                "yellow"
            ),
            UserWarning
        )

    OmegaConf.update(config, key_path, value)
