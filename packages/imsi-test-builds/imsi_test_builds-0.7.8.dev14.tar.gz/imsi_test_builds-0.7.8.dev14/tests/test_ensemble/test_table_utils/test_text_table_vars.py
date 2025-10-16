import pytest
from omegaconf import OmegaConf, DictConfig
from pydantic import ValidationError
from imsi.tools.ensemble.table_utils.table_model import TextTableVars
from imsi.tools.ensemble.table_utils.data_model import (
    MemberLevelVars,
    EnsembleLevelVars,
)

@pytest.fixture
def config_params():
    """Static defaults so the tests don’t need CLI options."""
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
def config_data_one(setup_config):
    """A minimal but valid member-level configuration."""
    return OmegaConf.create(
        {"member_level": {"setup": {**setup_config, "runid": ["run1"]}}}
    )


@pytest.fixture
def text_table_basic(tmp_path):
    """setup:runid  setup:exp"""
    p = tmp_path / "basic.txt"
    p.write_text(
        "setup:runid  setup:exp\n"
        "run-01       cmip6-piControl\n"
        "run-02       cmip6-piControl\n"
    )
    return str(p)


@pytest.fixture
def text_table_nested(tmp_path):
    """one:two:three in addition to setup keys."""
    p = tmp_path / "nested.txt"
    p.write_text(
        "setup:runid  setup:exp  one:two:three\n"
        "run-01       cmip6-piControl  1\n"
        "run-02       cmip6-piControl  2\n"
    )
    return str(p)


@pytest.fixture
def text_table_conflict(tmp_path):
    """`one:two` AND `one:two:three` => conflict."""
    p = tmp_path / "conflict.txt"
    p.write_text(
        "setup:runid  one:two  one:two:three\n"
        "run-01       10       100\n"
        "run-02       20       200\n"
    )
    return str(p)


def _ensemble_cfg(path: str) -> DictConfig:
    """Create an ensemble-level DictConfig pointing at *path*."""
    return OmegaConf.create(
        {
            "user": "test_user",
            "run_directory": "./",
            "config_table": path,
            "share_repo": True,
        }
    )


def test_text_table_vars_valid(config_data_one, text_table_basic):
    member = MemberLevelVars(config_data=config_data_one["member_level"])
    ensemble = EnsembleLevelVars(**_ensemble_cfg(text_table_basic))

    obj = TextTableVars(member_level=member, ensemble_level=ensemble)
    assert isinstance(obj, TextTableVars)


def test_text_table_vars_invalid(config_data_one):
    """Passing an int for ensemble_level should trigger pydantic ValidationError."""
    member = MemberLevelVars(config_data=config_data_one["member_level"])
    with pytest.raises(ValidationError):
        TextTableVars(member_level=member, ensemble_level=int)  # type: ignore[arg-type]


def test_read_table_basic(config_data_one, text_table_basic):
    expected = OmegaConf.create(
        {
            "setup": {
                "runid": ["run-01", "run-02"],
                "exp": ["cmip6-piControl", "cmip6-piControl"],
            }
        }
    )

    member = MemberLevelVars(config_data=config_data_one["member_level"])
    ensemble = EnsembleLevelVars(**_ensemble_cfg(text_table_basic))

    tbl = TextTableVars(member_level=member, ensemble_level=ensemble)

    with pytest.warns(DeprecationWarning):
        result = tbl.read_table()

    assert result == expected


def test_read_table_nested_keys(config_data_one, text_table_nested):
    expected = OmegaConf.create(
        {
            "setup": {
                "runid": ["run-01", "run-02"],
                "exp": ["cmip6-piControl", "cmip6-piControl"],
            },
            "one": {"two": {"three": [1, 2]}},
        }
    )

    member = MemberLevelVars(config_data=config_data_one["member_level"])
    ensemble = EnsembleLevelVars(**_ensemble_cfg(text_table_nested))

    tbl = TextTableVars(member_level=member, ensemble_level=ensemble)
    with pytest.warns(DeprecationWarning):
        result = tbl.read_table()

    assert result == expected


def test_read_table_conflict_raises(config_data_one, text_table_conflict):
    member = MemberLevelVars(config_data=config_data_one["member_level"])
    ensemble = EnsembleLevelVars(**_ensemble_cfg(text_table_conflict))

    tbl = TextTableVars(member_level=member, ensemble_level=ensemble)

    with pytest.raises(ValueError):
        tbl.read_table()
