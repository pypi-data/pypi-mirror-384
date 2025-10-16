'''
Generates the shell interface to the modelling system.

In general this means creating a "config" directory with various files that the
model and downstream utilities ingest, such as namelists, and shell_parameters files.
'''
import os
import shlex
import subprocess

import os
import stat

from imsi.config_manager import config_manager as cm
from imsi import shell_interface as si
from imsi.config_manager import config_manager as cm
from imsi.shell_interface.config_hooks_manager import call_hooks
from imsi.utils.general import write_shell_script, write_shell_string
from imsi.utils.dict_tools import recursive_lookup
from imsi.utils.git_tools import ensure_git_config, git_add_all, get_head_hash, repo_has_commits
from imsi.user_interface.ui_utils import freeze_run_configuration

def build_config_dir(
    db: cm.ConfigDatabase, configuration: cm.Configuration, track=True, force=False
):
    """Main composition function to manange the build the config directory with appropriately parsed content"""

    # Unpacking for ease of reuse below.
    # FUTURE reconsider function args and potential coupling
    config_dict = configuration.model_dump()
    component_dict = configuration.components.model_dump()
    sequencing_config = configuration.sequencing.model_dump()
    run_dates = sequencing_config["run_dates"]
    imsi_config_path = configuration.get_unique_key_value("imsi_config_path")
    run_config_path = configuration.get_unique_key_value("run_config_path")
    work_dir = configuration.get_unique_key_value("work_dir")

    # 1. Create config directory structure
    si.shell_interface_utilities.create_config_dirs(
        run_config_path, component_dict.keys(), force=force
    )

    if track:
        # a temporary commit, before contents are added to /config
        has_commits = repo_has_commits(path=run_config_path)
        git_add_all(path=run_config_path)
        subprocess.run(shlex.split('git commit -q -m "tmp" --allow-empty'), cwd=run_config_path)
        base_sha = get_head_hash(run_config_path)

    # 2. shell_parameters files
    # Almost certainly should be done in config_manager, not here.
    # The fact that the db is used here and not elsewhere indicates this.
    # Like the db should only be used in the config not the interfaces, while the
    # configuration itself is used in the interfaces. i.e. the Configuration is the SSOT
    shell_config = si.shell_config_parameters.set_shell_config(
        db.get_config("shell_config"), config_dict
    )

    write_shell_script(
        os.path.join(run_config_path, "shell_parameters"),
        si.shell_config_parameters.generate_shell_parameters(shell_config),
    )

    # 3. Write computational env / compilation files
    # TODO refactor using common writing functions and to more explicitly
    # specify paths etc
    machine_comp_env = {
        configuration.machine.name: configuration.machine.computational_environment
    }
    for k, v in configuration.machine.site.items():
        machine_comp_env[k] = v["computational_environment"]

    basename_prefix = "computational_environment_"
    for m, c in machine_comp_env.items():
        write_shell_script(
            os.path.join(run_config_path, f"{basename_prefix}{m}"),
            si.shell_comp_environment.generate_computational_environment(
                c,
                m,
                compiler_name=configuration.compiler.name,  # !!
            ),
        )

    # write  the computational environment 'controller'
    write_shell_script(
        os.path.join(run_config_path, "computational_environment"),
        si.shell_comp_environment.generate_computational_environment_controller(
            configuration.machine, run_config_path, basename_prefix
        ),
    )

    write_shell_script(
        os.path.join(run_config_path, "compilation_template"),
        si.shell_comp_environment.generate_compilation_template(configuration),
    )

    # 4. Process namelists and cpp/compilation files
    # - take in reference versions ('templates') and modifying them according
    # to changes listed in component_config
    for component, component_config in component_dict.items():
        si.shell_inputs_outputs.process_model_config_files(
            component,
            component_config,
            imsi_config_path,
            run_config_path,
            "compilation",
            shell_config=shell_config,
        )

        si.shell_inputs_outputs.process_model_config_files(
            component,
            component_config,
            imsi_config_path,
            run_config_path,
            "namelists",
            shell_config=shell_config,
        )

    # extract identified utlitity scripts (like compile)
    files_to_extract = configuration.utilities.files_to_extract

    if not files_to_extract:  # backwards compatibility
        files_to_extract = {
            "save_restart_files.sh": "models/save_restart_files.sh",
            "imsi-tmp-compile.sh": "imsi-tmp-compile.sh",
        }
    si.shell_inputs_outputs.extract_utility_files(
        files_to_extract, imsi_config_path, work_dir
    )

    # 5. Write shell scripts for use in pre/post ludes
    # FUTURE Could split this by component and join with above for loop
    # input files (prelude)
    write_shell_script(
        os.path.join(run_config_path, "imsi_get_input_files.sh"),
        si.shell_inputs_outputs.generate_input_script_content(
            component_dict, shell_config
        ),
    )
    # directory packing in postlude
    write_shell_script(
        os.path.join(run_config_path, "imsi_directory_packing.sh"),
        si.shell_inputs_outputs.generate_directory_packing_content(component_dict),
    )
    # final saving in postlude
    write_shell_script(
        os.path.join(run_config_path, "imsi_save_output_files.sh"),
        si.shell_inputs_outputs.generate_final_file_saving_content(component_dict),
    )

    # 6. Write diag_parameters
    diag_config = config_dict["postproc"]
    write_shell_script(
        os.path.join(run_config_path, "diag_parameters"),
        si.shell_diag_parameters.generate_diag_parameters_content(diag_config),
    )

    # 7. Generate a file with the model run command
    output_path = os.path.join(run_config_path, "imsi-model-run.sh")
    run_commands = list(recursive_lookup('model_run_commands', sequencing_config))[0]
    write_shell_string(output_path, run_commands, make_executable=True)

    # 8. Write timing files
    si.shell_timing_vars.validate_timers_config(run_dates)
    write_shell_script(
        os.path.join(run_config_path, 'model_submission_job_start-stop_dates'),
        si.shell_timing_vars.generate_timers_config(run_dates,'model_submission_job')
        )

    write_shell_script(
        os.path.join(run_config_path, 'model_inner_loop_start-stop_dates'),
        si.shell_timing_vars.generate_timers_config(run_dates,'model_inner_loop')
        )

    write_shell_script(
        os.path.join(run_config_path, 'postproc_submission_job_start-stop_dates'),
        si.shell_timing_vars.generate_timers_config(run_dates,'postproc_submission_job')
        )

    # 9. call config_hooks:config
    # (constraints checked from configuration)
    call_hooks(configuration, "config", force=force)

    # 10. cp resolved configuration into /config
    freeze_run_configuration(configuration)

    # finally:
    if track:
        # create the final commit by resetting to the original hash
        # and amending *that* commit. this ensures that there is only
        # a single commit by the end of this function.
        # note: pass the path explicitly incase any of the hooks cwd
        subprocess.run(shlex.split(f'git reset -q --soft {base_sha}'), cwd=run_config_path)
        git_add_all(path=run_config_path)
        ensure_git_config()
        subprocess.run(shlex.split('git commit -q --amend -m "IMSI: config" --allow-empty'), cwd=run_config_path)

        # check if the most recent commit was empty. if so, we want
        # to revert to prev commit (and only if there is more than one
        # commit)
        proc = subprocess.run(shlex.split('git diff-tree --quiet HEAD'), cwd=run_config_path, capture_output=True)
        if proc.returncode == 0 and has_commits:
            subprocess.run(shlex.split('git reset -q --hard HEAD~1'), cwd=run_config_path)
