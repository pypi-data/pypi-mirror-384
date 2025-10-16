"""
maestro_cap
===========

A module used to initialize a maestro experiment folder and propagate
configuration for a maestro experiment from imsi to corresponding files
of the experiment.

Maestro is a suite of tools used to create and submit tasks to
computer systems. Configuring a new maestro experiment is usually done
via command-line tools and/or the Maestro Manager program `xm`.

This imsi-maestro interface is not fully generalized (ie. there is no
"python module for maestro"). Rather, this module depends on some
initial setup in native maestro to generate the module and resource
files for an experiment. These files are then used as templates
("default"/"source"). Specific flow configuration and job resources can
be set through imsi. In other words, given a pre-made maestro experiment
with defined flow, jobs, and resources, the user can use imsi and these
functions to set specific resources or switch out one template
flow file (flow.xml) for another.

Usage notes:
- the user cannot generate a new flow/task from this module alone
(templates must be specified).
- duplicate job names in maestro are allowed (under different tasks);
for job resources configuration from imsi will be applied to all of these
jobs identically.

Maestro and its tools were written by the Canadian Meteorological Centre.

There is no planned future development for maestro, but you may still
refer to the following internal resources:

- the maestro man page (`man maestro`)
- CMC wiki https://wiki.cmc.ec.gc.ca/wiki/Maestro
- maestro git repository https://gitlab.science.gc.ca/cmoi/maestro

"""

import os
import glob
import shutil
import subprocess
import time
from pathlib import Path
import re
from xml.etree import ElementTree
import traceback

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from imsi.config_manager.config_manager import Configuration
from imsi.utils.general import parse_memory_string_to_bytes, _get_memory_unit_factors_to_bytes
from imsi.utils.nml_tools import update_env_file
from imsi.tools.time_manager.time_manager import sim_time_factory
from imsi.sequencer_interface.sequencers import Sequencer
from imsi.sequencer_interface import maestro_status


_exec_requirements = [
    'maestro',
    'expbegin',
    'makelinks',
    'nodeinfo'
]

# required by maestro
MAESTRO_FOLDERS = [
    'hub',         # host-specific dirs (static -  ~/.suites/.default_links)

    'modules',     # flow (flow/tsk/cfg) <- imsi config
    'resources',   # resources (xml) <- imsi config

    'sequencing',  # for running exp (once sequencener executed), status, output, etc.
    'listings',    # log files of maestro tasks
    'logs',        # execution logs of maestro (used by xflow UI)
    ]
# subset of folders - used when running the experiment (not used for config)
MAESTRO_FOLDERS_RUNTMP = ['sequencing', 'listings', 'logs']

class MaestroSequencerInterface(Sequencer):
    """
    The maestro sequencer interface
    """

    # define list of attributes allowed in <BATCH> tags in
    # <NODE_RESOURCE>. Note: Every attributes in the BATCH tag is
    # optional (defaults will be used by maestro if not provided).
    # See:
    #   https://wiki.cmc.ec.gc.ca/wiki/Maestro/sequencer#Batch_System_Resources
    _NODE_RESOURCE_BATCH_ATTRIBUTES = [
        'catchup', 'cpu', 'cpu_multiplier', 'immediate', 'machine',
        'memory', 'mpi', 'queue', 'soumet_args', 'wallclock'
        ]

    # imsi -> maestro for <BATCH> attributes
    _NODE_RESOURCE_BATCH_ATTRIBUTE_ALIASES = {
        'processors': 'cpu'
    }

    def __init__(self):
        # v not great v
        _check_execs_available()

    def _check_if_setup(self, seq_exp_home: str):
        # rough check to see if setup already run
        # (weak check for some paths that exist)
        modules_path = os.path.join(seq_exp_home, 'modules')
        _required_structure = [os.path.join(seq_exp_home, 'EntryModule'), modules_path]
        _empty = False
        if os.path.exists(modules_path):
            if len(os.listdir(modules_path)) == 0:
                _empty = True

        if not any([os.path.exists(f) for f in _required_structure]) or _empty:
            raise OSError("maestro sequencer folder not setup; can't continue configuration.")

    def setup(self, configuration: Configuration, force=True):
        """Setup the maestro experiment folder."""
        # Note: this setup function currently mimics most of the
        # functionality and function structure of the CanESM system
        # setup-maestro script in CCCma_tools/maestro-suite/default-config-canesm

        runid = configuration.setup_params.runid
        maestro_config = configuration.sequencing.sequencer

        exp_flow = maestro_config['baseflows']

        maestro_src = exp_flow['maestro_defaults_src']          # source of templates
        maestro_dst = maestro_config['SEQ_EXP_HOME']            # destination for setup
        modules_provided = exp_flow['flow_definitions'].keys()  # ie folder names

        setup_maestro_from_src(maestro_src, maestro_dst, modules_provided, runid=runid, force=force)

    def config(self, configuration: Configuration, **kwargs):
        """Configure maestro experiment."""
        # Note: the original config-maestro script in
        #   CCCma_tools/maestro-suite/default-config-canesm
        # does three main "steps":
        #   - sets experiment resources (to resources.def and node
        #     resource xml files, via set_resources())
        #   - sets up the experiment flow (related to flow.xml files
        #      for each module, via set_experiment_flow())
        #   - sets experiment options (to ExpOptions.xml, via
        #     set_expoptions_file())
        # The steps can be done in any order.

        maestro_config = configuration.sequencing.sequencer
        flow_config = configuration.sequencing.sequencing_flow

        exp_flow = maestro_config['baseflows']
        flow_files = exp_flow['flow_definitions']

        # TODO consider removing this imsi dependency just to access
        # the number of model/postproc iterations
        n_model_chunks, n_postproc_chunks = _get_run_chunking(
            configuration.sequencing.model_dump()['run_dates']
        )

        target_dependency_loop_ratio = n_model_chunks/n_postproc_chunks  # dynamic adj

        if not float(target_dependency_loop_ratio).is_integer():
            raise ValueError(f'(number of model chunks) / (number of postproc chunks) must be integer greater than one, not {target_dependency_loop_ratio};'+\
                              ' check settings under "run_dates".')

        #RD: I'm not sure what conditions will trigger this. If postproc_chunk_size > run length, it will still have 1 chunk
        if n_postproc_chunks < 1:
            raise ValueError(f'number of postproc chunks must be integer greater than one, not {n_postproc_chunks};'+\
                              ' check settings under "run_dates".')


        # folder structure
        # root_dir is the path to the maetro experiment, ie SEQ_EXP_HOME
        # defaults is special, but other structure under root_dir is not
        defaults_dir = maestro_config['baseflows']['maestro_defaults_src']
        exp_root_dir = maestro_config['SEQ_EXP_HOME']

        if not os.path.exists(defaults_dir):
            raise FileNotFoundError(
                f"no folder for maestro experiment template files found: {defaults_dir}"
                )

        self._check_if_setup(exp_root_dir)

        # FIXME: suppose this could be part of the experiment flow
        # definition structure, eg:
        # {"sequencing": {"sequencers": {"maestro" : {"baseflows": {
        #     "AMIP": {"canam_split_job_flow": {
        #         "flow_definitions"  : {
        #             "postproc" : "..."
        #         },
        #         "flow_adjust_loop_dependency_ratio": {
        #             "postproc" : {
        #                 "from": ["rebuild_loop", "diagnostics_loop", "wrap_up_loop"],
        #                 "to": ["model_loop", "model_loop", "model_loop"]
        #             },
        #         }
        # for now, define separate dict hardcoded here (otherwise would just use exp_flow)
        exp_flow_adj = {
            "flow_adjust_loop_dependency_ratio": {
                "postproc": {
                    "rebuild_loop": "/canesm/model/model_loop",
                    "diagnostics_loop": "/canesm/model/model_loop",
                    "wrap_up_loop": "/canesm/model/model_loop",
                }
            }
        }
        loop_adjustments = exp_flow_adj.get("flow_adjust_loop_dependency_ratio", {})

        # note: in the imsi framework, most resources for maestro jobs
        # are specific at the job-level, so this section is quite
        # small
        # FIXME still some assumptions about naming/structure here
        updates = {
            "SEQ_JOBNAME_PREFIX": generate_maestro_jobname_prefix(
                configuration.setup_params.runid
            ),
            "NUMBER_OF_POSTPROC_LOOPS": n_postproc_chunks,
            "NUMBER_OF_MODEL_LOOPS": n_model_chunks,
        }

        update_exp = maestro_config.get("experiment.cfg", {})

        # get all the names of machines that will be used to filter
        # the list available
        mset = set(
            [
                spec["resources"].get("machine", None)
                for spec in flow_config["jobs"].values()
            ]
        )
        machines = [name for name in mset if name is not None]

        platform_config = {}

        # error handling: check if information for the machine an other site
        # machines are available:
        # (this is a little messy since for the setup machine the resources
        # are set within parameters, whereas for other machines in the site they
        # are set under site)
        for m in machines:
            # Determine the source of machine configuration
            mm = configuration.machine if m == configuration.machine.name else configuration.machine.site.get(m)

            # Extract resources, handle missing cases
            m_res = getattr(mm, 'resources', None) if m == configuration.machine.name else mm.get("resources")

            if m_res is None:
                raise KeyError(f"Resources must be configured for machine '{m}'")

            platform_config[m] = {'resources': m_res}

        config_maestro_from_src(
            defaults_dir,
            exp_root_dir,
            configuration.setup_params.runid,
            flow_files,
            dependency_loop_ratio=n_model_chunks/n_postproc_chunks,
            dependency_loop_adjustments=loop_adjustments,
            dependency_loop_iter=n_postproc_chunks,
            resource_def_config=updates,
            experiment_def_config=update_exp,
            job_resource_config=flow_config["jobs"],
            platform_config=platform_config,
        )

    def submit(self, configuration: Configuration):
        """Submit a maestro job using `expbegin`.

        Note that this call will pass the current time for the datestring
        argument (`-d`), to the nearest minute only.
        """
        # Note: TODO setting the date for expbegin does NOT currently
        # mimic the behaviour of expbegin (which can automatically
        # increment the date if the same job is resubmitted, will
        # default to unix epoch time if empty, and can accept less
        # precision and pad the rest of the string with zeros).
        #
        # For now, the behaviour is to resolve the current time to the
        # nearest minute only (seconds are always "00", YYYYMMDDhhmm00)
        dtstring = get_maestro_current_datetime_string()

        expbegin_path = _get_exec_fullpath('expbegin')
        SEQ_EXP_HOME = configuration.sequencing.sequencer[
            "SEQ_EXP_HOME"
        ]

        cmd = [expbegin_path, '-e', SEQ_EXP_HOME, '-d', dtstring]

        try:
            proc = subprocess.run(cmd, capture_output=True)
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            cmd_string = ' '.join(proc.args)

            # error handling in/via expbegin is inconsistent (the 'error
            # message' might be via stdout or sterr, so capture/print both)
            out = proc.stdout.decode().strip()
            err = proc.stderr.decode().strip()
            out = out if not out else '\n' + out
            err = err if not err else '\n' + err

            raise ChildProcessError(f"Command failed: {cmd_string}\n{out}{err}") from e

    def status(self, configuration: Configuration, setup_params):
        """
        Check the status of a maestro job from the command line.

        This method retrieves and displays the status of a maestro job by reading 
        the status files from the sequencer and presenting it in a formatted 
        table with color-coded statuses.

        Args:
            configuration (Configuration): The configuration object containing 
                setup parameters and sequencing parameters.
        Notes:
            - The status is displayed in a table format using the `rich` library.
            - Only directories with names matching the pattern with 14 numeric digits are considered.
            - Only recognized statuses will be displayed in the table.
            - This command is not robustly tested for all possible maestro statuses/outputs
        """

        # recognized statuses
        color_map = {
            "begin": "green4",
            "stop": "bright_red",
            "end": "dodger_blue1",
            "catchup": "purple",
            "submit": "grey70",
        }

        root_module = maestro_status.get_root_module(Path(setup_params.work_dir))
        status_dir = Path(
            configuration.sequencing.sequencer["SEQ_EXP_HOME"],
            "sequencing",
            "status",
        )

        if not status_dir.exists():
            try:
                raise FileNotFoundError(
                    f"Status directory not found at: {status_dir}. Was the run properly submitted?"
                )
            except FileNotFoundError:
                traceback.print_exc(limit=1)
                exit(1)

        # extract experiment folder names from status directory
        date_dirs = sorted([d for d in status_dir.iterdir() if d.is_dir() and re.match(r"^\d{14}$", d.name)])[::-1]

        if len(date_dirs) == 0:
            try:
                raise FileNotFoundError(f"No experiment directories found in the status directory {status_dir}. Was the run properly submitted?")
            except FileNotFoundError:
                traceback.print_exc(limit=1)
                exit(1)

        console = Console()
        legend_str = ", ".join([f"[{v}]{k}[/{v}]" for k, v in color_map.items()])
        table = Table(show_header=True, box=None, padding=(0, 1))

        table.add_column(f"{setup_params.runid}", justify="left")
        table.add_column("Status...", justify="left")

        for date in date_dirs:
            df = maestro_status.check_entry_and_get_dataframe(root_module, date)
            # ignore empty dataframes
            if df is None:
                continue
            df = maestro_status.filter_df(df)
            # update table
            table = maestro_status.update_table(table, date, df, color_map)
        panel = Panel(table, title=f"{root_module} status [{legend_str}]", border_style="cyan")
        console.print(panel)


def _check_execs_available(names=_exec_requirements):
    # lazy check if executables are available
    for n in names:
        _get_exec_fullpath(n)

def setup_maestro_from_src(src: str, dst: str, modules: list[str], runid: str = '', force=False):
    """Setup a maestro experiment from a template source `src` at the
    destination path `dst`.

    The `src` must contain `/modules` and its contents, and a
    `EntryModule` link (optionally: `experiment.cfg`).

    Parameters:
        src : path to maestro experiment template folder. This should
            contain all required files and folders for the maestro
            experiment modules, in the expected structure.
        dst : path to destination experiment folder.
        modules : list of folder (module) names, created under `/modules`.
        runid : model run ID specified by user (usually corresponds
            to filename of $SEQ_EXP_HOME)
    """
    prepare_dst_directory(dst, force=force)
    init_folders(src, dst, modules, force=force)
    config_hub(dst, runid)

def prepare_dst_directory(dst: str, force=False):
    """Create a folder for a maestro experiment
    (the desired path for maestro's `$SEQ_EXP_HOME`).
    """
    ex = not force
    if force:
        shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst, exist_ok=ex)

def init_folders(src: str, dst: str, modules: list[str], force=False):
    """Initialize maestro experiment folder structure at a destination
    path `dst` using a template source `src`.

    The `src` must contain `/modules` and its contents and a `EntryModule`
    link (optionally: `experiment.cfg`).

    Parameters:
        src : path to maestro experiment template folder. This should
            contain all required files and folders for the maestro
            experiment modules, in the expected structure.
        dst : path to destination experiment folder.
        modules : list of folder (module) names, created under `/modules`.
    """
    # initialize maestro folder structure
    init_maestro_experiment_folders(dst, force=force)

    copy_default_main_config(src, dst)

    # create module folders and link
    src_modules = os.path.join(src, 'modules')    # defaults
    dst_modules = os.path.join(dst, 'modules')

    entrymodule_name = get_entrymodule_name(src)
    init_maestro_module_folders(dst, entry_module=entrymodule_name, modules=modules)

    create_maestro_modules_from_src(src_modules, dst_modules)


def config_hub(seq_exp_home, experiment):
    """Create the host-specific directories in the maestro
    experiment `/hub`.

    This uses the `makelinks` program to create links to local storage
    on the appropriate machines. Note: this does not pass additional
    arguments to `makelinks`.
    """

    # setup links to machines using the makelinks maestro tool using
    # the makelinks utility (unless specified, uses
    # ~/.suites/.default_links)
    # makelinks requires:
    #   - the running location to be SEQ_EXP_HOME -> cwd
    #   - SEQ_EXP_HOME to be set as an env variable -> env
    # TODO the makelinks tool isn't overly complicated; in the future
    # it might desirable to remove this dependency in favour of
    # having the same functionality implemented here.

    makelinks_path = _get_exec_fullpath('makelinks')
    maestro_env = _set_maestro_env(seq_exp_home)

    cmd = [makelinks_path, '-f', f'--experiment={experiment}']

    try:
        proc = subprocess.run(cmd, cwd=seq_exp_home, env=maestro_env, capture_output=True)
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        raise Exception("Failed call: '{cmd}': {err}".format(cmd=' '.join(proc.args), err=proc.stderr))

def copy_default_main_config(src: str, dst: str):
    """Copy the configuration `experiment.cfg` file defined in
    source `src` directory to the destination `dst` directory.

    References:
        [1] https://wiki.cmc.ec.gc.ca/wiki/Maestro/experiment.cfg
    """
    exp_cfg = os.path.join(src, 'experiment.cfg')
    if os.path.exists(exp_cfg):
        shutil.copy2(exp_cfg, dst)

def init_maestro_module_folders(path: str, entry_module: str = 'module', modules: list[str] = None):
    """Initialize the experiment folder structure as required by maestro.

    Parameters:
        path: path to maestro experiment folder (top level), which contains
            the `/modules` folder (among others).
        entry_module: name of entry module, required by maestro. The
            EntryModule is then symlinked to the folder under
            `/modules/{entry_module}`
        modules: list of names of modules (subfolders). If None, will only
            include the `entry_module`.

    References:
        [1] https://wiki.cmc.ec.gc.ca/wiki/Maestro_Files_and_Folders
    """

    modules_path = os.path.join(path, 'modules')
    if os.path.exists(modules_path):
        shutil.rmtree(modules_path)
    os.makedirs(modules_path)

    if modules is None:
        modules = [entry_module]

    if not entry_module in modules:
        raise ValueError('entry_module must match one of modules provided')

    for m in modules:
        os.makedirs(os.path.join(modules_path, m))

    # this is a relative symlink
    entry_src = os.path.join('modules', entry_module)
    entry_dst = os.path.join(path, "EntryModule")
    if os.path.exists(entry_dst):
        os.remove(entry_dst)
    os.symlink(entry_src, entry_dst)

def init_maestro_experiment_folders(path: str, force=False):
    """Initialize the experiment folder structure at `path` as
    required by maestro. Only the folder structure is created;
    no folders are populated.

    References:
        [1] https://wiki.cmc.ec.gc.ca/wiki/Maestro_Files_and_Folders
    """
    for f in MAESTRO_FOLDERS:
        fpath = os.path.join(path, f)
        exists = os.path.exists(fpath)
        if f in MAESTRO_FOLDERS_RUNTMP:
            if force and exists:
                shutil.rmtree(fpath)
            os.makedirs(fpath, exist_ok=True)
        else:
            # always remake this folder
            if os.path.exists(fpath):
                shutil.rmtree(fpath)
            os.makedirs(fpath)

def get_entrymodule_name(path):
    """Given the `path` to EntryModule, get the real name of the module"""
    # note: path is the input to enforce finding the file with the
    # literal name "EntryModule" (maestro requirement)
    em = os.path.join(path, "EntryModule")
    if not os.path.exists(path) or not os.path.islink(em):
        raise FileNotFoundError(f"EntryModule not found; EntryModule must be a symlink located in {path}.")
    # get name of folder that EntryModule links to
    name = os.path.basename(os.path.realpath(em))
    return name

def create_maestro_modules_from_src(src: str, dst: str, copy=True):
    """Create maestro module structure from `src`/modules
    (default/templates) to `dst`/modules.

    If copy is True, folders and files from `src` is copied to `dst`.
    If copy is False, folder structure is copied, files (cfg, tsk) are symlinked.
    """

    if not os.path.basename(os.path.normpath(dst)) == 'modules':
        raise ValueError("dst path must be a folder named 'modules' for maestro")

    if copy:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        # get list of all files (recursively)
        src_files = [p for p in glob.glob(os.path.join(src, "**"), recursive=True) if os.path.isfile(p)]

        # only include folders that are subfolders of src and immediate
        # subfolders, ie. do not include src, src/module1, src/module2, etc.
        allfolders = glob.glob(os.path.join(src, '*/**/'), recursive=True)

        # use normpath before dirname to account for potential trailing os.sep
        # TODO a pathlib.Path solution would be cleaner:
        # [f.relative_to(src) for f in Path(src).rglob(".") if not f.samefile(src) and not f.parent.samefile(src)]
        src_rel_folders = [os.path.relpath(f, src) for f in allfolders if os.path.dirname(os.path.normpath(f)) != src]

        # create local dirs within modules
        for f in src_rel_folders:
            dst_folder = os.path.join(dst, f)
            if os.path.exists(dst_folder):
                shutil.rmtree(f)
            os.makedirs(dst_folder)

        # link in version controlled files
        for f in src_files:
            s = os.path.relpath(f, src)
            os.symlink(f, os.path.join(dst, s))

def create_experiment_flow_file(src: str, dst: str):
    """Create a `flow.xml` file at the destination path `dst` by copying
    a template flow file (`xml`) `src`. While the `src` filename
    (basename) can be any name, the resulting file at `dst` is always
    `flow.xml` (maestro requirement).

    This function can be used to swap out different flow files for the
    same experiment.
    """
    if not os.path.exists(src):
        raise FileNotFoundError(f'no existing flow template file found: {src}')
    if not os.path.exists(dst):
        raise FileNotFoundError(f'no existing module set up for {dst}')
    if not os.path.basename(os.path.dirname(os.path.normpath(dst))) == 'modules':
        raise ValueError(f'incorrect destination for modules: {dst}')

    dst_flow_file = os.path.join(dst, 'flow.xml')
    shutil.copy(src, dst_flow_file)

def update_experiment_options_file(src, dst, short_name=None, display_name=None):
    """Update the attributes of the `ExpOptions` tag in the ExpOptions.xml
    file.

    The `ExpOptions.xml` is an optional file used in `xflow_overview` to
    help display experiment information.

    Note: This function has extremely limited functionality. It is
    currently only used to update two attributes on the root node
    ExpOptions tag.

    References:
        [1] https://wiki.cmc.ec.gc.ca/wiki/Maestro/ExpOptions.xml
    """

    expoptions_basename = "ExpOptions.xml"

    if short_name is None and display_name is None:
        raise ValueError('one of short_name or display_name must be specified')

    default_expoptions_file = os.path.join(src, expoptions_basename)
    if not os.path.exists(default_expoptions_file):
        raise FileNotFoundError(f'no default {default_expoptions_file} file found in {src}')

    target_expoptions_file = os.path.join(dst, expoptions_basename)
    shutil.copy2(default_expoptions_file, target_expoptions_file)

    # set attributes
    exop = ElementTree.parse(target_expoptions_file)
    root = exop.getroot()
    if short_name:
        root.set("shortName", short_name)
    if display_name:
        root.set("displayName", display_name)
    exop.write(target_expoptions_file)

def set_dependency_loop_index_by_ratio(
        flow_file: str, from_loop: str, to_loop: str, ratio: int = 1,
        n_iter : int = 1, start_iter: int = 1):
    """Set the `DEPENDS_ON` loop dependency by ratio between the index
    and the local loop, and generate each `DEPENDS_ON` element for
    the requested number of iterations.

    From the maestro docs, "a `DEPENDS_ON` element can specify
    dependencies. It tells the sequencer that the current node cannot
    be submitted until the dependency is satisfied." This function
    allows for setting iteration `N` of one task (`from_loop`) to
    depend on iteration `N` of another task (`to_loop`), ie.
    `M = r * N`, where `r` is a constant (`ratio`).

    This function edits the `flow.xml` file to 'manually' add each
    dependency loop, starting from `start_iter` index until the total
    number of iterations (`n_iter`) are reached.

    Note: This function does not check the current state of the
    `DEPENDS_ON` element. If `ratio = 1` or `n_iter = 1`, then no edits
    will be made, but this does not ensure that there is a 1-to-1
    dependency.

    Parameters:
        flow_file : path to flow file (usually `flow.xml`). Must contain
            at least one `LOOP` with name `to_loop`, which has at
            least one dependency `DEPENDS_ON` element.
        from_loop : name of loop that is the `dep_name` (dependency name)
            and is submitted for every `index`.
        to_loop : path name of loop that will be submitted for every
            `local_index`.
        ratio : ratio of loop iteration between `from_loop` and `to_loop`.
        n_iter : total number of iterations of the `to_loop` (`local_index`).
        start_iter : starting index of first iteration.

    Examples:

    In `flow.xml`, a 1-to-1 loop dependency is written as:

    ```xml
    <!-- input flow.xml -->
    <MODULE name="postproc">
        <SUBMITS sub_name="task_loop" />
        <LOOP name="task_loop">
            <DEPENDS_ON dep_name="/path/to/model_loop" index="model_loop=$((LOOP_INDEX))"
            local_index="task_loop=$((LOOP_INDEX))"
            />
        </LOOP>
    </MODULE>
    ```

    For illustration, use this function to modify the original xml
    with a 2-to-1 loop dependency (one iteration of `task_loop`
    will run after 2 iterations of `model_loop`):

    >>> set_dependency_loop_index_by_ratio('flow.xml',
    from_loop='task_loop', to_loop='/path/to/model_loop', ratio=2, n_iter=3)

    ```xml
    <!-- output flow.xml -->
    <MODULE name="postproc">
        <SUBMITS sub_name="task_loop" />
        <LOOP name="task_loop">
            <DEPENDS_ON dep_name="/path/to/model_loop" index="model_loop=2" local_index="task_loop=1" />
            <DEPENDS_ON dep_name="/path/to/model_loop" index="model_loop=4" local_index="task_loop=2" />
            <DEPENDS_ON dep_name="/path/to/model_loop" index="model_loop=6" local_index="task_loop=3" />
        </LOOP>
    </MODULE>
    ```

    References:
        [1] https://wiki.cmc.ec.gc.ca/wiki/Maestro/dependency
    """
    # Note: an issue was opened to add this feature directly into
    # maestro. The issue has since been addressed and closed, but has
    # not been tested yet by our team. Once confirmed, this function
    # may be greatly simplified if the LOOP_INDEX still needs to be set
    # dynamically.
    # https://gitlab.science.gc.ca/CMOI/maestro/-/issues/423

    #RD: this check should probably be done earlier if it is indeed necessary
    if not float(ratio).is_integer():
        raise ValueError(f'ratio must be integer greater than one, not {ratio}')

    if n_iter < 1:
        raise ValueError(f'n_iter must be integer greater than one, not {n_iter}')
    elif n_iter > 1 or ratio > 1:
        # Note: (n_iter == 1 and ratio == 1) means there's nothing to update

        tree = ElementTree.parse(flow_file)
        root = tree.getroot()

        # find the loop node
        # ensure that there is only one LOOP named loop_name
        target_loop = root.findall(f'.//LOOP[@name="{from_loop}"]')
        if not target_loop:
            raise ValueError(f'malformed flow file {flow_file}; does not contain loop {from_loop}')
        if len(target_loop) > 1:
            raise ValueError(f'malformed flow file {flow_file}; contains more than one loop for {from_loop}')
        target_loop = target_loop[0]  # safe

        # find all nodes in DEPENDS_ON node
        target_dep_nodes = list(target_loop.findall("DEPENDS_ON"))

        # make sure the dep_name for each DEPENDS_ON node matches to_loop
        filtered_nodes = []
        for node in target_dep_nodes:
            if os.path.basename(node.get('dep_name')) == os.path.basename(to_loop):
                filtered_nodes.append(node)

        if not filtered_nodes:
            raise ValueError(f'requested to_loop {to_loop} does not exist in flow file {flow_file}')

        # now that the list is filtered, use the current attribs for the
        # DEPENDS_ON nodes and reconstruct new nodes with modified attribs
        for node in filtered_nodes:

            # get attribs
            index_name = node.get('index').split('=')[0]
            local_index_name = node.get('local_index').split('=')[0]
            tail = node.tail

            # remove node
            target_loop.remove(node)

            # loop to construct new nodes based on original attribs
            for idx,i in enumerate(range(start_iter, n_iter+1)):
                target_index = int(i*ratio)
                target_index_def = f'{index_name}={target_index:d}'
                target_local_index_def = f'{local_index_name}={i:d}'

                # create xml element
                new_dep_node = ElementTree.Element('DEPENDS_ON')
                new_dep_node.set('dep_name', to_loop)
                new_dep_node.set('index', target_index_def)
                new_dep_node.set('local_index', target_local_index_def)
                new_dep_node.tail = tail

                # insert to node
                target_loop.insert(idx, new_dep_node)

        # save updated flow (overwrite)
        tree.write(flow_file)

def set_resources_def(resource_file: str, updates: dict = None):
    """Update parameters in resources.def file"""
    update_env_file(resource_file, updates=updates, key_value_only=True)

def config_node_resource_file(filename: str, resources: dict, aliases: dict = None,
                              max_bytes=None):
    """Set attributes in node resource job file.

    Parameters:
        filename : full filename of `.xml`
        resources : dict of resources to set. See Note [1].
        aliases : mapping of keys in `resources` dict to name of
            attributes allowed in maestro NODE_RESOURCES (key should
            be name in `resources`, value should be name for maestro
            node resource attribute).

    Note:
        [1] the 'memory' resource should be set by total memory (not
        memory per cpu as required by maestro; this will be handled
        internally).

    Examples:

    Given the input file `xml_file`:

    ```xml
    <NODE_RESOURCES><BATCH machine="machine" wallclock="10" /></NODE_RESOURCES>
    ```
    >>> config_node_resource_file(xml_file,
        resources={'amount_of_time': '120', 'memory': '40 g'},
        aliases={'amount_of_time': 'wallclock'})

    Output:
    ```xml
    <NODE_RESOURCES><BATCH machine="machine" wallclock="120" memory="40G" /></NODE_RESOURCES>
    ```
    """
    # note: aliases are used here just so that we can avoid renaming
    # the keys of the input resources dict

    aliases = {} if aliases is None else aliases

    # attributes for NODE_RESOURCES accepted by maestro.
    # use these as a simple check for valid config; if these are
    # variable, suggest to implement a check via `nodeinfo` instead.
    accepted_attributes = MaestroSequencerInterface._NODE_RESOURCE_BATCH_ATTRIBUTES

    try:
        contents = ElementTree.parse(filename)
    except ElementTree.ParseError as e:
        raise Exception(f'malformed resource file: {filename}') from e

    root = contents.getroot()
    if root.tag != 'NODE_RESOURCES':
        # confirm that this is the correct xml contents
        raise ValueError(f'{filename} must begin with a <NODE_RESOURCE> tag')

    batch_node = contents.findall('BATCH')
    if len(batch_node) != 1:
        raise ValueError(f'{filename} must only contain one <BATCH> tag')
    batch_node = batch_node[0]   # safe

    for k, v in resources.items():

        if k in aliases:
            k = aliases[k]

        if k not in accepted_attributes:
            # not permitted in maestro BATCH resource
            continue

        if not v:
            # empty (""), nothing to replace
            # NOTE: not used to "null" in template
            # (TODO also have not tested if empty value in xml
            # works for maestro)
            continue

        # check value of specific attributes
        if k == 'wallclock':
            _maestro_check_wallclock(v)
        elif k == 'memory':
            proc = int(resources.get('processors', 1))
            mpi = bool(int(batch_node.get('mpi', False)))
            v = _imsi_to_maestro_memory_resource(v, processors=proc, unit='G', mpi=mpi, max_bytes=max_bytes)

        batch_node.set(k, v)

    contents.write(filename)

def copy_resources_from_src(src, dst):
    # copy in the structure/files
    if not os.path.exists(dst) or not any(os.scandir(dst)):
        # if doesn't exist or empty
        # dirs_exist_ok will then only ignore parent dir (desired)
        shutil.copytree(src, dst, copy_function=shutil.copy2, dirs_exist_ok=True)
    else:
        # TODO this is the previous behaviour- should this do something different? (raise / recopy?)
        print('resource directory already populated')

def _get_run_chunking(run_dates_dict):
    # run_dates_dict is the dict required to create a SimulationTime
    # object using the from_kwargs method.
    # this could be more explicit (ie only use args needed to generate
    # chunk sizes), but using built in object for now:
    # sim_timers = SimulationTime.from_kwargs(**run_dates_dict)
    chunks = {}
    for timer_name in ['model_submission_job', 'postproc_submission_job']:
        sim_timer = sim_time_factory(run_dates_dict, timer_name)
        chunks[f"n_{sim_timer.chunk_prefix}s"] = sim_timer.NumChunks

    return chunks['n_model_chunks'], chunks['n_postproc_chunks']


def _create_basename_lookup(filelist):
    """Given a list of files (`filelist`), create lookup dictionary
    by filename (keys) to all file paths with the same filename
    (values). Each list is the full path including the original
    basename (with extension). Real/abs paths are not resolved,
    duplicates are preserved.

    Examples:
    >>> _create_basename_lookup(['/path/to/file_a', '/path/to/file_b', 'path/to/another/file_a'])
    {'file_a': ['/path/to/file_a', 'path/to/another/file_a'],
     'file_b': ['/path/to/file_b']}
    >>> _create_basename_lookup(['/path/to/file_a', '/path/to/file_a'])  # duplicates
    {'file_a': ['/path/to/file_a', '/path/to/file_a']}
    """
    basename_lookup = {}
    for f in filelist:
        fname = os.path.splitext(os.path.basename(f))[0]
        if fname in basename_lookup:
            basename_lookup[fname].append(f)
        else:
            basename_lookup[fname] = [f]
    return basename_lookup

def update_experiment_config(path: str, updates: dict = None):
    # append exerpiment variables to end of experiment.cfg
    cfg = os.path.join(path, 'experiment.cfg')
    if not os.path.exists(cfg):
        with open(cfg, 'a') as f:
            pass
    update_env_file(cfg, updates=updates, key_value_only=False)

def generate_maestro_jobname_prefix(s, sep='-') -> str:
    """Generate a jobname prefix start with `s` and ending with `sep`.
    By convention, `s` is usually the "runid" of the job. `sep` is only
    added if `s` does not already end with `sep`.
    """
    if s.endswith(sep):
        return s
    else:
        return f'{s}{sep}'

def config_maestro_from_src(
        src: str, seq_exp_home: str, runid: str, flow_files_lookup: dict,
        dependency_loop_ratio: int = 1,
        dependency_loop_iter: int = 1,
        dependency_loop_adjustments: dict = None,
        resource_def_config: dict = None,
        experiment_def_config : dict = None,
        job_resource_config: dict = None,
        platform_config: dict = None):
    """Configure the maestro experiment resources from templates (source).
    Set the main `flow.xml` files and configure the job node resource
    `.xml` files with requested resources.

    Parameters:
        src : path to maestro experiment template folder that contains
            the template files under a `/resources` folder.
        seq_exp_home : destination for maestro sequencer setup.
        runid : model run ID specified by user (usually corresponds
            to filename of $SEQ_EXP_HOME)
        flow_files_lookup : dict where keys are the name of the maestro
            experiment module and values are paths to the template flow
            files. These template flow files may have any name and will
            be renamed to `flow.xml` in the appropriate destination
            module folder when copied.
        dependency_loop_ratio : int
        dependency_loop_iter : int
        dependency_loop_adjustments : dict
        resource_def_config : where keys are names of a maestro resource
            resource in `resources.def` and values are the desired setting.
        experiment_def_config : where keys are names of a maestro setting
            to update in the experiment.cfg file.
        job_resource_config : nested dict of settings for each maestro
            job, which contains a dict of 'resources' for maestro. eg:
            {'job_name_A' : {'resources': {'wallclock': '120'}}}
    """
    validate_maestro = True
    max_bytes_fallback = 1.87E11   # bytes (= 187000 MB)

    # src / templates
    resources_src_dir = os.path.join(src, 'resources')

    # dst / experiment folder
    modules_dst_dir = os.path.join(seq_exp_home, 'modules')
    resources_dst_dir = os.path.join(seq_exp_home, 'resources')

    dlr = dependency_loop_ratio
    dli = dependency_loop_iter
    dla = dependency_loop_adjustments

    #-- set experiment options (ExpOptions)
    update_experiment_options_file(
        src, seq_exp_home,
        short_name=runid, display_name=runid
        )

    #-- set module flows (flow.xml)
    for module, src_flow_file in flow_files_lookup.items():

        create_experiment_flow_file(src_flow_file, os.path.join(modules_dst_dir, module))

        # special edits as defined in dla for dependency loops
        # (maestro DEPENDS_ON)
        if module in dla:
            # ratio of n loops of different experiment components
            # (see info in set_dependency_loop_index_by_ratio)

            if dlr > 1:
                adjust_flow = os.path.join(modules_dst_dir, module, 'flow.xml')
                for from_loop,to_loop in dla[module].items():
                    set_dependency_loop_index_by_ratio(
                        from_loop=from_loop,
                        to_loop=to_loop,
                        flow_file=adjust_flow,
                        ratio=dlr,
                        n_iter=dli
                        )


    #-- add common experiment variables
    if experiment_def_config:
        update_experiment_config(seq_exp_home, experiment_def_config)

    #-- set common task resources (resources.def)
    copy_resources_from_src(resources_src_dir, resources_dst_dir)

    # made by running copy_resources_from_src (risky?)
    resource_file = os.path.join(resources_dst_dir, 'resources.def')

    set_resources_def(resource_file=resource_file, updates=resource_def_config)

    #-- set specific job node resources (xml NODE_RESOURCES)

    # get all the xml files - use the ones in the dst experiment folder
    # (they have been copied in and now need "updating" with specific
    # configuration)
    taskfiles = glob.glob(os.path.join(resources_dst_dir, '**/*.xml'), recursive=True)

    # the lookup below handles duplicate filenames between different
    # folders. This assumes that the file contents and resources
    # requested are IDENTICAL.
    taskfile_lookup = _create_basename_lookup(taskfiles)

    # configure resources for each job
    #
    # this loop goes over the the jobs defined in the json; this means
    # there can be templates for other jobs/resources that are not
    # explicitly configured through the imsi interface.
    # note: therefore, with this loop over jobs from json, there is no need
    # to explicitly handle (skip) 'container.xml' files
    for name,spec in job_resource_config.items():

        # find corresponding task file
        try:
            taskfiles = taskfile_lookup[name]
        except KeyError:
            # if the job is defined in imsi, then it must exist in
            # maestro defaults -> raise if not
            raise FileNotFoundError(
                    "no corresponding maestro task file found "
                    f"for '{name}' in sequencing_flow; settings "
                    "will not be applied"
                    )

        resources = spec['resources']

        for tf in taskfiles:

            # if the machine is specified in the resources, then
            # it will be used for configuration of the job via
            # config_node_resource_file(). This means we can
            # grab the corresponding max_bytes memory for that machine
            # here.
            # if machine is not set in resources, then it could be
            # defined in the xml resource file itself (or not). this
            # information is only available once the xml file is read
            # (which currently happens inside the next function call),
            # which then makes it clumsy to try to determine the correct
            # max_byte memory from inside.
            # FIXME: instead, set the max_mem in this case to a reasonable
            # guess for now.
            machine_name = resources.get('machine', None)
            if machine_name is None or platform_config is None:
                max_bytes = max_bytes_fallback
            else:
                max_mem = platform_config.get(machine_name, {}).get('resources', {}).get('max_mem_per_node', None)
                if max_mem is None:
                    max_bytes = max_bytes_fallback
                else:
                    max_bytes = parse_memory_string_to_bytes(max_mem, base=10)

            config_node_resource_file(
                tf, resources=resources,
                aliases=MaestroSequencerInterface._NODE_RESOURCE_BATCH_ATTRIBUTE_ALIASES,
                max_bytes=max_bytes
            )

    if validate_maestro:
        validate_maestro_exp(seq_exp_home)

def validate_maestro_exp(seq_exp_home: str):
    """Validate maestro experiment setup using the nodeinfo tool.

    nodeinfo will catch syntax errors, unset global resources, etc.
    """

    resource_dir = os.path.join(seq_exp_home, 'resources')

    # The maestro_cap behaves such that *any* cfg/tsk/xml files in the
    # template folder are copied into the current experiment folder,
    # even if they aren't used in the specified flow.xml. These are
    # generally benign, but will throw non-zero exit status from nodeinfo.
    # The stderr from checking these nodes will start with:
    #     'Unable to get to the specified node'.
    # This can also be triggered for an arbitrary node that that
    # doesn't exist (`nodeinfo -n path/made/up`), but this won't
    # occur in this validation because only the nodes (file structure)
    # that exists in the exp folder is checked.
    err_startswith = 'Unable to get to the specified node'
    nodeinfo_path = _get_exec_fullpath('nodeinfo')
    maestro_env = _set_maestro_env(seq_exp_home)

    allfiles = glob.glob(os.path.join(resource_dir, "**/*"), recursive=True)
    exp_nodes = [os.path.splitext(os.path.relpath(f, start=resource_dir))[0] for f in allfiles if not os.path.basename(f).endswith('def') and not os.path.basename(f) == 'container.xml']

    # there isn't clear/nice way to execute multiple shell commands
    # (avoid shell=True or writing a temporary script), so loop over
    # instead (might be inefficient; look into tempfile)
    for node in exp_nodes:
        cmd = [nodeinfo_path, "-n", node]
        try:
            proc = subprocess.run(cmd, cwd=seq_exp_home, env=maestro_env, capture_output=True)
            proc.check_returncode()
        except subprocess.CalledProcessError as e:
            stdout = proc.stdout.decode().strip()
            stderr = proc.stderr.decode().strip()
            if not stderr.startswith(err_startswith):
                raise ChildProcessError(
                    "Maestro validation error:\nSEQ_EXP_HOME={exp}\nCalled: {cmd}\n{stdout}\n{stderr}".format(
                    exp=seq_exp_home, cmd=' '.join(proc.args),
                    stdout=stdout, stderr=stderr
                    )
                )

def _set_maestro_env(seq_exp_home: str):
    # set environment variables required by maestro - SEQ_EXP_HOME
    maestro_env = os.environ.copy()
    maestro_env['SEQ_EXP_HOME'] = seq_exp_home
    return maestro_env

def _maestro_check_wallclock(duration):
    """Check wallclock value format"""
    if not float(duration).is_integer():
        raise ValueError(f'invalid wallclock value: {duration}')

def _maestro_format_resource_memory(nbytes, unit='G', precision=0, base=2):
    """Take number of bytes `nbytes` and return a string formatted with
    the memory in the units of `unit`. The string can be used for
    configuring maestro resources (xmls).
    """
    unit_map = _get_memory_unit_factors_to_bytes(base)
    cm = nbytes / unit_map[unit]
    return '{cm:.{n}f}{unit}'.format(cm=cm, unit=unit, n=precision)

def _imsi_to_maestro_memory_resource(imsi_memory: str, processors=1, unit='G', precision=0, mpi=False, max_bytes=None):
    """Convert memory specified in imsi (total memory) to maestro
    requirement (memory per cpu/processor).

    Examples:
    >>> _imsi_to_maestro_memory_resource("120GB")
    '120G'
    >>> _imsi_to_maestro_memory_resource("480 GB", processors=240)
    '2G'

    References:
        [1] https://wiki.cmc.ec.gc.ca/wiki/Maestro/sequencer#Batch_System_Resources
        [2] https://portal.science.gc.ca/confluence/display/SCIDOCS/ord_soumet+Usage
    """
    base = 10    # maestro/ord_soumet uses base 10
    nbytes = parse_memory_string_to_bytes(imsi_memory, base=base)

    # FIXME this is not quite right but gets the behaviour
    # we want for now
    if mpi:
        cm_bytes = nbytes / processors    # mem per cpu
    else:
        cm_bytes = nbytes

    if max_bytes is not None:
        # check if cm_bytes exceeds maximum allowed
        # when max is exceeded, maestro will throw an abort in the submission
        # listing that says the memory "maximum possible is 187000MB".
        # note: may need to refactor this section once behaviour of ord_soumet
        # is better understood re: mpi
        if cm_bytes > max_bytes:
            # ord_soumet is base 10
            cm_bytes_fmt = _maestro_format_resource_memory(
                cm_bytes, unit=unit, precision=precision, base=base
                )
            max_bytes_fmt = _maestro_format_resource_memory(
                max_bytes, unit=unit, precision=precision, base=base
                )
            raise ValueError(
                f"memory per cpu ({cm_bytes_fmt}) exceeds maximum allowed ({max_bytes_fmt}); "
                f"check total memory ({imsi_memory}) and processors requested ({processors}). "
                f"(mpi = {mpi})"
                )

    fmt = _maestro_format_resource_memory(cm_bytes, unit=unit, precision=precision, base=base)

    return fmt

def _get_exec_fullpath(program_name: str) -> str:
    # return full path to a maestro executable -> `which`
    pgm = shutil.which(program_name)
    if pgm is None:
        raise FileNotFoundError(
            f"No program '{program_name}' found. For using the maestro "
            "sequencer, maestro-related tools must be available "
            "on your system."
            )
    return pgm

def get_os_time() -> time.struct_time:
    return time.localtime(time.time())

def get_maestro_current_datetime_string() -> str:
    """Generate a string of datetime information for the current date
    and time that can be used by maestro's `expbegin` tool, to the
    nearest minute (`YYYYMMDDhhmm00`).

    Note: while `expbegin` accepts a datetime string up to 14 characters (ie.
    `YYYYMMDDhhmmss`), this function only generates a datetime string
    to the nearest minute (forced to zero).
    """
    t = get_os_time()
    fmt = "%Y%m%d%H%M00"
    dts = time.strftime(fmt, t)
    return dts
