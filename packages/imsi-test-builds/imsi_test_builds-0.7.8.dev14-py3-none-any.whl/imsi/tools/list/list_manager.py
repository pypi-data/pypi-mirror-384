
from pathlib import Path
from typing import Iterable
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from imsi.config_manager.config_manager import database_factory
from typing import Callable, Hashable


def _filter_dataframe(
    df: pd.DataFrame,
    filters: dict[Hashable, str | None],
    match_fn: Callable[[pd.Series, str], pd.Series] = lambda col, val: col == val,
) -> pd.DataFrame:
    for column, value in filters.items():
        if value is not None:
            df = df[match_fn(df[column], value)]
    return df


def _load_model_experiment_pairs(imsi_config_path: Path) -> pd.DataFrame:
    experiments_db = database_factory(imsi_config_path / "experiments")
    experiments = experiments_db.get_config("experiments")

    data = []
    for experiment in experiments:
        models = experiments_db.get_parsed_config("experiments", experiment).get("supported_models", [])
        for model in models:
            data.append((model, experiment))

    df = pd.DataFrame(data, columns=["model", "experiment"]) if data else pd.DataFrame()

    return df


def gather_choices_df(
    repo_paths: Iterable[Path],
    repo_sources: Iterable[str],
    relative_imsi_config_path: Path,
    filter_model: str = None,
    filter_experiment: str = None,
) -> pd.DataFrame:

    all_rows = []
    for repo, source in zip(repo_paths, repo_sources):
        imsi_config_path = repo / relative_imsi_config_path
        df = _load_model_experiment_pairs(imsi_config_path)

        if df.empty:
            continue

        df["repo"] = str(repo)
        df["source"] = source

        filters = {
            "model": filter_model,
            "experiment": filter_experiment,
        }
        df = _filter_dataframe(df, filters)

        if not df.empty:
            all_rows.append(df)

    if not all_rows:
        return pd.DataFrame()

    return pd.concat(all_rows, ignore_index=True)


def render_choices_table(df: pd.DataFrame) -> None:
    """
    Render available models/experiments grouped by site/source,
    always showing full model names.
    """
    console = Console()

    if df.empty:
        console.print("[red]No matching configurations found.[/red]")
        return

    grouped_data = []
    for (source, repo), df_group in df.groupby(["source", "repo"]):
        grouped = df_group.groupby("model")["experiment"].apply(
            lambda exps: ", ".join(sorted(set(exps)))
        )
        grouped_data.append(((source, repo), grouped))

    # Render each group
    for (source, repo), grouped in grouped_data:
        table = Table(show_header=True, box=None, padding=(0, 1))

        table.add_column("Model", justify="left", style="magenta", no_wrap=True)
        table.add_column("Supported Experiments", justify="left", style="cyan", overflow="fold")

        for model, experiments in grouped.items():
            table.add_row(model, experiments)

        panel_title = f"[green]{repo}[/green] ({source})"
        console.print(Panel(table, title=panel_title, border_style="cyan"))


def list_all_choices(
    repo_paths: Iterable[Path],
    repo_sources: Iterable[str],
    relative_imsi_config_path: Path,
    filter_model: str = None,
    filter_experiment: str = None,
):
    df = gather_choices_df(
        repo_paths=repo_paths,
        repo_sources=repo_sources,
        relative_imsi_config_path=relative_imsi_config_path,
        filter_model=filter_model,
        filter_experiment=filter_experiment
    )
    render_choices_table(df)
