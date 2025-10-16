# tests/test_yaml_vars.py
import pytest
from omegaconf import OmegaConf, DictConfig

from imsi.tools.ensemble.table_utils.table_model import YAMLVars
from imsi.tools.ensemble.table_utils.data_model import MemberLevelVars

VER = "v5.1.7-imsi"


def _base_setup():
    return {
        "ver": VER,
        "repo": "git@gitlab.science.gc.ca:CanESM/CanESM5.git",
        "fetch_method": "clone",
        "machine": "ppp6",
        "model": "canesm51_p1",
    }


@pytest.fixture
def cfg_two_runids() -> DictConfig:
    """Two explicit run IDs (run1, run2)"""
    return OmegaConf.create(
        {"member_level": {"setup": {**_base_setup(), "runid": ["run1", "run2"]}}}
    )


@pytest.fixture
def cfg_auto_runid() -> DictConfig:
    """
    Single sentinel 'auto-gen-runid' plus a list field (model) of len 2 → 2
    members with auto‑generated unique run IDs expected.
    """
    return OmegaConf.create(
        {
            "member_level": {
                "setup": {
                    **_base_setup(),
                    "model": ["canesm51_p1", "canesm51_p1"],
                    "runid": "auto-gen-runid",
                }
            }
        }
    )


def test_yamlvars_broadcast_two_members(cfg_two_runids):
    member = MemberLevelVars(config_data=cfg_two_runids["member_level"])
    yaml_vars = YAMLVars(member_level=member)

    table = yaml_vars.get_table(show_diffs=False)
    table_plain = [OmegaConf.to_container(cfg, resolve=True) for cfg in table]

    expected = [
        {"setup": {**_base_setup(), "runid": "run1"}},
        {"setup": {**_base_setup(), "runid": "run2"}},
    ]
    assert table_plain == expected


def test_yamlvars_auto_generated_runids(cfg_auto_runid):
    member = MemberLevelVars(config_data=cfg_auto_runid["member_level"])

    # expand_config emits a warning for auto‑generated IDs
    with pytest.warns():
        yaml_vars = YAMLVars(member_level=member)
        table = yaml_vars.get_table(show_diffs=False)

    runids = [cfg.setup.runid for cfg in table]

    # Expect two unique IDs that start with 'auto-gen-runid-'
    assert len(runids) == 2
    assert len(set(runids)) == 2
    assert all(str(rid).startswith("auto-gen-runid") for rid in runids)
