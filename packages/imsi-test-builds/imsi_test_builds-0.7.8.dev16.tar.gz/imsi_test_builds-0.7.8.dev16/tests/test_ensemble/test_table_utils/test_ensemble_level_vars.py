from imsi.tools.ensemble.table_utils.data_model import EnsembleLevelVars
from pydantic import ValidationError
import pytest
from pathlib import Path

parent_dir = Path(__file__).resolve().parent


# test various class instantiations with some purposefully incorrect inputs
good_example_vars = {
    "user": "test_user",
    "run_directory": str(parent_dir / "."),
    "config_table": str(parent_dir / "config.yaml"),
    "aliases": {"alias1": "banana"},
    "share_repo": True,
}

bad_example_vars_user = {
    "user": 1,
    "run_directory": "/path/to/run",
    "config_table": "/path/to/config_table",
    "aliases": {"alias1": "banana"},
    "share_repo": True,
}

bad_example_vars_run_directory = {
    "user": "test_user",
    "run_directory": "123",
    "config_table": "/path/to/config_table",
    "aliases": {"alias1": "banana"},
    "share_repo": True,
}

bad_example_vars_config_table = {
    "user": "test_user",
    "run_directory": "/path/to/run",
    "config_table": "123",
    "aliases": {"alias1": "banana"},
    "share_repo": True,
}

bad_example_vars_aliases = {
    "user": "test_user",
    "run_directory": "/path/to/run",
    "config_table": "/path/to/config_table",
    "aliases": "banana",
    "share_repo": True,
}

bad_example_vars_share_repo = {
    "user": "test_user",
    "run_directory": "/path/to/run",
    "config_table": "/path/to/config_table",
    "aliases": {"alias1": "banana"},
    "share_repo": True,
}


def test_good_ensemble_level_vars():
    EnsembleLevelVars(**good_example_vars)


@pytest.mark.parametrize(
    "ensemble_level_vars",
    [
        (bad_example_vars_user),
        (bad_example_vars_run_directory),
        (bad_example_vars_config_table),
        (bad_example_vars_aliases),
        (bad_example_vars_share_repo),
    ],
)
def test_bad_ensemble_level_vars(ensemble_level_vars):
    with pytest.raises(ValidationError):
        EnsembleLevelVars(**ensemble_level_vars)
