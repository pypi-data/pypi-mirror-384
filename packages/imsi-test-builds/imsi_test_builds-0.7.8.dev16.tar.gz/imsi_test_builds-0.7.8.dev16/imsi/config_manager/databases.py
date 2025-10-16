import os
from abc import ABC, abstractmethod
from typing import Dict

from imsi.utils.dict_tools import combine_yaml_configs, combine_json_configs, parse_config_inheritance

class ConfigDatabase(ABC):
    '''Defines an abstract interface for a config DB
       This might be useful if in the future different DBs could be used.
       For instance there could be an sqlite or xml based db instead of json,
       which is why the ConfigDatabase abstraction is in place, allowing future
       flexibility (Open for expansion, closed for change principle)

       The interface defines two "get" methods which return a dictionary of the
       config
    '''
    @abstractmethod
    def get_config(self, config_name: str) -> Dict:
        '''Returns all entries under a configuration category, for example
        if config_name="machines", it would return a dict containing the configurations
        for all machines in the library (which machine names as keys)'''
        pass

    @abstractmethod
    def get_parsed_config(self, config_name: str, config_key: str) -> Dict:
        '''Returns a specific named entry from a specific configuration category.
        For example if config_name="machines", and config_key="ppp6", it would \
        return a dict containing the machine configuration for ppp6'''
        pass

class YAMLConfigDatabase(ConfigDatabase):
    """A specific implementation of a ConfigDatabase, which reads the inputs from a hierachy
    of YAML files.
    """

    def __init__(self, imsi_config_path):
        self.imsi_config_path = imsi_config_path
        self.database = self._load_config()

    def _load_config(self) -> Dict:
        """Parses the imsi_config_path for all json files and combines
        them into one big dict
        """
        if not os.path.exists(self.imsi_config_path):
            raise FileNotFoundError(
                f"Could not find imsi config directory at: {self.imsi_config_path}"
            )

        return combine_yaml_configs(self.imsi_config_path)

    def get_config(self, config_name: str) -> Dict:
        """Returns all entries under a configuration category, for example
        if config_name="machines", it would return a dict containing the configurations
        for all machines in the library (which machine names as keys)"""
        if config_name not in self.database:
            raise NameError(
                f"{config_name} not found in database created from {self.imsi_config_path}"
            )
        return self.database[config_name]

    def get_parsed_config(self, config_name: str, config_key: str) -> Dict:
        """Returns a specific named entry from a specific configuration category.
        For example if config_name="machines", and config_key="ppp6", it would \
        return a dict containing the machine configuration for ppp6"""
        config_realm_data = self.get_config(config_name)
        if config_key not in config_realm_data:
            raise NameError(
                f"{config_key} not found in {config_name} in the configuration "
                f"database created from {self.imsi_config_path}"
            )
        return parse_config_inheritance(config_realm_data, config_key)

class JsonConfigDatabase(ConfigDatabase):
    '''A specific implementation of a ConfigDatabase, which reads the inputs from a hierachy
       of json files.
    '''
    def __init__(self, imsi_config_path):
        self.imsi_config_path = imsi_config_path
        self.database = self._load_config()


    def _load_config(self) -> Dict:
        '''Parses the imsi_config_path for all json files and combines
        them into one big dict
        '''
        if not os.path.exists(self.imsi_config_path):
            raise FileNotFoundError(f'Could not find imsi config directory at: {self.imsi_config_path}')

        return combine_json_configs(self.imsi_config_path)

    def get_config(self, config_name: str) -> Dict:
        '''Returns all entries under a configuration category, for example
        if config_name="machines", it would return a dict containing the configurations
        for all machines in the library (which machine names as keys)'''
        if config_name not in self.database:
            raise NameError(f'{config_name} not found in database created from {self.imsi_config_path}')
        return self.database[config_name]

    def get_parsed_config(self, config_name: str, config_key: str) -> Dict:
        '''Returns a specific named entry from a specific configuration category.
        For example if config_name="machines", and config_key="ppp6", it would \
        return a dict containing the machine configuration for ppp6'''
        config_realm_data = self.get_config(config_name)
        if config_key not in config_realm_data:
            raise NameError(f'{config_key} not found in {config_name} in the configuration '
                            f'database created from {self.imsi_config_path}')
        return parse_config_inheritance(config_realm_data, config_key)
