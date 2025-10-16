from imsi.utils.general import delete_or_abort, get_active_venv
from imsi.utils import git_tools
from imsi.user_interface.ui_manager import (
    create_imsi_configuration,
    build_run_config_on_disk,
    validate_version_reqs
)

from pydantic import BaseModel, field_validator, Field, model_validator
from typing import Optional, Generator
from pathlib import Path
import shutil
import os
import subprocess
import re
import contextlib
import warnings


@contextlib.contextmanager
def change_dir(path: Path) -> Generator:
    """Temporarily changes the working context to the given path."""
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)

# Matches valid Git repository URLs in SSH or HTTPS format:
# - Starts with either 'https://' or 'git@'.
# - Followed by one or more word characters, dots, or hyphens (domain or hostname).
# - Contains either a ':' or '/' (separator for host and repository path).
# - Followed by one or more word characters, slashes, or hyphens (repository path).
# - Optionally ends with '.git'.
GIT_URL_PATTERN = re.compile(
    r"^(https:\/\/(?:[^@\/]+@)?|git@)[\w\.-]+(:|\/)[\w\/-]+(\.git)?$"
)

# runid can contain one or more of the following characters:
#   - Lowercase letters (`a-z`).
#   - Digits (`0-9`).
#   - Hyphens (`-`).
RUNID_PATTERN = re.compile(r"^[a-z0-9-]+$")


class InvalidSetupConfig(Exception):
    """Used to catch invalid setup configurations and provide
    useful feedback to user"""

    pass


class SetupConfigWarning(UserWarning):
    pass


class GitRepositoryValidator(BaseModel):
    repo_url: str
    remote_branch: Optional[str] = None

    @field_validator("repo_url", mode="after")
    def is_valid_repo_url(url: str) -> bool:
        """Check if a given URL is a valid Git repository."""
        result = subprocess.run([
                    "git", "ls-remote", "--heads", url
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise InvalidSetupConfig(f"Invalid Git repository URL: '{url}'.")
        return url

    @model_validator(mode="after")
    def is_valid_remote_ref(self):
        """Validate that self.remote_branch is a valid branch or tag in the remote repo.
        Skip validation if it looks like a SHA-1 hash."""

        # Skip validation for anything that looks like a SHA-1 (7 to 40 hex characters)
        if git_tools.is_sha1(self.remote_branch):
            return self

        # Get all refs from remote (branches, tags, etc.)
        result = subprocess.run(
            ["git", "ls-remote", self.repo_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        lines = result.stdout.strip().splitlines()
        refs = {
            ref.split()[1]: ref.split()[0]
            for ref in lines if len(ref.split()) == 2
        }

        # Build sets of remote branch/tag names
        remote_branches = {
            ref.replace("refs/heads/", "") for ref in refs if ref.startswith("refs/heads/")
        }
        remote_tags = {
            ref.replace("refs/tags/", "") for ref in refs if ref.startswith("refs/tags/")
        }

        target = self.remote_branch

        if target not in remote_branches and target not in remote_tags:
            raise InvalidSetupConfig(
                f"'{target}' is not a valid remote branch or tag in {self.repo_url}."
            )

        return self


class ValidatedSetupOptions(BaseModel):
    """Validate setup inputs early in single location."""

    runid: str = Field(..., max_length=21)
    repo: str
    ver: Optional[str] = None
    exp: str | None
    model: Optional[str]
    fetch_method: str
    seq: Optional[str] = None
    machine: Optional[str] = None
    flow: Optional[str] = None
    compiler: Optional[str] = None
    postproc: Optional[str] = None

    @field_validator("runid")
    def validate_runid(cls, value):
        if RUNID_PATTERN.match(value) and len(value) < 20:
            return value
        elif len(value) >= 20:
            raise InvalidSetupConfig(
                f"Your runid ---> {value} <--- is too long at {len(value)} chars! It must be less than 20 characters."
            )

        raise InvalidSetupConfig(
            f"Your runid ---> {value} <--- contains unsupported characters! "
            "You must use a runid containing only lowercase alphanumeric characters 'a-z0-9', or hyphens '-'"
            "Also, remember to make it short (<20chars) and unique to you"
            "Examples: runid=ncs-tst-ctrl-01"
        )

    @field_validator("fetch_method")
    def validate_fetch_method(cls, value):
        valid_fetch = ["clone", "clone-full", "link", "copy"]
        if value not in valid_fetch:
            raise InvalidSetupConfig(
                f"'{value}' is not a valid fetch method. Must in {valid_fetch}."
            )
        return value

    @model_validator(mode="after")
    def error_if_version_unused(self):
        if self.fetch_method in ["clone", "clone-full"] and self.ver is None:
            raise InvalidSetupConfig(
                "\n\n**ERROR**: When --fetch_method is clone, --ver must be specified."
            )
        return self

    @model_validator(mode="after")
    def error_if_version_used(self):
        if self.fetch_method in ["copy", "link"] and self.ver is not None:
            raise InvalidSetupConfig(
                "\n\n**ERROR**: When --fetch_method is copy or link, --ver cannot be specified."
            )
        return self

    @field_validator("repo")
    def validate_git_or_path(cls, value):
        if not Path(value).exists() and not GIT_URL_PATTERN.match(value):
            raise InvalidSetupConfig(
                f"Check that the repository or path exists: {value}. Ensure remote patterns match: git@<remote>:<project>/<repo> or is a valid URL if using https."
            )
        else:
            return value

    @model_validator(mode="after")
    def error_if_bad_git(self):
        if self.fetch_method in ["clone", "clone-full"]:
            GitRepositoryValidator(repo_url=self.repo, remote_branch=self.ver)
        if (self.fetch_method == "clone") and git_tools.is_sha1(self.ver):
            # using a hash for setting up a repo as a shall clone (fetch_method=clone)
            # is problematic for repos with submodules; use the full depth clone
            # instead
            warnings.warn(
                "Can't use --fetch_method=clone and --ver=sha1; continuing with --fetch_method=clone-full",
                SetupConfigWarning
                )
            self.fetch_method = 'clone-full'
        return self


def overwrite_or_abort(runid: str, force: bool):
    """Overwrite path if exists or abort"""
    if Path(runid).exists():
        if force:
            shutil.rmtree(runid)
        else:
            print(f"\n\n**WARNING**: The directory {runid} already exists.")
            delete_or_abort(runid)


def setup_run(setup_args: ValidatedSetupOptions, force: bool = False):
    """
    Create a run directory, clone in the source code, and checkout version ver

    Inputs:
    -------
    runid : ValidatedSetupOptions
        A validated set of setup options for the run
    Outputs:
    --------
    Returns nothing, but creates the directory named for runid and recursively
    clones the code from repo and afterwards checks out ver.
    """

    overwrite_or_abort(setup_args.runid, force)

    work_dir = Path(setup_args.runid).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    # Clone, soft link or copy the source code
    super_repo_source = "src"
    src_dir = work_dir / super_repo_source

    if setup_args.fetch_method == "clone":
        print(f"Cloning (shallow) {setup_args.ver} from {setup_args.repo} for {setup_args.runid}")
        git_tools.clone(setup_args.repo, super_repo_source, setup_args.ver, path=work_dir, depth=1)
    elif setup_args.fetch_method == 'clone-full':
        print(f"Cloning {setup_args.ver} from {setup_args.repo} for {setup_args.runid}")
        git_tools.clone(setup_args.repo, super_repo_source, setup_args.ver, path=work_dir, depth=None)
    elif setup_args.fetch_method == "link":
        print(f"Soft linking source from {setup_args.repo} for {setup_args.runid}")
        os.symlink(setup_args.repo, src_dir)
    elif setup_args.fetch_method == "copy":
        print(f"Copying source from {setup_args.repo} for {setup_args.runid}")
        shutil.copytree(
            setup_args.repo,  # src
            src_dir,          # dst
            symlinks=True,
            ignore_dangling_symlinks=True,
        )

    imsi_config_path = (
        src_dir / "imsi-config"
    )  # Requirement that imsi-config appears at the highest setup_args.repo level of a supported setup_args.model setup_args.repo.
    if not imsi_config_path.exists():
        raise ValueError(
            "\n\n **ERROR**: setup_args.'imsi-config' directory not found at the top setup_args.repo level, but is required. Is this a valid imsi configured setup_args.code base?"
        )
    validate_version_reqs(imsi_config_path)

    imsi_venv = get_active_venv()

    setup_params = {
        "model_name": setup_args.model,  # user input
        "experiment_name": setup_args.exp,  # user input
        "machine_name": setup_args.machine,  # user input - optional
        "compiler_name": setup_args.compiler,  # user input - optional
        "runid": setup_args.runid,
        "work_dir": str(work_dir),  # implicitly set by user
        "source_path": str(
            src_dir
        ),  # Make settable in upstream imsi (machine) config? and/or at cmd line?
        "source_repo": setup_args.repo,  # about tracking, but not so used
        "source_version": setup_args.ver,  # "
        "run_config_path": str(work_dir / "config"),  # convention. Make settable?
        "imsi_config_path": str(imsi_config_path),  # convention. Make settable?
        "fetch_method": setup_args.fetch_method,
        "sequencer_name": setup_args.seq,
        "flow_name": setup_args.flow,
        "imsi_venv": imsi_venv,
        "postproc_profile": setup_args.postproc
    }

    # Everything above this could be extracted to an "external" setup command, while everything else
    # could in theory come from within the repo, ala current setup/adv-setup. Not sure how to manage
    # that in the context of python packaging though!
    with change_dir(work_dir):
        configuration, db = create_imsi_configuration(imsi_config_path, setup_params)
        build_run_config_on_disk(configuration, db)
        print(
            f"\nIMSI setup complete. You can now: \n\n\t\t cd {setup_args.runid} \n"
            f"to continue with configuration/compilation/submission, see:\n\t\t imsi -h"
        )
