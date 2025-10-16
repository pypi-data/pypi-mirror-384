
ALLOWED_JOB_STATUSES = {
    'queued': 'QUEUED',
    'running': 'RUNNING',
    'success': 'COMPLETED',
    'fail': 'FAILED'
}
ACTIVE_JOB_STATUSES = [
    ALLOWED_JOB_STATUSES['queued'],
    ALLOWED_JOB_STATUSES['running']
]

UNAWARE_DATETIME_FORMAT = "%Y%m%d%H%M%S"
UNAWARE_DATETIME_PATTERN = (
    r"(^\d{4})([0-2][0-9])([0-3][0-9])([0-2][0-9])([0-5][0-9])([0-5][0-9])"
)

JOB_STATUS_FILENAME_TEMPLATE = '{job_name}_{start_time}_{stop_time}.status'

SCRIPT_INTERPRETER_DIRECTIVE = "#!/bin/bash"
SCRIPT_COMMENT_CHAR = "#"

SCRIPT_HEADER_TEMPLATE = """
{interpreter}
set -e

# Imsi created shell environment file
# {tool_title} created on date: {date_string}
{header_comments}
{methods}

"""

SCRIPT_IMSI_ENV_COMMAND = """
# method to invoke imsi environment:
with_venv() {
    local venv_path="$1"
    shift
    ( source "$venv_path/bin/activate" && "$@" )
}
"""
# note that the body this is a raw literal string (prefix r) so that
# escapes on slashes are not needed; and it can still be used with
# f-formatted literal string
SCRIPT_BODY_TEMPLATE = r"""
job_name={job_name}
timer_name={timer_name}
timer_tracking_file={timer_tracking_file}
sequencing_dates_file={sequencing_dates_file}
sequencing_dir={sequencing_dir}
listings_dir={listings_dir}
submit_next={submit_next_bool}
submit_dependents={submit_dependents_bool}
iss_cfg={iss_config_file}
clean_scratch={clean_scratch_bool}

# source required input information regarding env vars, settings and timers.
source {run_config_dir}/computational_environment
source {run_config_dir}/shell_parameters

# Create a scratch directory
IMSI_SCRATCH={sequencing_scratch_dir}/{runid}/{runid}_scratch_{job_name}_${{{timer_name}}}_$$
mkdir -p $IMSI_SCRATCH
cd $IMSI_SCRATCH

# Parse timers for this job, and set appropriate shell variables
with_venv "$IMSI_VENV" imsi chunk-manager create-time-env-file from-tracking-file --timer-name $timer_name --tracking-file $timer_tracking_file --output-file {run_config_dir}/job_env_dates_$timer_name --prefix 'job'
source {run_config_dir}/job_env_dates_$timer_name

# Update job status
with_venv "$IMSI_VENV" imsi iss set-status -t RUNNING -j $job_name -s "$job_start_date" -e "$job_stop_date" -o "$listings_dir"

# User defined scripting
return_status=0
source {user_script} || return_status=$?

# check for errors and set status
if (( return_status == 0 )); then
    with_venv "$IMSI_VENV" imsi iss set-status -t COMPLETED -j $job_name -s "$job_start_date" -e "$job_stop_date" -o "$listings_dir"
else
    with_venv "$IMSI_VENV" imsi iss set-status -t FAILED -j $job_name -s "$job_start_date" -e "$job_stop_date" -o "$listings_dir"
    exit 1
fi

#
# wrap
#
cd {work_dir}
if $clean_scratch; then
    rm -rf $IMSI_SCRATCH
fi

#
# job cycling
#

# dependents
if [[ "$submit_dependents" = true ]]; then
    dependent_jobs=$( with_venv "$IMSI_VENV" imsi iss get-job-dependents -j $job_name -c $iss_cfg )
    for dep_job in $dependent_jobs; do
        dep_is_ready=$( with_venv "$IMSI_VENV" imsi iss ready-to-submit -j $dep_job -c $iss_cfg )
        if (( dep_is_ready == 1 )); then

            # get timer info
            d_tn=$( with_venv "$IMSI_VENV" imsi iss get-timer-name -j $dep_job -c $iss_cfg )
            d_st=$( with_venv "$IMSI_VENV" imsi iss get-timer-state -n $d_tn -i $timer_tracking_file --element START )
            d_et=$( with_venv "$IMSI_VENV" imsi iss get-timer-state -n $d_tn -i $timer_tracking_file --element END )

            # submit and update status
            with_venv "$IMSI_VENV" imsi iss submit -j $dep_job -c $iss_cfg
            with_venv "$IMSI_VENV" imsi iss set-status -t QUEUED -j $dep_job -s "$d_st" -e "$d_et" -o "$listings_dir"

        fi
    done
fi

# next iteration

# increment the timer
with_venv "$IMSI_VENV" imsi chunk-manager increment --timer-name $timer_name --tracking-file $timer_tracking_file --chunk-file $sequencing_dates_file

if [[ "$submit_next" = true ]]; then
    job_is_ready=$( with_venv "$IMSI_VENV" imsi iss ready-to-submit -j $job_name -c $iss_cfg )
    if (( job_is_ready == 1 )); then

        # get timer info
        st=$( with_venv "$IMSI_VENV" imsi iss get-timer-state -n $timer_name -i $timer_tracking_file --element START )
        et=$( with_venv "$IMSI_VENV" imsi iss get-timer-state -n $timer_name -i $timer_tracking_file --element END )

        # submit and update status
        with_venv "$IMSI_VENV" imsi iss submit -j $job_name -c $iss_cfg
        with_venv "$IMSI_VENV" imsi iss set-status -t QUEUED -j $job_name -s "$st" -e "$et" -o "$listings_dir"

    fi
fi

"""

SCRIPT_FOOTER = """
"""

# NOTE: adding these here from chunk_manager.py because they were not
# actually used in time_manager...
# these are the indices of the "columns" in a sequencing dates file.
# these are defined so that we can easily map between the date file
# and a timer file (which has a dict/json structure with key,value pairs).
# TODO: this may be changed to a class or better named data structure.
TIME_CHUNK_INDICES = {'RESTART': 0, 'START': 1, 'END': 2}
