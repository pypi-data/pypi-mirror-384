import click
from pydantic import ValidationError
from rich.prompt import Prompt
from imsi.user_interface.setup_manager import ValidatedSetupOptions, InvalidSetupConfig
from imsi.tools.list.list_cli import get_repo_paths
from imsi.tools.menu.menu_helpers import (
    select_imsi_config_with_questionary,
    prompt_additional_options,
    build_setup_command,
    print_command,
    execute_command,
)


@click.command(name="setup-menu", short_help="Interactive menu to explore IMSI configurations.")
@click.option('--repo-path', default=None, help="Path to a repo or directory of repos.")
@click.option('--execute', is_flag=True, help="Execute the setup command after selection.")
def setup_menu(repo_path, execute):
    repo_paths, repo_sources, config_path = get_repo_paths(repo_path)

    while True:
        # Step 1: Prompt for selection
        selection = select_imsi_config_with_questionary(repo_paths, repo_sources, config_path)
        if not selection:
            print("\033[1;31m[✗] No item selected\033[0m")
            return

        # Step 2: Prompt for CLI extras
        additions = prompt_additional_options()
        if additions is None:
            return
        else:
            selection.update(additions)

        # Step 3: Validate
        try:
            ValidatedSetupOptions(**selection)
            break  # valid config, exit loop
        except (InvalidSetupConfig, ValidationError) as e:
            print(f"\033[1;31m[✗] Invalid setup options: {e}\033[0m")
            if Prompt.ask("Try again?", choices=["yes", "no"], default="yes") == "no":
                print("\033[2m[Exiting setup]\033[0m")
                return

    # Step 4: Build and show setup command
    setup_cmd = build_setup_command(selection)
    print_command(setup_cmd)

    # Step 5: Ask if it should be executed
    if execute or Prompt.ask("Execute now?", choices=["yes", "no"], default="yes") == "yes":
        execute_command(setup_cmd)