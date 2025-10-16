from imsi.cli.entry import cli
import shutil
# import pytest
from pathlib import Path
from click.testing import CliRunner
import os
import subprocess
from imsi.tools.time_manager.time_manager import sim_time_factory
from imsi.shell_interface.shell_timing_vars import generate_timers_config
from imsi.utils.general import write_shell_script

#WIP: testing ground for time-manager and chunk-manager routines
#Need to implement testing protocol (pytest?)
#and test a number of configurations.
#Also, diff output files and cleanup afterwards.

# Outputs a bunch of timer lists nested in the timer_dates directory
# Demonstrates some of the capability of the current time manager

output_path = Path('timer_dates')
output_path.mkdir(exist_ok=True)

config_list = [
                {"name": "12MS-12MS-Jan1", "run_segment_start_time": "6000-01-01T00:00:00",  "model_chunk_size": "P12MS", "model_internal_chunk_size": "P12MS"},
                {"name": "1MS-1MS-Jan1", "run_segment_start_time": "6000-01-01T00:00:00", "model_chunk_size": "P1MS", "model_internal_chunk_size": "P1MS"},
                {"name": "12M-12M-Jan15", "run_segment_start_time": "6000-01-15T00:00:00", "model_chunk_size": "P12M", "model_internal_chunk_size": "P12M"},
                {"name": "1M-1M-Jan15", "run_segment_start_time": "6000-01-15T00:00:00", "model_chunk_size": "P1M", "model_internal_chunk_size": "P1M"},
                {"name": "12MS-12MS-Jan15", "run_segment_start_time": "6000-01-15T00:00:00",  "model_chunk_size": "P12MS", "model_internal_chunk_size": "P12MS"},
                {"name": "1MS-1MS-Jan15", "run_segment_start_time": "6000-01-15T00:00:00", "model_chunk_size": "P1MS", "model_internal_chunk_size": "P1MS"},
                {"name": "12MS-1MS-Jan1", "run_segment_start_time": "6000-01-01T00:00:00",  "model_chunk_size": "P12MS", "model_internal_chunk_size": "P1MS"},
                {"name": "12MS-1DS-Jan1", "run_segment_start_time": "6000-01-01T00:00:00",  "model_chunk_size": "P12MS", "model_internal_chunk_size": "P1DS"},
                {"name": "1DS-1DS-Jan1-12pm", "run_segment_start_time": "6000-01-01T12:00:00",  "model_chunk_size": "P1DS", "model_internal_chunk_size": "P1DS"},
                {"name": "1D-1D-Jan1-12pm", "run_segment_start_time": "6000-01-01T12:00:00",  "model_chunk_size": "P1D", "model_internal_chunk_size": "P1D"},
              ]

# Test settings
run_dates = {
        "run_start_time": "6000-01-01T00:00:00",
        "run_stop_time": "6010-12-31T23:59:59",
        "run_segment_start_time": "6000-01-01T00:00:00",
        "run_segment_stop_time": "6010-12-31T23:59:59",
        "model_chunk_size": "P1MS",
        "model_internal_chunk_size": "P12MS",
        "postproc_chunk_size": "P12MS"
}

for config in config_list:

    run_dates.update(config)

    #First output the dates file using the time manager.
    #This file is still in use by ISS/SSS though will
    #not be used anymore by Maestro. We need to do some
    #more careful work to see if we can remove the need
    #for dates files in ISS/SSS
    run_config_path = output_path / config["name"]
    run_config_path.mkdir(exist_ok=True)

    dates_list = run_config_path / 'model_submission_job_start-stop_dates'
    if dates_list.exists():
        dates_list.unlink()
    write_shell_script(os.path.join(str(run_config_path), 'model_submission_job_start-stop_dates'),
                    generate_timers_config(run_dates, 'model_submission_job'))

    dates_list = run_config_path / 'model_inner_loop_start-stop_dates'
    if dates_list.exists():
        dates_list.unlink()
    write_shell_script(os.path.join(str(run_config_path), 'model_inner_loop_start-stop_dates'),
                    generate_timers_config(run_dates, 'model_inner_loop'))


