import pytest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from imsi.user_interface.setup_manager import ValidatedSetupOptions, InvalidSetupConfig


# Fixtures
@pytest.fixture
def mock_path_exists():
    """Fixture to mock Path.exists() method."""
    with patch.object(Path, "exists", return_value=True):
        yield


@pytest.fixture
def valid_inputs(request):
    pars = {
        "repo": request.config.getoption("--target-repo"),
        "ver": request.config.getoption("--target-branch"),
        "model": request.config.getoption("--target-model"),
        "exp": request.config.getoption("--target-exp"),
        "runid": "valid-runid",
        "fetch_method": "clone",
        "seq": "sequence",
        "machine": request.config.getoption("--target-machine"),
        "flow": "flow-abc",
        "postproc": "bananas!"
    }
    return pars


# Test cases for field validation
@pytest.mark.parametrize(
    "runid, should_raise",
    [
        ("valid-runid", False),
        ("invalid_runid!", True),
        ("runid_with_uppercase", True),
        ("short", False),
        ("run-id-hyphen-09", False),
    ],
)
def test_validate_runid(valid_inputs, runid, should_raise):
    valid_inputs["runid"] = runid
    if should_raise:
        with pytest.raises(InvalidSetupConfig, match="Your runid --->"):
            ValidatedSetupOptions(**valid_inputs)
    else:
        options = ValidatedSetupOptions(**valid_inputs)
        assert options.runid == runid


@pytest.mark.parametrize(
    "repo, should_raise",
    [
        # get the valid repo from the command line args
        ("placeholder", False),
        ("git@github.com:user/repo.git", True),  # doesn't exist!
        ("invalid_repo_url", True),
        ("", True),
    ],
)
def test_validate_git_clone(valid_inputs, repo, should_raise):
    if repo == "placeholder":
        repo = valid_inputs["repo"]
    valid_inputs["repo"] = repo
    if should_raise:
        with pytest.raises(
            InvalidSetupConfig
        ):
            ValidatedSetupOptions(**valid_inputs)
    else:
        options = ValidatedSetupOptions(**valid_inputs)
        assert options.repo == repo


@pytest.mark.parametrize(
    "fetch_method, ver, should_raise",
    [
        ("clone", "develop_canesm", False),
        ("clone", None, True),
        ("link", None, False),
        ("copy", None, False),
        ("invalid_method", None, True),
    ],
)
def test_validate_fetch_method(valid_inputs, fetch_method, ver, should_raise):
    valid_inputs["fetch_method"] = fetch_method
    valid_inputs["ver"] = ver
    if should_raise:
        with pytest.raises(
            InvalidSetupConfig
        ):
            ValidatedSetupOptions(**valid_inputs)
    else:
        options = ValidatedSetupOptions(**valid_inputs)
        assert options.fetch_method == fetch_method


@pytest.mark.parametrize(
    "fetch_method, ver, should_raise",
    [
        ("clone", "develop_canesm", False),
        ("clone", None, True),
        ("link", "develop_canesm", True),
        ("copy", "develop_canesm", True),
        ("link", None, False),
        ("copy", None, False),
    ],
)
def test_error_if_version_unused_or_used(valid_inputs, fetch_method, ver, should_raise):
    valid_inputs["fetch_method"] = fetch_method
    valid_inputs["ver"] = ver

    if should_raise:
        with pytest.raises(InvalidSetupConfig):
            ValidatedSetupOptions(**valid_inputs)
    else:
        options = ValidatedSetupOptions(**valid_inputs)
        assert options.fetch_method == fetch_method
        assert options.ver == ver


# Test missing required fields
@pytest.mark.parametrize("missing_field", ["runid", "repo", "fetch_method", "exp"])
def test_missing_required_fields(valid_inputs, missing_field):
    valid_inputs.pop(missing_field, None)
    with pytest.raises(ValidationError, match=f"{missing_field}"):
        ValidatedSetupOptions(**valid_inputs)


@pytest.mark.parametrize(
    "ver, should_raise",
    [
        ("develop_canesm", False),
        ("bad-branch-yolo", True),  # pretty sure nobody will name a branch this ;)
        ("v5.1.6", False),
        ("68e8a27e42ab80588a08d7326af3c8a793f6f774", False),  # commit hash
        ("68e8a27", False),  # Partial commit hash
        ("??$?$?", True)  # invalid commit hash
    ],
)
def test_validate_branch(valid_inputs, ver, should_raise):
    valid_inputs["ver"] = ver
    if should_raise:
        with pytest.raises(
            InvalidSetupConfig, match="not a valid remote branch or tag"
        ):
            ValidatedSetupOptions(**valid_inputs)
    else:
        options = ValidatedSetupOptions(**valid_inputs)
        assert options.ver == ver
