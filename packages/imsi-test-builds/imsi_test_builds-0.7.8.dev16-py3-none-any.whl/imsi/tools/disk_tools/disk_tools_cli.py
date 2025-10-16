import click


@click.command(help="Deletes directories. "
               "By default cleans up scratch and storage directories.")
@click.option(
    "--runid_path",
    default=None,
    required=True,
    type=click.Path(),
    help='Directory where the run has been created. Must contain imsi config file for the run.',
)
@click.option("-s", "--setup", is_flag=True, help="Clean setup directory.")
@click.option("-t", "--scratch_dir", "temp", is_flag=True, help="Clean scratch data.")
@click.option("-d", "--storage_dir", "data", is_flag=True, help="Clean storage data.")
@click.option("-a", "--all", "clean_all", is_flag=True, help="Clean all locations.")
def clean(runid_path, setup, temp, data, clean_all):
    # If no options selected by default cleans data and temp directories
    from imsi.tools.disk_tools.disk_tools import clean_run

    if clean_all:
        setup, temp, data = (True, True, True)
    else:
        temp, data = (True, True) if not any([temp, setup, data]) else (temp, data)

    clean_run(runid_path, setup, temp, data)
