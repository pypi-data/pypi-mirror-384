"""
# Markten / Actions / __editor

Actions associated with text editors
"""

from pathlib import Path

from markten.__action_session import ActionSession
from markten.actions import process
from markten.actions.__action import markten_action


@markten_action
async def zed(
    action: ActionSession,
    *paths: Path,
):
    """
    Launch a new Zed window with the given Paths.
    """
    # -n = new window
    # -w = CLI waits for window exit
    _ = await process.run(
        action.make_child(process.run),
        "zed",
        "-nw",
        *[str(p) for p in paths],
    )
