import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock
from imsi.config_manager.databases import ConfigDatabase
from imsi.config_manager.schema.machine import MachineFactory, Machine, BatchCommands


@pytest.fixture
def valid_machine_data():
    """Fixture to provide valid machine data."""
    return {
        'name': 'test_machine',
        'site': {},
        'nodename_regex': 'test.*',
        'supported_compilers': ['gcc', 'intel'],
        'default_compiler': 'gcc',
        'scratch_dir': '/scratch',
        'storage_dir': '/storage',
        'sequencers': ['sequencer1', 'sequencer2'],
        'default_sequencing_suffix': '_seq',
        'batch_commands': {
            'scheduler': 'slurm',
            'mpi_exec': 'mpirun',
            'pes_per_node': 16,
        },
        'login_nodes': ['node1', 'node2'],
        'modules': {'python': '3.8'},
        'environment_variables': {'OMP_NUM_THREADS': '4'},
        'environment_commands': {'source': '/env/setup.sh'},
        'resources': {'cpu': 64, 'memory': '128GB'},
    }


@pytest.fixture
def valid_batch_commands():
    """Fixture to provide valid batch commands."""
    return {
        'scheduler': 'slurm',
        'mpi_exec': 'mpirun',
        'pes_per_node': 16,
    }


def test_missing_required_fields():
    """Ensure required fields cannot be omitted."""
    with pytest.raises(ValidationError):
        Machine(site={})  # Missing required fields


def test_invalid_default_compiler(valid_machine_data):
    """Ensure default_compiler must be in supported_compilers."""
    valid_machine_data['default_compiler'] = 'nonexistent_compiler'
    with pytest.raises(ValueError, match='not in supported compilers'):
        Machine(**valid_machine_data)


def test_optional_fields(valid_machine_data):
    """Ensure optional fields can be omitted or set to None."""
    valid_machine_data.pop('login_nodes')
    valid_machine_data['modules'] = None
    valid_machine_data['environment_variables'] = None
    valid_machine_data['environment_commands'] = None
    valid_machine_data['resources'] = {'1': '2'}
    machine = Machine(**valid_machine_data)
    assert machine.modules is None
    assert machine.login_nodes is None  # Should default to None
    assert machine.environment_variables is None
    assert machine.environment_commands is None


def test_missing_resources(valid_machine_data):
    """Ensure resources are defined in the site configuration or machine configuration."""
    valid_machine_data['resources'] = None
    valid_machine_data['site'] = {'resources': None}
    with pytest.raises(ValueError, match='Resources must be defined'):
        Machine(**valid_machine_data)


def test_invalid_nodename_regex(valid_machine_data):
    """Ensure nodename_regex is a valid regular expression."""
    valid_machine_data['nodename_regex'] = '[a-z'
    with pytest.raises(
        ValueError, match='Invalid regular expression for nodename_regex'
    ):
        Machine(**valid_machine_data)


def test_create_from_database():
    """Ensure create_from_database correctly retrieves machine info."""
    mock_db = MagicMock(spec=ConfigDatabase)
    mock_db.get_parsed_config.side_effect = lambda section, name: {
        'nodename_regex': 'test.*',
        'supported_compilers': ['gcc', 'intel'],
        'default_compiler': 'gcc',
        'scratch_dir': '/scratch',
        'storage_dir': '/storage',
        'sequencers': ['seq1'],
        'default_sequencing_suffix': '_seq',
        'batch_commands': {'scheduler': 'slurm', 'mpi_exec': 'mpirun'},
        'resources': {'cpu': 64, 'memory': '128GB'},
    }
    mock_db.get_config.side_effect = lambda section: {
        'sites': {'test_site': ['test_machine']},
        'machines': {'test_machine': {'nodename_regex': 'test.*'}},
    }

    machine = Machine.create_from_database(mock_db, 'test_machine')
    assert machine.name == 'test_machine'
    assert machine.default_compiler == 'gcc'


@pytest.mark.parametrize('required_key', ['scheduler', 'mpi_exec'])
def test_batch_commands_missing(valid_batch_commands, required_key):
    valid_batch_commands.pop(required_key)
    with pytest.raises(ValidationError):
        BatchCommands(**valid_batch_commands)


def test_batch_commands_optional_fields(valid_batch_commands):
    """Ensure optional fields can be omitted or set to None."""
    valid_batch_commands['pes_per_node'] = None
    batch_commands = BatchCommands(**valid_batch_commands)
    assert batch_commands.pes_per_node is None
    assert batch_commands.pes_per_node is None  # Should default to None
    assert batch_commands.mpi_exec == 'mpirun'
    assert batch_commands.scheduler == 'slurm'


def test_validate_compiler(valid_machine_data):
    """Ensure validate_compiler raises error if compiler is not in supported_compilers."""
    valid_machine_data['supported_compilers'] = ['gcc', 'intel']
    machine = Machine(**valid_machine_data)
    with pytest.raises(ValueError, match=r'Compiler .* is not supported by machine .*'):
        machine.validate_compiler('nonexistent_compiler')

@pytest.mark.xfail(raises=(NameError, AttributeError, TypeError))
def test_find_matching_machine(valid_machine_data):
    machine_config_dict = {valid_machine_data['name']: Machine(**valid_machine_data)}
    MachineFactory.find_matching_machine(machine_config_dict)
