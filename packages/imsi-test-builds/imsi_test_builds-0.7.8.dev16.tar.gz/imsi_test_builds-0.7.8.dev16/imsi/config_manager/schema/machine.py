import re
import socket

from pydantic import BaseModel, model_validator, field_validator, Field, ConfigDict
from typing import Optional, Union, List, ClassVar

from imsi.config_manager.databases import ConfigDatabase


# TODO this class is slated for revision given that it no longer contains
# a constructor (moved to Machine to handle machine/site config).
class MachineFactory:
    #  Implemented to encapsulate the several methods required,
    #  this keeping the Machine class itself simple.
    @classmethod
    def get_machine_name_from_hostname(cls, db: ConfigDatabase) -> str:
        machine_configs = db.get_config('machines')
        return cls.find_matching_machine(machine_configs)

    @classmethod
    def find_matching_machine(cls, machine_configs: dict) -> str:
        hostname = cls.get_hostname()
        for machine_name, config in machine_configs.items():
            if re.search(config['nodename_regex'], hostname):
                return machine_name
        raise NameError(
            f'Could not find any IMSI-supported machine matching hostname {hostname}'
        )

    @staticmethod
    def get_hostname() -> str:
        try:
            return socket.gethostname()
        except OSError as e:
            raise ValueError(f'Could not determine the hostname: {e}')


class BatchCommands(BaseModel):
    """Batch commands"""

    model_config = ConfigDict(extra='allow')
    scheduler: str = Field(..., description='Scheduler')
    mpi_exec: str = Field(..., description='MPI executable')
    # TODO Make required
    # (maestro cap should be updated to use these once the site
    # config is added and these are added for each machine)
    pes_per_node: Optional[int] = Field(None, description='Number of PEs per node')


class Machine(BaseModel, validate_assignment=True):
    """Machine configuration"""

    model_config = ConfigDict(extra='allow')
    name: str = Field(..., description='Machine name')
    site: dict
    site_attrs: ClassVar[list] = [
        'resources',
        'computational_environment',
        'nodename_regex',
    ]
    # FUTURE: if site_attrs shuold be strictly enforced at construction, validation
    # could be done through __post_init__ on the Machine instance and site dict
    nodename_regex: str = Field(
        ..., description='Regular expression to match the machine name'
    )
    supported_compilers: list = Field(..., description='List of supported compilers')
    default_compiler: str = Field(..., description='Default compiler')
    scratch_dir: str = Field(..., description='Scratch directory')
    storage_dir: str = Field(..., description='Storage directory')
    sequencers: list = Field(..., description='List of sequencers')
    default_sequencing_suffix: str = Field(..., description='Default sequencing suffix')
    batch_commands: BatchCommands
    login_nodes: Optional[Union[List[str], str]] = Field(
        None, description='List of login nodes or a single login node'
    )
    modules: Optional[dict] = Field(None, description='Modules to load')
    environment_variables: Optional[dict] = Field(
        None, description='Environment variables'
    )
    environment_commands: Optional[dict] = Field(
        None, description='Environment commands'
    )
    resources: Optional[dict] = Field(None, description='Resources')

    @model_validator(mode='after')
    def check_resources_defined(data):
        """Ensure that resources are defined in the site configuration."""
        if not data.site.get('resources') and not data.resources:
            raise ValueError(
                'Resources must be defined in either the site configuration or the machine configuration'
            )
        return data

    @field_validator('nodename_regex')
    def validate_nodename_regex(nodename_regex):
        """Validate that nodename_regex is a valid regular expression."""
        if nodename_regex:
            try:
                re.compile(nodename_regex)
            except re.error as e:
                raise ValueError(f'Invalid regular expression for nodename_regex: {e}')
        return nodename_regex

    @model_validator(mode='after')
    def check_compilers(data):
        """Ensure the default compiler is in the supported compilers list."""
        if not data.supported_compilers:
            raise ValueError('No supported_compilers found in machine configuration')

        if data.default_compiler not in data.supported_compilers:
            raise ValueError(
                f'Default compiler {data.default_compiler} not in supported compilers'
            )

        return data

    def validate_compiler(self, compiler_name: str):
        """Ensure the selected compiler is in the supported_compilers list."""
        if compiler_name not in self.supported_compilers:
            raise ValueError(
                f"Compiler '{compiler_name}' is not supported by machine '{self.name}'."
            )

    def get_default_sequencer(self) -> str:
        """Retrieve the default compiler from the machine configuration"""
        return self.sequencers[0]

    @classmethod
    def create_from_database(cls, db: ConfigDatabase, machine_name: str = None):
        """Create an instance of Machine from the ConfigDatabase given the desired machine name"""

        machine_name = machine_name or MachineFactory.get_machine_name_from_hostname(db)
        machine_data = db.get_parsed_config('machines', machine_name)

        site_configs = db.get_config('sites')
        site = {k: v for k, v in site_configs.items() if machine_name in v}
        if not site:
            raise ValueError('Bad config: machine must belong to a site.')
        if len(site) > 1:
            raise ValueError('Bad config: machine can only belong to one site.')

        site_name, site_machines = site.popitem()
        site_machines = [m for m in site_machines if m != machine_name]

        # for every machine name in the site info, get the machine site info:
        sites = {}
        machine_data['site_name'] = site_name
        for ms in site_machines:
            ms_data = db.get_parsed_config('machines', ms)
            try:
                # explicit required keys
                sites[ms] = {k: ms_data[k] for k in cls.site_attrs}
            except KeyError:
                raise KeyError(f'Missing config for {ms}')

        return cls(name=machine_name, site=sites, **machine_data)
