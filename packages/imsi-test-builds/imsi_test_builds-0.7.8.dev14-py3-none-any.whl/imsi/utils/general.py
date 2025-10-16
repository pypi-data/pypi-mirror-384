from datetime import datetime
import os
import re
from typing import List
from pathlib import Path
import shutil
import stat
import sys
from pathlib import Path

def is_path(var : str) -> bool:
    """
    Determines if the given string represents a path or a base filename.

    Args:
        var (str): The string to check, which may be a base filename or a path.

    Returns:
        bool: True if `var` includes a directory component, indicating it's a path;
              False if it's only a base filename.

    Example:
        is_path("woo")     => False
        is_path("boo/woo") => True
    """
    pth = Path(var)
    return pth.parent != Path(".") # '.' is returned if there is no path component

def write_shell_string(file_path: str, script_content: str, mode="w", make_executable=False):
    """Write string to shell script preserving newlines"""
    with open(file_path, mode) as f:
        f.write(script_content)
    if make_executable:
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)

def get_active_venv():
    # Check if the VIRTUAL_ENV environment variable is set
    venv_path = os.getenv('VIRTUAL_ENV')

    if venv_path:
        return venv_path
    else:
        # Fallback: Check if sys.prefix is not the same as sys.base_prefix (which indicates a venv is active)
        if sys.prefix != sys.base_prefix:
            return sys.prefix
        else:
            return None

def write_shell_script(file_path: str, script_content: List[str], mode='w', make_executable=False):
    """Write shell script content to a file."""
    with open(file_path, mode) as f:
        f.write('\n'.join(script_content))
    if make_executable:
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)

def get_date_string():
    """Return a datestring of now time"""

    now = datetime.now() # current date and time
    return now.strftime("%Y-%m-%d %H:%M")

def delete_or_abort(path):
    """Asks a user for input to abort or delete and replace an existing directory.
    """
    choice = input(f'{path} already exists: Abort (a) or replace (r)?')
    if choice == "a":
        print( "Exiting")
        exit()
    elif choice == "r":
        print(f"Deleting {path}")
        shutil.rmtree(path)
    else:
        print("Invalid input! Choices are 'a' or 'r'")
        delete_or_abort(path)


def yes_or_no(question, compact=True):
    """Prompts a user if they want to proceed (y) or not (n) given the prompt
    (the question).
    """
    _options = {'n': 'no', 'y': 'yes'}
    if compact:
        option_string = '[{}]'.format('/'.join(_options))
    else:
        option_string = ' '.join([f'{v} ({k})' for k,v in _options.items()])
    choice = input(f'{question}: {option_string} ')
    if choice == "n":
        print( "Exiting")
        exit()
    elif choice == "y":
        pass
    else:
        option_keys = ', '.join([f"'{k}'" for k in _options.keys()])
        print(f"Invalid input! Choices are: {option_keys}")
        yes_or_no(question)


def _get_memory_unit_factors_to_bytes(base=2):
    # conversion factors for memory unit to bytes
    if base == 2:
        return {'K': 1 << 10, 'M': 1 << 20, 'G': 1 << 30}
    elif base == 10:
        return {'K': 1e3, 'M': 1e6, 'G': 1e9}
    else:
        raise ValueError('base must be 2 or 10')

def parse_memory_string_to_bytes(memory : str, base=2):
    """Parses a string that specifies memory value and unit and
    returns the value in bytes.

    Parameters
        memory : a string composed of the value and units, where units
            are denoted as KB, MB, or GB (case insensitive, with or
            without trailing 'b'). Space is permitted between the value
            and units.
        base : either 2 or 10, denoting the conversion from the input
            units to bytes. Use with caution. Default 2.

    Returns
        value of the information in bytes

    Example
    >>> parse_memory_string_to_bytes("1 kb")
    1024
    >>> parse_memory_string_to_bytes("10GB")
    10737418240
    """
    unit_map = _get_memory_unit_factors_to_bytes(base)
    M = memory.upper()
    valid = re.search(r"([0-9]+)\s?([KMG]B?\b)", M)
    if valid is None:
        raise ValueError(f"unsupported memory format for '{memory}'; units must be one of {{K, G, M, KB, GB, MB}} (case insensitive)")
    value = int(valid.group(1))
    units = valid.group(2).rstrip('B')
    nbytes = int(value * unit_map[units])
    return nbytes
