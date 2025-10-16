import questionary
from imsi.tools.list.list_manager import gather_choices_df

from typing import Dict, List
import subprocess
from rich.console import Console
from rich.panel import Panel


def select_imsi_config_with_questionary(repo_paths, repo_sources, relative_imsi_config_path) -> dict | None:
    df = gather_choices_df(repo_paths, repo_sources, relative_imsi_config_path)
    if df.empty:
        return None

    # Step 1: Select repo
    repo_choices = sorted(df["repo"].unique())
    repo = questionary.select("Choose a repo:", choices=repo_choices, use_shortcuts=True).ask()
    if not repo:
        return None

    # Step 2: Select model within that repo
    model_choices = sorted(df[df["repo"] == repo]["model"].unique())
    if not model_choices:
        return None

    model = questionary.select("Choose a model:", choices=model_choices, use_shortcuts=True).ask()
    if not model:
        return None

    # Step 3: Select experiment within that model+repo
    exp_choices = sorted(df[(df["repo"] == repo) & (df["model"] == model)]["experiment"].unique())
    if not exp_choices:
        return None

    experiment = questionary.select("Choose an experiment:", choices=exp_choices, use_shortcuts=True).ask()
    if not experiment:
        return None

    return {
        "repo": repo,
        "model": model,
        "exp": experiment,
    }


def prompt_additional_options() -> Dict[str, str]:

    runid_question = "Enter runid (e.g., my-run-01):"
    runid = questionary.text(
        "Enter runid (e.g., my-run-01):",
        validate=lambda x: True if len(x) > 0 else runid_question
    ).ask()
    # above is an input validation - not imsi validation

    if not runid:
        return None

    fetch_method = questionary.select(
        "Select fetch_method:",
        choices=["copy", "link"],
        default="copy"
    ).ask()

    if not fetch_method:
        return None

    return {"runid": runid, "fetch_method": fetch_method}


def build_setup_command(options: Dict[str, str]) -> List[str]:
    cmd = ["imsi", "setup"]
    for key, value in options.items():
        if value:
            cmd.extend([f"--{key}", str(value)])
    return cmd


def print_command(cmd: List[str]):
    console = Console()
    command_str = " ".join(cmd)

    console.print(Panel(
        command_str,
        title="[bold yellow]Setup Command[/bold yellow]",
        border_style="bold green",
        expand=False,
        padding=(1, 2)
    ))


def execute_command(cmd: List[str]):
    print(f"\n\033[2mExecuting: {' '.join(cmd)}\033[0m")
    try:
        subprocess.run(cmd, check=True)
        print("\033[1;32m[✓] Command executed successfully!\033[0m")
    except subprocess.CalledProcessError as e:
        print(f"\033[1;31m[✗] Error executing command: {e}\033[0m")
    except FileNotFoundError:
        print("\033[1;31m[✗] Error: 'imsi' command not found. Ensure it's in your PATH.\033[0m")
