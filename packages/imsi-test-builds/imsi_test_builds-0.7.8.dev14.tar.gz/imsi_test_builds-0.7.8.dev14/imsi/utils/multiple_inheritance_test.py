def parse_config_inheritance(configs, selected_config, config_hierarchy=None):
    """
    Parse a configuration recursively inheriting attributes from all "parents".

    Inputs:
    -------
       configs: dict
          dictionary of all possible configurations, typically from an imsi_database.
       selected_config: str
          The configuration to choose
       config_hierarchy: list
          Typically not user specified, but used in the recursive function call to
          layer configurations in the correct order of inheritance.
    """
    if config_hierarchy is None:
        config_hierarchy = []

    config = configs[selected_config]
    config_hierarchy.append(config)

    if 'inherits_from' in config and config['inherits_from']:
        parent_configs = config['inherits_from']
        if isinstance(parent_configs, str):
            parent_configs = [parent_configs]

        for parent_config in reversed(parent_configs):
            if parent_config in configs.keys():
                config = parse_config_inheritance(configs=configs, selected_config=parent_config, config_hierarchy=config_hierarchy)
            else:
                raise NameError(f'{parent_config} not found. Check inheritance in {selected_config}')
    else:
        if len(config_hierarchy) > 1:
            config = {}
            config_hierarchy.reverse()
            for child in config_hierarchy:
                config = update(config, child)

    return config

def update(config, child):
    """
    Update the config with values from child, overriding existing keys.

    Inputs:
    -------
       config: dict
          The configuration to be updated.
       child: dict
          The configuration with updates.

    Returns:
    --------
       dict: Updated configuration.
    """
    for key, value in child.items():
        if isinstance(value, dict) and key in config:
            config[key] = update(config[key], value)
        else:
            config[key] = value
    return config

# Example usage
configs = {
    'base_config': {
        'param1': 'value1',
        'param2': 'value2'
    },
    'config1': {
        'inherits_from': 'base_config',
        'param2': 'override_value2',
        'param3': 'value3'
    },
    'config2': {
        'inherits_from': ['config1', 'config3'],
        'param4': 'value4'
    },
    'config3': {
        'inherits_from': '',
        'param5': 'value5'
    }

}

selected_config = 'config2'
resolved_config = parse_config_inheritance(configs, selected_config)
print(resolved_config)