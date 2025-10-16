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

#At present, this will run each of the three chunk manager methods:
# loop index, tracker file, and iso8601 date
# for a two year segment.
# The index method and tracker method below
# attempt to run a third (out of bounds) year and we see the result:
# index method will raise an error
# tracker method will duplicate the timers for 2nd year

# Test settings
run_dates = {
        "run_start_time": "6000-01-01T00:00:00",
        "run_stop_time": "6010-12-31T23:59:59",
        "run_segment_start_time": "6000-01-01T00:00:00",
        "run_segment_stop_time": "6001-12-31T23:59:59",
        "model_chunk_size": "P12MS",
        "model_internal_chunk_size": "P12MS",
        "postproc_chunk_size": "P12MS"
}
prefix = "job"
output_file = "job_time_params"

output_path = Path('chunk_manager_2yr_test')
output_path.mkdir(exist_ok=True)

#First output the dates file using the time manager.
#This file is still in use by ISS/SSS though will
#not be used anymore by Maestro. We need to do some
#more careful work to see if we can remove the need
#for dates files in ISS/SSS
run_config_path = output_path / 'dates_files'
run_config_path.mkdir(exist_ok=True)
dates_list = run_config_path / 'model_submission_job_start-stop_dates'
if dates_list.exists():
    dates_list.unlink()
write_shell_script(os.path.join(str(run_config_path), 'model_submission_job_start-stop_dates'),
                  generate_timers_config(run_dates, 'model_submission_job'))

###################################### index method
#test loop index method (maestro and model inner loop)
#put in nested directory
new_dir = output_path / "chunk_index_method"
new_dir.mkdir(exist_ok=True)

for loop_index in range(1,4):
    cmd = f"imsi chunk-manager create-time-env-file from-index --start-time={run_dates['run_segment_start_time']} " + \
        f"--stop-time={run_dates['run_segment_stop_time']} --chunk-size={run_dates['model_chunk_size']} " + \
        f"--loop-index={loop_index} --prefix={prefix} --output-file={str(new_dir)}/{output_file}_loop_{loop_index}"
    proc = subprocess.run(cmd, shell=True)

###################################### tracker method
#test tracker file routines (iss/sss)
new_dir = output_path / "chunk_tracker_method"
new_dir.mkdir(exist_ok=True)

# test init for creation of tracker file
chunk_file = Path(run_config_path) / 'model_submission_job_start-stop_dates'
tracker = new_dir / '.simulation.time.state'
if tracker.exists():
    tracker.unlink()
timer = 'model-submission'
cmd = f"imsi chunk-manager init --chunk-file={str(chunk_file)} --tracking-file={str(tracker)} --timer-name={timer}"
proc = subprocess.run(cmd, shell=True)

for loop_index in range(1,4):
    cmd = f"imsi chunk-manager create-time-env-file from-tracking-file --tracking-file={tracker} " + \
        f"--timer-name={timer} --prefix={prefix} --output-file={str(new_dir)}/{output_file}_loop_{loop_index}"
    proc = subprocess.run(cmd, shell=True)

    #increment to the next timer
    cmd = f"imsi chunk-manager increment --chunk-file={str(chunk_file)} --tracking-file={tracker} --timer-name={timer}"
    proc = subprocess.run(cmd, shell=True)


###################################### isodate method
#test isodate method (cylc)
new_dir = output_path / "chunk_iso8601_method"
new_dir.mkdir(exist_ok=True)

simTime =  sim_time_factory(run_dates, 'model_submission_job')

loop_index = 1
for chunk in simTime.ChunkIndexStart:
    cmd = f"imsi chunk-manager create-time-env-file from-date --isostr={chunk.isoformat()} --chunk-delta={simTime.chunk_size_str} " + \
          f"--prefix={prefix} --output-file={str(new_dir)}/{output_file}_loop_{loop_index}"
    proc = subprocess.run(cmd, shell=True)
    loop_index += 1