"""
# Markten / Utils

Utility functions.
"""

import asyncio
import os
import shutil
from pathlib import Path
from types import FunctionType

from rich.console import Console
from rich.panel import Panel
from typing_extensions import override

from . import __consts as consts


def relativize_file(file: Path, to: Path | None = None) -> Path:
    """
    Return file path relative to given dir, or cwd
    """
    if to is None:
        to = Path(os.getcwd())

    if file.is_relative_to(to):
        return file.relative_to(to)
    else:
        return file


async def copy_file(src: Path, dest: Path, *, preserve_metadata: bool = False):
    """Copy file from src to dest in an asyncio thread"""
    fn = shutil.copy2 if preserve_metadata else shutil.copyfile
    _ = await asyncio.to_thread(fn, src, dest)


async def unlink_file(f: Path) -> None:
    """Unlink the file at the given path in an asyncio thread"""
    _ = await asyncio.to_thread(lambda: f.unlink())


def recipe_banner(
    recipe_name: str | None,
    recipe_file: str | None,
) -> None:
    """Display a banner to the console for the given recipe

    Parameters
    ----------
    recipe_name : str | None
        Name of recipe
    recipe_file : str | None
        File of recipe
    """
    console = Console()

    text: list[str] = []
    if recipe_name:
        text.append(f"Recipe: [cyan]{recipe_name}[/]")
    if recipe_file:
        text.append(f"File: [cyan]{relativize_file(Path(recipe_file))}[/]")

    panel = Panel("\n".join(text), title=f"Markten v{consts.VERSION}")
    console.print(panel)


class TextCollector:
    """
    Collects text when called. When stringified, it produces the output, joined
    by newlines. With leading and trailing whitespace stripped.
    """

    def __init__(self) -> None:
        self.__output: list[str] = []

    def __call__(self, line: str) -> None:
        self.__output.append(line)

    @override
    def __str__(self) -> str:
        return "\n".join(self.__output).strip()


def friendly_name(obj: object) -> str:
    """Returns a "human-friendly" name for an object

    * For a function or class, this is the qualified name
    * For anything else, it's the regular string

    Parameters
    ----------
    obj : object
        object to get name of

    Returns
    -------
    str
        Human-friendly name
    """
    if isinstance(obj, FunctionType | type):
        mod = obj.__module__
        name = obj.__qualname__
        if mod in ["builtins", "__main__"]:
            return name
        else:
            return f"{mod}.{name}"
    else:
        return str(obj)
