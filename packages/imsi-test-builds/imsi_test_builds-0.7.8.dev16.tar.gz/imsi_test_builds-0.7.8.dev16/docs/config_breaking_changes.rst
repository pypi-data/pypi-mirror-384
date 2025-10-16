Config Breaking Changes
=======================

.. contents:: Table of Contents
   :local:

As ``imsi`` progresses, developers will make an effort to keep the configuration files *relatively*
stable, in order to limit the amount of times users of ``imsi`` need to update their config files in order to
use the latest updates from ``imsi``.

However, there will be times when ``imsi`` needs updates that *will* be considered "config breaking" and
users *will* need to update their config files in order to use the latest version(s). This page is meant to
document this versioning practice.

Versioning Practice
-------------------
As is common in semantic versioning, ``imsi`` utilizes the following versioning scheme:

**Major.Minor.Patch**

where:

* Major: will be incremented with new major releases
* Minor: **will be incremented when config breaking changes are introduced**
* Patch: will be incremented as updates are added to address bugs, or add small new features

Notably, with the release of ``imsi`` ``0.4.0``, it now expects a ``version_requirements.json`` file
**directly beneath** ``imsi_config``, which should look like:

.. code-block:: json

    {
        "version_requirements_description" : [ "Defines the imsi version requirements for these configurations." ],
        "imsi_version_requirements" : "Y.X"
    }

where ``Y.X`` should be replaced by the ``Major.Minor`` version that your configuration files were created for.
For example, if the config files were created for versions ``0.4.*``, ``imsi_version_requirements`` should be set to
``0.4``.

Missing Version Requirements Files?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your ``imsi-config`` directory doesn't contain any version requirements document, you'll see something like this:

.. code-block:: none

 /path/to/imsi-config/imsi_version_requirements.json doesn't exist! This is likely because your repo hasn't been setup to work with Y.X. Please update your config files or use an older version of imsi.

where ``Y.X`` would be replaced with the ``major.minor`` version associated with your active ``imsi`` environment. To alleviate
this, simply add the above noted file.

Version Mismatch
^^^^^^^^^^^^^^^^

If your ``imsi-config`` directory was setup to work with an older version of ``imsi``, than the active ``imsi`` environment, you will see

.. code-block:: none

 ValueError: IMSI VERSION MIS-MATCH! Your source repo's config filess are setup to use
     -> Y.X.* <-
 But you are using
     -> Z.N.M <-
 the Major and Minor version must match!

 See https://imsi.readthedocs.io/en/main/config_breaking_changes.html for more information.

where ``Y.X.*`` will be replaced with what your configuration files were setup to use (from the version requirements file) and
``Z.N.M`` will be replaced by the active ``imsi`` version.

When users encounter the above version mismatch error, they should first assess the future of their config files:

* is it a one off test where you wish to reproduce old behaviour? Or
* do you plan on continuing to develop/use these configs?

**If a one off test to reproduce old behaviour**, using an old version of ``imsi`` is likely the best course of action. For
*centrally installed environments*, the recommended practice is to install multiple versions in the same location *with the*
*version string in the environment name*. As such, users are encouraged to check the enviroment path to see if there is
already an installed version to suit their needs. If the required version is not present, users are guided to the
`installation guidance <https://imsi.readthedocs.io/en/main/readme.html#installation>`_ for ``imsi`` in order to easily
build an environment of the desired version.

**If the plan is to keep developing/using these configs**, the best course of would be to refer to the
:ref:`config breaking changes <Configuration Breaking Changes>` section for guidance on what updates are required.

Configuration Breaking Changes
------------------------------

0.6 to 0.7
^^^^^^^^^^

- Moved from the ``json`` format to ``yaml`` to future proof for ``OmegaConf`` and make use of ``yaml`` features.

0.5 to 0.6
^^^^^^^^^^

- move to a ``Pydantic`` schema model that requires the fundem>ental portions of a configuration must now adhere to the schemas defined `here <https://gitlab.com/cccma/imsi/-/tree/main/imsi/config_manager/schema?ref_type=heads>`_. Some notable changes are:

   - the ``components`` section must explicitly have the fields defined `here <https://gitlab.com/cccma/imsi/-/blob/main/imsi/config_manager/schema/components.py?ref_type=heads#L12>`_. This means "faux" components like ``ENV`` or ``CCCma_tools`` have to be removed
   - ``mip_era`` is required under ``experiments`` for the new schema

- The key ``model_config`` has been renamed to ``model_type`` due to an `attribute clash with pydantic <https://docs.pydantic.dev/2.10/errors/usage_errors/#model-config-invalid-field-name>`_.
- The subdirectories of ``config_dir`` have been explicitly added to the configs to reduce coupling with imsi. For example, the file namelist is under the ``EXP00`` subdirectory, and its path has been changed to be more explicit, e.g. ``EXP00/namelist``.
- ``config_dir`` has been made more explicit by defining it starting one level above, so that the ``models`` path doesn't need to be hardcoded in imsi. This change was motivated by relative paths in the configs. ``config_dir`` used to be defined to the ``EXP00`` level.
- ``cpp_defs`` has been renamed to ``compilation``. The relative path to these files has been removed as per above.
- The ``merged_model_experiment`` construct has been removed from the downstream JSON. Under ``model_options.json`` there are configs that are applied on top of the resolved JSON. These needed to be backed out to be compatible.

0.4 to 0.5
^^^^^^^^^^

.. _machine-comp-env:

Machine: Computational environment
""""""""""""""""""""""""""""""""""

Under a machine in the ``"machines"`` configuration files, the following
keys must moved under a new ``"computational_environment"`` key:

- ``"modules"``
- ``"environment_variables"``
- ``"environment_commands"``

These parameters are already part of the machine configuration so must
simply be rearranged.

For downstream resolved imsi configuration file (``imsi_configuration_{runid}.json``),
the change is analogous:

.. code-block:: json

    {
        "machine": {
            "name": "machine-A",
            "parameters": {
                // ... other parameters ...
                "computational_environment": {    // new
                    "modules": {
                        // ...
                    },
                    "environment_variables": {
                        // ...
                    },
                    "environment_commands": {
                        // ...
                    }
                }
            }
        }
    }

Machine sites
"""""""""""""

High performance computing platforms are often comprised of several interconnected
machines. In imsi, certain modelling components can be set up across multiple machines
for a single experiment. In imsi ``0.4``, an explicit definition of a machine "site"
is required to establish the relationship between various machines.
This is used to pull specific attributes from different machines onto the machine
specified at setup/config time.

Suppose you have machine configuration for three machines:

.. code-block:: json

    {
        "machines": {
            "machine-A": {
                // ...
            },
            "machine-B": {
                // ...
            },
            "machine-C": {
                // ...
            }
        }
    }

A "site" is simply a list of machines that are already defined in the imsi configuration
json files. No changes are required to the ``"machines"`` configuration themselves
(other than those described in :ref:`machine-comp-env`), and no changes are required
when initilizing a run via ``imsi setup``. Rather, there must be a file
that contains a ``"sites"`` configuration:

.. code-block:: json

    {
        "sites": {
            "site-name-1": ["machine-A", "machine-B"],
            "site-name-2": ["machine-C"],
        }
    }

The requirements are that:

1. a site is comprised of one or more machines.
2. **each** machine (defined in jsons under the ``"machines"`` key) must be
   associated with a site.

Once a run folder is setup (``imsi setup --runid={runid} ...``) and the resolved
configuration file (``imsi_configuration_{runid}.json``) is generated, the ``"machine"``
configuration will contain the ``"site_name"`` under ``"parameters"`` and an additional
key called ``"site"``, which contains the names of associated machines across the
site and their attributes.

In this version, the attributes that are required are:

- ``nodename_regex``
- ``resources``
- ``computational_environment`` (see :ref:`machine-comp-env`)

Following the example above, to setup an experiment run on ``machine-A``:

.. code-block:: bash

    imsi setup --runid=sample-runid --machine=machine-A ...   # no change


The resolved configuration file for ``machine-A`` (``./sample-runid/imsi_configuration_sample-runid.json``)
contains:

.. code-block:: json

    {
        "machine": {
            "name": "machine-A",
            "parameters": {
                // ...
                "site_name": "site-name-1"     // new
            },
            "site": {                          // new
                "machine-B": {
                    "nodename_regex": "mb.*",
                    "resources": {
                        // ...
                    },
                    "computational_environment": {
                        // ...
                    }
                }
            }
        }
    }

While ``"sites"`` is configured as a top-level key in the imsi configuration files,
``"site"`` is resolved as a sub-key of a ``"machine"`` for the resolved configuration.

0.3 to 0.4
^^^^^^^^^^

ISO Durations and More Explicit Date Units
""""""""""""""""""""""""""""""""""""""""""
To help better handle durations in the ``imsi`` backend and downstream utilities, ``0.4`` now expects ``iso`` durations, i.e.

.. code-block::

   P12MS

instead of the previous

.. code-block::

   12MS

where ``P`` stands for "period". The affected duration variables are generally contained in the sequencing configuration files, or under
the ``sequencing`` portion of the dictionaries. For example, say this was main sequencing file:

.. code-block:: json

    {
        "sequencing" :{
            "run_dates" : {
                "comment" : "times will be filled from experiment",
                "run_start_time" : "{{start_time}}",
                "run_stop_time" : "{{end_time}}",
                "run_segment_start_time" : "{{start_time}}",
                "run_segment_stop_time" : "{{end_time}}",
                "model_chunk_size" : "12MS",
                "model_internal_chunk_size" : "12MS",
                "postproc_chunk_size" : "12MS"
            }
        }
    }

the diff on the file should be:

.. code-block:: diff

    diff --git a/CONFIG/imsi-config/sequencing/imsi-sequencing-config.json b/CONFIG/imsi-config/sequencing/imsi-sequencing-config.json
    index 605ad1e73..9cd3d6088 100644
    --- a/CONFIG/imsi-config/sequencing/imsi-sequencing-config.json
    +++ b/CONFIG/imsi-config/sequencing/imsi-sequencing-config.json
    @@ -6,9 +6,9 @@
                 "run_stop_time" : "{{end_time}}",
                 "run_segment_start_time" : "{{start_time}}",
                 "run_segment_stop_time" : "{{end_time}}",
    -            "model_chunk_size" : "12MS",
    -            "model_internal_chunk_size" : "12MS",
    -            "postproc_chunk_size" : "12MS"
    +            "model_chunk_size" : "P12MS",
    +            "model_internal_chunk_size" : "P12MS",
    +            "postproc_chunk_size" : "P12MS"
            }
        }
    }

Now its worth noting that there are likely downstream effects that your codes will need to be adapted to. Notably:

* if your codes relies on internal looping of the model, within the model job, note that the file containing the internal dates is now named ``model_inner_loop_start-stop_dates`` instead of the previous ``model_execution_loop_start-stop_dates``
* the main date variables will now adhere to the following syntax, ``YYYY-MM-DDTHH:MM:SS``, matching the ``iso861`` standard. As such, if you're scripting is using these variables beyond simple comparisons, you'll need to account for the addition of the internal ``T`` as opposed to the previous space.
* some chunk size variables in the scripting implicitly assumed they were using months, i.e. ``POSTPROC_CHUNK_SIZE``, ``MODEL_INTERNAL_CHUNK_SIZE``, ``MODEL_CHUNK_SIZE``. These variables are now produced with ``_MONTHS`` appended to the end. As such, if your scripting uses these vars, they need to be updated.


The exact nature of these updates depends on your specific code-base, but as an example, here are some example diffs made to account for this:

.. code-block:: diff

	diff --git a/CONFIG/imsi-config/lib/pre_nemo_imsi.sh b/CONFIG/imsi-config/lib/pre_nemo_imsi.sh
	index 2ae75d0d9..19bcfdef4 100644
	--- a/CONFIG/imsi-config/lib/pre_nemo_imsi.sh
	+++ b/CONFIG/imsi-config/lib/pre_nemo_imsi.sh
	@@ -43,4 +43,4 @@ if [[ "$chunk_start_date" != "$run_start_date" ]]; then
	 fi

	 # update counters
	-update_nemo_counters start_date=${chunk_start_YYYY}-${chunk_start_MM}-${chunk_start_DD} stop_date=${chunk_stop_YYYY}-${chunk_stop_MM}-${chunk_stop_DD} nemo_timestep=3600 ref_date=${run_start_date% *} namelist_file=namelist
	+update_nemo_counters start_date=${chunk_start_YYYY}-${chunk_start_MM}-${chunk_start_DD} stop_date=${chunk_stop_YYYY}-${chunk_stop_MM}-${chunk_stop_DD} nemo_timestep=3600 ref_date=${run_start_date%T*} namelist_file=namelist

or

.. code-block:: diff

    diff --git a/maestro-suite/default-imsi/modules/model/model_loop/model_run.tsk b/maestro-suite/default-imsi/modules/model/model_loop/model_run.tsk
    index e4b3a6e0..637cff2c 100644
    --- a/maestro-suite/default-imsi/modules/model/model_loop/model_run.tsk
    +++ b/maestro-suite/default-imsi/modules/model/model_loop/model_run.tsk
    @@ -5,7 +5,7 @@ source ${CANESM_SRC_ROOT}/CCCma_tools/tools/CanESM_shell_functions.sh

     # This dates file would have been generated by imsi during setup/config
     # and contains all the chunk start/stop dates
    -internal_dates_file=${WRK_DIR}/config/model_execution_loop_start-stop_dates
    +internal_dates_file=${WRK_DIR}/config/model_inner_loop_start-stop_dates
     readarray -t chunk_start_stop_dates < "$internal_dates_file"

     # This loop goes through all dates in the file, and checks if chunk dates are within the range
    diff --git a/tools/CanESM_shell_functions.sh b/tools/CanESM_shell_functions.sh
    index f120f372..69f163ab 100644
    --- a/tools/CanESM_shell_functions.sh
    +++ b/tools/CanESM_shell_functions.sh
    @@ -1422,7 +1422,7 @@ function get_list_of_cmorized_netcdf_files(){
     # systems in parallel. The older ones should be retired once possible.
     #NCS July 2024

    -iso8061_date_format_regex='^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$'
    +iso8061_date_format_regex='^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$'

     function get_start_stop_times_from_file_by_index() {
         # Read start and stop dates from a file by index (linenumber), using zero indexing
    @@ -1464,7 +1464,7 @@ function split_date(){
         local input_date
         local input_date_array
         local local_date_format_regex
    -    local_date_format_regex='^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$' # YYYY-MM-DD HH:MM:SS
    +    local_date_format_regex='^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$' # YYYY-MM-DD HH:MM:SS
         input_date=$1

         if [ -z "$input_date" ]; then
    @@ -1472,11 +1472,11 @@ function split_date(){
             return 1
         fi
         if ! [[ $input_date =~ $local_date_format_regex ]]; then
    -        echo "split_date expects dates as YYYY-MM-DD HH:MM:SS" >&2
    +        echo "split_date expects dates as YYYY-MM-DDTHH:MM:SS" >&2
             return 1
         fi

    -    IFS='-: ' read -r year month day hour minute second <<< "$input_date"
    +    IFS='-: T' read -r year month day hour minute second <<< "$input_date"
         echo "$year $month $day $hour $minute $second"
     }

    ...

    diff --git a/maestro-suite/default-imsi/modules/postproc/rebuild_loop/rebuild_ocean_tiles.tsk b/maestro-suite/default-imsi/modules/postproc/rebuild_loop/rebuild_ocean_tiles.tsk
    index 2a2352b8..134f83d8 100644
    --- a/maestro-suite/default-imsi/modules/postproc/rebuild_loop/rebuild_ocean_tiles.tsk
    +++ b/maestro-suite/default-imsi/modules/postproc/rebuild_loop/rebuild_ocean_tiles.tsk
    @@ -4,7 +4,7 @@ if (( with_rbld_nemo == 1 )); then
         #~~~~~~~~~~~~~~~~~~~~~~
         # Set static variables
         #~~~~~~~~~~~~~~~~~~~~~~
    -    months_gcm=${MODEL_INTERNAL_CHUNK_SIZE} # defines how big the model chunk size was
    +    months_gcm=${MODEL_INTERNAL_CHUNK_SIZE_MONTHS} # defines how big the model chunk size was
     
         #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         # Check if we need to rebuild the initial restart files
    @@ -15,7 +15,7 @@ if (( with_rbld_nemo == 1 )); then
             echo "Rebuilding ocean tiles from the initial restart"
             (
                 canesm_nemo_rbld_save_hist=${canesm_nemo_rbld1st_save_hist};    \
    -            mon=$(( run_start_month - MODEL_INTERNAL_CHUNK_SIZE + 12 ));    \
    +            mon=$(( run_start_month - MODEL_INTERNAL_CHUNK_SIZE_MONTHS + 12 ));    \
                 year=$(( run_start_year - 1 ));                                 \
                 mon=$(pad_integer $mon 2);                                      \
                 year=$(pad_integer $year 4);                                    \
    @@ -29,7 +29,7 @@ if (( with_rbld_nemo == 1 )); then
         #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         # Note:
         #   - we need to run the repacking for each model chunk
    -    num_model_chunks_per_post_proc=$(( POSTPROC_CHUNK_SIZE / months_gcm ))
    +    num_model_chunks_per_post_proc=$(( POSTPROC_CHUNK_SIZE_MONTHS / months_gcm ))
         int_year=${job_start_year}
         for n in $(seq ${num_model_chunks_per_post_proc}); do
             int_mon=$(( (n-1) * months_gcm + job_start_month ))

ISS Configuration Changes
"""""""""""""""""""""""""
To improve the functionality of the "imsi simple sequencer" (``iss``), there were notable updates to the ``iss`` codes between 0.3 and 0.4, which
require changes to the following configuration files **if you're application uses** ``iss``:

* the ``iss`` sequencing config files and
* the flow configuration files that get **used** by ``iss``

Specifically:

1. ``iss`` flows now supports two job names -> ``model`` and ``postproc``. So your config files will now need to adhere to this if using ``iss``, largely due to the two job assumption that ``iss`` makes.
2. ``iss`` now requires some extra information under ``["sequencing"]["sequencers"]["iss"]``, specifically under the ``baseflows`` section.

   For example, in earlier ``CanESM`` configs, we just had:

   .. code-block:: json

    "ESM" :{
        "canesm_two_job_flow" : {
            "model_run_script": "{{source_path}}/CCCma_tools/maestro-suite/default-imsi/modules/model/model_loop/model_run.tsk",
            "diagnostic_run_script": "{{imsi_config_path}}/lib/iss/imsi_diag_canesm.sh"
        }
    }

   but now we have:

   .. code-block:: json

    "ESM" :{
        "canesm_two_job_flow" : {
            "flow_definitions": {
                "model": "{{source_path}}/CCCma_tools/maestro-suite/default-imsi/modules/model/model_loop/model_run.tsk",
                "postproc": "{{imsi_config_path}}/lib/iss/imsi_diag_canesm.sh"
                }
            "flow" : {
                "model": {
                    "submit_next": 1
                },
                "postproc": {
                    "submit_next": 1,
                    "depends_on" : {"model": "END"}
                }
            }
        }
    }

   where the "``flow_definitions``" section defines the user scripts to be used, and the "``flow``" section defines how
   the jobs depend on each other. For example, ``submit_next`` is used to say if the job should try to submit itself, and
   ``depends_on`` is used to define the dependencies.

3. ``iss`` now expects batch directives, for jobs that will be ran as part of ``iss``, to be part of the sequencer agnostic flow definitions - generally the machine specific extensions of them, as resources/schedulers depend on the individual machines. This is necessary because ``iss`` does not have the ability to translate general definitions under ``resources`` into scheduler specific directives. As such, in order for ``iss`` to support the given baseflow, it needs a section like

   .. code-block:: json

    "model": {
        ...
        "resources" : {
            ...
            "directives" : [
                "-S /bin/bash",
                "-q development",
                "-j oe",
                "-l walltime=03:00:00",
                "-lplace=scatter -lselect=1:ncpus=80:mpiprocs=33:ompthreads=2:mem=130gb+2:ncpus=80:mpiprocs=80:ompthreads=1:mem=120gb"
            ]
        }

