from typing import Any
from omegaconf import DictConfig, OmegaConf
from typing import List, Union, Dict
import warnings


def convert_to_bracket_notation(key_string: str) -> str:
    """Convert a key string to bracket notation compatible with omegaconf keypaths"""
    keys = key_string.split(":")
    keylist = [f"[{key}]" for key in keys[1:]]
    return keys[0] + "".join(keylist)


def replace_aliases(cfg: DictConfig, aliases: dict) -> DictConfig:
    """Replace top-level keys in cfg with nested aliases (like 'setup:exp')."""
    for alias, target_path in aliases.items():
        target_path = convert_to_bracket_notation(target_path)
        if alias in cfg:
            value = cfg[alias]
            OmegaConf.update(cfg, target_path, value, merge=True)
            del cfg[alias]
    return cfg


def add_nested_key(config_dict: DictConfig, key: str, value: Any):
    """
    Traverse key with ':' to add it to a nested dictionary structure.
    """
    try:
        key_path_full = convert_to_bracket_notation(key)
        OmegaConf.update(
            config_dict,
            key_path_full,
            value,
            force_add=True,
            merge=True,
        )
    except Exception as e:
        raise ValueError(
            f"Error adding key {key} to config_dict. This may be caused by conflicting definitions of key paths provided as both a parameter and nested key."
        ) from e


def get_keys(member: DictConfig, prefix="") -> set:
    """Recursively extract all keys from a DictConfig or dictionary, including nested ones."""
    keys = set()
    for key, value in member.items():
        full_key = f"{prefix}:{key}" if prefix else key
        keys.add(full_key)
        if isinstance(value, (DictConfig, dict)):
            keys.update(get_keys(value, full_key))
    return keys


def warn_on_overlapping_keys(cfg1: DictConfig, cfg2: DictConfig):
    """Warn if any keypaths overlap between two configs."""
    keys1 = get_keys(cfg1)
    keys2 = get_keys(cfg2)
    overlap = keys1 & keys2
    if overlap:
        warnings.warn(
            colour(
                f"Overlapping keys detected between table and entry config: {sorted(overlap)}. The values in the table will override those in the entry config.",
                "yellow"
            ),
            UserWarning
        )


def colour(text, c):
    """Basic ANSI colourizer."""
    codes = dict(red="\033[91m", green="\033[92m", yellow="\033[93m", reset="\033[0m")
    return f"{codes[c]}{text}{codes['reset']}"


def check_keys_against_reference(dict_list: List[Union[DictConfig, dict]]):
    """Compare each config to the first one and report any key mismatches."""
    if not dict_list:
        print(colour("⚠️  Config list is empty — skipping key comparison.", "yellow"))
        return

    ref_keys = get_keys(dict_list[0])

    for i, member in enumerate(dict_list[1:], start=1):
        member_keys = get_keys(member)
        extra = member_keys - ref_keys
        missing = ref_keys - member_keys

        if extra or missing:
            print(colour(f"\n  Key mismatch between config[0] (reference) and config[{i}]:", "yellow"))
            print(colour("\n  This message can be safely ignored if this is intentional.", "yellow"))
            if extra:
                print(colour(f"  - Extra keys in member[{i}]:", "green"))
                for key in sorted(extra):
                    print(f"    + {key}")
            if missing:
                print(colour(f"  - Missing keys in member[{i}]:", "red"))
                for key in sorted(missing):
                    print(f"    - {key}")
        else:
            print(colour(f"✓ Member[{i}] keys exactly match reference keys.", "green"))


def remove_explicit_none(member):
    """Remove keys with explicit None values recursively from config_list"""
    for k, v in list(member.items()):
        if v is None:
            member.pop(k)
        if isinstance(v, (dict, DictConfig)):
            remove_explicit_none(v)
    return OmegaConf.create(member)


def validate_runids(cfg_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate or auto-generate unique 'runid' values in each configuration's 'setup' block."""

    # Check and collect runids
    runid_list = []
    for idx, member in enumerate(cfg_list):
        try:
            runid = member['setup']['runid']
            runid_list.append(runid)
        except (KeyError, TypeError):
            raise ValueError(
                colour(
                    f"\n❌ Missing 'setup.runid' in member index {idx}. Each member must have a 'setup' dictionary with a 'runid' key.",
                    "red"
                )
            )

    # Check uniqueness
    unique_runids = set(runid_list)
    if len(unique_runids) < len(cfg_list):
        warnings.warn(
            colour(
                f"\n⚠️  Duplicate 'runid' values detected across {len(cfg_list)} ensemble members "
                f"(only {len(unique_runids)} unique): {runid_list}\n"
                "➡️  To ensure consistent file naming and output isolation, each runid will be auto-suffixed with its index (e.g., 'runid-0', 'runid-1', ...).",
                "yellow"
            )
        )

        for i, member in enumerate(cfg_list):
            old_runid = member['setup']['runid']
            new_runid = f"{old_runid}-{i}"
            cfg_list[i]['setup']['runid'] = new_runid

    return cfg_list


def validate_table_data(table, show_diffs=False):
    table = [remove_explicit_none(d) for d in table]
    table = validate_runids(table)
    if show_diffs:
        check_keys_against_reference(table)

    return table
