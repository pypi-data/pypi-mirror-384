import pytest
from pathlib import Path
from unittest.mock import patch
from imsi.tools.list.list_cli import load_rc, get_repo_paths


@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    """Fixture to set up fake site/user rc files and environment variables."""
    site_file = tmp_path / "imsi.site.rc"
    user_file = tmp_path / "imsi.user.rc"

    site_file.write_text("VAR1=site_value\nVAR2=multi:val:ue\n")
    user_file.write_text("VAR1=user_value\n")

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("VAR1", "env_value")
    monkeypatch.setenv("VAR3", "only_env")

    return site_file, user_file


def test_load_rc_merges_and_splits(mock_env):
    site_file, user_file = mock_env

    with patch("imsi.tools.list.list_cli.files") as mock_files, \
         patch("imsi.tools.list.list_cli.dotenv_values") as mock_dotenv:
        # fake return values for dotenv_values
        def dotenv_values_side_effect(dotenv_path):
            if str(dotenv_path).endswith("imsi.site.rc"):
                return {"VAR1": "site_value", "VAR2": "multi:val:ue"}
            if str(dotenv_path).endswith("imsi.user.rc"):
                return {"VAR1": "user_value"}
            return {}

        mock_dotenv.side_effect = dotenv_values_side_effect
        mock_files.return_value.joinpath.return_value = site_file

        result = load_rc("VAR2")
        assert ("multi", "imsi.site.rc") in result
        assert ("val", "imsi.site.rc") in result
        assert ("ue", "imsi.site.rc") in result
        # ensures no colons left
        assert all(":" not in v for v, _ in result)


def test_load_rc_returns_none_if_not_found(mock_env):
    with patch("imsi.tools.list.list_cli.files") as mock_files, \
         patch("imsi.tools.list.list_cli.dotenv_values", return_value={}):
        mock_files.return_value.joinpath.return_value = mock_env[0]
        result = load_rc("MISSING_VAR")
        assert result is None


def test_get_repo_paths_with_cli_arg(tmp_path):
    repo = tmp_path / "repo"
    config = repo / "imsi-config"
    config.mkdir(parents=True)

    with patch("imsi.user_interface.ui_manager.validate_version_reqs") as mock_validate:
        paths, sources, rel_path = get_repo_paths(str(repo))

    assert paths == [repo]
    assert sources == ["CLI args"]
    assert rel_path == Path("imsi-config")


def test_get_repo_paths_with_invalid_dir(tmp_path):
    bad_path = tmp_path / "not_a_repo"
    bad_path.write_text("file")

    with pytest.raises(ValueError):
        get_repo_paths(str(bad_path))


def test_get_repo_paths_with_rc(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    config = repo / "imsi-config"
    config.mkdir(parents=True)

    with patch("imsi.tools.list.list_cli.load_rc", return_value=[(str(repo), "rc_source")]), \
         patch("imsi.user_interface.ui_manager.validate_version_reqs") as mock_validate:
        paths, sources, rel_path = get_repo_paths(None)

    assert paths == [repo]
    assert sources == ["rc_source"]
    assert rel_path == Path("imsi-config")
