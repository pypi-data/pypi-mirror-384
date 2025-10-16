from imsi.utils.dict_tools import flatten

def generate_diag_parameters_content(diag_config):
    """
    This creates content for the diag_parameters file for the simulation, that contains
    variable definitions required by downstream shell scripting.
    Currently this is just a pure propagation of variables from the diagnostic
    config. Ultimately, the interaction of imsi with diagnostics needs to be refined.
    """
    diag_parameters_content = list() # to populate with strings and return

    # We are making the hard assumption that there are not duplicated keys.
    # If there are, earlier ones will be overwritten with later ones.
    flat_diag_config = flatten(diag_config, sep='>')
    flat_diag_config_onekey = {}
    for k, v in flat_diag_config.items():
        key = k.split('>')[-1]
        flat_diag_config_onekey[key] = v

    diag_parameters_content.append("# Imsi created diag environment file\n")

    for k, v in flat_diag_config_onekey.items():
        if isinstance(v, list):
            # Join list elements into a single string with spaces
            var_string = " ".join(map(str, v))
        elif isinstance(v, (str, int, float, bool)):
            # Convert non-list types to string, preserving their format
            var_string = str(v)
        else:
            # Handle unexpected types, or log an error
            raise TypeError(f"Unsupported type {type(v)} for key {k}")

        # Append the export command to the list
        diag_parameters_content.append(f'export {k}="{var_string}"')
    return diag_parameters_content