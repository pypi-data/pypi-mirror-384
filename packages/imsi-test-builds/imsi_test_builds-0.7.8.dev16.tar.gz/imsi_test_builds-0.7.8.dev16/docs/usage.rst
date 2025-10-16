=====
Usage
=====

Configuring user defaults
-------------------------

.. warning::

    This concept is a work in progress and not implemented yet. As such, if you add
    a user config file like this, it `won't` be used.

The file

.. code-block:: bash

    ~/.imsi/imsi-user-config.yaml

can be used to set user preferences and options. These are always respected over any
other choices.

Setting up a run
----------------

Using ``imsi setup`` to create a run directory, obtain the model source code,
and extract all required model configuration files. The setup will result
in an imsi configured directory, from which futher interaction with the run
is conducted. 

The output of ``imsi setup -h``:

.. program-output:: imsi setup -h

The imsi setup creates some subdirectories for the run, including ``bin`` (for executables),
and ``config``. The ``config`` directory contains various run configuration files, including
cpp directives and namelists, that have been extracted and modified according to the choice
of model and experiment.

Example
+++++++

.. code-block:: bash

    >> imsi setup --repo=https://gitlab.com/cccma/canesm --ver=develop_canesm --exp=cmip6-piControl --model=canesm51_p1 --runid=<unique-runid>

The setup also creates a log file (``.imsi-setup.log``), and a readable/writable ``yaml`` state file containing the
full details of the configuration options (``imsi_configuration_<runid>.yaml``). Additionally, it will extract
the ``save_restart_files.sh`` and ``imsi-tmp-compile.sh`` scripts from the ``imsi-config`` directory within the
housing model repo.

.. warning::

   Changes to the above ``imsi_configuration_<runid>.yaml`` file are
   **not automatically applied to your run**. If you want changes to take affect,
   you need to run ``imsi config`` after making updates to this local ``yaml``
   file.

Once you make the desired changes, if any (see :ref:`here <Modifying basic run parameters>` for details
on making simple changes to a configuration), you then
need to step through the following steps:

.. code-block:: bash

    >> imsi build         # run the compilation tool to build your model's execs
    >> imsi save-restarts # save your model's restarts
    >> imsi submit        # submit your jobs!

to launch your experiment!


Querying available configurations
-----------------------------------
Use imsi list to query the supported models, and experiments known to IMSI.

If you are already in an imsi-configured repository, the results will be based on that repository's ``imsi-config`` directory. If you are not in an imsi-configured repository, you can:
1. Point directly to a single repository using ``--repo-path <path>``

2. Point to a directory containing multiple repositories (each with an imsi-config) using ``--repo-path <directory>``

3. Using ``IMSI_DEFAULT_CONFIG_REPOS``. Users can set this value in two ways (each definition is treated additively): 

    i. In ``$HOME/imsi.user.rc``

    ii. In a bash session as an environment variable, under ``imsi.user.rc``.

Default fall-back values are packaged with imsi under the ``imsi/imsi.site.rc`` file and are site-specific. 

You can further narrow the results with:

``--filter-model <name>`` -- show only configurations for a given model name 

``--filter-experiment <name>`` -- show only configurations for a given experiment name

Example commands:

.. code-block:: bash

    # List configurations from the current repository
    imsi list

    # List configurations from a specific repo path
    imsi list --repo-path /path/to/model-repo

    # List configurations from multiple repos in a directory
    imsi list --repo-path /path/to/repos-dir

    # Filter by model and experiment
    imsi list --filter-model canesm53_b1_p1 --filter-experiment cmip6-historical

The output of imsi list -h:

.. program-output:: imsi list -h

Modifying basic run parameters
------------------------------

To modify an run paramters, there are basically four choices, in order of preference:

1. **Use** ``imsi set``

    This is  work in progress method, but provided a model repo has been setup to use it, ``imsi set`` 
    can be used to apply a specific option or selection (see set usage below) and reload the configuration.

2. **Modify the upstream** ``.yaml`` **files in the** ``imsi-config`` **directory for your run**

    *This is ultimately the most reproducible/shareable way to make changes* as involves making changes
    in the upstream ``yaml`` files under ``src/imsi-config``.

    Once you have made your changes, run

    .. code-block:: bash

       >> imsi reload

    to have ``imsi`` reparse the source repo and update the configs with your changes. **This is the primary
    configuration development method**.

3. **Modify the local** ``imsi_configuration_<runid>.yaml`` **file, and run** ``imsi config``

    This is great for simple/common changes like restart and/or date settings,
    but its not a great way to `develop` configurations as the changes aren't
    under version control and thus aren't easily shareable. With that in mind,
    all you need to do is open the local ``imsi_configuration_<runid>.yaml``
    file, search for the desired settings and change then, then run

    .. code-block:: bash

       >> imsi config

    to load the updated yaml file and apply the changes to your run.

4. **Edit files in the** ``config`` **directory directly**

    These files are ultimately what are actually used by the model simulation,
    so you can simply modify the text files created here. This is great for
    simple testing/debugging changes, but it is important to note that **these
    types of changes can be very easily overwritten** so caution should be
    taken when using this method. Specifically, running ``imsi config`` or ``imsi reload``
    after these changes are made will very likely overwrite them.

The `CanESM Changes Tutorial <https://gitlab.com/CP4C/cp4c-docs/-/blob/main/cp4c-tutorial-apr-2024/canesm_changes_tutorial.ipynb>`_
provides some direct examples of making common changes like altering parent_runid and simulation dates.

Common changes
++++++++++++++

Changing restarts
~~~~~~~~~~~~~~~~~

1. **changing the defaults for a given experiment**:

    To change the values in reproducible way, simply

        1. navigate to ``imsi_config`` in your source repo
        2. find the desired experiment definition (typically under ``experiments``) 
        3. modify ``parent_runid`` and ``parent_branch_time`` as desired

    Then either setup a new run from the updated repo, **or if you've already setup a run with the experiment you modified**, run

    .. code-block::

       >> imsi reload

    To have the new settings applied

2. **one off changes for testing in a setup run**:

    As alluded to above, you can utilize quick testing by modifying the values in ``imsi_configuration_<runid>.yaml`` - so just
    open the file and modify ``parent_runid`` and ``parent_branch_time``, then reconfigure ``imsi`` with

    .. code-block::

       >> imsi config

Changing namelist parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **changing defaults for a given model/experiment combo**:

    First it should be noted that, by design, experiment settings override the settings defined in model definitions. As such

        1. navigate to ``imsi_config`` in the source repo
        2. find desired model or experiment file
        3. search for the desired setting under ``components`` and change the default value

    Then either setup a new run with ``imsi setup`` or run ``imsi reload`` from a setup run.

2. **one off changes for testing in a setup run**:

    Noting that **if you want others to use this change**, its wiser to use the first method. For fast tests, that won't have
    values in the ``config`` directory overwritten, open ``imsi_configuration_<runid>.yaml`` and modify the desired parameter, then
    reconfigure with:

    .. code-block::

        >> imsi config

Changing input files
~~~~~~~~~~~~~~~~~~~~

See above notes on `changing namelist parameters <changing namelist parameters>`_, except note that you'd
be altering fields under ``input_files``.

Altering post processing settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **changing defaults for a given "postproc profile"**:

    For a given model/experiment combination, the postprocessing settings are defined by the ``postproc_profile``, which
    contains the downstream settings for any postprocessing operations. So:

        1. navigate to ``imsi_config`` in the source repo
        2. identify what ``postproc_profile`` your model/experiment is using (experiment definition takes precedence)
        3. find the associated ``postproc_profile`` definition
        4. modify the desired settings

    Then either setup a new run with ``imsi setup`` or run ``imsi reload`` from a setup run.

2. **one off changes for testing in a setup run**:

    For fast, non shareable tests that won't have
    values in the ``config`` directory overwritten, open
    ``imsi_configuration_<runid>.yaml`` search for ``postproc`` and modify the
    desired parameter, then
    reconfigure with:

    .. code-block::

        >> imsi config

Altering resource settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **changing defaults for a given** ``sequencing_flow``:

    With ``imsi``, the resource specifications are defined under the
    ``sequencing_flow`` :ref:`section of the configuration <Sequencing Flow>`,
    which specific job resources under ``jobs``. There is some nuance in how it is set
    but you can find which files under the
    ``imsi_config`` directory contain these sections via a simple:

    .. code-block::

       >> cd src/imsi-config
       >> grep -nr "sequencing_flow"

    Which one is selected depends on the ``sequencer`` (defaults to ``maestro``
    for ECCC systems, and ``iss`` for Niagara), the value of ``model_type``
    associated with your model (eg: ``ESM``, ``AMIP``, ``OMIP``), and
    lastly the machine you're running on.

    For example, say I have a config repo setup such that I have files like:

    .. code-block:: yaml

       sequencing:
          sequencers:
             maestro:
                ...
                baseflows:
                   ESM:
                      canesm_split_job_flow:
                   AMIP:
                      canam_split_job_flow:
                   OMIP:
                      cannemo_split_job_flow:

    This will mean that for the "baseflow", ``ESM`` simulations will use ``canesm_split_job_flow``
    as the default for ``maestro`` and likewise, ``AMIP`` will use
    ``canam_split_job_flow``, while ``OMIP`` will use
    ``cannemo_split_job_flow``. With this baseflow in hand, ``imsi`` uses this
    combined with ``default_sequencing_suffix`` in the ``machine`` configuration files to build
    the machine specific flow name : ``{baseflow}-{default_sequencing_suffix}``.

    And so to alter default resources:

    1. navigate to ``imsi_config`` in the source repo
    2. determine the ``model_type`` used in your model/experiment
    3. determine the ``baseflow`` used your sequencer
    4. to modify resources for all machines that use this flow, change the values for the flows `without` ``default_sequencing_suffix``
    5. to modify resources for a specific machine that uses this flow, find ``default_sequencing_suffix`` and modify the settings under ``{baseflow}-{default_sequencing_suffix}``

    Then either setup a new run with ``imsi setup`` or run ``imsi reload`` from a setup run.

2. **one off changes for testing in a setup run**:

    For fast, non shareable tests that won't have
    values in the ``config`` directory overwritten, open
    ``imsi_configuration_<runid>.yaml`` search for ``jobs`` and modify the
    desired parameter, then
    reconfigure with:

    .. code-block::

        >> imsi config

.. note::

   In some job specification sections you might see ``directives`` in addition to more specific ``resources`` fields like
   ``walclock``, ``memory``, or ``processors``. This is only utilized by specific sequencers - specifically, it is used for ``iss`` and
   ignored by ``maestro``.

Using imsi set
++++++++++++++

The above examples are all simple, standard modifications of single variables,
which make them well posed for easy modification.  For higher level settings,
``imsi set``  can be used for an already setup run.  Which selections can be
set are given by ``imsi list`` (as above), most notably ``experiments`` and
``models``, but there are others!

The output of ``imsi set -h``:

.. program-output:: imsi set -h


Example
~~~~~~~

Say you wish to change the experiment to ``cmip6-historical`` after setting up a run:

.. .. code-block:: bash

..    imsi set -o pe_config=2+4 # removing this example until we think more on the options

.. code-block:: bash

    imsi set -s exp=cmip6-historical

Or change to an different experiment/model altogether

.. code-block:: bash

    imsi set -s exp=cmip6-amip -s model=canam51_p1

This will reconfigure the setup for the historical experiment. Similarly you could change
``machine``, ``compiler``, or any of the available model options.

.. note::

   Model options are a work in progress.

Building run executables
------------------------

.. code-block::

   >> imsi build

It is worth noting that all this does is call the extracted ``imsi-tmp-compile.sh`` script. Additionally,
if `any` arguments/flags are provided after ``imsi build``, it will send the arguments to extracted script.

For example:

.. code-block::

   >> imsi build -f -a

would send the ``-f -a`` flags to ``imsi-tmp-compile.sh``.


Saving restarts
---------------

.. code-block:: bash

    >> imsi save-restarts

Note that likewise to ``imsi build``, ``imsi save-restarts`` just calls the extracted ``save_restart_files.sh``
script `and` any arguments and/or flags given to to the call are sent to the underlying script.

Submitting the run
------------------

.. code-block:: bash

    >> imsi submit

This will interact with the sequencer in use and intelligently execute a sequencer/machine specific submission
command.

Monitoring a run
----------------

While many HPC users will be accustomed to monitoring simulations/jobs via sequencer specific tools (``xflow``
for ``maestro`` users) or job-scheduler commands like ``qstat`` or ``squeue``. Provided the sequencer being used
support this, ``imsi`` also provides a method for monitoring the status of a simulation (or ensemble of simulations):

.. code-block:: bash

   >> imsi status

This CLI command ultimately interfaces with the sequencer caps, so **the behaviour of this command is sequencer specific**

maestro
+++++++++++

For ``maestro``, ``imsi status`` will result in:

.. image:: _static/maestro_status.png
   :alt: Maestro ``imsi status`` output
   :align: center

.. raw:: html

   <div style="height:10px"></div>


which will tell you all the ``maestro`` experiments running, and within each experiment, it will show you
which jobs are currently queued, running, failed, completed, or in ``maestro``'s "catchup" status.

iss
+++++++

This feature has not yet been implemented for ``iss`` - if you execute this command while using ``iss``, you will
see a ``NotImplementedError`` raised.


Other tips
----------

Enabling tab-completion of imsi commands
++++++++++++++++++++++++++++++++++++++++

If you are using bash v >= 4.4 and Python click v >= 8.x, you can enable tab-completion
for imsi cli commands. These are not required and are simply for convenience.

**Steps:**

1. Activate an imsi environment

.. code-block:: bash

   $ source /path/to/imsi/bin/activate

You can confirm that the environment is active by entering ``which imsi`` on your command line.

2. Generate the shell functions required, and save them to a file in a location accessible to you.

.. code-block::

   $ _IMSI_COMPLETE=bash_source imsi > ~/.imsi-complete.bash

In the example above, the file ``.imsi-complete.bash`` is saved to the user's home directory.

3. Source the file. You can do this on the command line or from within your profile.

.. code-block:: bash

   # .profile
   source ~/.imsi-complete.bash

**Result:**

You should now be able to use tabs to trigger suggested functions and options
for imsi commands. These tab-completions are triggered using **two** tabs.

.. code-block:: bash

   $ imsi <TAB><TAB>
   build          config         list           save-restarts  status
   chunk-manager  ensemble       log-state      set            submit
   clean          iss            reload         setup
   $ imsi setup -<TAB><TAB>
   --runid         --ver           --model         --seq           --flow          -h
   --repo          --exp           --fetch_method  --machine       --postproc      --help

The generalized instructions can also be found in the
`click documentation on Shell Completion <https://click.palletsprojects.com/en/stable/shell-completion/>`_
