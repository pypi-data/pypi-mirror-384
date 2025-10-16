from imsi.tools.ensemble.config import (
    load_config,
)

import pytest
from unittest.mock import MagicMock, patch
from omegaconf import OmegaConf

from pathlib import Path

parent_dir = Path(__file__).resolve().parent

@pytest.fixture
def mock_cfg():
    """Mock configuration with default settings."""
    return MagicMock(
        ensemble_level=OmegaConf.create({
            "user": "test_user",
            "config_table": "holder",
        }),
        member_level=OmegaConf.create({}),
    )


def test_load_config_csv(mock_cfg):
    """Test loading a CSV configuration."""
    with patch("imsi.tools.ensemble.table_utils.table_model.CSVTableVars") as mock_csv:
        mock_csv.return_value.get_table.return_value = "mock_csv_table"
        mock_cfg.ensemble_level["config_table"] = (
            str(parent_dir / "test_table_utils" / "test_config.csv")
        )
        ensemble_config, table = load_config(mock_cfg, show_diffs=False)
        assert table == [
                {'setup': {'runid': 'run-01', 'exp': 'cmip6-piControl'}},
                {'setup': {'runid': 'run-02', 'exp': 'cmip6-piControl'}}
        ]


def test_load_config_text(mock_cfg):
    """Test loading a CSV configuration."""
    with patch("imsi.tools.ensemble.table_utils.table_model.TextTableVars") as mock_csv:
        mock_csv.return_value.get_table.return_value = "mock_csv_table"
        mock_cfg.ensemble_level["config_table"] = (
            str(parent_dir / "test_table_utils" / "test_config.txt")
        )
        ensemble_config, table = load_config(mock_cfg, show_diffs=False)
        assert table == [
                {'setup': {'runid': 'run-01', 'exp': 'cmip6-piControl'}},
                {'setup': {'runid': 'run-02', 'exp': 'cmip6-piControl'}}
        ]


def test_load_config_unsupported_file_type(mock_cfg):
    """Test loading an unsupported file type."""
    mock_cfg.ensemble_level["config_table"] = (
        str(parent_dir / "test_table_utils" / "test_config_unsupported_file_type.db")
    )

    with pytest.raises(ValueError, match="Unsupported file type:"):
        load_config(mock_cfg, show_diffs=False)
