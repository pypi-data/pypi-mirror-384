"""
A utility that launches calls to 'hook's (functions) in
`config_hooks_collection.py` using conditions set in the config json.
"""

import os
from pathlib import Path

from imsi.config_manager.config_manager import Configuration
from imsi.shell_interface import config_hooks_collection
from imsi.utils.dict_tools import flatten, load_config_file


def get_hook_config(step):
    # for now make this a hard-coded file
    path = os.path.dirname(__file__)
    filename = os.path.join(path, 'config_hooks_collection_config.yaml')

    c = load_config_file(Path(filename))
    try:
        return c['config_hooks'][step]
    except KeyError:
        return {}


def call_hooks(configuration: Configuration, step='config', **kwargs):
    """Call all the hooks under the `step` based on current state of `Configuration`.

    The values in `Configuration` will be matched against the constraints
    (conditional requirements) defined in the config json. If all constraints
    are met, all hooks defined under the `step` are called (where hook names
    match the function names in config_hooks_collection.py)
    """

    key_sep = ":"
    config_hooks = get_hook_config(step)

    if not config_hooks:
        # no hooks defined for this step
        return

    # make sure that all the hooks (function names) exists
    for hook in config_hooks:
        try:
            fx = getattr(config_hooks_collection, hook['run'])
        except AttributeError as e:
            raise KeyError('imsi error: function hook {} does not exist'.format(hook['run'])) from e

    # validate all constraints
    # the first key must correspond to an imsi subconfig
    constraint_subconfigs_requested = [l for s in [c['constraints'].keys() for c in config_hooks] for l in s]
    for c in constraint_subconfigs_requested:
        try:
            configuration.model_dump()[c]
        except (ValueError, KeyError, AttributeError) as e:
            raise e

    # all subconfig are valid, then check:
    #   1. if config exists/is valid (if not, fail), then
    #   2. if constraints are met (if so, run hook)
    for hook in config_hooks:

        constraints = hook['constraints']
        constraints_met = []

        for subconfig_name, subconfig in constraints.items():

            # leverage flattened keys to do easy nested-dict comparisons
            flat_config = flatten(
                configuration.model_dump()[subconfig_name], sep=key_sep
            )
            flat_constraints = flatten(subconfig, sep=key_sep)

            for keypath, rule in flat_constraints.items():

                # test if exists
                try:
                    setting = flat_config[keypath]
                except KeyError:
                    raise ValueError("the following constraints are not configured in the current configuration for the config hook {}:\n{}".format(hook['run'], subconfig))

                # test if constraints met
                constraints_met.append(setting == rule)

        if all(constraints_met):
            # if all constraints are met, then run the hook.
            # *the function is called dynamically*
            hook_fx = getattr(config_hooks_collection, hook['run'])
            hook_fx(configuration, **kwargs)
