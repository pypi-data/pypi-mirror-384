from pathlib import Path

import pytest
from omegaconf import OmegaConf
from pydantic import ValidationError

from imsi.tools.ensemble.table_utils.table_model import (
    YAMLTableVars,
)
from imsi.tools.ensemble.table_utils.data_model import (
    MemberLevelVars,
)


parent_dir = Path(__file__).resolve().parent


@pytest.fixture
def config_params():
    return {
        "repo": "origin",
        "branch": "main",
        "model": "canam",
        "experiment": "piControl",
    }


@pytest.fixture
def setup_config(config_params):
    return OmegaConf.create(
        {
            "ver": config_params["branch"],
            "repo": config_params["repo"],
            "fetch_method": "clone",
            "machine": "ppp6",
            "model": config_params["model"],
        }
    )


@pytest.fixture
def config_data_two(setup_config):
    """Two‑member runid list so ensemble_size == 2."""
    return OmegaConf.create(
        {
            "member_level": {
                "setup": {
                    **setup_config,
                    "runid": ["run-01", "run-02"],
                }
            }
        }
    )


def test_yaml_table_vars_get_table_ok(tmp_path, config_data_two):
    """A simple 2‑row YAML table is read back unchanged."""
    table_rows = [
        {
            "setup": {
                "ver": "main",
                "repo": "origin",
                "fetch_method": "clone",
                "machine": "ppp6",
                "model": "canam",
                "runid": "run-yaml-001",
                "exp": "cmip6-piControl",
            }
        },
        {
            "setup": {
                "ver": "main",
                "repo": "origin",
                "fetch_method": "clone",
                "machine": "ppp6",
                "model": "canam",
                "runid": "run-yaml-002",
                "exp": "cmip6-historical",
            },
            "components": {
                "CanAM": {
                    "namelists": {
                        "canam_settings": {
                            "pp_rdm_num_pert": 2
                        }
                    }
                }
            },
        },
    ]
    table_path = Path(parent_dir, "config_table.yaml")

    member = MemberLevelVars(config_data=config_data_two["member_level"])
    yaml_vars = YAMLTableVars(member_level=member, config_table=table_path)

    result = yaml_vars.get_table(show_diffs=False)
    assert result == table_rows


def test_yaml_table_vars_no_table_raises(tmp_path, config_data_two):
    member = MemberLevelVars(config_data=config_data_two["member_level"])
    yaml_vars = YAMLTableVars(member_level=member)  # config_table=None

    with pytest.raises(ValueError, match="No config table provided"):
        yaml_vars.get_table(show_diffs=False)


def test_yaml_table_vars_invalid_path(config_data_two, tmp_path):
    member = MemberLevelVars(config_data=config_data_two["member_level"])
    bogus_path = tmp_path / "does_not_exist.yaml"

    with pytest.raises(ValidationError):
        YAMLTableVars(member_level=member, config_table=bogus_path)


def test_yaml_table_vars_length_mismatch(tmp_path, config_data_two):
    """Table has 1 row but ensemble_size is 2 → triggers assertion in our stub."""
    table_path = Path(parent_dir, "config_table_identical_keypaths.yaml")

    member = MemberLevelVars(config_data=config_data_two["member_level"])
    yaml_vars = YAMLTableVars(member_level=member, config_table=table_path)

    with pytest.raises(ValueError, match="does not match the number of table entries"):
        yaml_vars.get_table(show_diffs=False)
