import pytest
from pydantic import ValidationError
from imsi.config_manager.schema.sequencing import Sequencing


@pytest.fixture
def valid_sequencing():
    return {
        'run_dates': {
            'run_start_time': '2023-01-01',
            'run_stop_time': '2023-12-31',
            'run_segment_start_time': '2023-01-01',
            'run_segment_stop_time': '2023-12-31',
            'model_chunk_size': '1d',
            'model_internal_chunk_size': '1h',
            'postproc_chunk_size': '1h',
        }
    }


@pytest.fixture
def invalid_sequencing():
    return {
        'run_dates': {
            'run_start_time': '2023-01-01',
            'run_stop_time': '2023-12-31',
            'run_segment_start_time': '2023-01-01',
            'run_segment_stop_time': '2023-12-31',
            # Missing model_chunk_size
            'model_internal_chunk_size': '1h',
            'postproc_chunk_size': '1h',
        }
    }


@pytest.fixture
def invalid_sequencing_types():
    return {
        'run_dates': {
            'run_start_time': 20230101,  # Invalid type (should be str)
            'run_stop_time': '2023-12-31',
            'run_segment_start_time': '2023-01-01',
            'run_segment_stop_time': '2023-12-31',
            'model_chunk_size': 1234324,
            'model_internal_chunk_size': '1h',
            'postproc_chunk_size': '1h',
        }
    }


def test_sequencing_valid_config(valid_sequencing):
    """Test valid Sequencing configuration"""
    sequencing = Sequencing(**valid_sequencing)
    assert sequencing.run_dates.run_start_time == '2023-01-01'
    assert sequencing.run_dates.model_chunk_size == '1d'


def test_sequencing_invalid_config(invalid_sequencing):
    """Test invalid Sequencing configuration"""
    with pytest.raises(ValidationError, match='Field required'):
        Sequencing(**invalid_sequencing)


def test_sequencing_invalid_types(invalid_sequencing_types):
    """Test invalid Sequencing configuration with wrong types"""
    with pytest.raises(ValidationError, match='should be a valid string'):
        Sequencing(**invalid_sequencing_types)


def test_sequencing_extra_fields(valid_sequencing):
    """Test Sequencing configuration with extra fields"""
    valid_sequencing['extra_field'] = 'extra_value'
    sequencing = Sequencing(**valid_sequencing)
    assert sequencing.extra_field == 'extra_value'


def test_datacoerce(valid_sequencing):
    """Test DateCoerce conversion"""
    valid_sequencing['run_dates']['run_start_time'] = 20230101  # Coerce int to str
    sequencing = Sequencing(**valid_sequencing)
    assert sequencing.run_dates.run_start_time == '20230101'
    assert isinstance(sequencing.run_dates.run_start_time, str)
