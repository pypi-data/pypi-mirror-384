"""
A collection of 'hooks' (functions) that can be called by imsi.

Mainly designed to be executed with config_hooks_manager.py

Functions are named using the following convention:

    {imsi_step}_{further description}

While naming convention is useful for organization, it is left to the
developer to name and call these functions appropriately.
"""

import os
import subprocess

from imsi.config_manager.config_manager import Configuration
from imsi.shell_interface.shell_config_parameters import generate_shell_parameters
from imsi.utils.general import write_shell_script

def config_postproc_netcdf_conversion(configuration: Configuration, force=False):
    """Configuration for netcdf conversion (ncconv) metadata via pop_nc_tables.

    While netcdf conversion occurs as a post-processing step, configuring
    the metadata required can be done upstream.
    """

    def _get_imsi_config_for_netcdf_conversion():
        # get configuration sections/parameters required for ncconv config

        # from setup_params
        setup_config = {
            "WRK_DIR": configuration.setup_params.work_dir,
            "runid": configuration.setup_params.runid,
        }

        # from model/experiment - required metadata
        wanted_model_keys = ['source_id', 'variant_id']
        wanted_experiment_keys = [
            'activity_id', 'experiment_id', 'parent_branch_time', 'parent_runid', 'subexperiment_id'
            ]

        model_config = dict(
            (k, configuration.model.model_dump()[k])
            for k in wanted_model_keys
        )
        experiment_config = dict(
            (k, configuration.experiment.model_dump()[k])
            for k in wanted_experiment_keys
        )
        # merge model and experiment config
        # into a single dictionary
        modex_config = {**model_config, **experiment_config}

        # from sequencing - time params
        rundt = configuration.sequencing.model_dump()['run_dates']
        seq_config = {
            'run_start_time': rundt['run_start_time'],
            'run_stop_time': rundt['run_stop_time']
        }

        # from postproc netcdf_conversion - processing info / metadata

        ncconv_config = configuration.postproc.netcdf_conversion

        configout = {
            "setup_params": setup_config,
            "modex": modex_config,
            "sequencing": seq_config,
            "postproc": ncconv_config,
        }

        return configout

    SRC_PATH = configuration.setup_params.source_path  # /src -> /CanESM super-repo
    pop_nc_tables_exec = os.path.join(SRC_PATH, 'CCCma_tools', 'scripts', 'comm', 'pop_nc_tables')

    #--------------------
    # get config
    #--------------------

    config_for_ncconv = _get_imsi_config_for_netcdf_conversion()

    # merge all config together
    # **CAUTION** the insertion ORDER MATTERS of the parameters
    # (key-value in ncconv_shell_config) for when the shell file
    # is sourced downstream (ie variable interpolation)
    # FIXME not ideal beacause the string interpolation within imsi config
    # could change and then this could be mangled.
    # For now, at least keep this outside of the subfunction.
    ncconv_shell_config = {'SRC_PATH': SRC_PATH}
    ncconv_shell_config.update(config_for_ncconv['setup_params'])
    ncconv_shell_config.update(config_for_ncconv['modex'])
    ncconv_shell_config.update(config_for_ncconv['sequencing'])
    ncconv_shell_config.update(config_for_ncconv['postproc'])

    # renaming (imsi -> config-canesm)
    # this is required because the pop_nc_tables script expects certain
    # variable names (originally developed for config-canesm tooling)
    aliases = {
        'ncconv_exptab_src': 'ncconv_exptab_repo',
        'ncconv_exptab_commit': 'ncconv_exptab_cmmt',
        'ncconv_commit': 'ncconv_cmmt',
        'ncconv_exptab_commit': 'ncconv_exptab_cmmt'
    }

    ncconv_shell = {}
    for k,v in ncconv_shell_config.items():
        k = aliases[k] if k in aliases else k
        ncconv_shell[k] = v

    force_arg = "true" if force else "false"

    #--------------------
    # write shell file
    #--------------------
    shfile_path = os.path.join(
        configuration.get_unique_key_value('run_config_path'),'ncconv_shell_parameters'
        )

    write_shell_script(shfile_path, generate_shell_parameters(ncconv_shell), mode='w')

    #--------------------
    # call executable
    #--------------------
    # final check for args passed to pop_nc_tables (redundant)
    if not all([os.path.exists(shfile_path), os.path.exists(SRC_PATH)]):
        raise FileNotFoundError("can't execute pop_nc_tables")

    try:
        # pop_nc_tables args:
        #    config  -  config file that containin configuration params (shell)
        #    srcdir  -  source repo location (source code)
        proc = subprocess.run(
            [pop_nc_tables_exec, f'config={shfile_path}', f'srcdir={SRC_PATH}', f'force={force_arg}']
            )
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        raise ChildProcessError("Failed call: {cmd}\n{err}".format(cmd=' '.join(proc.args), err=proc.stderr))
