Imsi Tracking
=============

``imsi`` has been built to facilate the setup, configuration, and running of
complex physics-based models on different HPC platforms. For these problems,
there are countless degrees of freedom involved:

1. model code version
2. physical parameters/settings
3. compiler configuration (ex: compiler used; optimization settings)
4. technical parameters/settings (ex: MPI layout)
5. sequencing configuration
6. machine specific settings
7. etc...

All of these settings can make reproducibility hard to ensure, as it is easy for
human eyes to lose track of all the settings they have activated. As such, a tracking toolkit has been
added to ``imsi`` to help with this - specifically it tracks:

1. What ``imsi`` commands were executed to setup and manipulate the run
2. What config files are actually used by the simulation and how they've changed throughout it
3. What version of the source code has been used for the simulation and if any changes occurred during it

What is tracked?
----------------

At a high level, there are three distinct items that need to be considered to reproduce a run:

1. what version of the source repo was used?
2. what version of the config files were used?
3. what machine was the simulation ran on?

Where No. 3 is implicitly tracked in the config files. As such, the majority of the
``imsi`` tracking system is devoted to tracking the status/version of the source repo under ``src/``
and the config files under ``config/`` - it is important to note that to faciliate easy tracking of the files under ``config/``,
``imsi`` initiates it as a local ``git`` repo.

With the above stated, for each of these directories ``imsi`` tracks:

1. the commit hash
2. the status of the repo
3. any ``diffs`` found in the repos

where the details are stored under ``.imsi/states`` within the run's setup directory.

The ``imsi`` ``states`` directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To track the uniqueness of the ``config`` and ``src`` directories, ``imsi`` relies on ``md5sum`` to checksum
the contents and produce one unique hash to represent the status of these directories - these unique hashes are
what users will find under

.. code-block:: bash

   .imsi/states

Under each hash directory, you can find:

.. code-block:: bash

   src_*_rev.txt
   src_*_status.txt
   src_*_diff.diff
   config_*_rev.txt
   config_*_status.txt
   config_*_diff.diff

where (for each relevant repo):

* ``*_rev.txt`` files contain the current git commit hashes
* ``*_status.txt`` files contain information on what files have changes
* ``*_diff.diff`` files contain the actual ``git diff`` output


When does tracking occur
------------------------

By default, ``imsi`` only logs the above information for certain ``cli`` commands - specifically:

* ``imsi config``
* ``imsi reload``
* ``imsi set``
* ``imsi build```
* ``imsi submit``
* ``imsi save-restarts``

In addition to tracking the ``config/`` and ``src/`` repos, ``imsi`` also stores a
cli command log at ``.imsi-cli.log`` in the setup directory.

.. note::

   Due to the implementation of ``imsi ensemble``, if the above commands are executed
   using ``imsi ensemble <command>``, ``imsi`` will still log the necessary information for
   each member of the ensemble

How to add tracking points
^^^^^^^^^^^^^^^^^^^^^^^^^^

While the above mentioned log points provide a good default state-logging framework, users
might wish to have explicit state-logging at other points throughout their job scripts. For example,
some groups might wish to explicitly track state of things right before the model launches in order
to ensure no local user changes might go un-noticed. To do this, users can instrument their scripting with

.. code-block:: bash

   imsi log-state -m "USEFUL LOGGING MESSAGE" -p /path/to/runid/setup/directory

This will then make imsi track the state of the various directories at that exact point.

What to do with tracking artifacts?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are on an HPC system where you can keep runs on-disk for a `long` time, simply relying on
the various directory structures might be enough for you. `However` in most cases, users will need
to clean-up simulations after they are completed and so the necessary reproducibility information might
be lost.

As such, if you have access to an archiving system, it is recommended that users setup a job to dump

* the local ``config/`` directory and
* the local ``.imsi/states`` directory

to whatever archive system their machines have access to. With this, users should be able to determine
all the necessary details to `potentially` re-run past simulations.
