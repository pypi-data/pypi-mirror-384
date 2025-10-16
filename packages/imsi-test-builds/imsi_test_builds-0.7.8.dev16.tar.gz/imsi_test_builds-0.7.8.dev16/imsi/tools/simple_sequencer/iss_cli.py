import click
import sys

from imsi.tools.simple_sequencer.iss_globals import (
    ALLOWED_JOB_STATUSES,
    JOB_STATUS_FILENAME_TEMPLATE,
    TIME_CHUNK_INDICES
)


def _input_check_timestr_fmt(ctx, param, value):
    import imsi.tools.simple_sequencer.iss as ssi
    pprint = ctx.params.get('print_all')  # for handling mutex args
    if pprint is None or pprint is False:
        if value is not None:
            try:
                ssi.to_unaware_datetime_str(value)
            except Exception as e:
                raise ValueError("input time string must be in format: YYYYmmDDHHMMSS or iso8601") from e
            return value
        else:
            return value
    else:
        return value


@click.group(short_help="Commands for imsi simple sequencer (ISS)",
             help="""Commands for imsi simple sequencer (ISS).

             ISS is a portable batch sequencing tool. Job scripts are generated
             based on IMSI configuration for jobs, and submitted sequentially
             to the system's scheduler. Its CLI commands are used within the job
             scripts themselves. The user may also use them for further
             development and debugging.
             """,
            context_settings={'show_default': True})
def iss():
    pass

@iss.command(help="Set the status of a job (a specific instance).",
             epilog="A job's status file is stored under the `tracking_dir` with the format: {}".format(JOB_STATUS_FILENAME_TEMPLATE))
@click.option('-j', '--job-name', required=True,
              help="Job name.")
@click.option('-t', '--status', required=True, type=click.Choice(list(ALLOWED_JOB_STATUSES.values()), case_sensitive=True),
              help="Job status (valid iss status option).")
@click.option('-s', '--start-time', required=True, callback=_input_check_timestr_fmt,
              help="Start time string (format: YYYYmmDDHHMMSS or iso8601).")
@click.option('-e', '--stop-time', required=True, callback=_input_check_timestr_fmt,
              help="Stop time string (format: YYYYmmDDHHMMSS or iso8601).")
@click.option('-o', '--tracking-dir', required=False, default=None, type=click.Path(),
              help="Path to tracking directory, ie. where status files are accessed (usually under the run's `/sequencer/listings`)")
def set_status(status, job_name, start_time, stop_time, tracking_dir):
    import imsi.tools.simple_sequencer.iss as ssi

    ssi.set_job_status(job_name, status, start_time, stop_time, tracking_dir)


@iss.command(short_help="Get the current status of a job (a specific instance).",
             help="Get the current status of a job (a specific instance).",
             epilog="A job's status file is stored under the `tracking_dir` with the format: {}".format(JOB_STATUS_FILENAME_TEMPLATE))
@click.option('-j', '--job-name', required=True,
              help="Job name.")
@click.option('-s', '--start-time', required=False, callback=_input_check_timestr_fmt,
              help="Start time string (format: YYYYmmDDHHMMSS or iso8601).")
@click.option('-e', '--stop-time', required=False, callback=_input_check_timestr_fmt,
              help="Start time string (format: YYYYmmDDHHMMSS or iso8601).")
@click.option('-o', '--tracking-dir', required=False, default=None, type=click.Path(),
              help="Path to tracking directory, ie. where status files are accessed (usually under the run's `/sequencer/listings`)")
@click.option('--print-all', is_flag=True,
              help="print all statuses for the job in the tracking dir provided")
def get_status(job_name, start_time, stop_time, tracking_dir, print_all):
    '''cli options and mutex (mutually exclusive) arguemnts handled here, within
    option callback, and option params (note required=False)'''

    import imsi.tools.simple_sequencer.iss as ssi

    mutex_args = {'start_time': start_time, 'stop_time': stop_time}  # w/ print_all
    if print_all:
        for k,v in mutex_args.items():
            if v is not None:
                click.echo(f"INFO: ignored --{k} {v}")
        click.echo(ssi.get_job_status_summary_message(job_name, tracking_dir=tracking_dir))
    else:
        # extra check for cleaner user message
        for k,v in mutex_args.items():
            if v is None:
                raise click.BadParameter(f"--{k} is required")
        click.echo(ssi.get_job_status(job_name, start_time, stop_time, tracking_dir=tracking_dir))

@iss.command(short_help="Get current timer information for the timer.",
             help="""Get current timer information for the timer.

             By default, this function returns all timer elements, where the
             element and it's value are separated by an equal sign (=), and
             multiple elements are separated by a single comma.
             """)
@click.option('-n', '--timer-name', required=True,
              help="Timer name.")
@click.option('-i', '--tracking-file', required=True, default=".simulation.time.state", type=click.Path(exists=True),
              help="Timer tracking file (state file).")
@click.option('--element', required=False, default=None, type=click.Choice(list(TIME_CHUNK_INDICES.keys())))
def get_timer_state(timer_name, tracking_file, element):
    import imsi.tools.time_manager.chunk_manager as cm

    timer_info = cm.get_current_chunk(tracking_file, timer_name)
    if element is None:
        click.echo(",".join(["{}={}".format(k, v) for k,v in timer_info.items()]))
    else:
        click.echo(timer_info[element])

@iss.command(short_help="Submit the job to the scheduler.",
             help="""Submit the job to the scheduler.

             iss internally uses the scheduler's submission command.
             """,
             epilog="The submit command will (naively) submit the job specified. It does not check for up/down stream dependencies or current job or timer state.")
@click.option('-j', '--job-name', required=True,
              help="Job name.")
@click.option('-c', '--cfg-file', required=True, default='.iss.json', type=click.Path(exists=True),
              help="The iss configuration file (json).")
def submit(job_name, cfg_file):
    import imsi.tools.simple_sequencer.iss as ssi

    sequencer = ssi.IMSISimpleSequencer.load_from_json(cfg_file)
    sequencer.run(job_name)

@iss.command(short_help="Determine if the job is ready to submit to the scheduler.",
             help="""Determine if the job is ready to submit to the scheduler.

             A job is deemed "ready to submit" when the job status and timer state
             are resolved and the dependency criteria are met. Further information
             are provided in the documentation.

             Returns:

                 0 : the job is NOT ready to submit.

                 1 : the job is ready to submit (state and dependency conditions are met).
             """
            )
@click.option('-j', '--job-name', required=True,
              help="Job name.")
@click.option('-c', '--cfg-file', required=True, default='.iss.json', type=click.Path(exists=True),
              help="The iss configuration file (json).")
def ready_to_submit(job_name, cfg_file):
    import imsi.tools.simple_sequencer.iss as ssi

    proceed = ssi.ready_to_submit(job_name, cfg_file)
    if proceed:
        click.echo(1)
    else:
        click.echo(0)

@iss.command(short_help="Return a list of dependent job names for the job specified.",
             help="""Return a list of dependent job names for the job specified.

             If there are dependent jobs for the (parent) job specified, the list of
             job names will be separated by a single space.
             """)
@click.option('-j', '--job-name', required=True,
              help="Job name (the parent).")
@click.option('-c', '--cfg-file', required=True, default='.iss.json', type=click.Path(exists=True),
              help="The iss configuration file (json).")
def get_job_dependents(job_name, cfg_file):
    import imsi.tools.simple_sequencer.iss as ssi

    sequencer = ssi.IMSISimpleSequencer.load_from_json(cfg_file)
    if job_name not in sequencer.flow.jobs:
        click.echo(f"job '{job_name}' not found in current configuration: {cfg_file}", err=True)
        sys.exit(1)
    if job_name in sequencer.flow.job_dependents:
        click.echo(' '.join([j.job_name for j in sequencer.flow.job_dependents[job_name]]))
    else:
        # the job doesnt have dependents - nothing to return
        sys.exit(0)

@iss.command(help="Get the timer name for the job specified.")
@click.option('-j', '--job-name', required=True,
              help="Job name.")
@click.option('-c', '--cfg-file', required=True, default='.iss.json', type=click.Path(exists=True),
              help="The iss configuration file (json).")
def get_timer_name(job_name, cfg_file):
    import imsi.tools.simple_sequencer.iss as ssi

    timer_name = ssi.get_timer_name(job_name, cfg_file)
    click.echo(timer_name)

@iss.command(help="Query information for argument specified.")
@click.argument('arg', type=click.Choice(['jobs', 'scheduler', 'submit']))
@click.option('-c', '--cfg-file', required=False, default='.iss.json', type=click.Path(exists=True, dir_okay=False),
              help="The iss configuration file (json).")
def which(arg, cfg_file):
    import imsi.tools.simple_sequencer.iss as ssi

    if arg == "jobs":
        click.echo(ssi.which_jobs(cfg_file))
    elif arg == "scheduler":
        click.echo(ssi.which_scheduler(cfg_file))
    elif arg == "submit":
        click.echo(ssi.which_submit(cfg_file))

if __name__ == "__main__":
    iss()
