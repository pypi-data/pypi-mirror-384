# IMSI v0.2 layout

The major components:

## CLI
  - user interaction
                            
## setup
   - initial clone/directory creation                                      
      - could be split into 2 steps, ala setup-canesm and adv-setup, 
      but not currently.

## config_manager
    - parses user input with config_database to form a complete Configuration,
       a data object containing the full config settings                             
       
# shell_interface
   - generates "shell" files on disk to be ingested by the model and downstream 
     infrastructure, using data from the Configuration data object to fill
     templates (known required data structures, with variables that differ 
     by experiment/model/user-choice and supplied by Configuration) 
   - These are shell files typically common to all sequencers
   - Theoretically extendable by users, even in preludes etc (i.e
   new utilities can be written which leverage the Configuration data object)
   - What is provided now are known common functions.

# Sequencer_interface
   - Creates specific structures / files to setup a given sequencer to run
     the simulation.
     - includes a "scheduler_interface" (?) that configures a given sequencer
       (and model run commands, etc) to taget a specific scheduler (pbs, slurm and
       associate mpirun or srun etc). [might be separate interface above sequencer]

# utilities
- common functions for things like 
   - reading json, 
   - parsing inheritance (in nested dicts)
   - replacing variables
   - interacting with cpp / namelist files
   - writing shell files
        
# TODO:
- Major Functionality
   - Refactor sheduler / sequencer tools and connect to refactored code

- To clarify:
   - replace `imsi_config` with something like `imsi_global_config_dir_path` and 
   - define the path the run specific `imsi_configuration_${runid}.json` file as `imsi_run_config_file_path` or such

- New features / additional refactoring
   - More extensive use of getters and setters of config_manager objects
   - Implement "template" functionality more formally - as typified by set_shell_config
   