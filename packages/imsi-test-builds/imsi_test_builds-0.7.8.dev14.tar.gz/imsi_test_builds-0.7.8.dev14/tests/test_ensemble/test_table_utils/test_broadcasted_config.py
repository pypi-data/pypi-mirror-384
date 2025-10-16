import pytest
from omegaconf import OmegaConf, ListConfig

from imsi.tools.ensemble.table_utils.data_model import MemberLevelVars
from imsi.tools.ensemble.table_utils.table_model import BroadcastedConfigList


@pytest.fixture
def _base_setup(request):
    return {
        "ver": request.config.getoption("--target-branch"),
        "repo": request.config.getoption("--target-repo"),
        "fetch_method": "clone",
        "machine": "ppp6",
        "model": request.config.getoption("--target-model"),
    }


@pytest.fixture
def config_data_one(_base_setup):
    return OmegaConf.create(
        {"member_level": {"setup": {**_base_setup, "runid": ["run1"]}}}
    )


@pytest.fixture
def config_data_two(_base_setup):
    return OmegaConf.create(
        {
            "member_level": {
                "setup": {
                    **_base_setup,
                    "runid": ["run-01", "run-02"],
                }
            }
        }
    )


@pytest.fixture
def config_data_auto_runid(_base_setup):
    return OmegaConf.create(
        {
            "member_level": {
                "setup": {
                    **_base_setup,
                    "model": ["canesm51_p1", "canesm51_p1"],
                    "runid": "auto-gen-runid",
                }
            }
        }
    )


def test_expand_config_basic(config_data_one):
    member = MemberLevelVars(config_data=config_data_one["member_level"])
    bcl = BroadcastedConfigList(member_level=member)

    configs = bcl.expand_config(ensemble_size=1)
    assert isinstance(configs, ListConfig)
    assert len(configs) == 1
    # Whatever naming convention the implementation uses, a non‑empty runid
    # string must be present.
    assert configs[0].setup.runid


def test_expand_config_two_members(config_data_two):
    member = MemberLevelVars(config_data=config_data_two["member_level"])
    bcl = BroadcastedConfigList(member_level=member)

    configs = bcl.expand_config(ensemble_size=2)
    assert isinstance(configs, ListConfig)
    assert len(configs) == 2
    # All runids must be unique
    runids = [cfg.setup.runid for cfg in configs]
    assert len(set(runids)) == 2


def test_expand_config_auto_generated_runids(config_data_auto_runid):
    member = MemberLevelVars(config_data=config_data_auto_runid["member_level"])

    # The constructor (and expand_config) emit a warning in this scenario
    bcl = BroadcastedConfigList(member_level=member)
    configs = bcl.expand_config(ensemble_size=2)

    runids = [cfg.setup.runid for cfg in configs]

    assert len(runids) == 2
    assert all(str(rid).startswith("auto-gen-runid") for rid in runids)
