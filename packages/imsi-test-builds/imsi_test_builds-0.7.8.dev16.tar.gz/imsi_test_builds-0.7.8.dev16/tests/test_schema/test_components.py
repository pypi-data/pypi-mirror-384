import pytest
from pathlib import Path
from pydantic import ValidationError
from imsi.config_manager.schema.model import Model
from imsi.config_manager.schema.experiment import Experiment
from imsi.config_manager.schema.components import (
    Component,
    Components,
    ComponentResources,
)


# Mocking filesystem presence for config_dir validator
@pytest.fixture(autouse=True)
def mock_path_exists(monkeypatch):
    def mock_exists(path):
        # Simulate that all paths exist except "bad_dir"
        return path != Path('src', 'imsi-config', 'bad_dir')

    monkeypatch.setattr(Path, 'exists', mock_exists)


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


# test the merging of model and experiment components
@pytest.fixture
def valid_model():
    return {
        'name': 'test_model',
        'source_id': 'test_source',
        'variant_id': 'test_variant',
        'short_name': 'test_short',
        'description': 'Test model description',
        'postproc_profile': 'default',
        'inherits_from': ['parent_model'],
        'scientifically_validated': True,
        'repository_tag': 'v1.0',
        'uxxx': None,
        'prefix': None,
        'model_filename_prefix': None,
        'model_rs_filename_prefix': None,
    }


@pytest.fixture
def valid_experiment():
    """Fixture to provide valid experiment data."""
    return {
        'name': 'Test Experiment',
        'experiment_id': 'exp_001',
        'subexperiment_id': 'sub_001',
        'activity_id': 'act_001',
        'mip_era': 'CMIP6',
        'model_type': 'AOGCM',
        'start_time': '2025',
        'end_time': '2025',
        'parent_runid': 'parent_123',
        'parent_branch_time': '2024',
        'inherits_from': None,
        'supported_models': ['ModelA', 'ModelB'],
        'components': {'atmosphere': 'AMIP', 'ocean': 'OMIP'},
    }


def test_merged_components(valid_model, valid_experiment, valid_component):
    """Test merging of model and experiment components"""
    model = Model(**valid_model)
    model.components = valid_component
    experiment = Experiment(**valid_experiment)

    # Assuming the components are merged into the model
    merged_components = {**model.components, **experiment.components}

    assert len(merged_components) == len(model.components) + len(experiment.components)


def test_invalid_component_resources():
    """Test ComponentResources validation with invalid data"""
    with pytest.raises(ValidationError):
        ComponentResources(mpiprocs='invalid', ompthreads=8)


def test_missing_components_config_dir():
    """Test Component validation with invalid input"""
    invalid_components = {
        'CanTEST': {
            'exec': 'test_exec',
            'resources': {'mpiprocs': 4, 'ompthreads': 8},
            'namelists': {'namelist1': {}},
            'compilation': {'comp1': {}},
            'input_files': {'input1': 'input_path'},
            'output_files': {'output1': 'output_path'},
        }
    }
    with pytest.raises(FileNotFoundError):
        Components(**invalid_components)


def test_missing_config_dir():
    """Test Component validation when 'config_dir' is missing"""
    invalid_component = {
        'exec': 'test_exec',
        'config_dir': 'bad_dir',
        'resources': {'mpiprocs': 4, 'ompthreads': 8},
        'namelists': {'namelist1': {}},
        'compilation': {'comp1': {}},
        'input_files': {'input1': 'input_path'},
        'output_files': {'output1': 'output_path'},
    }

    with pytest.raises(FileNotFoundError):
        Component(**invalid_component)


def test_fail_single_component():
    """Test Component validation with minimum required fields"""
    invalid_component = {
        'exec': 'test_exec',
        'resources': {'mpiprocs': 4, 'ompthreads': 8},
        # Missing config_dir
    }

    with pytest.raises(ValidationError):
        Component(**invalid_component)


def test_fail_component_resources():
    """Test ComponentResources validation with missing fields"""
    invalid_component_resources = {
        'mpiprocs': 4,
        # Missing ompthreads
    }

    test_component = {
        'exec': 'test_exec',
        'resources': invalid_component_resources,
        'config_dir': 'valid_config',
    }

    test_components = {
        'CanTEST': test_component,
    }

    with pytest.raises(ValidationError):
        Components(**test_components)
