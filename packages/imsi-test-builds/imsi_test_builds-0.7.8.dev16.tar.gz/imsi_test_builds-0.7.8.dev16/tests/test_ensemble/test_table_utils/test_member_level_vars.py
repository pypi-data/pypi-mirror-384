import pytest
from imsi.tools.ensemble.table_utils.data_model import MemberLevelVars
from omegaconf import OmegaConf

from pathlib import Path

parent_dir = Path(__file__).resolve().parent


@pytest.fixture
def config_params(request):
    pars = OmegaConf.create({
        "repo": request.config.getoption("--target-repo"),
        "branch": request.config.getoption("--target-branch"),
        "model": request.config.getoption("--target-model"),
        "experiment": request.config.getoption("--target-exp")
    })
    return pars


@pytest.fixture
def setup_block(config_params):
    return OmegaConf.create({
        "ver": config_params["branch"],
        "repo": config_params["repo"],
        "fetch_method": "clone",
        "machine": "ppp6",
        "model": config_params["model"],
    })


@pytest.fixture
def config_data_one(setup_block):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_block,
                "runid": ["run1"],
            }
        }
    })


@pytest.fixture
def config_bash_resolve(setup_block):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_block,
                "runid": ["run1"],
            },
            "some_path": "/this/is/a/path/\\${member_level.setup.runid}",
        }
    })


@pytest.fixture
def config_data_two(setup_block):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_block,
                "runid": ["run1", "run2"],
            }
        }
    })


@pytest.fixture
def good_multiple_lists(setup_block):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_block,
                "runid": ["run1", "run2"],
            },
            "param": {"param1": [1, 2]},
            "another_param": {"another_another_param": [1, 2]},
        }
    })


@pytest.fixture
def bad_multiple_lists(setup_block):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_block,
                "runid": ["run1", "run2"],
            },
            "param": {"good_param": [1, 2]},
            "another_param": {"another_bad_param": [1]},
        }
    })


@pytest.fixture
def config_data_no_lists(setup_block):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_block,
                "runid": "run1",
            }
        }
    })


@pytest.mark.parametrize("config_data,expected", [
    ("config_data_one", 1),
    ("config_data_two", 2),
])
def test_ensemble_size_property(request, config_data, expected):
    member_level = MemberLevelVars(config_data=request.getfixturevalue(config_data))
    assert member_level.ensemble_size == expected


@pytest.mark.parametrize("config_data,expected", [
    ("good_multiple_lists", None),
    ("bad_multiple_lists", ValueError),
])
def test_check_list_size_equal(request, config_data, expected):
    member_level = MemberLevelVars(config_data=request.getfixturevalue(config_data))
    if expected:
        with pytest.raises(expected):
            member_level.get_listed_vars(member_level.config_data)
    else:
        member_level.get_listed_vars(member_level.config_data)


@pytest.mark.parametrize("config_data,extracted_list", [
    ("config_data_one", {("member_level", "setup", "runid"): ["run1"]}),
    ("config_data_two", {("member_level", "setup", "runid"): ["run1", "run2"]}),
    ("good_multiple_lists", {
        ("member_level", "setup", "runid"): ["run1", "run2"],
        ("member_level", "param", "param1"): [1, 2],
        ("member_level", "another_param", "another_another_param"): [1, 2],
    }),
])
def test_get_listed_vars(request, config_data, extracted_list):
    member_level = MemberLevelVars(config_data=request.getfixturevalue(config_data))
    assert member_level.get_listed_vars(member_level.config_data) == extracted_list


def test_no_lists(config_data_no_lists):
    member_level = MemberLevelVars(config_data=config_data_no_lists)
    assert member_level.ensemble_size is None


def test_bash_resolve(config_bash_resolve):
    member_level = MemberLevelVars(config_data=config_bash_resolve)
    assert member_level.config_data.member_level.some_path == "/this/is/a/path/${member_level.setup.runid}"