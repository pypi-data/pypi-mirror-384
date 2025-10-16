"""
# Markten / Actions / fs.py

Actions associated with the file system.
"""

import asyncio
import shutil
from pathlib import Path
from tempfile import mkdtemp

import aiofiles
import aiofiles.ospath

from markten import ActionSession
from markten.actions.__action import markten_action


@markten_action
async def temp_dir(action: ActionSession, remove: bool = False) -> Path:
    """Create a temporary directory, and return its path.

    Parameters
    ----------
    action : ActionSession
        Action session
    remove : bool, optional
        Whether to remove the temporary directory during teardown, by default
        False

    Returns
    -------
    Path
        Path to temporary directory.
    """
    action.message("Creating temporary directory")

    # Need to manually run mkdtemp in executor, as a version that is not
    # removed is not provided by `aiofiles.tempfile`
    loop = asyncio.get_event_loop()
    file_path = await loop.run_in_executor(
        None, lambda: mkdtemp(prefix="markten-")
    )

    async def teardown():
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: shutil.rmtree(file_path))

    if remove:
        action.add_teardown_hook(teardown)

    action.succeed(file_path)
    return Path(file_path)


@markten_action
async def write_file(
    action: ActionSession,
    file: Path,
    text: str,
    /,
    overwrite: bool = False,
) -> None:
    """Write the given text into the given file.

    Unlike standard file management functions, this raises an exception if the
    file already exists, unless the `overwrite` option is given.

    Parameters
    ----------
    action : ActionSession
        Action session
    file : Path
        File to write into
    text : str
        Text to write
    overwrite : bool, optional
        Whether to overwrite the file if it already exists, by default False

    Raises
    ------
    FileExistsError
        File already exists.
    """
    if await aiofiles.ospath.exists(file) and not overwrite:
        raise FileExistsError(
            f"Cannot write into '{file}' as it already exists"
        )
    action.message(f"Writing {file}")
    async with aiofiles.open(file, "w") as f:
        await f.write(text)


@markten_action
async def read_file(action: ActionSession, file: Path) -> str:
    """Read text from the given file.

    Returns the text as a `str`.

    Parameters
    ----------
    action : ActionSession
        Action session
    file : Path
        File to read from.

    Returns
    -------
    str
        File contents.
    """
    action.message(f"Read {file}")
    async with aiofiles.open(file) as f:
        return await f.read()
