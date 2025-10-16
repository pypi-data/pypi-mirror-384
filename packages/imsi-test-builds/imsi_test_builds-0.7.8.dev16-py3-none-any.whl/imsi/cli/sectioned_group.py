import click
from imsi.cli.lazy import LazyGroup


class SectionedGroup(LazyGroup):
    """Like LazyGroup, but prints commands and sub‑groups in separate sections in the help message."""

    def format_commands(self, ctx, formatter):
        commands, groups = [], []

        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is None or cmd.hidden:
                continue
            row = (name, cmd.get_short_help_str())
            # check if in a group or a command
            (groups if isinstance(cmd, click.Group) else commands).append(row)

        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(commands)

        if groups:
            # Blank line between sections is automatic
            with formatter.section("Command Groups"):
                formatter.write_dl(groups)
