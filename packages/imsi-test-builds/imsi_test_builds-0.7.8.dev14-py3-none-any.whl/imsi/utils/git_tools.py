"""
git_tools
=========

This is a module to collect common version control operations.

It might be worth checking out e.g. https://gitpython.readthedocs.io/en/stable/

However, for now to reduce dependencies, and given the basic operations needed,
I'm just implementing a few functions here.

NCS, 10/2021
"""
from getpass import getuser
import os
from re import fullmatch
import shlex
import subprocess
from collections import OrderedDict
from typing import Optional

# NOTE: many git commands issued via subprocess are kept as full strings
# so that they are more easily searchable, but then split using shlex so
# that we don't have to use shell=True.

class GitException(Exception):
    """Exceptions from running git commands"""
    # generic
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message
    def __str__(self):
        return str(self.message)

def is_git_repo(path):
    # simple check -- no subprocess  TODO replace
    if path is None:
        path = os.path.getcwd()
    git_dir = os.path.join(path, '.git')
    if os.path.exists(git_dir):
        return True
    else:
        return False


def is_sha1(s):
    """Return True if string is like SHA-1 (7 to 40 hex characters)"""
    return True if fullmatch(r"[0-9a-fA-F]{7,40}", s) else False


def ensure_git_config(id_as_fallback=True):
    """ensures that git config for local repo is set if there isn't a global one.
    (necessary for a commit).
    """
    USER_FALLBACK = "IMSI USER"
    CONTACT_EMAIL_FALLBACK = '<>'   # TODO not great, better idea?
    git_user = subprocess.run(shlex.split('git config user.name'), capture_output=True)
    git_email = subprocess.run(shlex.split('git config user.email'), capture_output=True)

    if not git_user.stdout.decode().strip():
        if id_as_fallback:
            USER = getuser()
            subprocess.run(shlex.split(f'git config user.name {USER}'))
        else:
            subprocess.run(shlex.split(f'git config user.name {USER_FALLBACK}'))
    if not git_email.stdout.decode().strip():
        subprocess.run(shlex.split(f'git config user.email {CONTACT_EMAIL_FALLBACK}'))

def git_add_all(path=None):
    if path is None:
        path = os.getcwd()
    subprocess.run(shlex.split('git add -A'), cwd=path)

def git_add_commit(path=None, msg='commit'):
    if path is None:
        path = os.getcwd()
    ensure_git_config()
    clean, _ = is_repo_clean(path)
    if not clean:
        git_add_all(path=path)
        subprocess.run(shlex.split(f'git commit -q -m "{msg}"'), cwd=path)

def get_head_hash(path=None):
    if path is None:
        path = os.getcwd()
    proc = subprocess.run(shlex.split('git rev-parse HEAD'), cwd=path, capture_output=True)
    sha = proc.stdout.decode().strip()
    return sha

def init_repo(path=None, branch=None):
    # It is safe to run git init in a repo that is already initialized
    # so there is no check for this
    # see: https://git-scm.com/docs/git-init

    if path is None:
        path = os.getcwd()

    # could make initial branch match runid with
    #     git init -q --initial-branch branch-name
    # if we checked git version (not available in older versions)
    subprocess.run(shlex.split('git init -q'), cwd=path)

    if branch is not None:
        proc_branch = subprocess.run(shlex.split('git rev-parse --abbrev-ref HEAD'), cwd=path, capture_output=True)

        # note: keep on current branch if set, forgo checking returned == branch
        # otherwise:
        if (proc_branch.returncode != 0):
            # error = branch doesn't exist yet
            subprocess.run(shlex.split(f'git checkout -b {branch} -q'), cwd=path)

def clear_repo(path):
    subprocess.run(shlex.split('git rm -rfq .'), cwd=path)
    subprocess.run(shlex.split('git clean -dfxq'), cwd=path)

def clone(repo_address, local_name, ver, path=None, depth: Optional[int] = None):
    """Clone a git repository, for standard repositories or containing submodules.
    If there are submodules, clone the repository recursively, and
    checkout a specified version across all submodules.

    Inputs:
        repo_address : str
            The address to clone from, typically a url.
        local_name : str
            The name to use for the on disk code
        ver : str
            The reference to checkout. Can be a branch name or tag (used
            with the `--branch` arg in git clone). When a SHA-1 is used,
            a full clone of the repo is done and then checked out to the
            SHA-1 (`depth` is ignored).
        path : str, None
            Path of where to clone the repo, path/local_name. If None, cwd used.
        depth : int, None
            Depth to which the repository is cloned, including submodules.
            If None, the full git history is cloned. Can't be used when ver
            is a SHA1
    """
    if path is None:
        path = os.getcwd()
    local_name_path = os.path.join(path, local_name)

    if depth is None or is_sha1(ver):
        # full clone
        clone_args = ["git", "clone", "--recursive", repo_address, local_name]
    elif depth >= 1:
        # shallow clone - only if ver is branch or tag
        clone_args = [
            "git", "clone", "--branch", ver, "--recurse-submodules",
            "--depth", f"{depth}", "--shallow-submodules", repo_address,
            local_name
            ]
    else:
        raise ValueError(f"Can't clone repo with ver '{ver}' and depth '{depth}'")

    # for clone: passing local_name instead of '.' with cwd set,
    # thus local_folder_path is not created in this function
    subprocess.run(clone_args, cwd=path, check=True)
    subprocess.run(["git", "checkout", "--recurse-submodules", ver], cwd=local_name_path)
    subprocess.run(["git", "submodule", "update", "--recursive", "--init", "--checkout"], cwd=local_name_path)

def is_repo_clean(path=None):
    if path is None:
        path = os.getcwd()
    cmd_git_has_changes = "git status --porcelain=v1"           # strict version
    try:
        proc = subprocess.run(shlex.split(cmd_git_has_changes), capture_output=True, cwd=path)
    except subprocess.CalledProcessError as e:
        raise GitException(e.stderr.decode())
    return (False if proc.stdout else True, proc.stdout.decode().strip())


def repo_has_commits(path=None):
    if path is None:
        path = os.getcwd()

    # check if it is a git repo by first running:
    is_repo_clean(path)

    cm = 1
    try:
        proc = subprocess.run(shlex.split('git log'), capture_output=True, cwd=path)
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        # does not have any commits yet
        cm = 0
    return cm


if __name__ == '__main__':
    SystemExit('Version control module not directly callable')