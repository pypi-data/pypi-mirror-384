import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from imsi.tools.list.list_manager import (
    _filter_dataframe,
    _load_model_experiment_pairs,
    gather_choices_df,
)


def test_filter_dataframe():
    df = pd.DataFrame({
        "model": ["A", "B", "A"],
        "experiment": ["exp1", "exp2", "exp2"],
    })
    filters = {"model": "A", "experiment": None}
    filtered = _filter_dataframe(df, filters)
    assert all(filtered["model"] == "A")


def test_load_model_experiment_pairs():
    mock_db = MagicMock()
    mock_db.get_config.return_value = ["exp1"]
    mock_db.get_parsed_config.return_value = {"supported_models": ["A", "B"]}

    with patch("imsi.tools.list.list_manager.database_factory", return_value=mock_db):
        df = _load_model_experiment_pairs(Path("fake"))
    assert set(df["model"]) == {"A", "B"}
    assert set(df["experiment"]) == {"exp1"}


def test_gather_choices_df_filters(tmp_path):
    repo = tmp_path
    config_path = Path("imsi-config")

    mock_df = pd.DataFrame({
        "model": ["A", "B"],
        "experiment": ["exp1", "exp2"],
    })

    with patch("imsi.tools.list.list_manager._load_model_experiment_pairs", return_value=mock_df):
        df = gather_choices_df(
            repo_paths=[repo],
            repo_sources=["src"],
            relative_imsi_config_path=config_path,
            filter_model="A"
        )
    assert set(df["model"]) == {"A"}
    assert set(df["experiment"]) == {"exp1"}
