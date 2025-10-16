import pytest
from pathlib import Path
from pydantic import ValidationError
from imsi.config_manager.schema.model import Model
from imsi.config_manager.schema.components import Component, ComponentResources


# Helper fixture for valid ComponentResources
@pytest.fixture
def valid_component_resources():
    return {'mpiprocs': 4, 'ompthreads': 8}


# Helper fixture for a valid Component
@pytest.fixture
def valid_component(valid_component_resources):
    return {
        'exec': 'test_exec',
        'resources': valid_component_resources,
        'config_dir': 'valid_config',
        'namelists': {'namelist1': {}},
        'compilation': {'comp1': {}},
        'input_files': {'input1': 'input_path'},
        'output_files': {'output1': 'output_path'},
    }


# Mocking filesystem presence for config_dir validator
@pytest.fixture(autouse=True)
def mock_path_exists(monkeypatch):
    def mock_exists(path):
        # Simulate that all paths exist except "bad_dir"
        return path != Path('src', 'imsi-config', 'bad_dir')

    monkeypatch.setattr(Path, 'exists', mock_exists)


def test_component_resources_validation(valid_component_resources):
    """Test ComponentResources validation"""
    comp_res = ComponentResources(**valid_component_resources)
    assert comp_res.mpiprocs == 4
    assert comp_res.ompthreads == 8


def test_component_validation(valid_component):
    """Test Component validation with valid input"""
    comp = Component(**valid_component)
    assert comp.exec == 'test_exec'
    assert comp.config_dir == 'valid_config'


def test_component_missing_exec(valid_component):
    """Test Component validation when 'exec' is missing"""
    invalid_component = valid_component.copy()
    del invalid_component['exec']

    with pytest.raises(ValidationError):
        Component(**invalid_component)


def test_component_invalid_config_dir():
    """Test Component fails if config_dir does not exist"""
    with pytest.raises(FileNotFoundError):
        Component(
            exec='test_exec',
            resources={'mpiprocs': 4, 'ompthreads': 8},
            config_dir='bad_dir',
        )


def test_model_validation(valid_component):
    """Test Model validation with at least one component"""
    model = Model(
        name='test_model',
        source_id='test_source',
        variant_id='v1',
        short_name='tm',
        description='Test model',
        postproc_profile='default',
        components={'atm': valid_component},
    )
    assert model.name == 'test_model'
    assert 'atm' in model.components
