import pytest
from click.testing import CliRunner
from imsi.cli.entry import cli
from pathlib import Path
import subprocess
import shutil
import os


@pytest.fixture
def config_params(request):
    pars = {
        "repo": request.config.getoption("--target-repo"),
        "branch": request.config.getoption("--target-branch"),
        "model": request.config.getoption("--target-model"),
        "experiment": request.config.getoption("--target-exp"),
        "machine": request.config.getoption("--target-machine"),
        "seq": request.config.getoption("--target-sequencer"),
    }
    return pars


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def local_test_dir(request):
    """Create a temporary test directory under the current working directory and clean up after."""
    tmp_dir = Path.cwd() / f"test_tmp_{request.node.name}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


def clone_repo(target_repo, target_branch, tmp_dir, local_repo='local_repo'):
    """Generic shallow clone command for testing."""
    subprocess.run(
        [
            "git", "clone",
            "--depth", "1",
            "--shallow-submodules",
            "--branch", target_branch,
            target_repo,
            local_repo,
        ],
        check=True,
        cwd=Path(tmp_dir).resolve(),
    )

    repo_path = Path(tmp_dir, local_repo).resolve()
    subprocess.run(["git", "submodule", "init", "CanNEMO"], check=True, cwd=repo_path)
    subprocess.run(["git", "submodule", "update", "--init", "--recursive", "CanNEMO"], check=True, cwd=repo_path)


def run_test(
    runner,
    fetch_method,
    tmp_dir,
    target_repo,
    target_model,
    target_experiment,
    target_machine,
    target_sequencer,
    target_branch=None,
):

    runid = "test-run-tmp"

    copy_link_cmd = [
        "-f", "setup",
        f"--runid={runid}",
        f"--repo={target_repo}",
        f"--fetch_method={fetch_method}",
        f"--model={target_model}",
        f"--exp={target_experiment}",
        f"--machine={target_machine}",
        f"--seq={target_sequencer}",
    ]
    clone_cmd = [
        "-f", "setup",
        f"--runid={runid}",
        f"--repo={target_repo}",
        "--fetch_method=clone",
        f"--model={target_model}",
        f"--ver={target_branch}",
        f"--exp={target_experiment}",
        f"--machine={target_machine}",
        f"--seq={target_sequencer}",
    ]

    # 👇 manually change into tmp_dir
    cwd_before = os.getcwd()
    os.chdir(tmp_dir)
    try:
        result = runner.invoke(
            cli,
            copy_link_cmd if fetch_method in ["copy", "link"] else clone_cmd,
            catch_exceptions=False,
        )
    finally:
        os.chdir(cwd_before)

    try:
        test_run_dir = Path(tmp_dir) / runid
        assert result.exit_code == 0, result.output
        assert test_run_dir.exists(), f"Run directory not found: {test_run_dir}"
        assert (test_run_dir / ".imsi-setup.log").exists(), "Log file not found"
        assert (test_run_dir / "src").exists(), "Source code not found"
    except Exception as e:
        print(f"Error occurred: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)

def test_setup_tree_clone(config_params, runner, local_test_dir):
    run_test(
        runner=runner,
        fetch_method="clone",
        tmp_dir=local_test_dir,
        target_repo=config_params["repo"],
        target_model=config_params["model"],
        target_experiment=config_params["experiment"],
        target_machine=config_params["machine"],
        target_sequencer=config_params["seq"],
        target_branch=config_params["branch"],
    )


@pytest.mark.parametrize("fetch_method", ["copy", "link"])
def test_setup_tree_copy_link(config_params, runner, local_test_dir, fetch_method):
    local_repo_name = "local_repo"
    repo_path = local_test_dir / local_repo_name

    clone_repo(
        target_repo=config_params["repo"],
        target_branch=config_params["branch"],
        tmp_dir=local_test_dir,
        local_repo=local_repo_name,
    )

    run_test(
        runner=runner,
        fetch_method=fetch_method,
        tmp_dir=local_test_dir,
        target_repo=repo_path.resolve(),
        target_model=config_params["model"],
        target_experiment=config_params["experiment"],
        target_machine=config_params["machine"],
        target_sequencer=config_params["seq"],
    )


def test_setup_invalid_arguments(config_params, runner, local_test_dir):
    cwd_before = os.getcwd()
    os.chdir(local_test_dir)
    try:
        result = runner.invoke(cli, ["-f", "setup", "--runid=test_run"])
    finally:
        os.chdir(cwd_before)
    assert "Your runid" in result.output, "Configuration error not correctly being raised"
