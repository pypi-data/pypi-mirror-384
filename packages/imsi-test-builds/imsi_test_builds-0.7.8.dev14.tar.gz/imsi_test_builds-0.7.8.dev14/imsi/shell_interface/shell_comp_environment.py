import copy
import collections
import os
import textwrap
from typing import List

from imsi.config_manager.config_manager import Configuration, Machine
from imsi.utils.dict_tools import flatten

# FUTURE: consider
# - a template in the imsi input jsons rather than (implicitly) constructing a
# template through code below.
# - moving some steps up to config_manager to resolve config

def generate_computational_environment(comp_env: dict, machine_name, compiler_name: str = None) -> List[str]:
    """Generate content of a file that can be sourced in a shell
       to set the computational environment for compiling and running the model.

       Here we just generate and return a list of strings, that will be written
       to file elsewhere using a common tool.
    """
    comp_env_content = list()

    # Note: order of keys is important (Ordereddict might be necessary) because they
    # represent the order of shell vars/commands
    comp_env_content.append("# Imsi created model environment file for compiling and running\n")
    comp_env_content.append(f"# Created for {machine_name}\n")

    # modules
    #

    # The below code combines the module actions under "all" with those under the specific
    # compiler being used and writes these out to the file.
    # It is important NOT to change the order of the keys below, as module command
    # order is important.
    # ---
    # TODO This is definitely a "configuration" step, not an interface step!
    if compiler_name in comp_env["modules"]:
        module_config_compiler = comp_env["modules"][compiler_name]
    else:
        module_config_compiler = {}

    module_config = comp_env["modules"]["all"]
    if module_config:
        # Surely there is a better way than this V!
        # Combine the lists of keys, strictly preserving the order of the
        # all keys list. Normally I would use a set() if order was not important.
        compiler_keys = list(module_config_compiler.keys())
        all_keys = list(module_config.keys())
        for k in all_keys:
            if k in compiler_keys:
                compiler_keys.remove(k)
        module_cmd_keys = all_keys + compiler_keys
        # Here we append the strings together.
        # Note that this is purely additive.
        if module_cmd_keys:
            comp_env_content.append("\n# Module definitions")
        for modcmd in module_cmd_keys:
            argstr = ""
            if modcmd in module_config_compiler.keys():
                argstr += " ".join(module_config_compiler[modcmd])
            if modcmd in module_config.keys():
                argstr += " " + " ".join(module_config[modcmd])
            comp_env_content.append(f"module {modcmd} {argstr}")

    #
    # environment variables
    #
    comp_env_content.append("\n# Environment variables")
    env_variable_config = comp_env["environment_variables"]["all"]
    for k, v in env_variable_config.items():
        comp_env_content.append(f"export {k}={v}")

    #
    # environment commands
    #
    comp_env_content.append("\n # Environment commands")
    env_command_config = comp_env["environment_commands"]["all"]

    # script contents
    for k, v in env_command_config.items():
        comp_env_content.append(f"{k} {v}")

    return comp_env_content


def generate_computational_environment_controller(
        machine_config: Machine, run_config_path: str, basename_prefix: str = None) -> List[str]:
    """Generate the contents of the computational environment 'controller' file.

    The controller is a passthrough shell file that simply sources the correct
    computational_environment file for the machine at runtime. It does so
    by matching the hostname of the current machine (via regex) to the machine
    name (used in imsi config). Both the regex and machine name are known from
    upstream config and supplied via the `machine_config` (instance of `Machine`).
    The file that is sourced is then: `{run_config_path}/{basename_prefix}_{machine name}`.

    Parameters:
        machine_config: Machine
            machine configuration object
        run_config_path: str
            path to run config folder (usually `{runid}/config`)
        basename_prefix: str
            file basename prefix for file names to source.

    Returns:
        contents of the controller file, a list of strings (lines)
    """
    if basename_prefix is None:
        basename_prefix = "computational_environment_"

    # map machine name -> host name regex
    machine_name = machine_config.name
    machine_host_lookup = {machine_name: machine_config.nodename_regex}
    machine_host_lookup |= {k:v['nodename_regex'] for k,v in machine_config.site.items()}

    # regex transform for for shell case statement
    machine_host_lookup_shell = {k:v.replace('.*', "*") for k,v in machine_host_lookup.items()}

    # case block - options
    CASE_OPTION_TEMPLATE = """{cs})\n    COMP_ENV_MAC="{machine}"\n    ;;"""
    case_options = [
        textwrap.indent(CASE_OPTION_TEMPLATE.format(cs=r, machine=m), " " * 4)
        for m, r in machine_host_lookup_shell.items()
    ]

    # case block - full
    CASE_BLOCK_TEMPLATE_l = (
        ["case $HOSTNAME in"]
        + case_options
        + ['    *)', '        >&2 echo "Unknown machine for $HOSTNAME"', "exit 1", "        ;;", "esac;"]
    )

    # full script
    filename_template = os.path.join(run_config_path, f'{basename_prefix}$COMP_ENV_MAC')
    script_contents = (
        ['#!/bin/bash', 'HOSTNAME=$( hostname )']
        + CASE_BLOCK_TEMPLATE_l
        + [f'source {filename_template}']
    )

    return script_contents

def generate_compilation_template(configuration: Configuration):
    """Generate the compilation_template file contents based on a Configuraiton instance

    Here we just generate and return a list of strings, that will be written
    to file elsewhere using a common tool.
    """
    machine_name = configuration.machine.name
    compiler_name = configuration.compiler.name
    compiler_config = copy.deepcopy(configuration.compiler.model_dump())
    comp_env_content = list()

    comp_env_content.append("# Imsi created model environment file for compilation\n")
    comp_env_content.append(f"# Created for the compiler: {compiler_name} on machine: {machine_name}\n")
    comp_env_content.append("# Compiler flag options")
    for language, lang_config in compiler_config.items():
        comp_env_content.append(f'\n#{language} options')
        if isinstance(lang_config, collections.abc.MutableMapping):
            flat_lang_config = flatten(lang_config)
            for k,v in flat_lang_config.items():
                if isinstance(v, list):
                    argstr=' '.join(v)
                else:
                    argstr=v
                comp_env_content.append(f'{k}={argstr}')
    return comp_env_content

if __name__ == "__main__":
    pass