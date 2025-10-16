# This module has been set as an imsi entry point, and is used by SSS
# However, it also contains functionality that replaces the set_env_vars functions in shell_functions
# and overlaps / builds from the old cylc get-time-vars.
#
# What should be done is to split apart the part of this that is SSS specific, and put that in
# SSS, which should be made it own stand alone tool within imsi
#
# The, the part that is more generally useful (write_env_variables_to_file), should be made
# its own tool, and add to as needed to replace the shell_functions currently used.
# Part of the expansion / refactor of this and time_manager, should be to use these tools
# to do the setting etc of both the internal loop (replace shell loops / searches) and
# the external loop setting in both maestro and cylc.
import click
import csv
import json
import sys
from imsi.tools.time_manager.cftime_utils import _parse_iso8601_with_reso, get_date_type
from imsi.tools.time_manager.time_manager import SimDuration, SimTimer
from datetime import timedelta

"""
Module for managing chunk progression based on tracking and chunk files.

This module provides functionality to read time chunk definitions from a CSV file,
track the current position of a timer in a JSON tracking file, and manage
incrementing through defined time chunks. It can also produce an file containing "standard"
CCCma timer variables, that can be sourced in the shell.

It includes a command-line interface
(CLI) for easy interaction.
"""

def read_chunks(file_path):
    """Read the chunk file and return the chunks as a list of lists.

    Each chunk is represented by [RESTART, START, END], where these values are
    timestamps in a string format.

    Parameters:
    - file_path (str): Path to the CSV file containing the time chunks.

    Returns:
    - chunks (list): A list of lists, each representing a time chunk.
    """
    try:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            chunks = [row for row in reader]
        return chunks
    except FileNotFoundError:
        click.echo(f"Error: The file {file_path} does not exist.", err=True)
        sys.exit(1)

def load_tracking_data(tracking_file):
    """Load the tracking data from the JSON tracking file.

    Parameters:
    - tracking_file (str): Path to the tracking file.

    Returns:
    - data (dict): The tracking data as a dictionary. Will raise:
       - FileNotFoundError if file does not exist
       - json.JSONDecodeError if file is mangled
    """
    try:
        with open(tracking_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise e
    except json.JSONDecodeError as e:
        raise e

def get_tracking_data(tracking_file):
    """Get the tracking data from the JSON tracking file.

    Parameters:
    - tracking_file (str): Path to the tracking file.

    Returns:
    - data (dict): The tracking data as a dictionary. If no file exists,
    return an empty dict.
    """
    try:
        return load_tracking_data(tracking_file)
    except FileNotFoundError:
        return {}

def save_tracking_data(tracking_file, data):
    """Save the tracking data to the JSON tracking file.

    Parameters:
    - tracking_file (str): Path to the tracking file.
    - data (dict): Dictionary to save in the tracking file.
    """
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=4)

def get_current_chunk(tracking_file, timer_name):
    """Get the current tracked chunk for the specified timer from the tracking file.

    Parameters:
    - tracking_file (str): Path to the tracking file.
    - timer_name (str): The name of the timer for which the current chunk is being tracked.

    Returns:
    - current_chunk (dict): The current chunk as a dictionary (RESTART, START, END), or None if not found.
    """
    data = load_tracking_data(tracking_file)
    return data.get(timer_name)

def set_current_chunk(tracking_file, timer_name, restart, start, end):
    """Write the full chunk (RESTART, START, END) to the tracking file under the specified timer_name.

    Parameters:
    - tracking_file (str): Path to the tracking file.
    - timer_name (str): The name of the timer to track the chunk for.
    - restart (str): The RESTART time of the chunk.
    - start (str): The START time of the chunk.
    - end (str): The END time of the chunk.
    """
    data = get_tracking_data(tracking_file)
    data[timer_name] = {
        "RESTART": restart,
        "START": start,
        "END": end
    }
    save_tracking_data(tracking_file, data)

def get_chunk_by_start(chunks, start_time):
    """Find a chunk by its START time.

    Parameters:
    - chunks (list): List of time chunks.
    - start_time (str): The START time to search for.

    Returns:
    - chunk (list): The found chunk, or None if not found.
    - index (int): The index of the found chunk, or -1 if not found.
    """
    for idx, chunk in enumerate(chunks):
        if chunk[1] == start_time:
            return chunk, idx
    return None, -1

def increment_chunk_logic(chunk_file, tracking_file, timer_name):
    """
    Move to the next time chunk for a given timer and update the tracking file.

    This function locates the current chunk for the specified timer, increments
    to the next chunk in the sequence, and updates the tracking file accordingly.

    Outputs status codes for shell usage:
    - 0: success (the chunk was incremented)
    - 1: end_of_chunks (no more chunks available)
    - 2: initialized_first_chunk (first chunk being tracked)

    Parameters:
    - chunk_file (str): Path to the file containing the list of available time chunks.
    - tracking_file (str): Path to the tracking file where the current chunk status is stored.
    - timer_name (str): The name of the timer to track the chunks for.
    """
    chunks = read_chunks(chunk_file)
    current_chunk = get_current_chunk(tracking_file, timer_name)

    if current_chunk:
        # Find the index of the current chunk
        current_start = current_chunk["START"]
        _, current_idx = get_chunk_by_start(chunks, current_start)

        # Get the next chunk if available
        next_idx = current_idx + 1
        if next_idx < len(chunks):
            next_chunk = chunks[next_idx]
            set_current_chunk(tracking_file, timer_name, next_chunk[0], next_chunk[1], next_chunk[2])
            return "0"  # success
        else:
            return "1"  # end_of_chunks
    else:
        # Default to the first chunk if no tracking data exists
        first_chunk = chunks[0]
        set_current_chunk(tracking_file, timer_name, first_chunk[0], first_chunk[1], first_chunk[2])
        return "2"  # initialized_first_chunk


def init_tracking_file(chunk_file, tracking_file, timer_name, overwrite_timer=False):
    """
    Initialize the tracking file with the first chunk for a specified timer.

    Parameters:
    - chunk_file (str): Path to the CSV file containing the time chunks.
    - tracking_file (str): Path to the tracking file where the current chunk status is stored.
    - timer_name (str): The name of the timer to track.

    If the timer_name already exists in the tracking file, no changes will be made.
    """
    chunks = read_chunks(chunk_file)
    first_chunk = chunks[0]

    # Load existing tracking data
    data = get_tracking_data(tracking_file)

    # Only add if the timer does not already exist or overwrite is on (True)
    if (timer_name not in data) or overwrite_timer:
        data[timer_name] = {
            "RESTART": first_chunk[0],
            "START": first_chunk[1],
            "END": first_chunk[2]
        }
        save_tracking_data(tracking_file, data)
    else:
        print(f"Timer '{timer_name}' is already initialized.")

def parse_cftime(date_string, calendar):
        """Parse ISO 8601 date string into a cftime object."""
        parsed, _ = _parse_iso8601_with_reso(get_date_type(calendar), date_string)
        return parsed

def segment_chunk_size_to_cftime(start_date_str, stop_date_str, chunk_size, loop_index, calendar):
    """
    Calculate current dates from segment dates, chunk size, and loop index.
    Return in cftime object format.

    :param start_date_str: Date string in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
    :param stop_dat_str: Date string in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
    :param chunk_size: Duration string in format PnYnMnDTnHnMnS (ISO 8601)
    :param loop_index: Integer index of the desired chunk
    :param calendar: Calendar system for cftime (e.g., "gregorian", "noleap", "360_day")
    """

    sim_timer = SimTimer.from_iso('job', start_date_str, stop_date_str, chunk_size,
                      'job', 'job', calendar=calendar)
    current_start_date = sim_timer.ChunkIndexStart[loop_index-1]
    current_stop_date = sim_timer.ChunkIndexStop[loop_index-1]
    current_restart_date = current_start_date - timedelta(seconds=1)

    return current_restart_date, current_start_date, current_stop_date

def date_strings_to_cftime(restart_date_str, start_date_str, stop_date_str, calendar="gregorian"):
    """
    Take current time strings and convert to cftime objects.

    The restart, start, and stop dates are expected in ISO 8601 format but are processed using `cftime`
    to handle a wide range of calendar systems.

    :param restart_date_str: Date string in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
    :param start_date_str: Date string in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
    :param stop_date_str: Date string in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
    :param calendar: Calendar system for cftime (e.g., "gregorian", "noleap", "360_day")
    """

    start_date_cftime = parse_cftime(start_date_str, calendar)
    stop_date_cftime = parse_cftime(stop_date_str, calendar)
    restart_date_cftime = parse_cftime(restart_date_str, calendar)

    return restart_date_cftime, start_date_cftime, stop_date_cftime

def date_start_duration_to_cftime(start_date_str, duration_str, calendar="gregorian"):
    """
    Take start time and duration strings and convert to cftime objects.

    The date and duration are expected in ISO 8601 format but are processed using `cftime`
    to handle a wide range of calendar systems.

    :param start_date_str: Date string in format YYYY-MM-DDTHH:MM:SS (ISO 8601)
    :param duration_str: Duration string in format PnYnMnDTnHnMnS (ISO 8601)
    :param calendar: Calendar system for cftime (e.g., "gregorian", "noleap", "360_day")
    """

    start_date_cftime, reso = _parse_iso8601_with_reso(get_date_type(calendar), start_date_str)
    duration = SimDuration(duration_str)

    stop_date_cftime = start_date_cftime + duration.duration - timedelta(seconds=1)
    restart_date_cftime = start_date_cftime - timedelta(seconds=1)

    return restart_date_cftime, start_date_cftime, stop_date_cftime

def check_if_first_chunk(timer_name, chunk_file, tracking_file):
    # compare time in timer tracking file with FIRST entry of list in
    # chunk file for the given timer

    # chunk file:
    chunk_times = read_chunks(chunk_file)
    first_chunk_times = chunk_times[0]

    # timer tracking file:
    current_timer = get_current_chunk(tracking_file, timer_name)

    is_first_chunk = list(current_timer.values()) == first_chunk_times
    return is_first_chunk

def write_env_variables_to_file(restart_date, start_date, stop_date, prefix, output_file):
    """
    Write environment variables based on restart, start, and stop dates into a shell script.
    These variables can be sourced in a shell session.
    The restart, start, and stop dates are expected in ISO 8601 format but are processed using `cftime`
    to handle a wide range of calendar systems.

    :param restart_date: Date as a cftime object
    :param start_date: Date as a cftime object
    :param stop_date: Date as a cftime object
    :param prefix: String prefix for environment variables
    :param output_file: Path to output shell file
    :param calendar: Calendar system for cftime (e.g., "gregorian", "noleap", "360_day")
    """

    def extract_cftime_fields(cftime_obj):
        """Extract year, month, day, and hour fields from a cftime object."""
        return {
            "year": cftime_obj.year,
            "month": cftime_obj.month,
            "day": cftime_obj.day,
            "hour": cftime_obj.hour,
            "YYYY": f"{cftime_obj.year:04d}",
            "MM": f"{cftime_obj.month:02d}",
            "DD": f"{cftime_obj.day:02d}",
            "HH": f"{cftime_obj.hour:02d}"
        }

    # Parse the restart, start, and stop dates using cftime
    restart_info = extract_cftime_fields(restart_date)
    start_info = extract_cftime_fields(start_date)
    stop_info = extract_cftime_fields(stop_date)

    # Create a list to hold all the environment variable strings
    env_vars = [
        f'export {prefix}_restart_date="{restart_date.isoformat()}"',
        f"export {prefix}_restart_year={restart_info['year']}",
        f"export {prefix}_restart_month={restart_info['month']}",
        f"export {prefix}_restart_day={restart_info['day']}",
        f"export {prefix}_restart_hour={restart_info['hour']}",
        f"export {prefix}_restart_YYYY={restart_info['YYYY']}",
        f"export {prefix}_restart_MM={restart_info['MM']}",
        f"export {prefix}_restart_DD={restart_info['DD']}",
        f"export {prefix}_restart_HH={restart_info['HH']}",

        f'export {prefix}_start_date="{start_date.isoformat()}"',
        f"export {prefix}_start_year={start_info['year']}",
        f"export {prefix}_start_month={start_info['month']}",
        f"export {prefix}_start_day={start_info['day']}",
        f"export {prefix}_start_hour={start_info['hour']}",
        f"export {prefix}_start_YYYY={start_info['YYYY']}",
        f"export {prefix}_start_MM={start_info['MM']}",
        f"export {prefix}_start_DD={start_info['DD']}",
        f"export {prefix}_start_HH={start_info['HH']}",

        f'export {prefix}_stop_date="{stop_date.isoformat()}"',
        f"export {prefix}_stop_year={stop_info['year']}",
        f"export {prefix}_stop_month={stop_info['month']}",
        f"export {prefix}_stop_day={stop_info['day']}",
        f"export {prefix}_stop_hour={stop_info['hour']}",
        f"export {prefix}_stop_YYYY={stop_info['YYYY']}",
        f"export {prefix}_stop_MM={stop_info['MM']}",
        f"export {prefix}_stop_DD={stop_info['DD']}",
        f"export {prefix}_stop_HH={stop_info['HH']}"
    ]

    # Write all the environment variables to the file in one go
    with open(output_file, "w") as f:
        f.write("\n".join(env_vars) + "\n")
