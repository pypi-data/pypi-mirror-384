import os
from typing import List, Dict
import shutil
from pathlib import Path
from imsi.utils.dict_tools import replace_variables
from imsi.utils import nml_tools
from imsi.utils.general import is_path

def process_model_config_files(component: str, component_config: dict,
                               imsi_config_path: str, run_config_path: str,
                               file_type: str, shell_config: dict):
    """Process namelist and compilation files for all component defined in component_config

      Does replacements of {{}} variables using shell_config inputs
      Updates reference files from "ref_file_path" with "file_content"
    """
    config_path = os.path.join(run_config_path, component)

    # For backwards compatibility
    if file_type == 'compilation':
        dirname='compilation'
    else:
        dirname=file_type

    if not component_config or not file_type in component_config:
        # TODO silently skip making subfolders and further steps (no content
        # to process)
        # for now, create the subfolders for consistency
        os.makedirs(os.path.join(config_path, dirname), exist_ok=True)
        return
    if "config_dir" not in component_config:
        raise KeyError(f'"config_dir" missing from configuration for model component {component}')

    # make the subfolders for the components required
    os.makedirs(os.path.join(config_path, dirname), exist_ok=True)

    # There is a bit of configuration by convention here.
    component_config_path = os.path.join(
        imsi_config_path, component_config["config_dir"]
    )

    for file_name, file_content in component_config[file_type].items():
        ref_file_path = os.path.abspath(os.path.join(component_config_path, file_name))
        if not os.path.exists(ref_file_path):
            raise FileNotFoundError(f"Can't find template file {file_name} in {component_config_path}")

        target_file_path = os.path.join(config_path, dirname, os.path.basename(file_name))

        if file_content:
            print(f"Updating {file_type}: {os.path.basename(file_name)}")
            if file_type == 'compilation':
                process_cpp_file(ref_file_path, target_file_path, file_content)
            elif file_type == 'namelists':
                process_namelist_file(ref_file_path, target_file_path, file_content, shell_config)
            else:
                shutil.copyfile(ref_file_path, target_file_path)
        else:
            shutil.copyfile(ref_file_path, target_file_path)


def process_cpp_file(ref_file_path, target_file_path, file_content):
    """Process cpp files
    Updates default cpp files from ref_file_path with "file_content"
    """
    nml_tools.cpp_update(ref_file_path, target_file_path, file_content)


def process_namelist_file(ref_file_path, target_file_path, file_content, shell_config):
    """Process namelist files
       Does replacements of {{}} variables using shell_config inputs
       Updates default namelists from ref_file_path with "file_content"
    """
    file_content = replace_variables(file_content, shell_config)
    nml_tools.nml_update(ref_file_path, target_file_path, file_content)


def add_atmos_forcing_preamble(component_config, script_content):
    #ocean only runs require a specification of the atmos forcing files
    #we add some logic to make sure imsi_get_input_files.sh pulls the correct ones

    #Add the forcing variables to the input file script
    for key, value in component_config['forcing']['atmos_forcing'].items():
        script_content.append(f"{key}={value}")

    #The current year, relative to the start time of entire simulation:
    script_content.append("yearca=$(( job_start_year - run_start_year + 1 ))")

    #The size of the forcing loop, in years:
    script_content.append("yd=$(( iaf_loop_year - iaf_year_offset ))")

    #The forcing years. yd is added to yearca-1 to prevent negative values in fylm1 (year 1, e.g.)
    # which the modulo operator does not convert to positive values in shell arithmatic
    script_content.append("fyl=$(( iaf_year_offset + 1 + (yd+yearca-1)%yd ))")
    script_content.append("fylp1=$(( iaf_year_offset + 1 + (yd+yearca)%yd ))")
    script_content.append("fylm1=$(( iaf_year_offset + 1 + (yd+yearca-2)%yd ))")

    #Pad the forcing years with zeros like NEMO expects:
    script_content.append("forcing_year=$(echo ${fyl} | awk  '{printf \"%04d\",$1}')")
    script_content.append("forcing_year_plus1=$(echo ${fylp1} | awk  '{printf \"%04d\",$1}')")
    script_content.append("forcing_year_minus1=$(echo ${fylm1} | awk  '{printf \"%04d\",$1}')")


def generate_input_script_content(component_dict: dict, shell_config: dict) -> List[str]:
    """Generate content for the input files script (to be called at runtime with access' etc)"""
    script_content = ["# Imsi created input file", "# Obtain executables and namelists"]

    for component, component_config in component_dict.items():
        if component_config:
            script_content.append(f'# Obtaining {component} inputs')

            # Obtain namelists
            component_namelist_dir = os.path.join(shell_config['WRK_DIR'], 'config', component, 'namelists')
            if "namelists" in component_config:
                for namelist in component_config['namelists'].keys():
                    component_namelist_path = Path(component_namelist_dir) / Path(namelist).name
                    script_content.append(f"cp {component_namelist_path} .")

            # Obtain executables
            if "exec" in component_config:
                component_exe_path = os.path.join(shell_config['EXEC_STORAGE_DIR'], component_config["exec"])
                script_content.append(f"cp {component_exe_path} .")

            if 'forcing' in component_config:
                if 'atmos_forcing' in component_config['forcing']:
                    add_atmos_forcing_preamble(component_config, script_content)

            # Obtain files listed in component 'input_files' config
            if 'input_files' in component_config:
                for k, v in component_config['input_files'].items():
                    if not v:
                        raise ValueError(f"\n ** No input file is specified for the required input {k} by component {component}. \n\n")
                    if is_path(v):
                        # a path has been given.. use link
                        script_content.append(f"ln -s {v} {k}")
                    else:
                        # as base filename as been given.. assume its being routed through a database
                        script_content.append(f"access {k} {v}")

    return script_content


def generate_directory_packing_content(component_dict: dict) -> List[str]:
    """Generate directory packing commands based on content in an imsi "components" config, to be called post model run"""
    packing_content = ["\n# Imsi created directory packing list"]

    for component, component_config in component_dict.items():
        if component_config and 'directory_packing' in component_config:
            packing_content.append(f'# Directory packing for: {component}')
            for target_dir, source_dir in component_config['directory_packing'].items():
                packing_content.append(f'csf_mv_files_to_dir "{source_dir}" "{target_dir}"')

    return packing_content


def generate_final_file_saving_content(component_dict: dict) -> List[str]:
    """Generate all required saved commands for final outputs based on an imsi "components" config (dict) to be called
    post model run and post directory packing"""
    saving_content = ["\n# Imsi created output files"]

    for component, component_config in component_dict.items():
        if component_config and 'output_files' in component_config:
            saving_content.append(f'# Saving files/dirs from: {component}')
            for file_name, target_dir in component_config['output_files'].items():
                saving_content.append(f'save {file_name} {target_dir}')

    return saving_content


def extract_utility_files(files_to_extract: Dict, imsi_config_path: str, work_dir: str):
    '''Extract utility files from the source repository into workdir for use.
       The file source path is defined relative to imsi_config_path
       The destination path is defined relative to the run work_dir
       The destination path cannot be in: src, config, sequencer
    '''
    prohibited_folder_names = ['src', 'config', 'sequencer']
    for target, source in files_to_extract.items():
        source_fullpath = os.path.join(imsi_config_path, source)
        target_fullpath = os.path.join(work_dir, target)

        target_dir = os.path.dirname(target_fullpath)
        if target_dir != work_dir:
            if os.path.basename(target_dir) in prohibited_folder_names:
                raise IOError(f"extracting {source_fullpath} to {target_dir} is prohibited")
            # this means there was part of a path potentially added
            # on the target - make these subfolders if needed:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

        shutil.copy(source_fullpath, target_fullpath)
