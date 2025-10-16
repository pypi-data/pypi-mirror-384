import pytest
from pydantic import ValidationError
from imsi.config_manager.schema.experiment import Experiment


@pytest.fixture
def valid_experiment_data():
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


def test_missing_required_fields():
    """Ensure required fields cannot be omitted."""
    with pytest.raises(ValidationError):
        Experiment(name='Test Experiment')


def test_datecoerce_validation(valid_experiment_data):
    """Ensure start_time and end_time accept valid date-like values."""
    valid_experiment_data['start_time'] = 2025
    valid_experiment_data['end_time'] = '2026'
    experiment = Experiment(**valid_experiment_data)
    assert isinstance(experiment.start_time, str)


def test_invalid_supported_model(valid_experiment_data):
    """Ensure error is raised if model_name is not in supported_models."""
    valid_experiment_data['supported_models'] = ['ModelC', 1234]
    with pytest.raises(ValueError):
        Experiment(**valid_experiment_data)  # Not in supported_models


def test_check_supported_models(valid_experiment_data):
    """Ensure check_supported_models validator works."""
    model_name = 'ModelC'
    with pytest.raises(ValueError):
        Experiment(**valid_experiment_data).validate_model_name(model_name=model_name)


def test_optional_fields(valid_experiment_data):
    """Ensure optional fields can be omitted or set to None."""
    valid_experiment_data.pop('inherits_from')
    valid_experiment_data['components'] = None
    experiment = Experiment(**valid_experiment_data)
    assert experiment.inherits_from is None
    assert experiment.components is None  # Should default to None


def test_missing_start_time(valid_experiment_data):
    """Ensure missing start_time field triggers an error."""
    valid_experiment_data.pop('start_time')
    with pytest.raises(ValidationError):
        Experiment(**valid_experiment_data)
