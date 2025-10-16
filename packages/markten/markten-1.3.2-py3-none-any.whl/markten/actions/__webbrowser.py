"""
# Markten / Actions / web browser

Actions associated with web browsers
"""

import sys

from markten.__action_session import ActionSession
from markten.actions import process
from markten.actions.__action import markten_action

__all__ = [
    "open",
]


@markten_action
async def open(
    action: ActionSession,
    url: str,
    /,
    new_tab: bool = False,
    new_window: bool = False,
) -> None:
    """Open the given URL in the user's default web browser.

    Parameters
    ----------
    url : str
        URL to open
    new_tab : bool
        Open a new tab
    new_window : bool
        Open in a new window
    """
    if new_tab and new_window:
        raise ValueError(
            "`new_tab` and `new_window` options are mutually exclusive"
        )

    options = []
    if new_tab:
        options.append("-t")
    if new_window:
        options.append("-n")
    action.running("Launching browser")
    # Run `python -m webbrowser` in a subprocess so we can hide the stdout
    # and stderr
    await process.run_detached(
        action,
        sys.executable,
        "-m",
        "webbrowser",
        *options,
        url,
    )
    action.succeed()
