"""
An interface between IMSI upstream configuration and tooling and the iss.

imsi configuration is taken and processed into the configuration required for
iss. Specifically, the IMSISimpleSequencerInterface exposes methods that correspond
to imsi setup, config, and submit.
"""

import sys
import os
import shutil
from imsi.sequencer_interface.sequencers import Sequencer
from imsi.scheduler_interface.schedulers import create_scheduler, Scheduler
from imsi.config_manager.config_manager import Configuration
from imsi.config_manager.schema.machine import MachineFactory

import imsi.tools.simple_sequencer.iss as iss

# for future development
_ALLOWED_JOB_NAMES = ['model', 'postproc']

class IMSISimpleSequencerInterface(Sequencer):
    """An interface between upstream imsi tooling and the IMSISimpleSequencer."""

    def setup(self,configuration: Configuration, force=True):
        # Update to include explicit paths to write files at.
        work_dir = configuration.get_unique_key_value('work_dir')
        if not os.path.isdir(work_dir):
            raise FileExistsError(f'The run working directory at {work_dir} does not exist')

        sequencer_dir = configuration.get_unique_key_value('sequencer_dir')

        if force:
            shutil.rmtree(sequencer_dir)

        # makes /sequencer and /sequencer/listings
        listings_dir = os.path.join(sequencer_dir, 'listings')
        os.makedirs(listings_dir, exist_ok=True)

    def config(self, configuration: Configuration, force=True):
        """
        Write files needed for the imsi shell sequencer, including
        the `.simulation.time.state` file, and the submission files
        for the model and diagnostics.
        """

        sequencer_dir = configuration.get_unique_key_value('sequencer_dir')
        if not os.path.isdir(sequencer_dir):
            os.mkdir(sequencer_dir)

        # Creates scheduler and SSS sequencer/job objects
        scheduler = create_scheduler(configuration.get_unique_key_value('scheduler'))

        # Deal with cases where there is a prefix before the scheduler's submission
        # command that's required (eg. ssh).
        # it may not be defined for all machines. Could reconsider how this is done.
        try:
            submit_prefix = configuration.get_unique_key_value('submit_prefix')
        except (ValueError, KeyError):
            # note: get_unique_key_value() may raise a ValueError
            submit_prefix = ''
        scheduler.submission_command = submit_prefix + scheduler.submission_command

        shell_sequencer = create_shell_sequencer(configuration, scheduler)

        # Configure the files on disk
        shell_sequencer.configure(force=force)

        # Save this sequencer object for later resuse
        shell_sequencer.save_to_json(os.path.join(sequencer_dir, '.iss.json'))

    def submit(self, configuration: Configuration):
        """Submits the job to the queue.
        Also checks that this command is being run from the location (machine)
        that was used for configuration.
        """
        sequencer_dir = configuration.get_unique_key_value('sequencer_dir')
        shell_sequencer = iss.IMSISimpleSequencer.load_from_json(os.path.join(sequencer_dir, '.iss.json'))

        machine_name = configuration.machine.name
        current_hostname = MachineFactory.get_hostname()

        # exploit - reconstruct the machines config so that we can exploit the functions
        # in MachineFactory
        machine_config = {machine_name: configuration.machine.model_dump()}

        base_message = f"  submitting from: {current_hostname} "

        try:
            current_matched_machine = MachineFactory.find_matching_machine(machine_config)
            print(f"{base_message} ({current_matched_machine})\n")
        except NameError:
            config_mismatch_message = f"{base_message}\n  run configured for: {machine_name}"
            sys.exit(f'imsi error: Not on the machine configured. Make sure you run imsi submit for iss on the requested machine:\n{config_mismatch_message}\n')

        sequencer_dir = configuration.get_unique_key_value('sequencer_dir')
        shell_sequencer = iss.IMSISimpleSequencer.load_from_json(os.path.join(sequencer_dir, '.iss.json'))
        shell_sequencer.run()

    def status(self, configuration: Configuration, setup_params: dict):
        raise NotImplementedError("status command not implemented for IMSISimpleSequencerInterface")

def create_shell_sequencer(configuration: Configuration, scheduler: Scheduler=None):
    '''Create a IMSISimpleSequencer instance from a Configuration and Scheduler'''

    if scheduler is None:
        # FIXME this could be dangerous as the scheduler and configuration
        # are input separately - potential *UN*coupling. consider making
        # this function create both objects to preserve sync.
        scheduler = create_scheduler(configuration.get_unique_key_value('scheduler'))

    runid = configuration.get_unique_key_value('runid')
    sequencing = configuration.sequencing.model_dump()

    config_dir = configuration.get_unique_key_value('run_config_path')
    sequencer_dir = sequencing['sequencer']['sequencer_dir']
    job_config = sequencing['sequencing_flow']['jobs']
    job_list = job_config.keys()

    # TODO: the name of the jobs is essentially HARD-CODED because of the
    # dependency on the shell env timer files for the datetime chunk information
    # produced through shell_interface.shell_interface_manager.write_shell_script()
    #   (ie. files:
    #       'model_submission_job_start-stop_dates'      and
    #       'postproc_submission_job_start-stop_dates'
    #   )
    # An alternative could be to set these file in the imsi config for iss directly,
    # but this did not seem like a good strategy because it does not solve *all*
    # aspects of this issue (ie there would still only be two files available
    # with hard-coded names).
    # Until that part of the time config is made more flexible (infinite timer
    # files / flexible naming), we must check the names of the jobs:
    _qa_check_job_names(job_list)

    jobs = []
    for job_name in job_list:

        user_script = sequencing['sequencer']['baseflows']['flow_definitions'][job_name]

        # flow settings -- sensible defaults if dne
        flow_settings = sequencing['sequencer']['baseflows']['flow'].get(job_name, {})
        depends_on = flow_settings.get('depends_on', None)
        submit_next = bool(flow_settings.get('submit_next', True))  # to type required by SimpleJob

        job_specs = job_config[job_name]
        directives = job_specs['resources'].get('directives', [])
        directives = None if len(directives) == 0 else directives   # type changes - not great

        # file name construction (does not guarantee if the file exists)
        # (it is created through shell_interface_manager.build_config_dir(),
        # which may not have been called yet)
        job_dates_file = os.path.join(config_dir, f"{job_name}_submission_job_start-stop_dates")

        # basename of job's stdout file
        listings_basename = job_specs.get('listings_basename', None)
        if listings_basename is None:
            listings_basename = f"{job_name}_{runid}"

        jobs.append(create_job(runid, job_name, sequencer_dir, job_dates_file, user_script,
                    directives=directives, listings_basename=listings_basename,
                    depends_on=depends_on, submit_next=submit_next)
                    )

    # automatically makes the timer tracking file
    return  iss.IMSISimpleSequencer(
                runid=runid,
                run_config_dir=config_dir,
                sequencer_config_dir=sequencer_dir,
                sequencing_scratch_dir=configuration.get_unique_key_value('scratch_dir'),
                work_dir=configuration.get_unique_key_value('work_dir'),
                scheduler=scheduler,
                flow=iss.SimpleFlow(jobs)
            )

def create_job(run_id, job_name, script_dir, dates_file, user_script, \
               directives=None, clean_scratch=True, depends_on=None, \
               submit_next=True, submit_dependents=True, listings_basename=None):
    """
    Creates a SimpleJob object for a given configuration.

    script_dir: str, Path
        where the generated script file will go and be sourced from (make
        sure this is accesible by your system/scheduling system)
    """

    if listings_basename is None:
        # TODO not great
        # (this is currently set to the default from SimpleJob, which we shouldnt know here)
        listings_basename = "output"

    job = iss.SimpleJob(
        job_identifier=job_name,
        submission_script_fullpath=os.path.join(script_dir, f'{job_name}-{run_id}.sh'), # will be created
        user_script_to_source=user_script,
        directives=directives,
        sequencing_dates_file=dates_file,
        depends_on=depends_on,
        timer_name=job_name,
        submit_next=submit_next,
        submit_dependents_on_complete=submit_dependents,
        clean_scratch=clean_scratch,
        listings_basename=listings_basename
    )

    return job

def _qa_check_job_names(job_names):
    # check that the job names are allowed.
    # FUTURE: this is current REQUIRED by iss since the time variable names are
    # hard-coded in imsi. this may not be a strict requirement in the future.
    for j in job_names:
        if j not in _ALLOWED_JOB_NAMES:
            raise ValueError("job name '{}' not allowed; must be one of: {{{}}}".format(j, ', '.join(_ALLOWED_JOB_NAMES)))
    return True

