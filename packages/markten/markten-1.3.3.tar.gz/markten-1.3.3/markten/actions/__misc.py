"""
# Markten / Actions / Misc

Miscellaneous actions
"""

import sys
from pathlib import Path

from markten import ActionSession
from markten.actions import process
from markten.actions.__action import markten_action


@markten_action
async def open(action: ActionSession, file_or_url: str | Path) -> None:
    """
    Opens the given file or URL in the user's preferred application for
    handling that file or URL type.

    Under the hood, this executes a system-specific command-line utility:

    ======== =========
    Platform Program
    -------- ---------
    Linux    `xdg-open`
    MacOS    `open`
    Windows  `start`

    Examples
    --------

    ```py
    # Rick-roll the user
    open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    # Compose an email
    open("mailto:someone@example.com")

    # Open an image in their preferred image viewer
    open("/path/to/some/image.jpg")
    ```

    Parameters
    ----------
    file_or_url : str | Path
        File or URL to open.
    """
    match sys.platform:
        case "linux":
            program = "xdg-open"
        case "darwin":  # MacOS
            program = "open"
        case "win32":  # Windows
            program = "start"
        case _:
            raise RuntimeError(
                f"Unable to open file or URL. "
                f"Platform '{sys.platform}' is unsupported"
            )

    await process.run(action, program, str(file_or_url))
