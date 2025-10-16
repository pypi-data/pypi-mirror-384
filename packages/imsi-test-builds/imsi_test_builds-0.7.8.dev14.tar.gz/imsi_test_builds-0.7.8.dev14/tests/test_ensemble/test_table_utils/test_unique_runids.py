from imsi.tools.ensemble.table_utils.table_utils import validate_runids
import pytest

@pytest.fixture
def unique_runids():
    return [
        {"setup": {"runid": "run-yaml-002"}},
        {"setup": {"runid": "run-yaml-005"}}
    ]


@pytest.fixture
def non_unique_runids():
    return [
        {"setup": {"runid": "run-yaml-002"}},
        {"setup": {"runid": "run-yaml-002"}}
    ]



def test_check_unique_runids_pass(unique_runids):
    validate_runids(unique_runids)


def test_check_unique_runids_warn(non_unique_runids):
    with pytest.warns(UserWarning, match="Duplicate 'runid' values detected"):
        validate_runids(non_unique_runids)