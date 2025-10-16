"""
imsi CLI
--------

The entry-point console script that interfaces all users commands to imsi.

imsi has several categories of sub-commands. As this module develops further,
the sub-groups are implemented in the relevant downstream modules.
"""

import click
from imsi.cli.sectioned_group import SectionedGroup


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    cls=SectionedGroup,
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS,
)
@click.version_option()
@click.option("-f", "--force", is_flag=True, help="Force the operation")
@click.pass_context
def cli(ctx, force):
    """IMSI CLI — manage configs, builds, runs, and tools. Add the -h or --help flag to any command for more information."""
    ctx.ensure_object(dict)
    ctx.obj["FORCE"] = force


cli.add_lazy_command("imsi.cli.core_cli.setup")
cli.add_lazy_command("imsi.cli.core_cli.config", short_help="Configure a simulation with updated settings from on-disk repo")
cli.add_lazy_command(
    "imsi.cli.core_cli.save_restarts",
    name="save-restarts",
    short_help="Save restarts into the local run database & RUNPATH. Add -h for more information.",
    context_settings={"ignore_unknown_options": True},
    add_help_option=False,  # Disable automatic help flag,
    )
cli.add_lazy_command(
    "imsi.cli.core_cli.build",
    short_help="Compile model components. Add -h for more information.",
    context_settings={"ignore_unknown_options": True},
    add_help_option=False,  # Disable automatic help flag
)
cli.add_lazy_command("imsi.cli.core_cli.submit")
cli.add_lazy_command("imsi.cli.core_cli.status")
cli.add_lazy_command("imsi.tools.disk_tools.disk_tools_cli.clean")
cli.add_lazy_command("imsi.cli.core_cli.reload")
cli.add_lazy_command("imsi.cli.core_cli.set")
cli.add_lazy_command("imsi.tools.list.list_cli.list")
cli.add_lazy_command("imsi.cli.core_cli.log_state", name="log-state")

cli.add_lazy_command("imsi.tools.ensemble.ensemble_cli.ensemble")
cli.add_lazy_command("imsi.tools.time_manager.timer_cli.chunk_manager", name="chunk-manager")
cli.add_lazy_command("imsi.tools.simple_sequencer.iss_cli.iss")
cli.add_lazy_command("imsi.tools.menu.menu_cli.setup_menu", name="setup-menu", short_help="Interactive menu to explore IMSI configurations.")
cli.add_lazy_command("imsi.tools.validate.validate_cli.validate", name="validate", short_help="Validate imsi configuration files.")
