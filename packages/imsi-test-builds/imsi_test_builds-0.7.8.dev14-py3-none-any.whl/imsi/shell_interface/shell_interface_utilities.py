'''
General utility functions for creating the "shell interface" (config directory) and associated files.
'''
from typing import List
import os
import shutil

from imsi.utils.git_tools import init_repo, clear_repo
from imsi.utils.general import delete_or_abort, yes_or_no

def create_config_dirs(run_config_path: str, components: List[str], track=True, force=False):
    """Create the run config dir and subdirectories for each component."""

    if os.path.exists(run_config_path):
        if force:
            print(f"**WARNING**: config dir exists, overwriting at {run_config_path}")
        else:
            yes_or_no(f'{run_config_path} already exists, do you want to replace it?')

        if track:
            clear_repo(run_config_path)
        else:
            shutil.rmtree(run_config_path)

    os.makedirs(run_config_path, exist_ok=True)
    for component in components:
        os.makedirs(os.path.join(run_config_path, component), exist_ok=True)

    if track:
        branch = os.path.basename(os.path.dirname(run_config_path))  # convention
        init_repo(path=run_config_path, branch=branch)


if __name__ == "__main__":
    # Only for original dev testing. See shell_interface_manager for more up to date tests.
    pass
