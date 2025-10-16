
import click
import sys
import json

@click.group()
def chunk_manager():
    """Manage time information for the simulation"""
    pass

@chunk_manager.command()
@click.option('--tracking-file', default="tracking.json", help="Path to the tracking file.")
@click.option('--timer-name', required=True, help="The name of the timer to track the chunking session.")
def current(tracking_file, timer_name):
    """Get current chunk for specific timer from chunk_file."""
    import imsi.tools.time_manager.chunk_manager as cm

    chunk_data = cm.get_current_chunk(tracking_file, timer_name)
    if chunk_data is not None:
        print(json.dumps(chunk_data, indent=2))
    else:
        click.echo(f"Error: Timer '{timer_name}' not found in tracking file.", err=True)
        sys.exit(1)

@chunk_manager.command()
@click.option('--chunk-file', required=True, type=click.Path(exists=True), help="Path to the chunks file.")
@click.option('--tracking-file', required=True, default="tracking.json", help="Path to the tracking file.")
@click.option('--timer-name', required=True, help="The name of the timer to track the chunking session.")
def increment(chunk_file, tracking_file, timer_name):
    """Move to the next time chunk for a given timer and update the tracking file."""
    import imsi.tools.time_manager.chunk_manager as cm

    status = cm.increment_chunk_logic(chunk_file, tracking_file, timer_name)
    click.echo(status)

@chunk_manager.command()
@click.option('--chunk-file', required=True, type=click.Path(exists=True), help="Path to the chunks file.")
@click.option('--tracking-file', default="tracking.json", help="Path to the tracking file.")
@click.option('--timer-name', required=True, help="The name of the timer to track the chunking session.")
def init(chunk_file, tracking_file, timer_name):
    """Initialize the tracking file with the first chunk for the specified timer."""
    import imsi.tools.time_manager.chunk_manager as cm

    cm.init_tracking_file(chunk_file, tracking_file, timer_name)

@chunk_manager.group(
    short_help="Create an environment file of the chunk's time data.",
    help='Create the environment file that contains chunk time information as environment variables.'
    )
def create_time_env_file():
    pass

@create_time_env_file.command(
    short_help="Create an environment file of the chunk's time data using the timer tracking file.",
    help="Create an environment file of the chunk's time data using the timer tracking file.",
    )
@click.option('--tracking-file', required=True, default=".simulation.time.state", type=click.Path(exists=True),
              help="Path to the timer tracking file that contains the current time information for the simulation.")
@click.option('--timer-name', required=True, help="The name of the timer to track the chunking session.")
@click.option('--prefix', required=True, help="Prefix for environment variables.")
@click.option('--output-file', required=True, type=click.Path(), help="Path to the output shell file.")
@click.option('--calendar', default="noleap", help="Calendar system for cftime (e.g., 'gregorian', 'noleap', '360_day').")
def from_tracking_file(tracking_file, timer_name, prefix, output_file, calendar):
    """
    Create a shell file with environment variables based on the current chunk data.
    The tracking file contains only the current date/time information for the simulation,
    """
    import imsi.tools.time_manager.chunk_manager as cm


    # Get the current chunk data
    chunk_data = cm.get_current_chunk(tracking_file, timer_name)
    if chunk_data is None:
        click.echo(f"Error: Timer '{timer_name}' not found in tracking file.", err=True)
        sys.exit(1)

    # Extract relevant dates from the current chunk
    restart_date = chunk_data["RESTART"]
    start_date = chunk_data["START"]
    stop_date = chunk_data["END"]

    # Convert strings into cftime objects
    restart_date_cf, start_date_cf, stop_date_cf = cm.date_strings_to_cftime(restart_date, start_date, stop_date, calendar)

    # Call the function to write the environment variables to a file
    cm.write_env_variables_to_file(restart_date_cf, start_date_cf, stop_date_cf, prefix, output_file)
    click.echo(f"Environment variables written to {output_file}.")

@create_time_env_file.command(
    short_help="Create an environment file of the chunk's time data using the chunk's time information (iso8601).",
    help="Create an environment file of the chunk's time data using the chunk's time information (iso8601)."
    )
@click.option('--isostr', type=str, required=True, help="Date string in iso8601 format representing the start date of a simulation segment")
@click.option('--chunk-delta', type=str, required=True, help="Duration string in iso8601 format")
@click.option('--prefix', required=True, help="Prefix for environment variables.")
@click.option('--output-file', required=True, type=click.Path(), help="Path to the output shell file.")
@click.option('--calendar', default="noleap", help="Calendar system for cftime (e.g., 'gregorian', 'noleap', '360_day').")
def from_date(isostr, chunk_delta, prefix, output_file, calendar):
    import imsi.tools.time_manager.chunk_manager as cm

    restart_date, start_date, stop_date = cm.date_start_duration_to_cftime(isostr, chunk_delta, calendar)

    # Call the function to write the environment variables to a file
    cm.write_env_variables_to_file(restart_date, start_date, stop_date, prefix, output_file)
    click.echo(f"Environment variables written to {output_file}.")

@create_time_env_file.command(
    short_help="Create an environment file of the chunk's time data based on the loop index.",
    help="Create an environment file of the chunk's time data based on the loop index.",
    epilog="Primarily used for the maestro sequencer."
    )
@click.option('--start-time', required=True, type=str, help="Date string in iso8601 format representing the start date of a simulation segment")
@click.option('--stop-time', required=True, type=str, help="Date string in iso8601 format represent the stop date of a simulation segment")
@click.option('--chunk-size', required=True, type=str, help="Duration string in iso8601 format representing the size of a simulation segment")
@click.option('--loop-index', required=True, type=int, help="Integer value representing the index of a simulation segment")
@click.option('--prefix', required=True, help="Prefix for environment variables.")
@click.option('--output-file', required=True, type=click.Path(), help="Path to the output shell file.")
@click.option('--calendar', default="noleap", help="Calendar system for cftime (e.g., 'gregorian', 'noleap', '360_day').")
def from_index(start_time, stop_time, chunk_size, loop_index, prefix, output_file, calendar):
    import imsi.tools.time_manager.chunk_manager as cm

    restart_date, start_date, stop_date = cm.segment_chunk_size_to_cftime(start_time, stop_time, chunk_size, loop_index, calendar)

    # Call the function to write the environment variables to a file
    cm.write_env_variables_to_file(restart_date, start_date, stop_date, prefix, output_file)
    click.echo(f"Environment variables written to {output_file}.")

@chunk_manager.command()
@click.option('--chunk-file', required=True, type=click.Path(exists=True), help="Path to the chunks file.")
@click.option('--tracking-file', default="tracking.json", help="Path to the tracking file.")
@click.option('--timer-name', required=True, help="The name of the timer to track the chunking session.")
def is_first_chunk(chunk_file, tracking_file, timer_name):
    import imsi.tools.time_manager.chunk_manager as cm

    # boolean is cast to int
    click.echo(int(cm.check_if_first_chunk(timer_name, chunk_file, tracking_file)))
