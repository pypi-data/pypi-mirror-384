=======================================
Developing or modifying configurations
=======================================

.. TODO: add more examples here

Adding new options for future reuse
------------------------------------

Options allow for selection from a range or choices, similar to what would be
provided by an if statement or switch in scripting. In the ``imsi-config``
directory of the source code, modify the ``models`` / ``model_options.yaml``,
and add options following the examples provided. Any imsi setting can be
modified via this mechanism.

.. note::

   This is a work in-progress and examples will be added in the near future.

Adding new models or experiments
--------------------------------

To add new experiments of models, you must create a new model or experiment
file in the models ``imsi_config`` directory. Start from an experiment/model
that is as close to your target experiment as possible and copy and edit its
yaml file.  Use the ``inherits_from`` functionality to point to this experiment
as the parent. Then modify ONLY what you have to create your new
model/experiment. Using inheritance in this way reduces repetition, and ensure
that if a setting is altered in the parent configuration, that it is propagated
into yours.

The `CanESM Changes Tutorial <https://gitlab.com/CP4C/cp4c-docs/-/blob/main/cp4c-tutorial-apr-2024/canesm_changes_tutorial.ipynb>`_
provides some direct examples of creating a new experiment.

Porting an imsi based model to a new machine
--------------------------------------------

To add a new machine, you will need to:

1. add a new machine file/section at ``machines:MACHINE_NAME`` under ``imsi_config``

   These files are typically under a ``machines`` directory. Notable entries are

      * ``suported_compilers`` : defines what compilers `can` be used on the machine
      * ``default_compiler`` : defines what compiler will be used if the user doesn't provide one
      * ``sequencers`` : defines a list of sequencers available on this machine
      * ``default_sequencing_suffix`` : defines what suffix is attached to baseflows to determine the machine specific sequencer flow details

   .. note::

      if users `do not` provide the ``--seq SEQUENCER`` argument to ``imsi setup``,
      ``imsi`` will pull the **first** entry in the ``sequencers`` list.

   In addition, you will need to figure out details about the environment/variables that will need to be considered.
   In general it is easiest to start from a closely related machine and `when appropriate` use the ``inherits_from``
   field.

2. if a machine specific compiler definition is required, add a section for it under the ``compilers`` section

    These files are typically under a ``compilers`` directory. Likewise to the machines, it generally easiest to
    start from an example definition set and modify it as needed.

3. add a new sequencing section under ``sequencing:sequencing_flow:{DESIRED_BASEFLOW}-{default_sequencing_suffix}``

    where ``DESIRED_BASEFLOW`` is an existing baseflow you want to use on this
    machine, and ``default_sequencing_suffix`` will be defined in the machine configuration file. See
    :ref:`below <Sequencing and sequencer configuration>` for extra details on this. Again
    it is recommended using existing cases as a starting point, making use of ``inherits_from`` as applicable.

Using imsi with a different model alltogether
---------------------------------------------

While imsi was originally create to configure models from the CCCma Integrated Modelling System,
it can be used to configure any model in principle. The key requirements are to create the 
``imsi-config`` directory at the top level of the model code repository, and populate it with
the relavant ``yaml`` files that describe the configuration of the model.

The imsi code itself has no knowledge about the underlying model. All model specific information
is injected through the yaml configuration.

Sequencing and sequencer configuration
--------------------------------------

Configuring the sequencer/sequencing setup is more nuanced that other parts of the configuration due to the
interconnected nature between:

- models & experiments, which dictate:
   - what jobs you want to run
   - how many simulated years you might want
- machines, which dictates:
   - what sequencers are available
   - what resource configurations are allowed (i.e. how many days can be simulated in the allowable wall-clock?)
- sequencer choice, which dictates:
   - `how` jobs are ran and interconnected

As such, this section lays out how these things work together in order educate ``imsi`` users how
to build this consideration into their configuration. Again, developers are encouraged to use `existing`
examples to help guide future configurations.

Run Dates and Chunking
~~~~~~~~~~~~~~~~~~~~~~

As part of any configuration, you need to define things like:

* When does your simulation start and stop, and
* Do you want to launch only a `portion` of the simulation, or a "segment"
* How do you want to `chunk` your simulation within a segment

Note that a run "segment" refers to the portion of a simulation you plan on
running.  For example, your actual desired dates for the entire experiment
might be ``1850-01-01`` to ``2015-12-31``. However, you might wish to only
launch the first 50 years at first in order to assess how the run is
progressing. **This first 50 years would be a "run segment"** - after it
completes, you might then launch the second segment of the experiment, going
from ``1900-01-01`` to ``2015-12-31``. Within each segment, jobs will be need to
be chunked in order to fit within typical HPC wallclock limits.

With these details in mind, these settings are all defined via the:

.. code-block:: yaml

   sequencing:run_dates

key path. Specifically:

* ``run_start_time``: defines the true start time of this experiment (largely for meta data)
* ``run_stop_time``: defines the true stop time of this experiment (largely for meta data)
* ``run_segment_start_time``: defines the start time for the segment about to be launched
* ``run_segment_stop_time``: defines the stop time for the segment about to be launched
* ``model_chunk_size``: within one model job, this defines how long the model will execute
* ``model_internal_chunk_size``: allows for looping `within` a model job at the defined chunk size
* ``postproc_chunk_size``: defines chunk size for post-processing jobs

.. note::

   If ``run_segment_start_time == run_start_time``, and ``run_segment_stop_time
   == run_stop_time`` your simulation will attempt to execute in one segment.
   There will still be job chunking within that segment, according to the
   various ``*_chunk_size`` variables noted above.

.. note::

   The above variables follow ISO 8601 date standards - the ``time`` variables
   support ISO dates, while the ``chunk_size`` variables follow ISO duration
   standards. However it should be noted that the durations deviate from the
   standards slightly in that ``MS`` is used to state that jobs should stop at
   month boundaries, even if the initial start date isn't at a month boundary.

.. note::

   ``imsi`` supports the ability to extract unique variable values from other parts
   of the configuration. A common use of this is to make it so the ``run_dates`` section
   pulls the start/end times associated with experiment definitions - e.g.

   .. code-block:: yaml

      run_segment_start_time : '{{start_time}}'

   will tell ``imsi`` to pull the ``start_time`` value from the experiment definition.

In general, the dates should be automatically extracted from the experiment definition
so users will likely not need to modify these configs much. However, for experiments/configurations
with different computational complexity, users may wish to alter the chunk sizes
to account for this. Users can achieve this by either:

1. modifying the ``*_chunk_size`` variables under ``src/imsi-config`` and running ``imsi reload`` or
2. modifying the ``*_chunk_size`` variables under ``imsi_configuration_<runid>.yaml`` and running ``imsi config``

Sequencing Flow
~~~~~~~~~~~~~~~

To define what jobs will run and with what resources, ``imsi`` relies on the

.. code-block:: yaml

   sequencing:sequencing_flow

key path.

Specifically, ``imsi`` will look for ``sequencing:sequencing_flow:FLOW_NAME``, where
the flow name is determined by one of two methods:

1. **automatically via the** ``machine`` **and sequencer specific configuration**

   Specifically, this is achieved by ``imsi``:

   1. extracting the first sequencer in ``machines:MACHINE_NAME:sequencers`` to determine what sequencer it should use
   2. extracting the ``default_sequencing_suffix`` from machine config
   3. extracts the ``model_type`` from the experiment/model configuration
   4. extracts the `non-machine specific` ``FLOW_NAME`` from ``sequencing:sequencers:SEQUENCER_NAME:baseflows:model_type``
   5. appends ``default_sequencing_suffix`` to the `non-machine specific` ``FLOW_NAME`` such that ``FLOW_NAME=${FLOW_NAME}-${default_sequencing_suffix}``

2. **from the** ``--flow`` **argument to** ``imsi setup``

With this in mind, modifications/development of sequencer flows can be achieved via:

* if a user wishes to alter resources for **all machines that use a version of the flow**:

    Simply find the desired non-machine specific flow name under ``sequencing:sequencing_flow`` and alter the values
    as necessary. If already in a run, ``imsi reload`` will be required to apply the changes.

* if a user wishes to alter the resources **for a machine specific flow**:

    Similar to non-machine specific flows, but just find the machine specific flow name and make the modifications
    there.

* if a user wishes to **add a new flow**:

    Use an existing flow as a starting place and come up with a new name for it
    and build it out as desired.  **Note** that if you want to have this flow
    picked up automatically, you will need to add a non-machine specific flow,
    along with the machine specific equivalent. You will also need to add
    consideration in the :ref:`sequencer specific configuration <Sequencer
    Specific Configuration>`.


.. note::

   Some flow configurations make use of a ``directives`` field. This is `only`
   used by certain sequencers. Specifically, ``iss`` makes use of the
   ``directives``, while ``maestro`` uses the more specific variables like
   ``memory``, ``wallclock``, and ``processors``


Sequencer Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each supported sequencer, ``imsi`` requires knowledge of how they
`specifically` get configured. This
is achieved via the:

.. code-block:: yaml

   sequencing:sequencers:SEQUENCER_NAME

key path. The exact specifics of the sequencer unique fields will be documented
in sequencer specific documenation pages, but important common fields are:

* ``supported_machines``:

   Defines what machines can `use` this sequencer
* ``baseflows``:

   These define what "baseflows" this sequencer has been setup to use for each ``model_type``.
   Note that these aren't `machine specific` - ``imsi`` combines this knowledge with the
   ``sequencing_flow`` information to setup the sequencers.
