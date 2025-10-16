"""
# Markten / Actions / git.py

Actions associated with `git` and Git repos.
"""

import re
from logging import Logger
from pathlib import Path

from markten import ActionSession
from markten.actions import fs, process
from markten.actions.__action import markten_action
from markten.actions.__process import stdout_of

log = Logger(__name__)

DEFAULT_REMOTE = "origin"


async def branch_exists_on_remote(
    action: ActionSession,
    dir: Path,
    branch: str,
    remote: str = DEFAULT_REMOTE,
) -> bool:
    """
    Return whether the given branch exists on the remote

    Requires `git fetch` to have been run beforehand
    """
    remote_branches = await process.stdout_of(
        action, "git", "-C", str(dir), "branch", "--remote"
    )
    regex = re.compile(rf"^\s*{remote}/{branch}$")

    for remote_branch in remote_branches.splitlines():
        if regex.search(remote_branch.strip()) is not None:
            return True

    return False


@markten_action
async def clone(
    action: ActionSession,
    repo_url: str,
    /,
    branch: str | None = None,
    fallback_to_main: bool = False,
    dir: Path | None = None,
) -> Path:
    """Perform a `git clone` operation.

    By default, this clones the project to a temporary directory.

    Parameters
    ----------
    action : ActionSession
        Markten action
    repo_url : str
        URL to clone
    branch : str | None, optional
        Branch to checkout after cloning is complete, by default None
    fallback_to_main : bool, optional
        Whether to fall back to the main branch if the given `branch` does
        not exist, by default False, meaning that the action will fail if the 
        branch does not given.
    dir : Path | None, optional
        Directory to clone to, by default None for a temporary directory
    """
    repo_url = repo_url.strip()
    branch = branch.strip() if branch else None

    if dir:
        clone_path = dir
    else:
        clone_path = await fs.temp_dir(action.make_child(fs.temp_dir))

    program: tuple[str, ...] = ("git", "clone", repo_url, str(clone_path))

    _ = await process.run(action, *program)

    if branch:
        if await action.child(branch_exists_on_remote, clone_path, branch):
            checkout_action = action.make_child(checkout)
            try:
                await checkout(
                    checkout_action,
                    clone_path,
                    branch,
                )
            except Exception as e:
                checkout_action.fail(str(e))
                if fallback_to_main:
                    action.log("Note: remaining on main branch")
                else:
                    raise
        elif fallback_to_main:
            action.log(
                f"Branch {branch} does not exist. Remaining on main branch"
            )
        else:
            action.fail(f"Branch {branch} does not exist.")
            raise RuntimeError("Checkout failed")

    return clone_path


@markten_action
async def push(
    action: ActionSession,
    dir: Path,
    /,
    set_upstream: bool | str | tuple[str, str] = False,
    push_options: list[str] | None = None,
):
    """Perform a `git push` operation.

    By default, this pushes the current branch to its corresponding upstream
    branch on the remote.

    Parameters
    ----------
    action : ActionSession
        Markten action
    dir : Path
        Path to git repository
    set_upstream : bool | str | tuple[str, str], optional
        Whether to create an upstream branch on the remote, by default False.
        If this is `True`, the same branch name will be used on `origin`.
        If this is a `str`, its value will be used as the upstream branch name
        on the remote `origin`.
        If this is a `tuple[str, str]`, it will be treated as
        `(remote, branch)`.
    push_options : list[str], optional
        Push options. These can be used to perform actions on some remotes,
        such as creating a merge request or skipping continuous integration
        checks. Each option should be a string. The `-o` flag will be added
        automatically.
    """
    additional_flags: list[str] = []
    if push_options is not None:
        additional_flags = [
            # Flattened list of `-o option1 -o option2
            # Really not a fan of this syntax
            # https://stackoverflow.com/a/952952/6335363
            x
            for opt in push_options
            for x in ["-o", opt]
        ]

    if set_upstream is not False:
        if set_upstream is True:
            remote = DEFAULT_REMOTE
            branch = await current_branch(
                action.make_child(current_branch), dir
            )
        elif isinstance(set_upstream, str):
            remote = DEFAULT_REMOTE
            branch = set_upstream
        else:
            remote, branch = set_upstream

        additional_flags.extend(["--set-upstream", remote, branch])

    program = (
        "git",
        "-C",
        str(dir),
        "push",
        *additional_flags,
    )

    _ = await process.run(action, *program)


@markten_action
async def pull(action: ActionSession, dir: Path) -> None:
    """Perform a `git pull` operation."""
    program = ("git", "-C", str(dir), "pull")
    _ = await process.run(action, *program)


@markten_action
async def checkout(
    action: ActionSession,
    dir: Path,
    branch_name: str,
    /,
    create: bool = False,
    link_upstream: str | bool = False,
) -> None:
    """Perform a `git checkout` operation.

    This changes the active branch for the given git repository.

    Parameters
    ----------
    dir : Path
        Path to git repository
    branch_name : str
        Branch to checkout
    create : bool, optional
        Whether to pass a `-b` flag to the `git checkout` operation,
        signaling that `git` should create a new branch.
    link_upstream : str | bool, optional
        Whether to also link this branch to the given upstream remote. This
        requires the `create` flag to also be `True`. If `True` is given,
        this will set the upstream branch on the `origin` remote. If a `str` is
        given, the upstream branch will set to that origin. If the branch
        already exists on the remote, `git pull` will be run automatically.
    """

    if link_upstream and not create:
        raise ValueError(
            "Markten.actions.git.checkout: Cannot specify "
            + "`push_to_remote` if `create is False`"
        )
    program: tuple[str, ...] = (
        "git",
        "-C",
        str(dir),
        "checkout",
        *(("-b",) if create else ()),
        branch_name,
    )
    _ = await process.run(action, *program)

    if link_upstream is not False:
        remote = DEFAULT_REMOTE if link_upstream is True else link_upstream
        already_exists = await action.child(
            branch_exists_on_remote,
            dir,
            branch_name,
            remote,
        )
        if already_exists:
            _ = await action.child(
                process.run,
                "git",
                "-C",
                str(dir),
                "branch",
                f"--set-upstream-to={remote}/{branch_name}",
                branch_name,
            )
            await action.child(pull, dir)
        else:
            _ = await action.child(push, dir, set_upstream=True)
            

    action.succeed(
        f"Switched to{' new' if create else ''} "
        + f"branch {branch_name}"
        + " and set upstream"
        if link_upstream
        else ""
    )


@markten_action
async def add(
    action: ActionSession,
    dir: Path,
    files: list[Path] | None = None,
    /,
    all: bool = False,
) -> None:
    """Perform a `git add` operation

    This stages the given list of changes, making them ready to commit.

    If the `files` list is empty and `all` is not specified, this will have
    no effect.

    Parameters
    ----------
    dir : Path
        Path to git repository.
    files : list[Path] | None, optional
        List of files to add, by default None, indicating that no files
        should be added.
    all : bool, optional
        whether to add all modified files, including untracked files, by
        default False.

    Raises
    ------
    ValueError
        Files were specified when `all` is `True`
    """
    if files is None:
        files = []

    if all and len(files):
        raise ValueError(
            "Should not specify files to commit when using the `all=True` "
            + "flag."
        )

    program: tuple[str, ...] = (
        "git",
        "-C",
        str(dir),
        "add",
        *(["--all"] if all else map(str, files)),
    )

    _ = await process.run(action, *program)

    if all:
        action.succeed("Git: staged all files")
    else:
        action.succeed(f"Git: staged files {files}")


@markten_action
async def commit(
    action: ActionSession,
    dir: Path,
    message: str,
    /,
    files: list[Path] | None = None,
    all: bool = False,
    untracked: bool = False,
    push_after: bool = False,
    push_upstream: bool | str | tuple[str, str] = False,
    push_options: list[str] | None = None,
) -> None:
    """Perform a `git commit` operation.

    Parameters
    ----------
    action : ActionSession
        Action session
    dir : Path
        Path to git repository
    message : str
        Commit message
    all : bool, optional
        Whether to commit all changes. This will not commit untracked files.
        Defaults to `False.
    untracked : bool, optional
        Whether to also commit untracked files. Implies `all=True`. Defaults to
        False.
    push_after : bool, optional
        Whether to perform a `git push` operation after. Defaults to False.
    push_upstream : bool | str | tuple[str, str], optional
        Whether to push the commit to the remote, even if the branch doesn't
        already exist on the remote. Requires `push_after` to be `True`.
        Defaults to False.
    push_options : dict[str, str | True], optional
        Push options. Requires `push_after=True`. Defaults to `None`.
    """
    additional_flags: list[str] = []
    if all:
        additional_flags.append("-a")

    if files is not None or untracked:
        await add(action.make_child(add), dir, files, all=untracked)

    _ = await process.run(
        action,
        "git",
        "-C",
        str(dir),
        "commit",
        *additional_flags,
        "-m",
        message,
    )

    if push_after:
        await push(
            action.make_child(push),
            dir,
            set_upstream=push_upstream,
            push_options=push_options,
        )


@markten_action
async def current_branch(action: ActionSession, dir: Path) -> str:
    """Determine the current branch, returning it as the output of the action.

    Parameters
    ----------
    action : ActionSession
        Action session
    dir : Path
        Path to git repository
    """
    program = ("git", "-C", str(dir), "rev-parse", "--abbrev-ref", "HEAD")
    return await stdout_of(action, *program)
