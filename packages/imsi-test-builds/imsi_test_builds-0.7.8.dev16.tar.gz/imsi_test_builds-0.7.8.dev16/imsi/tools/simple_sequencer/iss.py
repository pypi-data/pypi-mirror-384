"""
IMSI Simple Sequencer (ISS)
===========================

ISS (iss) is a simple, portable batch sequencer for running jobs.

iss provides a simple time-looping mechanism to handle sequential job
submissions, and supports submission of downstream dependencies.

iss is: a set of classes and functions, a CLI (which exposes some of
the functions), and preset job script template.
"""
from collections import namedtuple
from dataclasses import dataclass, field, asdict
import datetime
from functools import cached_property
from glob import glob
import json
import os
import re
import subprocess
import textwrap
from typing import List, Dict, Optional

from imsi.scheduler_interface.schedulers import Scheduler, BatchJob
from imsi.tools.time_manager import chunk_manager as cm
from imsi.tools.time_manager.cftime_utils import parse_iso8601_like
from imsi.utils.general import get_date_string, write_shell_script
from imsi.tools.simple_sequencer.iss_globals import (
    ALLOWED_JOB_STATUSES,
    UNAWARE_DATETIME_FORMAT,
    UNAWARE_DATETIME_PATTERN,
    JOB_STATUS_FILENAME_TEMPLATE,
    SCRIPT_INTERPRETER_DIRECTIVE,
    SCRIPT_COMMENT_CHAR,
    SCRIPT_HEADER_TEMPLATE,
    SCRIPT_IMSI_ENV_COMMAND,
    SCRIPT_BODY_TEMPLATE,
    SCRIPT_FOOTER,
    TIME_CHUNK_INDICES
)


def to_shell_bool(boolean: bool):
    if boolean:
        return "true"
    else:
        return "false"

# simple containers
Parent = namedtuple('Parent', ['job_name', 'run_conditional_on'])
Dependent = namedtuple('Dependent', ['job_name', 'run_conditional_on'])

@dataclass
class SimpleJob:
    """An individal job

    Parameters:
        submission_script_fullepath (str) : Name/path of the job script.
        job_identifier (str) : Job name.
        user_script_to_source (path) :  A shell script that run's the
            job's contents (will be sourced).
        directives (list) : A list of directives for the scheduler (e.g.
            wallclock, cores).
        listings_basename (str) : Path/prefix of where to write job listings.
            [default: 'output']
        sequencing_dates_file (str) : The path to the sequencing dates file
            (CSV) which contains rows of time information for run "chunks"
            (from imsi chunk manager)
        timer_name (str) : The name of the timer for the job that will be used
            in the timer tracking file
        submit_next (bool) : If the job should submit the next iteration
            [default: True]
        submit_dependents_on_complete (bool) : if the job should submit its
            dependent jobs (listed in `depends_on`).
        depends_on (dict) : a dictionary that defines the dependent job
            names (keys) and the timer conditions for which they will be
            checked against this job (the parent) (values). See example below.
            [default: None]
        clean_scratch (bool) : Remove (delete) the scratch directory
            [default: True]

    Illustration:

        Suppose there are two jobs, `job_a` and `job_b`. `job_b` is instatiated as:

        ```
        job_b = SimpleJob(job_identifier="job_b", depends_on={"job_a": "END"}, **kwargs)
        ```

        This indicates that any iteration of `job_b` should depend on the
        previous iteration of `job_a` being successfully completed, and that
        the "END" time of `job_b` is no further along in time than the "END" of
        `job_a`.

        Do note that the `depends_on` is simply the *definition* of the
        relationship between `job_a` and `job_b`; other iss tooling can be used
        to check whether the depedency conditions are met for any job
        at any time for a particular run once set up.
    """
    # Note: these are only the ingredients that make the job, where the
    # job status is handled through run-time tooling

    submission_script_fullpath: str
    job_identifier: str
    user_script_to_source: str
    directives: list = field(default_factory=list)
    listings_basename: str ='output'
    sequencing_dates_file: str = ''
    timer_name: str = ''
    submit_next: bool = True
    submit_dependents_on_complete: bool = True
    depends_on: Optional[Dict[str, str]] = None
    clean_scratch: bool = True

def get_job_dependents(jobs: dict, job_name: str):
    """
    an ugly way to construct a relationship 'lookup' by flattening
    the config structure
    returns the information for a SINGLE job_name
    """
    if job_name not in jobs:
        raise KeyError()
    dependents = []
    for job,spec in jobs.items():
        if job == job_name:
            continue
        depends_on = spec.get('depends_on', None)
        if depends_on is not None:
            for dep in depends_on:
                if job_name == dep:
                    transposed_dep = Dependent(job, depends_on.get(job_name))
                    dependents.append(transposed_dep)
    return dependents

def get_job_parents(jobs: dict, job_name: str):
    """get parent job names for a requested job_name"""
    if job_name not in jobs:
        raise KeyError()
    r = jobs[job_name].get('depends_on', None)
    parents = []
    if r:
        for item in r.items():
            parents.append(Parent(*item))
    return parents

class SimpleFlow:
    """A simple flow object to help establish relationships between
    SimpleJob objects.

    Note: This is not akin to a formal tree/DAG and there is limited
    functionality.
    """

    def __init__(self, jobs: List[SimpleJob]):
        if isinstance(jobs, SimpleJob):
            jobs = [jobs]
        self._jobs = jobs
        self.entry = self._resolve_entry()
        self.job_dependents = self.__get_job_relationship("dependents")
        self.job_parents = self.__get_job_relationship("parents")

    @property
    def jobs(self):
        jobids = [j.job_identifier for j in self._jobs]
        if len(jobids) != len(set(jobids)):
            raise AttributeError("job identifiers must be unique")
        return {job.job_identifier: job for job in self._jobs}

    @jobs.setter
    def jobs(self, val: List[SimpleJob]):
        # FUTURE TODO dev if needed -- could do set self._jobs = val
        # and reset all other related props
        raise AttributeError("can't reset jobs once instantiated")

    @cached_property
    def __jobsdict(self):
        # convenience property
        return {job.job_identifier: asdict(job) for job in self.jobs.values()}

    def _resolve_entry(self):
        # validation
        # determine the entry job, ie. the one that doesn't have a `depends_on`
        # (which should 'None' by definition of the SimpleJob property)
        assumed_entry = [k.job_identifier for k in self._jobs if k.depends_on == None]
        if len(assumed_entry) == 1:
            # entry is defined
            self._validate_dependencies()
            return assumed_entry[0]
        elif len(self._jobs) == 1:
            # this means there is one job and it also has a depends_on
            raise AttributeError("single job flow cant have 'depends_on' attribute")
        else:
            raise AttributeError("bad flow design; can't have more than one entry job")

    def _validate_dependencies(self):
        # check properties of dependency job names (keys) and conditions (values)
        for name, j in self.__jobsdict.items():
            if j['depends_on']:
                for jn,val in j['depends_on'].items():
                    if jn == name:
                        raise KeyError(f"dependent of job '{name}' cannot be itself")
                    if jn not in self.__jobsdict:
                        raise KeyError(f"job '{name}' cannot depend on non-existent job '{jn}'")
                    if val not in TIME_CHUNK_INDICES:
                        raise ValueError(f"job dependency condition for '{name}' cannot be '{val}'")

    def __get_job_relationship(self, generation):
        # get the relationship between jobs, either the job's 'parents'
        # (upstream) or 'dependents' (downstream)
        if generation == 'parents':
            handler = get_job_parents
        elif generation == 'dependents':
            handler = get_job_dependents
        else:
            raise ValueError(
                f"handler must be one of 'parents' or 'dependents', not '{generation}'"
                )
        m = {}
        for job in self.jobs:
            m[job] = handler(self.__jobsdict, job)
        return m

@dataclass
class IMSISimpleSequencer:
    """A class to contain the top level information of a sequencer.

    Properties:
        runid : str
        work_dir: str, Path
        run_config_dir : str, Path
        sequencer_config_dir : str, Path
        sequencing_scratch_dir : str, Path
        scheduler : Scheduler
        flow : SimpleFlow
    """
    runid: str
    run_config_dir: str
    sequencer_config_dir: str
    sequencing_scratch_dir: str
    work_dir: str
    scheduler: Scheduler
    flow: SimpleFlow
    timer_tracking_file: str = field(init=False)     # required here for
    listings_dir: str = field(init=False)            #    serialization (re: asdict() vs through setter)

    def __post_init__(self):
        # just defining the path here (file created in self.configure())
        self.timer_tracking_file = os.path.join(self.sequencer_config_dir, ".simulation.time.state")
        self.listings_dir = os.path.join(self.sequencer_config_dir, "listings")

    def configure(self, force=True):
        '''Do the on disk setup of required files'''

        redirect_template = self.scheduler.output_redirect      # template

        for job_name, job in self.flow.jobs.items():

            kwargs = asdict(job)

            # create simple header
            # TODO this could be moved to SimpleJob instead
            # (could pass in more metadata from the Configuration object)
            entry_flag = to_shell_bool(self.flow.entry == job_name)
            kwargs['header_str'] = f'runid:  {self.runid}    job:  {job_name}    entry: {entry_flag}'

            # create/write the batch job using scheduler
            directives=job.directives
            if not directives:
                # TODO catch None or empty list
                directives = self.scheduler.default_directives
            output_path = os.path.join(self.listings_dir, job.listings_basename)
            output_redirect_cmd = redirect_template.format(PATH=output_path)       # not great
            directives = directives + [output_redirect_cmd]

            kwargs['output_redirect_path'] = output_redirect_cmd.split()[-1]       # not great
            script_content = self.generate_simple_shell_sequencing_content(**kwargs)

            # note: input to BatchJob must be a list
            batch_job = BatchJob(user_script=script_content.split('\n'), job_directives=directives)
            batch_script = batch_job.construct_job_script(self.scheduler)
            write_shell_script(job.submission_script_fullpath, batch_script, mode='w', make_executable=True)

            # Configure timers in timing file
            # note: this is within the loop because, though the tracking
            # file is the same, the individual timers are written to the
            # same file here
            cm.init_tracking_file(chunk_file=job.sequencing_dates_file,
                      tracking_file=self.timer_tracking_file,
                      timer_name=job.timer_name,
                      overwrite_timer=force)

    def run(self, job_name=None, init_first_job_status=True):
        """Submits the batch job to the queue.

        Optionally sets the initial status file of the job
        (`init_first_job_status=True`).
        """
        if job_name is None:
            # run the entry job if no job name provided
            job_name = self.flow.entry
        elif job_name not in self.flow.jobs:
            raise KeyError(f"can't run job '{job_name}' because it does not exist")
        job = self.flow.jobs[job_name]
        cmd_run = self.scheduler['submission_command'].split() + [job.submission_script_fullpath]
        subprocess.run(cmd_run, cwd=self.work_dir)

        # v TODO this is sort of messy because the job status is usually set
        # through the iss job scripts -- but this is the current implementation
        # to get the FIRST submission of the job to create a status file.
        # (it is NOT required for iss job scripts to work, but it is
        # ideal for the user).
        if init_first_job_status:
            job = self.flow.jobs[job_name]
            is_first = is_first_iteration(
                job_name,
                self.timer_tracking_file,
                job.sequencing_dates_file,
                timer_name=job.timer_name,
                listings_dir=self.listings_dir
                )
            if is_first:
                # set the status of job submitted
                # (timeinfo is needed to construct the name of the status file)
                timeinfo = cm.get_current_chunk(self.timer_tracking_file, job.timer_name)
                set_job_status(
                    job_name,
                    ALLOWED_JOB_STATUSES['queued'],
                    timeinfo['START'],
                    timeinfo['END'],
                    tracking_dir=self.listings_dir
                    )

        return job_name

    def generate_simple_shell_sequencing_content(
            self, job_identifier: str, user_script_to_source: str=None,
            timer_name: str='', sequencing_dates_file: str=None,
            clean_scratch: bool=True, header_str: str=None, **kwargs) -> str:
        """Generate job script contents for the simple sequencer.

        Each job will have a unique shell script generated. The parameters
        passed here are namely used to fill the script templates defined
        in the `sss` module.

        Parameters:
            job_identifier : str
                job ID, nominally the name of the job
            user_script_to_source : str
                full filename (including path) to the user's job script
            timer_name : str
                name of job's timer (used in the .simulation.time.state file)
            sequencing_dates_file : str
                full filename to list of all dates for the simulation
            clean_scratch : bool
                whether to clean the scratch directory (default True)
            header_str : str
                a string that will be written as a comment at the top of
                the job script
            kwargs :
                submit_next : bool
                submit_dependents_on_complete : bool
                output_redirect_path : str (PBSScheduler only)
        """
        # This creates a string (filled template), whose content reflects
        # the core sequencing logic of SSS

        def format_text_block(text):
            return textwrap.dedent(text).strip()

        submit_next = to_shell_bool(kwargs.get('submit_next', True))
        submit_dependents = to_shell_bool(kwargs.get('submit_dependents_on_complete', True))
        output_redirect_path = kwargs.get('output_redirect_path', None)

        # FIXME lazy test
        # if isinstance(self.scheduler, PBSScheduler):
        if (self.scheduler.directive_prefix == "#PBS") and (output_redirect_path is not None):
            # add some trap method to header to help with keeping output files
            # per run (only for previously run file -- and not fool proof!)
            methods = """
            listings_output={PATH}
            function cleanup_previous {{
                jid=$( echo $job_restart_date | sed 's/[ -:_T]//g' )
                [[ -z $jid ]] && jid=$$
                stem="${{listings_output%.*}}"
                ext="${{listings_output##*.}}"
                [[ -e $listings_output ]] && cp $listings_output "$stem"_"$jid"."$ext"
            }}
            trap cleanup_previous EXIT
            """.format(PATH=output_redirect_path)
        else:
            methods = ""

        # format a string for the name of this tool
        pretty_tool_name = ' '.join(re.split(r'(?=[A-Z][a-z])', self.__class__.__name__)).strip()

        if header_str is not None:
            if not (header_str).startswith(SCRIPT_COMMENT_CHAR):
                header_str = f'{SCRIPT_COMMENT_CHAR} {header_str}'
        else:
            header_str = ''

        # create and fill in the script templates

        header = SCRIPT_HEADER_TEMPLATE.format(
            interpreter=SCRIPT_INTERPRETER_DIRECTIVE,
            tool_title=pretty_tool_name,
            date_string=get_date_string(),
            header_comments=header_str,
            methods=SCRIPT_IMSI_ENV_COMMAND + '\n' + format_text_block(methods)
        )

        body = SCRIPT_BODY_TEMPLATE.format(
            runid=self.runid,
            work_dir=self.work_dir,
            job_name=job_identifier,
            timer_name=timer_name,
            timer_tracking_file=self.timer_tracking_file,
            sequencing_dates_file=sequencing_dates_file,
            sequencing_dir=self.sequencer_config_dir,
            listings_dir=self.listings_dir,
            submit_next_bool=submit_next,
            submit_dependents_bool=submit_dependents,
            iss_config_file=os.path.join(self.sequencer_config_dir, '.iss.json'),
            clean_scratch_bool=to_shell_bool(clean_scratch),
            user_script=user_script_to_source,
            run_config_dir=self.run_config_dir,
            sequencing_scratch_dir=self.sequencing_scratch_dir
        )

        footer = SCRIPT_FOOTER                    # dev: as is for now

        # dedent, strip trailing \s, join
        content = []
        for component in [header, body, footer]:
            content.append(format_text_block(component))
        content = '\n\n'.join(content) + '\n'

        return content

    def to_json(self) -> str:
        data = asdict(self)
        data.pop('flow')   # remove
        data['jobs'] = {k: asdict(v) for k, v in self.flow.jobs.items()}
        return json.dumps(data, indent=4)

    def save_to_json(self, file_path: str):
        json_str = self.to_json()
        with open(file_path, 'w') as file:
            file.write(json_str)

    @staticmethod
    def from_json(json_str: str) -> 'IMSISimpleSequencer':
        data = json.loads(json_str)

        # preserve objects and structure to pass back to constructor:
        data['flow'] = SimpleFlow([SimpleJob(**j) for j in data['jobs'].values()])

        # remove so that these are not passed to the IMSISimpleSequencer constructor
        data.pop('jobs')
        ttf = data.pop('timer_tracking_file')
        ld = data.pop('listings_dir')

        # init
        seq = IMSISimpleSequencer(**data)

        # reset / preserve from original input
        seq.timer_tracking_file = ttf
        seq.listings_dir = ld

        return seq

    @staticmethod
    def load_from_json(file_path: str) -> 'IMSISimpleSequencer':
        with open(file_path, 'r') as file:
            json_str = file.read()
        return IMSISimpleSequencer.from_json(json_str)

def iso8601_to_unaware(timestring):
    """Convert iso8601-like datetime string and convert to unaware
    time string (year through second, no sep).
    """
    # lazy type check -- will raise inside function if format isn't valid
    timeinfo = parse_iso8601_like(timestring)
    return "{year}{month}{day}{hour}{minute}{second}".format(**timeinfo)

def is_unaware_datetime_str(timestring):
    """Return 1 if timestring is in unaware datetime timestring format, otherwise return 0."""
    if re.match(UNAWARE_DATETIME_PATTERN, timestring) is None:
        return 0
    else:
        return 1

def to_unaware_datetime_str(timestring):
    """Convert iso8601 timestring to unaware datetime timestring format."""
    if is_unaware_datetime_str(timestring):
        # already unaware format
        return timestring
    else:
        return iso8601_to_unaware(timestring)

def to_unaware_datetime(timestring):
    return datetime.datetime.strptime(to_unaware_datetime_str(timestring), UNAWARE_DATETIME_FORMAT)

def create_status_basename(job_name, start_time, stop_time):
    """Create the filename basename (including extension) the given job
    parameters

    Parameters:
        job_name : str
        start_time, stop_time : str
            datetimes as strings that are iso8601-like OR are in 14-digit
            "unaware" format (`YYYYmmDDHHMMSS`).

    Returns:
        basename of status file: {job_name}_{starttimestr}_{stoptimestr}.status
        where start and stop time strings are in "unaware" format.
    """
    start_info_fmt = to_unaware_datetime_str(start_time)
    stop_info_fmt = to_unaware_datetime_str(stop_time)

    basename = JOB_STATUS_FILENAME_TEMPLATE.format(
        job_name=job_name,
        start_time=start_info_fmt,
        stop_time=stop_info_fmt
        )
    return basename

def set_job_status(job_name, status, start_time, stop_time, tracking_dir=None):
    """set the status of a job in a job state file

    a function that creates a file like
        {RUNID}_{JOB_NAME}_{job_start_date}_{job_stop_date}.state
    that contains:
        the current status, one of allowed iss.ALLOWED_JOB_STATUSES
    """
    if status not in ALLOWED_JOB_STATUSES.values():
        raise ValueError(
            "status '{status}' invalid; status must be one of: {options}".format(status=status, options=', '.join(ALLOWED_JOB_STATUSES.values()))
            )

    if tracking_dir is None:
        tracking_dir = os.getcwd()
    elif not os.path.exists(tracking_dir):
        raise FileNotFoundError(f"can't set status because tracking directory does not exist: {tracking_dir}")

    basename = create_status_basename(job_name, start_time, stop_time)

    # note: always overwrite file
    state_file = os.path.join(tracking_dir, basename)
    with open(state_file, 'w') as f:
        print(status, file=f)

def read_job_status_file_contents(state_file):
    with open(state_file, 'r') as f:
        status_contents = f.readlines()

    # ensure that this file is valid (one line, status only)
    if len(status_contents) == 1:
        status = status_contents[0].strip()
        if status not in ALLOWED_JOB_STATUSES.values():
            raise ValueError(f'invalid status file content: {status}')
    else:
        raise ValueError('invalid status file content')

    return status

def get_job_status(job_name, start_time, stop_time, tracking_dir=None):
    """Get the status of the job (a specific instance).

    The job name, start time, and stop time must all be provided (these form
    the basename of the status file).
    """

    if tracking_dir is None:
        tracking_dir = os.getcwd()

    basename = create_status_basename(job_name, start_time, stop_time)
    state_file = os.path.join(tracking_dir, basename)
    if not os.path.exists(state_file):
        raise FileNotFoundError(f"no tracking file found at: {state_file}")

    status = read_job_status_file_contents(state_file)

    return status

def get_timer_name(job_name, cfg_file) -> str:
    """Get associated timer name for a specific job_name"""
    # NOTE this is to avoid assuming that (job_name == timer_name), though
    # this should be the case.
    seq = IMSISimpleSequencer.load_from_json(cfg_file)
    if job_name not in seq.flow.jobs:
        raise KeyError(f"no job named '{job_name}' in sequencing config {cfg_file}")
    return seq.flow.jobs[job_name].timer_name

def get_job_name(timer_name, cfg_file) -> str:
    """Get the job_name from the given timer_name"""
    # NOTE this is to avoid assuming that (timer_name == job_name), though
    # this should be the case.
    seq = IMSISimpleSequencer.load_from_json(cfg_file)
    job_name = None
    for job, spec in seq.flow.jobs.items():
        if spec.timer_name == timer_name:
            job_name = job
            break
        else:
            pass
    if job_name is None:
        raise KeyError(f"no timer named '{timer_name}' in sequencing config {cfg_file}")
    return job_name

def ready_to_submit(job_name, iss_config_file) -> bool:
    """Determine if the job is ready to submit to the scheduler.

    A job is deemed "ready to submit" when the job status and timer state
    are resolved and the dependency criteria are met.

    Returns:
        True : the job is NOT ready to submit.
        False : the job is ready to submit (state and dependency conditions are met).
    """

    sequencer = IMSISimpleSequencer.load_from_json(iss_config_file)
    listings_dir = os.path.join(sequencer.sequencer_config_dir, "listings")
    timer_tracking_file = sequencer.timer_tracking_file

    job = sequencer.flow.jobs.get(job_name)
    if job is None:
        raise KeyError(f"job '{job_name}' doesnt exist")

    chunk_file = job.sequencing_dates_file
    timer_name = job.timer_name

    chunks = cm.read_chunks(chunk_file)
    current_chunk = cm.get_current_chunk(timer_tracking_file, timer_name)

    try:
        status = get_job_status(job_name, current_chunk['START'], current_chunk['END'], tracking_dir=listings_dir)
    except FileNotFoundError:
        # if the status file doesn't exist yet
        status = None

    # TODO FIXME: note that cm.get_chunk_by_start should be updated, it should
    # NOT not return -1 for index if not found (this is a valid index in python)
    _, idx = cm.get_chunk_by_start(chunks, current_chunk['START'])

    if (status is not None):
        # safety check
        # AND catch if chunk already active/complete
        proceed = False
    elif idx < len(chunks):
        # within list of chunks

        ref_chunk = chunks[idx]

        # use the definitions in the flow (rather than individual jobs)
        # to use convenience objects next
        depends_on = sequencer.flow.job_parents[job_name]

        if not depends_on:
            # no dependencies to check
            proceed = True

        else:
            # check that ALL dependencies are met
            all_dependencies_met = []

            for parent in depends_on:
                p_job = parent.job_name
                p_cond = parent.run_conditional_on
                p_timer_name = sequencer.flow.jobs.get(p_job).timer_name
                p_chunk = cm.get_current_chunk(timer_tracking_file, p_timer_name)

                # get datetimes for dependency and next chunk for the requested condition (START, etc)
                dt_p = to_unaware_datetime(p_chunk[p_cond])
                dt_ref = to_unaware_datetime(ref_chunk[TIME_CHUNK_INDICES[p_cond]])

                # the following ensures that the check is for conditions
                # of the 'most recent' parent job

                if dt_p > dt_ref:
                    # parent is further along than dependent
                    all_dependencies_met.append(True)

                elif dt_ref == dt_p:
                    # if parent and dependent are at the same time then
                    # check that the parent is complete

                    try:
                        p_job_status = get_job_status(
                            p_job, p_chunk["START"], p_chunk["END"], tracking_dir=listings_dir
                            )
                    except FileNotFoundError:
                        # note: this exception is unlikely unless there was
                        # intervention since the timer should not have
                        # advanced on the parent without a status file existing.
                        # since this will cause one condition failure, we can skip
                        # (break from) any other checks
                        all_dependencies_met.append(False)
                        break

                    status_condition_met = True if p_job_status == ALLOWED_JOB_STATUSES['success'] else False
                    all_dependencies_met.append(status_condition_met)

                else:
                    all_dependencies_met.append(False)

            if all(all_dependencies_met):
                # submit this next job
                proceed = True
            else:
                # not able to submit this next job
                proceed = False

    else:
        # safety - ran out of chunks
        proceed = False

    return proceed

def is_first_iteration(job_name, timer_tracking_file, chunk_file,
                       timer_name=None, listings_dir=None):
    # resolve the state of the job status between the timer tracking info
    # and the job's state
    if timer_name is None:
        timer_name = job_name

    is_first_chunk = cm.check_if_first_chunk(timer_name, chunk_file, timer_tracking_file)

    if is_first_chunk:
        timeinfo = cm.get_current_chunk(timer_tracking_file, timer_name)
        start_fmt = iso8601_to_unaware(timeinfo['START'])
        stop_fmt = iso8601_to_unaware(timeinfo['END'])

        try:
            status = get_job_status(job_name, start_fmt, stop_fmt, tracking_dir=listings_dir)
        except FileNotFoundError:
            status = None

        if status is None or (status == ALLOWED_JOB_STATUSES['fail']):
            # status didn't exist or previously failed (treated equivalently)
            first_iter = True
        else:
            first_iter = False

    else:
        first_iter = False

    return first_iter

def get_job_status_summary(job_name, tracking_dir=None):
    """Return a dict of status file names and file contents (the status),
    and a list of files that could not be read (errors).

    Paramters:
        job_name : job name
        tracking_dir : path to listings directory (location of .status files)

    Returns:
        statuses, errors
    """
    if tracking_dir is None:
        tracking_dir = os.getcwd()

    status_filelist = sorted(glob(os.path.join(tracking_dir, f"{job_name}*.status")))

    stats = {}
    error_files = []

    if len(status_filelist) == 0:
        pass
    else:
        for f in status_filelist:
            try:
                status = read_job_status_file_contents(f)
            except ValueError:
                error_files.append(f)
                continue
            stats[f] = status

    return stats, error_files

def get_job_status_summary_message(job_name, tracking_dir=None):
    """Return a formatted string of job status summary information.

    The string includes:
        - A list of status file names (basename, relative to `tracking_dir`)
        and the status (file content)
        - If applicable, a list of files that could not be interpreted.
    """
    if tracking_dir is None:
        tracking_dir = os.getcwd()

    statuses, error_files = get_job_status_summary(job_name, tracking_dir=tracking_dir)

    header_strs = [f'job status for: {job_name}', f'listings in: {tracking_dir}']
    output_strs = header_strs

    if statuses:
        status_strs = []
        for f,s in statuses.items():
            f_display = os.path.basename(f).replace('.status', '')
            status_strs.append("{}  {}".format(f_display, s))
        output_strs += status_strs
    else:
        output_strs += ['no status files found.']

    output_msgs = ['\n'.join(output_strs)]

    if error_files:
        error_str = "\n".join(error_files)
        output_msgs += ["\n".join([
            'job status could not be read from the following file(s):',
            f'{error_str}'
            ])
        ]
    msg = '\n\n'.join(output_msgs)
    return msg

def _get_iss_cfg_file(cfg_file):
    # returns path to iss config file (json), in current location
    # if not specified
    if cfg_file is None:
        cfg_file = os.path.join(os.getcwd(), '.iss.json')
    return cfg_file

def which_scheduler(cfg_file=None):
    """Return the scheduler name for the iss run."""
    cfg_file = _get_iss_cfg_file(cfg_file)
    sequencer = IMSISimpleSequencer.load_from_json(cfg_file)
    n = sequencer.scheduler.get('name', None)
    if n is None:
        n = sequencer.scheduler.get('directive_prefix')
    return n

def which_submit(cfg_file=None):
    """Return the scheduler submission command for the iss run."""
    cfg_file = _get_iss_cfg_file(cfg_file)
    sequencer = IMSISimpleSequencer.load_from_json(cfg_file)
    n = sequencer.scheduler.get('submission_command', None)
    if n is None:
        raise AttributeError('no command specified')
    return n

def get_job_chunk_dict(cfg_file):
    """Return the list of time chunks for a specific job for the iss run."""
    cfg = _get_iss_cfg_file(cfg_file)
    sequencer = IMSISimpleSequencer.load_from_json(cfg)

    jobs = sequencer.flow.jobs.keys()
    job_chunks = {}
    for j in jobs:
        chunk_file = sequencer.flow.jobs[j].sequencing_dates_file
        job_chunks[j] = cm.read_chunks(chunk_file)
    return job_chunks

def which_jobs(cfg_file=None):
    """Return a formatted string of the time chunks for each jobs
    of the iss run.
    """
    job_chunks = get_job_chunk_dict(cfg_file)

    LINE_TEMPLATE = "{:>7}{:>22}{:>22}{:>22}"
    header = list(TIME_CHUNK_INDICES.keys())

    msgs = ["jobs:"]
    for j,c in job_chunks.items():
        msgs.append("{job} (n = {n})".format(job=j, n=len(c)))
        msgs.append(LINE_TEMPLATE.format(*([''] + header)))
        msgs.append(('\n'.join([LINE_TEMPLATE.format(*([i+1] + row)) for i,row in enumerate(c)])))

    return '\n'.join(msgs)
