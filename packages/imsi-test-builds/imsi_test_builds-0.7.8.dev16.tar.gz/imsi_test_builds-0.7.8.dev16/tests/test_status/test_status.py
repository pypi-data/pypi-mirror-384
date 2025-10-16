import pytest
from pathlib import Path
from types import NoneType
import pandas as pd
from imsi.sequencer_interface.maestro_status import (
    get_root_module,
    check_entry_and_get_dataframe,
    create_maestro_dataframe,
    check_row_for_string,
    filter_df
)

# construct path relative to this file
mock_begin = Path(__file__).parent.resolve() / "mock_begin"
mock_empty = Path(__file__).parent.resolve() / "mock_empty"
mock_stop = Path(__file__).parent.resolve() / "mock_stop"
mock_end = Path(__file__).parent.resolve() / "mock_end"


@pytest.mark.parametrize("wrk_dir, expected", [
    (mock_begin, "canesm"),
    (mock_empty, "banana")
])
def test_get_root_module(wrk_dir, expected):
    assert get_root_module(wrk_dir) == expected


@pytest.mark.parametrize("root_module, entry_path, expected", [
    ("canesm", Path(mock_begin, "sequencer", "sequencing", "status", "12345678910123"), pd.DataFrame),
    ("canesm", Path(mock_end, "sequencer", "sequencing", "status", "20250224220900"), pd.DataFrame),
    ("canesm", Path(mock_stop, "sequencer", "sequencing", "status", "20250222000900"), pd.DataFrame),
    ("banana", Path(mock_empty), NoneType)
])
def test_check_entry_and_get_dataframe(root_module, entry_path, expected):
    assert isinstance(check_entry_and_get_dataframe(root_module, entry_path), expected)


@pytest.mark.parametrize("entry_path, expected", [
    (Path(mock_begin, "sequencer", "sequencing", "status", "12345678910123"), pd.DataFrame),
    (Path(mock_end, "sequencer", "sequencing", "status", "20250224220900"), pd.DataFrame),
    (Path(mock_stop, "sequencer", "sequencing", "status", "20250222000900"), pd.DataFrame),]
)
def test_create_maestro_dataframe(entry_path, expected):
    df = create_maestro_dataframe(entry_path)
    assert isinstance(df, expected)
    assert len(df) > 0
    assert len(df.columns) > 0


def test_check_row_for_string():
    df = pd.DataFrame({"col1": ["canesm", "banana", "apple"], "col2": ["canesm", "banana", "apple"]})
    assert check_row_for_string(df.iloc[0], "canesm")
    assert not check_row_for_string(df.iloc[1], "horse")


def test_filter_df():
    # Create a sample DataFrame
    data = {
        "col1": [
            "job1.+1.begin",
            "job2.+1.abort.stop",
            "job3.+1.end",
            "job4.+1.catchup",
            "job5.+1.submit",
            "job6.+1.other"  # check that it ignores non recognized statuses
        ],
        "col2": [
            "job1.+1.begin",
            "job2.+1.abort.stop",
            "job3.+1.end",
            "job4.+1.catchup",
            "job5.+1.submit",
            "job6.+1.other"
        ]
    }
    df = pd.DataFrame(data)

    # Expected DataFrame after filtering
    expected_data = {
        "col1": [
            "job1.+1.begin",
            "job2.+1.abort.stop",
            "job3.+1.end",
            "job4.+1.catchup",
            "job5.+1.submit",
        ],
        "col2": [
            "job1.+1.begin",
            "job2.+1.abort.stop",
            "job3.+1.end",
            "job4.+1.catchup",
            "job5.+1.submit",
        ],
        "job_file": [
            "job1.+1.begin",
            "job2.+1.abort.stop",
            "job3.+1.end",
            "job4.+1.catchup",
            "job5.+1.submit",
        ],
        "loop_number": [1, 1, 1, 1, 1],
        "job_base": [
            "job1",
            "job2",
            "job3",
            "job4",
            "job5"
        ],
        "job_status": [
            "begin",
            "stop",
            "end",
            "catchup",
            "submit"
        ]
    }
    expected_df = pd.DataFrame(expected_data)

    # Call the filter_df function
    filtered_df = filter_df(df)
    # Assert the filtered DataFrame is as expected
    pd.testing.assert_frame_equal(
        filtered_df.reset_index(drop=True),
        expected_df.reset_index(drop=True),
        check_dtype=False
    )
