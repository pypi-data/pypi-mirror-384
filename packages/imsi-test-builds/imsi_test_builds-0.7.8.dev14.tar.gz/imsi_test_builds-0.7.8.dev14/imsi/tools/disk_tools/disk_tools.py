import os
import glob
import getpass
from pathlib import Path
import shutil

from imsi.tools.ensemble.ensemble_manager import change_dir
from imsi.user_interface.ui_manager import load_run_config
from imsi.cli.core_cli import force_dirs


def get_path(starting_path, runid):
    '''Finds a specific path given a runid and starting location.
       Currently the depth is 2, so from a starting location checks all sub-locations up to depth 2.
       If 0 locations found it cannot find the runid from the starting path.
       If more than one location it can find at least 2 runids from the starting path.
    '''

    dir_list = [Path(p) for p in glob.glob(f"{starting_path}/*/{runid}")] + [Path(p) for p in glob.glob(f"{starting_path}/{runid}")]
    if len(dir_list) == 0:
        raise FileNotFoundError(f"Could not find a folder {runid} from starting location {starting_path}")
    elif len(dir_list) > 1:
        raise Exception(f"Found more than one folder {runid} from starting location {starting_path}")
    return dir_list[0]

def delete_location(starting_path, runid):
    '''Deletes the runid from the starting location either in "storage_dir" or "scratch_dir"'''
    try:
        runid_dir = get_path(starting_path, runid)
        shutil.rmtree(runid_dir)
        print(f"Cleaned space {runid_dir}")
    except FileNotFoundError:
        print(f"No runid could be found at {starting_path}")

def clean_run(runid_path, setup, temp, data):
    '''Cleans disk space for a run'''

    runid_path = Path(runid_path).resolve()
    # Check to see if WRK_DIR is set. If it is, make sure the path is the same as runid_path
    # If they are not the same we bail to prevent edge cases where you can accidentally clean 
    # the wrong run
    if Path(os.getenv("WRK_DIR", runid_path)).resolve() != runid_path.resolve():
        raise ValueError(
            "Your 'WRK_DIR' is currently set to a location that differs from the runid_path you used. "
            "Please make sure to unset 'WRK_DIR' before using imsi clean."
        )

    runid = runid_path.name

    # use change_dir in ensemble to change directory then change back when finished.
    with change_dir(runid_path):
        force_dirs(Path(f".imsi/.imsi_configuration_{runid}.pickle"))
        config = load_run_config(serialized=True)

    # Make an assumption that the run is being cleaned by the user who created the run.
    user_id = getpass.getuser()

    # deletes the information in the temp space
    if temp:
        temp_dir = config.machine.scratch_dir.replace('${USER}', user_id)
        delete_location(temp_dir, runid)

    # deletes the data from the run
    if data:
        data_dir = config.machine.storage_dir.replace('${USER}', user_id)
        delete_location(data_dir, runid)

    # deletes the setup directory. 
    if setup:
        shutil.rmtree(runid_path)
        print(f"Cleaned space {Path(runid_path).resolve()}")

