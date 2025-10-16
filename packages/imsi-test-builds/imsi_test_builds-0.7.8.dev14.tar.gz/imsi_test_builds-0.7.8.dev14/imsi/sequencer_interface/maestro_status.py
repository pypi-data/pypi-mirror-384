from pathlib import Path
from typing import Dict
import re

import pandas as pd
from rich.console import Console
from rich.table import Table


def get_root_module(work_dir: Path) -> str:
    """
    Retrieves the name of the root module from a given working directory.

    This function constructs a symlink path to the "EntryModule" within the "sequencer" directory
    of the specified working directory, resolves the symlink, and returns the name of the root module.

    Args:
        work_dir: The working directory containing the "sequencer" directory.

    Returns: The name of the root module.
    """
    symlink_path = Path(work_dir, "sequencer", "EntryModule")
    return symlink_path.resolve().name


def check_entry_and_get_dataframe(root_module: str, entry_path: Path) -> pd.DataFrame:
    """
    Checks if the specified root module entry exists in the given path and returns a DataFrame.

    This function verifies the existence of the root module within the provided entry path.
    If the root module does not exist, it prints an error message and lists the files found
    in the entry path. If the root module exists, it creates and returns a DataFrame using
    the `create_maestro_dataframe` function.

    Args:
        root_module (str): The name of the root module to check.
        entry_path (Path): The path where the root module entry is expected to be found.

    Returns:
        pd.DataFrame: A DataFrame created from the entry path if the root module exists,
                      otherwise None.
    """
    console = Console()
    files = Path(entry_path).glob(f"{root_module}.*")

    if not (entry_path / root_module).exists():
        console.print(f"[bright_red]Experiment '{entry_path.name}' for the root module '{root_module}' does not exist.[/bright_red]")
        console.print(f"Files found: {[file.name for file in files]}. Did the model submit properly?")
        console.print("If a new experiment date folder was created after re-submitting, this error will persist until the stale directory is removed.")

        return None

    return create_maestro_dataframe(entry_path=entry_path)


def create_maestro_dataframe(entry_path: Path):
    """
    Creates a pandas DataFrame from the directory structure starting at the given entry path.
    
    The DataFrame will contain the paths of all files located in the leaf directories (directories 
    that do not contain any subdirectories). The paths are split into their components and normalized 
    to the same depth. The resulting DataFrame will only include columns starting from the first 
    occurrence of the string 'canesm' in any of the paths.

    Parameters:
    entry_path (Path): The root directory path to start the search for leaf directories.

    Returns:
    pd.DataFrame: A DataFrame where each row represents a file path split into its components, 
                  normalized to the same depth, and filtered to start from the first occurrence 
                  of 'canesm'.
    """

    # Get all files from leaf directories
    leaf_files = []

    for dir_path in entry_path.rglob("*"):
        if dir_path.is_dir() and not any(subdir.is_dir() for subdir in dir_path.iterdir()):
            for file in dir_path.iterdir():
                if file.is_file():
                    leaf_files.append(file)

    if len(leaf_files) == 0:
        raise ValueError("No status files found in the sequencer/experiment directory tree.")

    # Split paths and normalize to the same depth
    split_paths = [list(path.parts) for path in leaf_files]
    max_depth = max(len(path) for path in split_paths)
    normalized_paths = [path + [None] * (max_depth - len(path)) for path in split_paths]

    # Create DataFrame and filter columns
    df = pd.DataFrame(normalized_paths, columns=[f'Level {i}' for i in range(max_depth)])
    df = df.iloc[:, df.columns.get_loc(df.columns[df.isin(['canesm']).any()][0]):]

    return df


def check_row_for_string(row: pd.Series, pattern: re.Pattern) -> bool:
    """
    Check if any element in a pandas Series row contains a given pattern.

    Parameters:
    row (pandas.Series): The row of data to check.
    pattern (str): The string pattern to search for within the row.

    Returns:
    bool: True if the pattern is found in any element of the row, False otherwise.
    """
    return row.astype(str).str.contains(pattern).any()


def filter_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters a DataFrame based on specific patterns and extracts relevant job information.

    This function filters rows in the input DataFrame `df` based on predefined regex patterns
    for job statuses such as 'begin', 'abort.stop', 'end', 'catchup', and 'submit'. It then
    extracts job-related information including job file, loop number, job base, and job status.
    The filtered DataFrame is sorted by loop number in descending order, duplicates are removed
    based on job base, and rows with all NaN values are dropped.

    Args:
        df (pd.DataFrame): The input DataFrame to be filtered.

    Returns:
        pd.DataFrame: The filtered DataFrame with extracted job information.
    """
    begin_pattern = re.compile(r'.+\..*\.begin')
    stop_pattern = re.compile(r'.+\..*\.abort\.stop')
    end_pattern = re.compile(r'.+\..*\.end')
    catchup_pattern = re.compile(r'.+\..*\.catchup')
    submit_pattern = re.compile(r'.+\..*\.submit')

    # Filter rows based on patterns
    filtered_df = df[
        df.apply(
            lambda row: (
                check_row_for_string(row, stop_pattern) or
                check_row_for_string(row, begin_pattern) or
                check_row_for_string(row, end_pattern) or
                check_row_for_string(row, catchup_pattern) or
                check_row_for_string(row, submit_pattern)
            ), axis=1
        )
    ].copy()

    # Extract job_file, loop_number, job_base, and job_status
    try:
        filtered_df['job_file'] = filtered_df.apply(lambda row: row.dropna().iloc[-1], axis=1)
        filtered_df["loop_number"] = (
            filtered_df["job_file"].str.extract(r"\.\+(\d+)").fillna(-1).astype(int)
        )
        filtered_df["job_base"] = filtered_df["job_file"].str.extract(
            r"^(.*?)(?:\.\+\d+\..*)?$"
        )
        filtered_df["job_status"] = filtered_df["job_file"].apply(
            lambda x: Path(x).suffix[1:]
        )

    except (KeyError, ValueError):
        msg = """The sequencer directory tree has not been filled with status files that match status patterns yet.
        This edge case occurs when there are status files that exist in the sequencer/experiment subtree, but don't
        match the status patterns. If you recently submitted a job, please wait for maestro to create the files and try again.
        """
        raise ValueError(msg)
    finally:

        # Sort and drop duplicates
        filtered_df = filtered_df.sort_values('loop_number', ascending=False).drop_duplicates('job_base')
        filtered_df = filtered_df.transpose().dropna().transpose()

        return filtered_df


def update_table(table: Table, exp: str, filtered_df: pd.DataFrame, color_map: Dict[str, str]) -> Table:
    """
    Update the given table with experiment status information.

    Args:
        table (Table): textualize rich table object to be updated.
        exp (str or Path): The experiment path containing the status files..
        filtered_df (pd.DataFrame): A DataFrame containing filtered job information with columns 'job_base', 
            'loop_number', and 'job_status'.
        color_map (Dict[str, str]): A dictionary mapping job statuses to their corresponding color codes.

    Returns:
        Table: The updated table object.
    """

    df_table = filtered_df[["job_base", "loop_number", "job_status"]].copy()
    row_list = [exp.name]
    endfile_exists = len(list(Path(exp).glob("*.end"))) > 0
    if endfile_exists:
        row_list.append(f'[{color_map.get("end")}]job finished![/{color_map.get("end")}]')
    for _, row in df_table.iterrows():
        if not row['job_status'] == 'end':
            color = color_map.get(row['job_status'], None)
            row_list.append(f"[{color}]{row['job_base']} (+{row['loop_number']})[/{color}]")
    table.add_row(*row_list)

    return table
