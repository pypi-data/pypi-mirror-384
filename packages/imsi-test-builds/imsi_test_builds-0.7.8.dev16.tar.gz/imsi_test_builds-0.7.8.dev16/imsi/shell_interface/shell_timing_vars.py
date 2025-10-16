from imsi.tools.time_manager.time_manager import sim_time_factory
from datetime import timedelta


def generate_timers_config(run_dates: dict, timer_name: str) -> dict:
    """Generate lists of timer variables for various jobs, to be written out and used
    downstream. Specifically returns start and stop lists for the model outer loop (job submission),
    model internal loop (within jobs), and the postproc loop.


    Parameters:
        run_dates (dict ) : A dict of run dates, in iso8061 format, with keys
                            [run_, run_segment]_[start,stop]_date, and keys
                            for model_chunk_size, model_internal_chunk_size
                            and postproc_chunk_size.
        timer_name (str) : The prefix of the job timer name (e.g. model_submission_job)

        Return:
         timer_lists (dict): key=timer_name and value=list of start -- stop times
    """
    # There are two big issues here to be resolved
    # 1. There is repetition of creating SimulationTime instance, with shell_config_parameters
    # 2. This occurs because this should be set upstream in config_manager, but how precisely to
    # populate templates has not really been properly figured out yet.

    # The details of these timers might need to change (e.g. for different sequencers or even flows),
    # and others could easily be added by referring to the time_manager "_generate_job_start_end_date_lists"
    # function. In fact, those calls might really belong here.

    # Use the time_manager module to get detailed timers for insertion into shell_parameters
    simTime = sim_time_factory(run_dates, timer_name)
    cftime_start_list = getattr(simTime, 'ChunkIndexStart')
    cftime_stop_list = getattr(simTime, 'ChunkIndexStop')
    if not (cftime_start_list and cftime_stop_list):
        raise ValueError(f"The timer name: {timer_name} did not return any content.")
    timeliststr = []
    for (start_time, stop_time) in zip(cftime_start_list, cftime_stop_list):
        restart_time = start_time - timedelta(seconds=1)
        timeliststr.append(f"{restart_time.isoformat(timespec='seconds')},{start_time.isoformat(timespec='seconds')},{stop_time.isoformat(timespec='seconds')}")
    return timeliststr


def validate_timers_config(run_dates: dict):
    """
    Validate the model timers supplied by the IMSI config json.
    model_internal_chunk_size must be less than model_chunk_size
    and the resulting start and stop times must line up.
    This essentially means that all of the outer loop dates
    (model_submission_job) must be present in the list of
    inner loop dates (model_inner_loop).

    Parameters:
        run_dates (dict ) : A dict of run dates, in iso8061 format, with keys
                            [run_, run_segment]_[start,stop]_date, and keys
                            for model_chunk_size, model_internal_chunk_size
                            and postproc_chunk_size.
    """

    outer = sim_time_factory(run_dates, 'model_submission_job')
    inner = sim_time_factory(run_dates, 'model_inner_loop')

    for chunk in outer.ChunkIndexStart:
        if chunk not in inner.ChunkIndexStart:
            raise ValueError("Misaligned start dates in model_submission_job and model_inner_loop! " +
                             "Must set model_internal_chunk_size / model_chunk_size to have an integer ratio less than 1, " +
                             "and the boundaries between chunks must align.")

    for chunk in outer.ChunkIndexStop:
        if chunk not in inner.ChunkIndexStop:
            raise ValueError("Misaligned stop dates in model_submission_job and model_inner_loop! " +
                             "Must set model_internal_chunk_size / model_chunk_size to have an integer ratio less than 1, "+
                             "and the boundaries between chunks must align.")
