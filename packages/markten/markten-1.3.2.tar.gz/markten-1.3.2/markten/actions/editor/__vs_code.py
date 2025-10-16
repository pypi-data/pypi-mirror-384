"""
# Markten / Actions / editor / vs_code

Code for managing the VS Code text editor.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import NotRequired, TypedDict

import aiosqlite
import platformdirs

from markten.__action_session import ActionSession
from markten.__utils import copy_file, unlink_file
from markten.actions import process
from markten.actions.__action import markten_action

log = logging.getLogger(__name__)


@markten_action
async def vs_code(
    action: ActionSession,
    *paths: Path,
    remove_history: bool = False,
    snippets: Path | None = None,
):
    """
    Launch a new VS Code window with the given paths.

    Parameters
    ----------
    action : ActionSession
        Action session
    path : Path
        Paths to open in VS Code.
    remove_history : bool
        Whether to remove this entry from VS Code's history after it quits.
        Defaults to `False`.
    snippets : Path
        Paths to a VS Code snippets file. It will be copied to the project
        directory while VS Code is open, and deleted once it exits. The
        snippets file must be a global snippet file such that it can be
        configured to not conflict with existing snippet files.
        https://code.visualstudio.com/docs/editing/userdefinedsnippets#_project-snippet-scope
    """
    # If there is a snippet file, copy it to the given path
    snippet_targets: list[Path] = []
    if snippets:
        for p in paths:
            snippet_dir = p / ".vscode"
            snippet_file = "markten.code-snippets"
            n = 0
            while (snippet_dir / snippet_file).exists():
                n += 1
                snippet_file = f"markten-{n}.code-snippets"

            target = snippet_dir / snippet_file
            snippet_targets.append(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            await copy_file(snippets, target, preserve_metadata=True)

    # -n = new window
    # -w = CLI waits for window exit
    _ = await process.run(
        action.make_child(process.run),
        "code",
        "-nw",
        *[str(p) for p in paths],
    )

    # After VS Code exits, we may need to remove the snippet
    # This is not a teardown step, since we don't want to accidentally commit
    # it
    async with asyncio.TaskGroup() as tg:
        for snip in snippet_targets:
            _ = tg.create_task(unlink_file(snip))

    # Add a hook to remove the temporary directory from VS Code's history
    if remove_history and len(paths):
        action.add_teardown_hook(lambda: cleanup_vscode_history(paths))
    return action


class VsCodeHistoryEntry(TypedDict):
    folderUri: NotRequired[str]
    """
    Path to folder, in the form `file://{path}`
    """
    fileUri: NotRequired[str]
    """Path to file, in the form `file://{path}`"""
    label: NotRequired[str]
    remoteAuthority: NotRequired[str]


async def cleanup_vscode_history(paths: tuple[Path, ...]):
    """
    Access VS Code's state database, in order to remove recent items from
    the data.

    Adapted from https://stackoverflow.com/a/74933036/6335363, but made
    async to avoid blocking other tasks.

    Note that annoyingly, the history won't be applied unless VS Code is
    entirely closed during this step.
    """
    log.info("Begin VS Code history cleanup")

    # Kinda painful that it's a database, not just a JSON file tbh
    state_path = (
        platformdirs.user_config_path() / "Code/User/globalStorage/state.vscdb"
    )
    log.info(f"VS Code state file should exist at {state_path}")

    # Create a backup copy
    state_backup = state_path.with_name("state-markten-backup.vscdb")
    await copy_file(state_path, state_backup, preserve_metadata=True)
    log.info(f"Created backup of VS Code state at {state_backup}")

    try:
        async with aiosqlite.connect(state_path) as db:
            cursor = await db.execute(
                "SELECT [value] FROM ItemTable WHERE  [key] = "
                + "'history.recentlyOpenedPathsList'"
            )
            history_raw = await cursor.fetchone()
            assert history_raw
            history: list[VsCodeHistoryEntry] = json.loads(history_raw[0])[
                "entries"
            ]

            def should_keep_entry(e: VsCodeHistoryEntry) -> bool:
                uri = e.get("folderUri", e.get("fileUri"))
                if uri is None:
                    return True
                else:
                    uri = uri.removeprefix("file://")
                    keep = True
                    for p in paths:
                        if Path(uri) == p.absolute():
                            keep = False
                    if not keep:
                        log.info(f"Remove history entry '{uri}'")
                    return keep

            # Remove this path from history
            new_history = [item for item in history if should_keep_entry(item)]

            # Then save it back out to VS Code
            new_history_str = json.dumps({"entries": new_history})
            _ = await db.execute(
                "UPDATE ItemTable SET [value] = ? WHERE key = "
                + "'history.recentlyOpenedPathsList'",
                (new_history_str,),
            )
            await db.commit()
            log.info("VS Code history removal success")
    except BaseException:
        log.exception(
            "Error while updating VS Code state, reverting to back-up"
        )
        await copy_file(state_backup, state_path, preserve_metadata=True)
        # Continue error propagation
        raise
