"""
# Markten / Parameters / FS

Gather parameters from the file system.
"""

import stat
import sys
from collections.abc import Callable, Iterable
from os import PathLike
from pathlib import Path

StrPath = str | PathLike[str]


def list_dir(
    path: StrPath,
    *filter_fns: Callable[[Path], bool],
    skip_hidden=True,
    directories=False,
    files=False,
) -> Iterable[Path]:
    """
    Get parameter values as files within a directory.
    """

    def has_hidden_attribute(filepath: Path) -> bool:
        """
        Returns whether a file has a hidden attribute on Windows

        Source: https://stackoverflow.com/a/6365265/6335363
        """
        if sys.platform == "win32":
            return bool(
                filepath.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN
            )
        else:
            return False

    def is_visible(filepath: Path) -> bool:
        """
        Returns whether a file is visible in the user's file system.

        This ignores files beginning with a `.` on all systems (not just
        UNIX-like ones), and also ignores files that have a hidden attribute on
        Windows.
        """
        name = filepath.absolute().name
        return not (name.startswith(".") or has_hidden_attribute(filepath))

    def is_dir(p: Path) -> bool:
        return p.is_dir()

    def is_file(p: Path) -> bool:
        return p.is_file()

    p = Path(path)
    filters = list(filter_fns)
    if directories:
        filters.append(is_dir)
    if files:
        filters.append(is_file)
    if skip_hidden:
        filters.append(is_visible)

    def keep_file(path: Path) -> bool:
        """Return whether to keep a file in the generator"""
        return all(f(path) for f in filters)

    return (f for f in p.iterdir() if keep_file(f))
