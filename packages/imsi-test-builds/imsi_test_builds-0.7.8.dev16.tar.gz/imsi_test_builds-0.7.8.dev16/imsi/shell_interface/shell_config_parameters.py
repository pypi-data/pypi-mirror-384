# Pure test to see if we can use the config_manager to do something.
# i.e. create a way to use the config manager in downstream utilities

import copy

from imsi.tools.time_manager.time_manager import sim_time_factory, SimStartStop
from imsi.utils.dict_tools import flatten, replace_curlies_in_dict
from imsi.utils.general import get_date_string


def set_shell_config(shell_config_template: dict, full_config_dict: dict) -> dict:
    """
    Set shell parameters based on shell_config.yaml and internal imsi variables

    Parameters:
        shell_config_template : dict
            A template of the shell config, from the database (contains {{}} enclosed strings to be replaced)

        full_config_dict : dict
            The full configuration as a single dictionary, which will be searched for key=value in order to
            do the replacements in the template above
    """
    # This should possibly be in the config_manager, as technically it is setting a config, not
    # just creating the shell interface. On the other hand, this is pretty specific to the
    # parameters required by shell downstream. More generall the broader
    # use of templates (beyond just shell_config) could be explored. Implicitly other "shell_" functions
    # are defining a type of template (e.g. for computational_env), but `shell_config` is the
    # only template explicitly defined in the imsi upstream configuration database.

    # This provides a general way to create a shell parameters file, built up from variables
    # defined somewhere in the imsi configuration. Its reliance on unique keys could be problematic, and the parsing
    # might lead to issues. Works in basic testing, however the robustness will need to be assessed in the wild.
    # Since we will set shell_config below, we need to first clear it, because it might already contain info
    # raw mapping of imsi to shell variables defined in shell_config.yaml
    # i.e. raw_shell_config is a template, containing {{var}}, where <var> is to be replaced
    raw_shell_config = copy.deepcopy(shell_config_template)
    full_config_dict = copy.deepcopy(full_config_dict) # avoid accidentally modifying upstream mutable dict

    sequencing_config = full_config_dict.get('sequencing')
    local_shell_config = {} # tmp structure to collect replacements
    # For each line of the template, look for {{variable}} to be replaced.
    local_shell_config = replace_curlies_in_dict(raw_shell_config, full_config_dict)

    # This adds selected information from each component to the list of shell parameters, include exe names and MPI sizes.
    # Having this accessing of the values inside the dict reflects substantial coupling!
    for component, component_config in full_config_dict['components'].items():
        if "exec" in component_config.keys():
            local_shell_config[f'{component}_EXEC'] = component_config["exec"]
        if "resources" in component_config.keys():
            # assumes both mpiprocs and ompthreads are present
            local_shell_config[f'{component}_MPIPROCS'] = component_config["resources"]["mpiprocs"]
            local_shell_config[f'{component}_OMPTHREADS'] = component_config["resources"]["ompthreads"]
        if "config" in component_config.keys():
            local_shell_config[f'{component}_CONFIG'] = component_config["config"]
        if "env_params" in component_config:
            local_shell_config.update(component_config["env_params"])

    # Use the time_manager module to get detailed timers for insertion into shell_parameters
    for timer in ['model_submission_job', 'model_inner_loop', 'postproc_submission_job']:
        sim_timer = sim_time_factory(sequencing_config['run_dates'], timer)
        tvars = sim_timer.shell_formatted_time_vars()
        local_shell_config.update(tvars)

    sim_start_stop = SimStartStop.from_kwargs(**sequencing_config['run_dates'])
    tvars = sim_start_stop.shell_formatted_time_vars()
    local_shell_config.update(tvars)

    return local_shell_config


def generate_shell_parameters(shell_config: dict):
    """
    This creates a shell_parameters file contents for the simulation, that contains
    variable definitions required by downstream shell scripting. What appears in
    this file is defined by the "shell_config" template in the imsi json.

    Here we just generate and return a list of strings, that will be written
    to file elsewhere using a common tool.
    """
    shell_config = copy.deepcopy(shell_config)

    shell_parameters_content = list()
    shell_parameters_content.append("# Imsi created shell environment file\n")
    for k, v in shell_config.items():
        shell_parameters_content.append(f'export {k}="{v}"')
    return shell_parameters_content


def generate_flattened_config(full_config_dict: dict):
    """
    This creates a far more extenives shell parameters file content for the simulation, that contains
    every variable defined in the imsi configuration.

    The idea is not to practically use this, but to demonstrate it could be possible
    to make a clean break and do anything in shell downstream of this.

    Here we just generate and return a list of strings, that will be written
    to file elsewhere using a common tool.
    """
    flattened_config = flatten(copy.deepcopy(full_config_dict))
    flattened_config_contents = list()

    flattened_config_contents.append("# Imsi created file\n")
    datestr = get_date_string()
    #f.write(f"# Created for the compiler: {self.compiler} on machine: {self.machine} on date: {datestr}\n")
    for k,v in flattened_config.items():
        flattened_config_contents.append(f'export {k}={v}')

    return flattened_config_contents
