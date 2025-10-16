import click
import importlib


class LazyCommand(click.Command):
    def __init__(
        self,
        import_path,
        name=None,
        short_help="",
        context_settings=None,
        add_help_option=False,
    ):
        self._import_path = import_path
        self._real_command = None
        self._short_help = short_help
        super().__init__(
            name or import_path.split(".")[-1],
            short_help=short_help,
            context_settings=context_settings or {},
            add_help_option=add_help_option,
        )

    def _load_command(self):
        if self._real_command is None:
            module_path, func_name = self._import_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            self._real_command = getattr(module, func_name)
        return self._real_command

    def invoke(self, ctx):
        return self._load_command().invoke(ctx)

    def get_help(self, ctx):
        return self._load_command().get_help(ctx)

    def get_params(self, ctx):
        return self._load_command().get_params(ctx)

    def format_help(self, ctx, formatter):
        return self._load_command().format_help(ctx, formatter)

    def format_usage(self, ctx, formatter):
        return self._load_command().format_usage(ctx, formatter)

    def get_short_help_str(self, limit=45):
        return self._short_help or self._load_command().get_short_help_str(limit)


class LazyGroup(click.Group):
    def __init__(self, *args, **kwargs):
        self._lazy_commands = {}
        super().__init__(*args, **kwargs)

    def add_lazy_command(
        self,
        import_path: str,
        name: str | None = None,
        short_help: str = "",
        **lazy_kwargs,
    ):
        """
        Register a lazy‑loaded command or group.

        Parameters
        ----------
        import_path : str
            Dotted import path to a click.Command or click.Group object.
        name : str, optional
            Override the command name shown in the CLI.
        short_help : str, optional
            One‑liner shown in the parent help without importing the module.
        **lazy_kwargs
            Extra keyword args forwarded to LazyCommand
            (e.g. context_settings, add_help_option).
        """
        name = name or import_path.split(".")[-1]
        self._lazy_commands[name] = (import_path, short_help, lazy_kwargs)

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._lazy_commands:
            import_path, short_help, extra = self._lazy_commands[cmd_name]
            module_path, func_name = import_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            real_cmd = getattr(module, func_name)

            # If it's a Group, return it as‑is (no wrapper needed)
            if isinstance(real_cmd, click.Group):
                return real_cmd

            # Else wrap it, forwarding all extra kwargs
            return LazyCommand(
                import_path,
                name=cmd_name,
                short_help=short_help,
                **extra,
            )

        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        cmds = list(self.commands.keys())
        lazies = [name for name in self._lazy_commands.keys() if name not in self.commands]
        return cmds + lazies
