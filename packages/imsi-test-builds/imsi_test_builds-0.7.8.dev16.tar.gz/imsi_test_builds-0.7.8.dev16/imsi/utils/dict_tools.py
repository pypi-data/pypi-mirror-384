"""
utils
=====

Utility functions used in imsi, largely for parsing json,
and updating, searching and modifying nested python dicts.

"""
import traceback
import yaml
import json5
import collections
import fnmatch
import os
import re
from collections import Counter
from pathlib import Path
from omegaconf import OmegaConf

def load_config_file(config_file):
    """Reads a config file using the appropriate
    function for the file type (supports yaml or json)"""
    if config_file.suffix == '.yaml':
        return OmegaConf.load(config_file)
    elif config_file.suffix in [".json", ".jsonc"]:
        return load_json(config_file)
    else:
        raise ValueError(f"Unsupported file type: {config_file}")

def load_json(config_file):
    """Reads a json config file"""
    with open(config_file) as f:
        # Note order can be important so use ordered dicts
        config = json5.load(f, object_pairs_hook={})
    return config


def update(d,u, verbose=False):
    """
    Recursively update a dictionary, d, with an update, u.
    If an item appears in only one dictionary, it is included in the result.

    Parameters:
      d : dict to update
      u : dict of updates

    Returns:
    --------
      d : updated dict
    """
    #Based on:
    #https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    #Note this is the workhorse of all imsi inheritance behaviour.
    for k, v in u.items():
        if verbose:
            print(f"Updating {k}={v}")
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def flatten(d, parent_key='', sep='_'):
    """Flatten a nested dict, using sep to join keys from levels in order"""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def recursive_lookup(key, d):
    """Find a unique key in a nested dict. Will not be graceful if there are duplicates!"""
    for k, v in d.items():
        if k == key:
            yield v
        elif isinstance(v, collections.abc.MutableMapping):
            for result in recursive_lookup(key, v):
                yield result

def combine_yaml_configs(rootpath):
    """combine all YAML files found recursively under rootpath into one dictionary.
    This effectively provides a dictionary-database to use.

    Parameters:
       rootpath : str
          The path to recursively search for input files ending in .yaml
          Normally this is the path to the imsi-config directory.

    Outputs:
       config: dict
          A dictionary of the contents of the json or combined json files found under rootpath.
    """
    # Note: obviously combine_configs should be generalized to arbitrary data format, just doing for now...

    config = {}
    for source_subpath in Path(rootpath).rglob("*.yaml"):
        try:
            temp_config = OmegaConf.load(source_subpath)
            temp_config = OmegaConf.to_container(temp_config, resolve=True)
            config = update(config, temp_config)
        except yaml.scanner.ScannerError:
            traceback.print_exc(limit=1)
            exit(1)

    return config

def combine_json_configs(rootpath):
    """combine all json files found recursively under rootpath into one dictionary.
       This effectively provides a dictionary-database to use.

       Parameters:
          rootpath : str
             The path to recursively search for input files ending in .json/.jsonc.
             Normally this is the path to the imsi-config directory.

       Outputs:
          config: dict
             A dictionary of the contents of the json or combined json files found under rootpath.
    """
    files = []
    config = {}
    patterns = ['*.json', '*.jsonc']
    for root, dir, filenames in os.walk(rootpath):
        for pattern in patterns:
            for f in fnmatch.filter(filenames, pattern):
                files.append(os.path.join(root, f))
                temp_dict = load_json(os.path.join(root, f))
                config = update(config, temp_dict)
    return config

def resolve_inheritance(configs, selected_config, config_hierarchy):
    """
    Resolve the inheritance tree through recursion and exclusion of duplicates.
    Ensure ancestors precede descendents.

    Parameters:
       configs: dict
          dictionary of all possible configurations, typically from an imsi_database.
       selected_config: str
          The configuration to choose
       config_hierarchy: list
          Typically not user specified, but used in the recursive function call to
          layer configurations in the correct order of inheritance.
    """

    config = configs[selected_config]

    if 'inherits_from' in config and config['inherits_from']:
        parent_configs = config['inherits_from']
        if isinstance(parent_configs, str):
            parent_configs = [parent_configs]

        for parent_config in reversed(parent_configs):
            if parent_config in configs.keys():
                config_hierarchy = resolve_inheritance(configs=configs, selected_config=parent_config, config_hierarchy=config_hierarchy)

            else:
                raise NameError(f'{parent_config} not found. Check inheritance in {selected_config}')

    if config not in config_hierarchy:
        config_hierarchy.append(config)

    return config_hierarchy

def parse_config_inheritance(configs, selected_config):
    """
    Parse a configuration, inheriting attributes from all "parents".

    Parameters:
       configs: dict
          dictionary of all possible configurations, typically from an imsi_database.
       selected_config: str
          The configuration to choose
       config_hierarchy: list
          Typically not user specified, but used in the recursive function call to
          layer configurations in the correct order of inheritance.
    """

    config = configs[selected_config]

    config_hierarchy = []
    config_hierarchy = resolve_inheritance(configs, selected_config, config_hierarchy)

    if len(config_hierarchy) > 1:
        config = {}

        for child in config_hierarchy:
            config = update(config, child)

    return config

def parse_config_inheritance_org(configs, selected_config, config_hierachy=None):
    """
    Parse a configuration recursively inheriting attributes from all "parents".

    Parameters:
       configs: dict
          dictionary of all possible configurations, typically from an imsi_database.
       selected_config: str
          The configuration to choose
       config_hierachy: dict
          Typically not user specified, but used in the recursive function call to
          layer configurations in the correct order of inheritance.
    """
    # Curiously, assigning config_hierachy to an empty default
    # leads to persistent values leaking across function calls. -> probably due to lists being mutable.
    if config_hierachy is None:
        config_hierachy = []
    config = configs[selected_config]
    config_hierachy.append(config)
    if 'inherits_from' in config and config['inherits_from']:
        parent_config = config['inherits_from']
        if parent_config in configs.keys():
            config = parse_config_inheritance(configs=configs, selected_config=parent_config, config_hierachy=config_hierachy)
        else:
            raise NameError(f'{parent_config} not found. Check inheritance in {selected_config}')
    else:
        if len(config_hierachy)>1:
            config = {}
            config_hierachy.reverse()
            for child in config_hierachy:
                config = update(config, child)
    return config

def parse_var(s):
    """
    Parse a key, value pair, separated by '='
    That's the reverse of ShellArgs.
    On the command line (argparse) a declaration will typically look like::

        foo=hello

    or::

        foo="hello world"

    Courtesy https://stackoverflow.com/questions/27146262/create-variable-key-value-pairs-with-argparse-python
    """
    items = s.split('=')
    key = items[0].strip() # we remove blanks around keys, as is logical
    if len(items) > 1:
        # rejoin the rest:
        value = '='.join(items[1:])
    return (key, value)


def parse_vars(items):
    """
    Parse a series of key-value pairs and return a dictionary
    Courtesy https://stackoverflow.com/questions/27146262/create-variable-key-value-pairs-with-argparse-python

    """
    d = {}

    if items:
        for item in items:
            key, value = parse_var(item)
            d[key] = value
    return d

# ChatGPT beauty
def replace_variables(obj, inputs):
    if isinstance(obj, dict):
        # If obj is a dictionary, iterate through its key-value pairs
        for key, value in obj.items():
            obj[key] = replace_variables(value, inputs)
        return obj
    elif isinstance(obj, list):
        # If obj is a list, iterate through its elements
        return [replace_variables(item, inputs) for item in obj]
    elif isinstance(obj, str):
        # If obj is a string, perform variable replacement
        return replace_variables_in_string(obj, inputs)
    else:
        # For other data types, return the object as is
        return obj

def replace_variables_in_string(s, inputs):
    # Define a function to replace variables in a string
    def replace(match):
        variable_name = match.group(1)
        if variable_name in inputs:
            return str(inputs[variable_name])  # Convert the value to a string
        else:
            return match.group(0)  # If variable not found, keep it as is


    # Use regular expression to find and replace variables in the string
    pattern = r'{{(.*?)}}'
    return re.sub(pattern, replace, s)

def replace_curlies_in_dict(input_dict, replacement_dict):
    pattern = re.compile(r"{{(.*?)}}")

    def replace_in_string(s, repl_dict):
        matches = pattern.findall(s)
        for match in matches:
            value = deep_get(repl_dict, match)
            if value is not None:
                s = s.replace(f"{{{{{match}}}}}", str(value))
        return s

    def deep_get(d, key):
        if isinstance(d, dict):
            if key in d:
                return d[key]
            for k, v in d.items():
                result = deep_get(v, key)
                if result is not None:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = deep_get(item, key)
                if result is not None:
                    return result
        return None

    def recursive_replace(d, repl_dict):
        if isinstance(d, dict):
            return {k: recursive_replace(v, repl_dict) for k, v in d.items()}
        elif isinstance(d, list):
            return [recursive_replace(i, repl_dict) for i in d]
        elif isinstance(d, str):
            return replace_in_string(d, repl_dict)
        else:
            return d

    def find_referenced_keys(d, pattern):
        referenced_keys = set()
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str):
                    matches = pattern.findall(v)
                    referenced_keys.update(matches)
                else:
                    referenced_keys.update(find_referenced_keys(v, pattern))
        elif isinstance(d, list):
            for item in d:
                referenced_keys.update(find_referenced_keys(item, pattern))
        return referenced_keys

    def check_for_duplicate_keys(replacement_dict, referenced_keys):
        key_counter = Counter()
        def count_keys(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k in referenced_keys:
                        key_counter[k] += 1
                    count_keys(v)
            elif isinstance(d, list):
                for item in d:
                    count_keys(item)

        count_keys(replacement_dict)

        duplicates = [k for k, count in key_counter.items() if count > 1]
        if duplicates:
            raise ValueError(f"Duplicate keys found in replacement_dict for referenced variables: {', '.join(duplicates)}")

    referenced_keys = find_referenced_keys(input_dict, pattern)
    check_for_duplicate_keys(replacement_dict, referenced_keys)

    return recursive_replace(input_dict, replacement_dict)
