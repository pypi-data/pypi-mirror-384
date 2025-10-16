import pytest
from imsi.tools.ensemble.table_utils.table_utils import (
    get_keys,
    remove_explicit_none,
    convert_to_bracket_notation,
    replace_aliases,
    add_nested_key,
    warn_on_overlapping_keys,
)
from imsi.tools.ensemble.config import load_config

from omegaconf import OmegaConf, DictConfig
import copy
from pathlib import Path

parent_dir = Path(__file__).resolve().parent


def make_cfg(mapping) -> DictConfig:
    """Convenience wrapper to create DictConfig objects from plain dicts."""
    return OmegaConf.create(mapping)


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
    return make_cfg({
        "ver": config_params["branch"],
        "repo": config_params["repo"],
        "fetch_method": "clone",
        "machine": "ppp6",
        "model": config_params["model"],
        "runid": ["run1"],
        "exp": config_params["experiment"]
    })


@pytest.fixture
def config_data_one(setup_config):
    """Configuration data for the first test case."""
    return make_cfg({
        "member_level": {
            "setup": setup_config,
        }
    })


@pytest.fixture
def config_data_two(setup_config):
    """Configuration data for the second test case."""
    return make_cfg({
        "member_level": {
            "setup": {
                **setup_config,
                "model": [setup_config["model"], setup_config["model"]],  # override for test
                "runid": ["run-yaml-001", "run-yaml-002"],
            }
        }
    })


def test_get_keys(config_data_two):
    cfg = make_cfg({
        "ensemble_level": {
            "user": "test_user",
            "run_directory": str(parent_dir / "."),
            "config_table": str(parent_dir / "config_table.yaml"),
        },
        "member_level": config_data_two["member_level"],
    })

    ensemble_config, constructed_table = load_config(cfg, show_diffs=False)
    assert get_keys(constructed_table[1]) == {
        'setup:exp',
        'components',
        'components:CanAM',
        'components:CanAM:namelists:canam_settings',
        'setup:runid',
        'components:CanAM:namelists:canam_settings:pp_rdm_num_pert',
        'setup:repo',
        'setup',
        'components:CanAM:namelists',
        'setup:ver',
        'setup:machine',
        'setup:fetch_method',
        'setup:model'
    }


@pytest.fixture
def config_with_explicit_none():
    """Configuration with an explicit None value."""
    return {
        "setup": {
            "runid": "run-yaml-002",
            "exp": "test_exp",
        },
        "components": {
            "CanAM": {"namelists": {"canam_settings": {"pp_rdm_num_pert": None}}}
        }
    }


@pytest.fixture
def config_with_explicit_none_removed():
    """Configuration with explicit None values removed."""
    return {
        "setup": {
            "runid": "run-yaml-002",
            "exp": "test_exp",
        },
        "components": {"CanAM": {"namelists": {"canam_settings": {}}}}
    }


def test_remove_explicit_none(config_with_explicit_none, config_with_explicit_none_removed):
    expected = config_with_explicit_none_removed
    assert remove_explicit_none(config_with_explicit_none) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("setup:runid",        "setup[runid]"),
        ("root:child:0",       "root[child][0]"),
        ("singlekey",          "singlekey"),          # no delimiter → unchanged
        ("a:b:c:d",            "a[b][c][d]"),
        ("numeric:123:4",      "numeric[123][4]"),    # numbers stay as strings
        ("leading:",           "leading[]"),          # trailing empty segment
        (":trailing",          "[trailing]"),         # leading empty segment
        ("",                   ""),                   # empty string remains empty
    ],
)
def test_convert_to_bracket_notation_happy(raw, expected):
    assert convert_to_bracket_notation(raw) == expected


@pytest.mark.parametrize(
    "bad_input, exception",
    [
        (None,              AttributeError),   # .split fails on NoneType
        (123,               AttributeError),   # int has no .split
        (["a:b"],           AttributeError),   # list has no .split
    ],
)
def test_convert_to_bracket_notation_type_errors(bad_input, exception):
    with pytest.raises(exception):
        convert_to_bracket_notation(bad_input)


def test_single_alias_replaced():
    """
    Top-level key 'exp' is moved under 'setup.exp', and the original is removed.
    """
    cfg = make_cfg({"exp": "piControl"})
    aliases = {"exp": "setup:exp"}
    result = replace_aliases(cfg, aliases)

    assert "exp" not in result                    # alias key removed
    assert result.setup.exp == "piControl"        # value moved
    # same DictConfig instance mutated in-place:
    assert result is cfg


def test_alias_absent_no_change():
    original = make_cfg({"foo": 1})
    cfg_copy = copy.deepcopy(original)
    aliases = {"missing": "setup:missing"}
    result = replace_aliases(original, aliases)

    assert result == cfg_copy                    # deep equality
    assert result is original                    # same object


def test_multiple_aliases():
    cfg = make_cfg({"exp": "piControl", "runid": ["01", "02"]})
    aliases = {"exp": "setup:exp", "runid": "setup:runid"}

    replace_aliases(cfg, aliases)

    assert OmegaConf.to_container(cfg) == {
        "setup": {"exp": "piControl", "runid": ["01", "02"]}
    }


def test_merge_into_existing_path():
    """
    If 'setup' already exists, new keys are merged (not overwritten) because
    replace_aliases calls OmegaConf.update(..., merge=True).
    """
    cfg = make_cfg(
        {
            "setup": {"existing": 123},
            "exp": "amip",
            "runid": "03",
        }
    )
    aliases = {"exp": "setup:exp", "runid": "setup:runid"}

    replace_aliases(cfg, aliases)

    # Existing content is preserved; new keys merged
    assert OmegaConf.to_container(cfg) == {
        "setup": {"existing": 123, "exp": "amip", "runid": "03"}
    }


def test_add_top_level_key():
    cfg = make_cfg({})
    add_nested_key(cfg, "foo", 123)

    assert cfg.foo == 123
    assert OmegaConf.to_container(cfg) == {"foo": 123}


def test_add_nested_key():
    cfg = make_cfg({})
    add_nested_key(cfg, "setup:exp", "piControl")

    assert cfg.setup.exp == "piControl"
    assert OmegaConf.to_container(cfg) == {"setup": {"exp": "piControl"}}


def test_merge_into_existing_node():
    cfg = make_cfg({"setup": {"existing": 1}})
    add_nested_key(cfg, "setup:exp", "amip")

    assert cfg.setup.existing == 1            # untouched existing data
    assert cfg.setup.exp == "amip"
    assert OmegaConf.to_container(cfg) == {
        "setup": {"existing": 1, "exp": "amip"}
    }


def test_overlap_emits_warning():
    """
    Both configs contain 'setup:runid' so a UserWarning must be raised.
    """
    cfg1 = make_cfg({"setup": {"runid": "01"}})
    cfg2 = make_cfg({"setup": {"runid": "02", "other": 1}})

    # `pytest.warns` passes when *exactly one* warning of the requested type
    # occurs (additional warnings are also captured/allowed).
    with pytest.warns(UserWarning) as record:
        warn_on_overlapping_keys(cfg1, cfg2)

    # Optional: assert the message contains the overlapping key
    assert "setup:runid" in str(record[0].message)


def test_no_overlap_emits_no_warning(recwarn):
    """
    Distinct key sets: the function should be silent.
    """
    cfg1 = make_cfg({"setup": {"runid": "01"}})
    cfg2 = make_cfg({"model": {"name": "canam"}})

    warn_on_overlapping_keys(cfg1, cfg2)

    # `recwarn` is the warnings recorded list; should stay empty
    assert len(recwarn) == 0
