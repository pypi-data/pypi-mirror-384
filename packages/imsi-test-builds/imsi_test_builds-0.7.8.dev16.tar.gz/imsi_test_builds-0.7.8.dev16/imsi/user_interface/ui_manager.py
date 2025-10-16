import os
import glob
import copy
from typing import Dict
import subprocess
from pathlib import Path
import shlex
from omegaconf import OmegaConf

from imsi.utils.git_tools import is_repo_clean
from imsi.config_manager import config_manager as cm
from imsi.shell_interface import shell_interface_manager
from imsi.utils.dict_tools import parse_vars, update, load_json
from imsi.user_interface.ui_utils import save_setup_configuration, load_run_config
from imsi.sequencer_interface.sequencers import create_sequencer
from imsi.shell_interface.config_hooks_manager import call_hooks
from imsi import __version__

def validate_version_reqs(source_config_path: Path = Path("src/imsi-config"), version_req_file: str = "version_requirements.yaml" ):
    """
    Checks the version requirements contained in the version controlled
    config files.

    The imsi minor version is toggled when there are config breaking changes, as such we
    only require the major and minor version match.

    TODO:
        - update output to better inform users on how to find/build the right environments
    """
    path_to_version_req_file = source_config_path/version_req_file
    current_version_no_patch = ".".join(__version__.split(".")[:2])

    # check that req file exists
    if not path_to_version_req_file.exists():
        raise ValueError(f"{path_to_version_req_file} doesn't exist! This is likely because your repo hasn't been setup"
                         f" to work with {current_version_no_patch}. Please update your config files or use an older version of imsi.")

    required_version = OmegaConf.load(path_to_version_req_file)["imsi_version_requirements"]

    # confirm major/minor version match
    if current_version_no_patch != required_version:
        raise ValueError(
            f"""IMSI VERSION MIS-MATCH! Your source repo's config files are setup to use
                -> {required_version}.* <-
            But you are using
                -> {__version__} <-
            The Major and Minor version must match!

            See https://imsi.readthedocs.io/en/main/config_breaking_changes.html for more information"""
        )

def create_imsi_configuration(
    imsi_config_path: str, setup_params: Dict
) -> (cm.Configuration, cm.ConfigDatabase):
    """Build and return configuration instance and config db given imsi_config_path"""
    if not os.path.isdir(imsi_config_path):
        raise FileNotFoundError(
            f"Could not find imsi config directory at: {imsi_config_path}"
        )

    # create a DB / cm
    db = cm.database_factory(imsi_config_path)
    config_manager = cm.ConfigManager(db)

    configuration = config_manager.create_configuration(**setup_params)
    # Save the configuration for future editing/reference
    save_setup_configuration(configuration, save_config=True)

    # Create a configuration based on user input from setup cli
    return (configuration, db)


def build_run_config_on_disk(
    configuration: cm.Configuration, db: cm.ConfigDatabase, track=True, force=False
):
    """This actually creates the physical config directory on disk, and extracts/modifies various relevant files"""
    # Build the actual config directory with contents for this configuration

    shell_interface_manager.build_config_dir(db, configuration, track=track, force=force)

    # Do scheduler/sequencer setup
    sequencer = create_sequencer(configuration.setup_params.sequencer_name)
    sequencer.setup(configuration, force=force)
    sequencer.config(configuration, force=force)

    # Do other config hooks (only if constraints are met as defined in current
    # config, which will be checked via call_hooks)
    call_hooks(configuration, "post-config", force=force)

    if track:
        run_config_path = configuration.get_unique_key_value('run_config_path')
        # hooks may have changed contents of config folder - track these
        clean, _ = is_repo_clean(run_config_path)
        if not clean:
            subprocess.run(shlex.split('git add -A'), cwd=run_config_path)
            subprocess.run(shlex.split('git commit -q -m "IMSI: config_hooks:post-hook"'), cwd=run_config_path)


def reload_config_from_source(force=False):
    """
    Build a new config directory from upstream imsi source

    This will re-extract everthing out of the cloned repository to re-create
    the config directory. I.e. if one made changes in the repo after setup, and
    wanted to apply them, they would call this update function.
    """
    original_configuration = load_run_config()

    # This will rebuild the config directory completely
    imsi_config_path = original_configuration.get_unique_key_value("imsi_config_path")
    new_configuration, db = create_imsi_configuration(
        imsi_config_path,
        original_configuration.setup_params.model_dump(),
    )
    build_run_config_on_disk(new_configuration, db, force=force)


def update_config_from_state(force=False):
    """Apply changes made in the "imsi_configuration_${runid}" state file
    to the configuration and update the config directory as appropriate.
    """
    # 1. Save configuration from the configuration object to .imsi...
    # 2. Load the configuration from the .imsi... file

    user_facing_configuration = load_run_config(serialized=False)

    save_setup_configuration(user_facing_configuration, save_config=False) # no need to instantly save again
    state_configuration = load_run_config()
    # This will rebuild the config directory completely based on what is in the configuration file.
    # It would be good if there were nominal validity testing.
    db = cm.database_factory(
        state_configuration.get_unique_key_value("imsi_config_path")
    )
    build_run_config_on_disk(state_configuration, db, force=force)

def set_selections(parm_file=None, selections=None, options=None, force=False):
    """Parse key=value pairs of selection given on the command line
    Try to apply these to the imsi selections for the sim.
    """
    # This function should be split to respect SRP
    print(f"set selections: {selections}")
    # get existing simulation config
    configuration = load_run_config()
    # This will rebuild the config directory completely based on what is in the configuration file.
    # It would be good if there were nominal validity testing.
    db = cm.database_factory(configuration.get_unique_key_value("imsi_config_path"))
    config_manager = cm.ConfigManager(db)

    updated_setup_params = copy.deepcopy(configuration.setup_params)

    if parm_file:
        file_values = load_json(
            parm_file
        )  # would actually be more valuable for options I think, since
        # selections are few bu options possibly many.
        # This is updating the ._config dict in place
        updated_setup_params = update(updated_setup_params, file_values)
    if selections:
        values = parse_vars(selections)
        setup_params = configuration.setup_params

        # selections must match imsi setup cli options to match parts of config
        # (some but not all allowed)
        updated_setup_params.model_name = values.pop('model', setup_params.model_name)
        updated_setup_params.experiment_name = values.pop('exp', setup_params.experiment_name)
        updated_setup_params.machine_name = values.pop('machine', setup_params.machine_name)
        updated_setup_params.compiler_name = values.pop('compiler', setup_params.compiler_name)
        updated_setup_params.sequencer_name = values.pop('sequencer', setup_params.sequencer_name)
        updated_setup_params.flow_name = values.pop('flow', setup_params.flow_name)
        updated_setup_params.postproc_profile = values.pop('postproc', setup_params.postproc_profile)

        # warn for bad selections, and don't add them to setup params
        # TODO: would be better to do this via cli (early)
        for k,v in values.items():
            print(f"**WARNING**: selection '{k}={v}' not in setup params; not added to configuration")
        print(updated_setup_params)

    # Create a new simulation that we imbue with these properties
    new_configuration = config_manager.create_configuration(**updated_setup_params.model_dump())

    if options:
        options_config = db.get_config("model_options")
        selected_option_names = parse_vars(options)
        new_configuration = apply_options(
            options_config, configuration, selected_option_names
        )

    # Update the saved configuration file accordingly
    # (including triggering rebuilding of /sequencer folder too, running
    # hooks, etc):
    build_run_config_on_disk(new_configuration, db, force=force)

    # Update the saved configuration file accordingly
    save_setup_configuration(new_configuration, save_config=True)

def apply_options(
    options_config: Dict, configuration: cm.Configuration, selected_option_names: Dict
) -> cm.Configuration:
    """
    Take a set of options or 'patches' and apply them to the simulation configuration and
    return an updated configuration.

    Input:
    ------
    selected_options : dict
       k-v pairs of option name and selection
    """
    # Check first the option is valid
    for option, selection in selected_option_names.items():
        if option in options_config.keys():
            if selection in options_config[option].keys():
                for target_config, target_values in options_config[option][
                    selection
                ].items():
                    # Add to list of applied options
                    # self.options[option] = selection
                    # Set the options in the simulations internal state
                    new_config_dict = configuration.model_dump()
                    update(new_config_dict[target_config], target_values)
                print(f"Updated {option} with {selection}")
            else:
                raise ValueError(
                    f"\n**ERROR**: there is no valid selection {selection} under the option named {option}. "
                    + f"Available selections are {list(options_config[option]['options'].keys())}"
                )
        else:
            raise ValueError(
                f"\n**ERROR**: there is no option named {option}. Available options are {list(options_config.keys())}"
            )
        return cm.Configuration(**new_config_dict)



# I think this is not a bad idea. But the way it SHOULD be implemented is as
# an abtract interface, with specific implementations (so support different models).
# Also, this is a utility, which should not be mixed directly with the core configuration
# classes.
def compile_model_execs(args):
    """
    Builds all component executables by calling an upstream script from the
    repository. Pretty rough go. Is it useful abstracting this in imsi TDB.
    """
    configuration = load_run_config()
    work_dir = configuration.get_unique_key_value("work_dir")
    if not os.path.isdir(work_dir):
        raise FileNotFoundError(
            f"Could not find the run working directory at: {work_dir}"
        )

    comp_script_basename = 'imsi-tmp-compile.sh'
    comp_script = os.path.join(work_dir, comp_script_basename)

    if not os.path.exists(comp_script):
        raise FileNotFoundError(
            f"Could not find compilation file {comp_script_basename} at: {work_dir}"
        )
    compile_task = subprocess.Popen([os.path.join('.', comp_script_basename)] + list(args), cwd=work_dir)
    compile_task.wait()
    streamdata = compile_task.communicate()[0]
    rc = compile_task.returncode
    if rc != 0:
        raise ValueError(f"Error: Compiling failed with {comp_script}")


def submit_run():
    """Instantiate the configuration object and submit job to queue"""
    configuration = load_run_config()
    setup_params = configuration.setup_params
    sequencer = create_sequencer(setup_params.sequencer_name)
    sequencer.submit(configuration)


def save_restarts(args):
    """Execute the save restarts script"""

    if Path("./save_restart_files.sh").exists():
        p = subprocess.Popen(["./save_restart_files.sh"] + list(args))
        p.wait()
    else:
        raise FileNotFoundError(
            "Could not find the save_restart_files.sh script. Are you in the correct directory?"
        )


def get_sequencer_status():
    configuration = load_run_config()
    setup_params = configuration.setup_params
    sequencer = create_sequencer(setup_params.sequencer_name)
    sequencer.status(configuration, setup_params)


# WIP
def query_time():
    """Instantiate the configuration / SimulationTime instances and enable querying timers"""
    configuration = load_run_config()
    sequencing_config = configuration.sequencing
