import pytest
from pydantic import ValidationError
from imsi.config_manager.schema.compiler import Compiler


def test_minimal_config():
    """Test minimal configuration of Compiler."""
    config = Compiler(name='test_compiler')
    assert config.name == 'test_compiler'

    with pytest.raises(ValidationError):
        Compiler()
