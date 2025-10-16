====================================================================
The imsi developer guide
====================================================================

.. IMPORTANT::
    This section of the documentation is under active development.
    Information contained herein is likely sparse and subject to change.
    Expect placeholders ahead. Readers and developers beware!


imsi is a comprehensive python package. As such, developers are able to modify
and adapt the source code to their needs  (as permitted through the
:ref:`imsi-license`). This section provides additional information
for those interested in developing imsi.


Contributing
--------------------------------

Bugs and feature requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..
    TODO: decide which repo bug reports should live in

If you find something broken in imsi or have a request for a feature,
please open an issue in the source repository.

Standards
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..
    TODO: list some guiding principles here

-
-

Testing
--------------------

imsi includes unit and integration tests located in the top-level tests directory.
The tests follow pytest standards and setup settings can be configured through ``tests/.env.test``, which sets environment variables used during execution.

These tests focus on common use cases of imsi and its underlying functions. They are not exhaustive, and ongoing development is needed to keep them aligned with code changes. Their purpose is to reduce the need for manual testing and to complement the bit-identity checks performed in CanESM.

Installing test dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


From the top-level of the imsi repository, install the test requirements:

.. code:: bash

    pip install -e .[tests]

Running all tests

.. code:: bash

    coverage run -m pytest tests/

Running a specific test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To avoid waiting for longer test suites to complete, you can run an individual test:

.. code:: bash

    coverage run -m pytest tests/path/to/test/test_file.py::specific_test_name

Coverage reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To inspect test coverage, run:

.. code:: bash

    coverage report
    coverage html


For more details, see the Coverage documentation <https://coverage.readthedocs.io/en/latest/>_.


When to run and write tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All contributors are responsible for keeping imsi tests up to date. Follow these rules whenever you make changes:

1. Run tests frequently

    - Run the full test suite (with coverage) whenever you modify the codebase.

    - Always run tests as part of your merge request into main to confirm no breaking changes are introduced.

2. Write or update tests

- Add tests whenever you:

    - Introduce new functionality.

    - Fix a bug (write a regression test to prevent it from reappearing).

    - Modify existing behavior (update tests only if the change is intentional).

    - Ensure your tests capture both expected behavior and common failure modes.

3. Before opening a merge request

    - Run coverage run -m pytest tests/.

    - Verify that all tests pass.

    - Check test coverage with coverage report or coverage html.

    - Confirm that any new code paths are covered by tests.

Following this checklist ensures imsi stays reliable, reduces manual testing, and speeds up code review.


Extending configuration
--------------------------------

hooks
^^^^^^

An experiment run is set up through various internal setup and configuration
commands in imsi. For certain modelling platforms or base configurations,
a developer may want to execute additional steps that alter or augment
actions in imsi. For instance, a developer may want to add a step that
calls a separate utility after the imsi config commands complete.

These types of additional steps can be added through a "hook", which is a
dynamically loaded and conditionally executed python function within the
imsi package. A hook is defined within and executed through the
``config_hooks_*`` files under ``/imsi/shell_interface``:

.. code:: bash

    # directory structure under /imsi
    ...
    ├── shell_interface
    │   ├── ...
    │   ├── config_hooks_collection_config.json   # conditions (constraints)
    │   ├── config_hooks_collection.py            # functions (hooks)
    │   ├── config_hooks_manager.py               # dynamically calls the hooks
    │   └── ...
    ...

As development of a modelling platform under imsi expands, managing control flow
can become unweildy. Developers can avoid having to write
these complex logic blocks into imsi code directly by instead defining a
hook as a function (in ``config_hooks_collection.py``) and a set of
conditions (in ``config_hooks_collection_config.json``).

**About hooks**

Individual hooks (functions) are stored in ``config_hooks_collection.py``. The functions
are named using the convention:

.. code:: python

    def {imsi_step}_{description_of_function}(configuration: Configuration):
        ...

While the naming convention is useful for organization, it is left to the
developer to name and call these functions appropriately.

A hook should only be run if certain constraints (conditions) within the
imsi configuration (stored within the ``Configuration`` object) are met.
The hook and corresponding conditions are defined in the
``config_hooks_collection_config.json`` file (the "config json"), as
structured lists of key-value pairs. The key-value pairs must match the
structure of the ``Configuration`` dictionary. Multiple hooks can be
defined under the same "hook set" (recommended naming as an imsi step):

.. code:: json

    {
        "config_hooks" : {           // required
            "stepname" : [           // step/hook set - a list of hooks follows
                {
                    "run": "stepname_do_a",     // function name
                    "constraints": {
                        "subconfigname": {      // conditions that must be
                            "condition_a": 1,   // met for function to run
                            "condition_b": {
                                "keyb": "on"
                            }
                        }
                    }
                }
            ]
        }
    }

.. NOTE::
    Currently, constraints are limited to only performing the operations
    "equal" for key-value pairs and "logical and" across multiple
    key-value pairs.

Again, while the constraints define when a hook *should* run,
it is left to the developer to make sure that the constraints are actually
checked *beforehand*. Instead of writing the checks into the function itself,
the main way to do this is to invoke the ``call_hooks()`` function as
a "wrapper" that will call all the hooks for the requested step (set). That is:

.. code:: python

    config_hooks_manager.call_hooks(configuration, step)

where ``configuration`` is the imsi ``Configuration`` object, and ``step``
corresponds to the set of hooks defined in the config json.

.. CAUTION::
    Hooks require advanced knowledge of the imsi package and any files
    produced by imsi as part of the modelling platform implemented.
    Developers should only implement hooks when absolutely
    necessary and ensure that they do not compromise imsi's functionality.

**Example: making a new hook**

For example, suppose you'd like to implement a hook that writes a
file to the ``/config`` folder of an experiment folder as part of imsi's
setup:

.. code:: python

    # config_hooks_collection.py
    def setup_write_exp_info(configuration):
        """Write config information to file in /config folder"""
        path = os.path.join(configuration.setup_params.work_dir, "config")
        source_id = configuration.source_id
        runid = configuration.setup_params.runid
        with open(os.path.join(path, "custom_output_file.txt"), "w") as f:
            f.write("# custom output\n")
            f.write(f"source_id={source_id}\n")
            f.write(f"runid={runid}\n")
            f.write(os.linesep)

Suppose you want to ensure that this function only runs if the
``source_id`` of the experiment is set to ``"ModelA1-2"``.
The constraints for this hook would then be:

.. code:: json

    // config_hooks_collection_config.json
    {
        "config_hooks" : {
            "setup" : [
                {
                    "run": "setup_write_exp_info",
                    "constraints": {
                        "model": {
                            "source_id": "ModelA1-2"
                        }
                    }
                }
            ]
        }
    }

Remember, the function name begins with ``setup_*``, indicating that
this should occurs after imsi's setup has completed, but as the imsi
developer it is up to you to find the appropriate place to call this
hook set. The call would then be:

.. code:: python
    :class: highlight-good

    # Correct:

    # Call of hooks using call_hooks()

    # inside the appropriate imsi module/function
    from imsi.utils.config_hooks_manager import call_hooks

    # Other code, then where needed:
    call_hooks(configuration, "setup")

.. code:: python
    :class: highlight-bad

    # Wrong:

    # Calling the hook directly will not automatically check
    # if the constraints are met.
    setup_write_exp_info(configuration)

Building on this example, if you wanted to add another hook to run at after the first,
simply add it to the list under the same hook set:

.. code:: python

    # config_hooks_collection.py
    def setup_another_hook(configuration):
        print("hello", configuration.setup_params.parameters['runid'])

.. code:: json

    // config_hooks_collection_config.json
    {
        "config_hooks" : {
            "setup" : [
                {
                    "run": "setup_write_exp_info",
                    "constraints": {
                        "model": {
                            "source_id": "ModelA1-2"
                        }
                    }
                },
                {
                    "run": "setup_another_hook",
                    "constraints": {
                        "model": {
                            "source_id": "ModelA1-2"
                        }
                    }
                }
            ]
        }
    }

You do not need to modify the ``call_hooks()`` call where it has been added
in the imsi code.


Building the docs
-------------------------------

Under the main repo directory, is a ``.readthedocs.yml`` file that configures the documentation build process for Read the Docs. This file specifies the necessary settings and dependencies for building the documentation.

Building the docs offline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can build a local version of imsi with the option to build the imsi docs with

.. code:: bash

    pip install .[docs]

This will install sphinx and other packages required for building.

To build the docs, you can use the sphinx CLI included when you install the optional docs dependencies. E.g.:

.. code:: bash

    sphinx-build -M html docs/ ~/public_html/docs

