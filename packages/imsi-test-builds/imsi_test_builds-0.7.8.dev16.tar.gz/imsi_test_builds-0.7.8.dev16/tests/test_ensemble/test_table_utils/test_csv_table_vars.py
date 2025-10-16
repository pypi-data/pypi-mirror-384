import pytest
from pathlib import Path

from pydantic import ValidationError
from imsi.tools.ensemble.table_utils.table_model import CSVTableVars
from imsi.tools.ensemble.table_utils.data_model import (
    MemberLevelVars,
    EnsembleLevelVars,
)
from imsi.tools.ensemble.config import load_config

from omegaconf import OmegaConf
from omegaconf.errors import ConfigTypeError

parent_dir = Path(__file__).resolve().parent


@pytest.fixture
def config_params(request):
    pars = {
        "repo": request.config.getoption("--target-repo"),
        "branch": request.config.getoption("--target-branch"),
        "model": request.config.getoption("--target-model"),
        "experiment": request.config.getoption("--target-exp")
    }
    return pars


@pytest.fixture
def setup_config(config_params):
    return OmegaConf.create({
        "ver": config_params["branch"],
        "repo": config_params["repo"],
        "fetch_method": "clone",
        "machine": "ppp6",
        "model": config_params["model"],
    })


@pytest.fixture
def config_data_one(setup_config):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_config,
                "runid": ["run1"],
            }
        }
    })


@pytest.fixture
def config_data_two(setup_config):
    return OmegaConf.create({
        "member_level": {
            "setup": {
                **setup_config,
                "runid": ["run1", "run2"],
            }
        }
    })


@pytest.fixture
def ensemble_config():
    return OmegaConf.create({
        "user": "test_user",
        "run_directory": str(parent_dir / "./"),
        "config_table": str(parent_dir / "config.yaml"),
        "share_repo": True,
    })


@pytest.fixture
def ensemble_config_txt_one():
    return {
        "user": "test_user",
        "run_directory": str(parent_dir / "./"),
        "config_table": str(parent_dir / "test_config.csv"),
        "aliases": {"alias1": "banana"},
        "share_repo": True,
    }


@pytest.fixture
def ensemble_config_with_aliases():
    return {
        "user": "test_user",
        "run_directory": str(parent_dir / "./"),
        "config_table": str(parent_dir / "test_config_alias.csv"),
        "aliases": {"banana": "setup:exp"},
        "share_repo": True,
    }


@pytest.fixture
def ensemble_config_with_nested_aliases():
    return {
        "user": "test_user",
        "run_directory": str(parent_dir / "./"),
        "config_table": str(parent_dir / "test_config_alias_nested.csv"),
        "aliases": {"banana": "setup:exp", "apple": "one:two:three"},
        "share_repo": True,
    }


@pytest.fixture
def ensemble_config_with_nested_alises_conflict():
    return {
        "user": "test_user",
        "run_directory": str(parent_dir / "./"),
        "config_table": str(parent_dir / "test_config_alias_nested_conflict.csv"),
        "aliases": {"banana": "setup:exp", "apple": "one:two:three"},
        "share_repo": True,
    }


def test_csv_table_vars_valid(config_data_one, ensemble_config):
    """
    MemberLevelVars + EnsembleLevelVars yield a valid CSVTableVars instance.
    """
    member_level = MemberLevelVars(config_data=config_data_one["member_level"])
    ensemble_level = EnsembleLevelVars(**ensemble_config)

    result = CSVTableVars(member_level=member_level, ensemble_level=ensemble_level)
    assert isinstance(result, CSVTableVars)


def test_csv_table_vars_invalid(config_data_one, ensemble_config):
    """
    Passing an obviously wrong type for `ensemble_level` should raise ValidationError.
    """
    member_level = MemberLevelVars(config_data=config_data_one["member_level"])
    with pytest.raises(ValidationError):
        CSVTableVars(member_level=member_level, ensemble_level=int)


def test_read_table_txt_one(config_data_one, ensemble_config_txt_one):
    expected = OmegaConf.create({
        "setup": {
            "runid": ["run-01", "run-02"],
            "exp": ["cmip6-piControl", "cmip6-piControl"],
        }
    })

    member_level = MemberLevelVars(config_data=config_data_one["member_level"])
    ensemble_level = EnsembleLevelVars(**ensemble_config_txt_one)

    table_vars = CSVTableVars(member_level=member_level, ensemble_level=ensemble_level)
    assert table_vars.read_table() == expected


def test_read_table_with_aliases(ensemble_config_with_aliases):
    config_data = OmegaConf.create({
        "member_level": {
            "setup": {
                "runid": ["run-01", "run-02"],
            },
            "banana": ["cmip6-piControl", "cmip6-piControl"]
        }
    })

    expected = [
        {'setup': {'runid': 'run-01', 'exp': 'cmip6-piControl'}},
        {'setup': {'runid': 'run-02', 'exp': 'cmip6-piControl'}}
    ]

    cfg = OmegaConf.create({
        "member_level": config_data["member_level"],
        "ensemble_level": ensemble_config_with_aliases
    })

    ensemble_config, table = load_config(cfg, show_diffs=False)
    assert table == expected, "Resolved table does not match expected output"


def test_read_table_with_nested_aliases(
    ensemble_config_with_nested_aliases
):
    config_data = OmegaConf.create({
        "member_level": {
            "setup": {
                "runid": ["run-01", "run-02"],
                "exp": ["cmip6-piControl", "cmip6-piControl"],
            },
            "apple": [1, 2],
        }
    })

    cfg = OmegaConf.create({
        "member_level": config_data["member_level"],
        "ensemble_level": ensemble_config_with_nested_aliases
    })

    expected = [
        {'setup': {'runid': 'run-01', 'exp': 'cmip6-piControl'}, 'one': {'two': {'three': 1}}},
        {'setup': {'runid': 'run-02', 'exp': 'cmip6-piControl'}, 'one': {'two': {'three': 2}}}
    ]

    ensemble_config, table = load_config(cfg, show_diffs=False)
    assert table == expected, "Resolved table does not match expected output"


def test_read_table_nested_alias_conflict(
    ensemble_config_with_nested_alises_conflict
):
    """This tests the case where a key is treated as both a parameter and a value.
    In this case, one:two is assigned a value in the csv table, but one:two:three is an alias
    for a sub-value. Such a situation raises a conflict.
    """
    config_data = OmegaConf.create({
        "member_level": {
            "setup": {
                "runid": ["run-01", "run-02"],
            },
            "banana": ["cmip6-piControl", "cmip6-piControl"],
            "apple": [1, 2],
        }
    })

    cfg = OmegaConf.create({
        "member_level": config_data["member_level"],
        "ensemble_level": ensemble_config_with_nested_alises_conflict
    })

    with pytest.raises(ConfigTypeError):
        # This should raise an error due to the conflict in aliases
        # where 'one:two' is both a parameter and an alias.
        ensemble_config, table = load_config(cfg, show_diffs=False)


def test_get_table(config_data_two, setup_config, ensemble_config_txt_one):

    member_level = MemberLevelVars(config_data=config_data_two["member_level"])
    ensemble_level = EnsembleLevelVars(**ensemble_config_txt_one)

    expected = [
        {
            "setup": {
                **setup_config,
                "runid": "run-01",
                "exp": "cmip6-piControl",
            }
        },
        {
            "setup": {
                **setup_config,
                "runid": "run-02",
                "exp": "cmip6-piControl",
            }
        },
    ]

    text_table_vars = CSVTableVars(
        member_level=member_level,
        ensemble_level=ensemble_level
    )

    assert text_table_vars.get_table(show_diffs=True) == expected
