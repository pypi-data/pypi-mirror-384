=============
Ensemble Tool
=============

.. code-block:: bash

   imsi ensemble --help

.. program-output:: imsi ensemble -h


Overview
--------

The ensemble tool is a comprehensive way to configure and run multiple ensemble members. It is designed to be flexible and user-friendly, allowing for easy setup of multiple ensemble members with minimal effort. The ensemble tool is built on top of the IMSI framework and so existing commands are replicated in the tool but applied across multiple ensemble members. Users can configure an ensemble run using one of two main methods: as a configuration of lists in a high-level configuration file, or as a list of configurations in a configuration table. Starting with the high-level configuration file, the ensemble tool sets up a new run for each unique value in the lists. The configuration table method is more flexible and allows for more complex configurations. The ensemble tool also supports broadcasting of configuration parameters from the high-level configuration file to all ensemble members.


High-Level Config: The Entry Config
-----------------------------------

Calling the ensemble tool requires a high-level config to be set in the ``--config-path`` argument. The default config file is ``config.yaml``. The high-level config is a YAML file that defines the ensemble-level and member-level parameters. The ensemble tool reads the high-level config and sets up the ensemble members accordingly.:

.. code-block:: bash

   imsi ensemble --config-path=config.yaml <command>

The entry config requires the definition of two main sub-levels: ``ensemble_level`` and ``member_level``.

``ensemble_level`` Parameters
+++++++++++++++++++++++++++++

These parameters need to be logically defined *once per ensemble run*. For example:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}  # required, recommended example sets omegaconf interpolation to $USER
     run_directory: /output/path/to/ensemble/setup_dirs/  # optional, defaults to cwd
     config_table: table.csv  # optional
     share_repo: true  # optional, defaults to false

.. list-table:: ``ensemble_level`` Parameters
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``user``
     - The user running the ensemble. Defaults to ``$USER`` but can be overridden.
   * - ``run_directory``
     - Directory where ensemble setup directories are created. Defaults to the current working directory.
   * - ``config_table``
     - Path to the configuration table. See details on configuration tables below.
   * - ``share_repo``
     - If True, the first ensemble member's setup ``src`` repository is symlinked to subsequent setup directories. Defaults to False.
   * - ``aliases``
     - ``alias: parameter`` pairs to help keep table headers short. Defaults to None.

The minimum required ``ensemble_level`` parameters are ``user``, so a minimal configuration would look like the following:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}

``member_level`` Parameters
+++++++++++++++++++++++++++

These parameters are defined *once per ensemble member* and represent *any* IMSI-compatible parameter. Most importantly, *any* ``member_level`` variable can be defined as either a value or a list of values. If a list is specified, the ensemble tool sets up a new run for each value in the list. All setup parameters must be defined under the subkey ``setup`` in order to be correctly used by imsi (e.g. ``setup:runid``).

.. note:: Single member runs can be defined under the ``member_level`` section, but values must be added as a list with a single value. For example, ``runid: [run-01]``. This is to maintain consistency with ensemble runs.

Supported Configuration Formats for ``ensemble_level: config_table``
---------------------------------------------------------------------

Configuration tables store discrete ensemble member runs and their associated parameter modifications. IMSI's ensemble tool supports ``.yaml`` and ``.csv`` formats. Legacy ``.txt`` support is still available but deprecated, with a ``DeprecationWarning`` issued when used. We recommend that users use the ``.yaml`` format due to its explicit representation of key heirarchies.

Example ``member_level`` configuration of two ensemble members:
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup:
       runid: [run-01, run-02]
       model: [canesm51_p1, canam51_p1]
       exp: [cmip6-piControl, cmip6-amip]

is equivalent to:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     config_table: config/example.csv
     share_repo: true

   member_level: {}

with ``config/example.csv`` containing:

.. code-block:: text

   setup:runid,  setup:model, setup:exp
   run-01,       canesm51_p1, cmip6-piControl
   run-02,       canam51_p1,  cmip6-amip

or YAML config table:

.. code-block:: yaml

   - setup:
       runid: run-01
       model: canesm51_p1
       exp: cmip6-piControl

   - setup:
       runid: run-02
       model: canam51_p1
       exp: cmip6-amip

Minimal ``member_level`` for config table-only runs:

.. code-block:: yaml

   member_level: {}


Broadcasting Configuration Parameters from ``member_level``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The ensemble tool resolves configurations as follows:

1. If a key exists in both ``member_level`` and ``config_table``, the ``config_table`` value overrides and issues a warning.
2. If a key exists only in ``member_level``:

   - Single values are **broadcasted** to all ensemble members.
   - Lists must match the number of ensemble members.
   - Any overlapping keys (even lists) are overridden by the ``config_table`` values. If they don't exist in the ``config_table``, they are broadcasted to all ensemble members.

.. note:: Broadcasting in this context means that singular values are copied and applied to each ensemble member. Lists are broadcasted to each ensemble member in the order they are defined.

For ``.csv`` and ``.yaml`` config tables, the ensemble tool now supports configurations where users can omit parameters from ensemble runs that are present in other members. For example, the following config tables are valid:

**CSV**:

.. code-block:: text

   setup:runid, setup:model, some:imsi:parameter
   run-01-csv,  canesm51_p1,
   run-02-csv,  canam51_p1,  123

**YAML**:

.. code-block:: yaml

   - setup:
       runid: run-01-yaml-table
       model: canesm51_p1

   - setup:
       runid: run-02-yaml-table
       model: canam51_p1
       some:
         imsi:
           parameter: 123


Modifying lower level configuration parameters
----------------------------------------------
The ensemble tool allows for the modification of any non-setup parameter in the resolved ``yaml`` file (i.e. ``imsi_configuration_{runid}.yaml``). For instance, to modify the parameter ``pp_rdm_num_pert``, the user can acheive this in multiple ways:

1. In the entry level config file, add the following:
+++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     ...
   member_level:
    setup:
      runid: [run-01, run-02]
    components:
      CanAM:
        namelists:
          canam_settings: 
            phys_parm:
              pp_rdm_num_pert: [0, 2]

.. important:: The parameter that is being modified must contain the entire heriarchy of the resolved yaml (i.e. ``imsi_configuration_{runid}.yaml``). The ensemble tool modifies the resolved yaml file in place and runs ``imsi config`` on the modified file. If a new key is added to the resolved yaml by the ensemble tool, it will warn users.

2. In a CSV config table, add the following:
++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: text
    
   runid,  model,       exp,             components:CanAM:namelists:canam_settings:phys_parm:pp_rdm_num_pert
   run-01, canesm51_p1, cmip6-piControl, 0
   run-02, canam51_p1,  cmip6-amip,      2

Or, if you're like us and think that column name is long and ugly, you can specify an alias for that very long key-path in your entry config:

.. code-block:: yaml
    
   ensemble_level:
     user: ${oc.env:USER}
     ...
     aliases:
       # the alias key can be any dictionary compatible string
       pp_rdm_num_pert: components:CanAM:namelists:canam_settings:phys_parm:pp_rdm_num_pert
   member_level: {}


And then in your CSV config table:

.. code-block:: text

   setup:runid,  setup:model, setup:exp,       pp_rdm_num_pert
   run-01,       canesm51_p1, cmip6-piControl, 0
   run-02,       canam51_p1,  cmip6-amip,      2

3. In a YAML configuration table (the most explicit way):
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml
    
    - setup:
        runid: run-01
        model: canesm51_p1
        exp: cmip6-piControl
      components:
        CanAM:
          namelists:
            canam_settings: 
              phys_parm:
                pp_rdm_num_pert: 0

    - setup:
        runid: run-02
        model: canam51_p1
        exp: cmip6-amip
      components:
        CanAM:
          namelists:
            canam_settings: 
              phys_parm:
                pp_rdm_num_pert: 2


Common configuration examples in the entry YAML:
------------------------------------------------
- Running an ensemble with a single model and multiple experiments.
- Running an ensemble with multiple models and a single experiment.
- Running an ensemble with multiple models and multiple experiments.

Example 1: Single model, multiple experiments
+++++++++++++++++++++++++++++++++++++++++++++
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup: 
       runid: [run-01, run-02]
       model: canesm51_p1 # this is broadcasted to all ensemble members and is equivalent to [canesm51_p1, canesm51_p1]
       exp: [cmip6-piControl, cmip6-amip]

Example 2: Multiple models, single experiment
+++++++++++++++++++++++++++++++++++++++++++++
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup:
       runid: [run-01, run-02]
       model: [canesm51_p1, canam51_p1]
       exp: cmip6-piControl # this is broadcasted to all ensemble members and is equivalent to [cmip6-piControl, cmip6-piControl]

Example 3: Multiple models, multiple experiments
++++++++++++++++++++++++++++++++++++++++++++++++
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup:
       runid: [run-01, run-02, run-03, run-04]
       model: [canesm51_p1, canam51_p1, canesm51_p2, canam51_p2]
       exp: [cmip6-piControl, cmip6-amip, cmip6-historical, cmip6-ssp585]



Common configuration examples from a YAML config table:
-------------------------------------------------------

Example 1: Single model, multiple experiments
+++++++++++++++++++++++++++++++++++++++++++++

Consider the following entry level YAML:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true
     config_table: config/example.yaml

   member_level:
     setup:
       ver: imsi-integration


In ``config/config.yaml``, the commented keys show how the values are resolved into the table

.. code-block:: yaml

   - setup:
       runid: run-01
       model: canesm51_p1
       exp: cmip6-piControl
     # ver: imsi-integration is broadcasted into resolved ensemble config and is equivalent to specifying directly
   - setup:
        runid: run-02
        model: canesm51_p1
        exp: cmip6-amip
     # ver: imsi-integration is broadcasted into resolved ensemble config and is equivalent to specifying directly
