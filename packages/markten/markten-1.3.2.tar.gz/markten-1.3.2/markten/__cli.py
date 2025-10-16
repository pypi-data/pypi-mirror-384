"""
# Markten / Spinner

Class for displaying multiple parallel spinners.

This is used to report the progress of tasks that run simultaneously.
"""

from collections.abc import Callable

from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.live import Live
from rich.padding import Padding
from rich.spinner import Spinner
from rich.text import Text

from markten.__action_session import ActionInfo, ActionSession, ActionStatus
from markten.__consts import TIME_PER_CLI_FRAME
from markten.more_itertools import hourglass

INDENT_MULTIPLIER = 2

PARTIAL_OUTPUT_LINES = 10


def action_status(action: ActionInfo, title: Text) -> RenderableType:
    # Need weird spacing to make things line up due to emoji annoyance
    if action.status == ActionStatus.Running:
        return Columns([Spinner("dots"), title])
    elif action.status == ActionStatus.Failure:
        return Text.assemble("❌ ", title, overflow="ellipsis", no_wrap=True)
    else:  # ActionStatus.Success
        return Text.assemble("✅ ", title, overflow="ellipsis", no_wrap=True)


def action_title(action: ActionInfo) -> Text:
    if action.status == ActionStatus.Running:
        return Text(action.name, style="cyan")
    elif action.status == ActionStatus.Failure:
        return Text(action.name, style="red")
    else:  # ActionStatus.Success
        return Text(action.name, style="green")


def draw_action_brief(action: ActionInfo) -> RenderableType:
    rest = Text.assemble(
        " - ",
        action_title(action),
        *((" - ", action.message) if action.message else ()),
        # For some reason, despite these preferences, Rich really wants to wrap
        # this across multiple lines. It used to be worse, but with much
        # experimentation this is about as good as I've managed to make it.
        # https://github.com/Textualize/rich/discussions/3801
        overflow="ellipsis",
        no_wrap=True,
    )
    return action_status(action, rest)


def draw_action_partial(action: ActionInfo) -> RenderableType:
    header = draw_action_brief(action)
    latest_logs = "\n".join(action.output[-PARTIAL_OUTPUT_LINES:])

    # Brief overview of child actions
    children = [
        Padding.indent(
            draw_action(child, draw_action_brief), INDENT_MULTIPLIER
        )
        for child in action.children
    ]

    return Group(
        header,
        *children,
        Padding.indent(latest_logs, INDENT_MULTIPLIER),
    )


def draw_action_full(action: ActionInfo) -> RenderableType:
    header = draw_action_brief(action)
    latest_logs = "\n".join(action.output)

    # Brief overview of child actions
    children = [
        Padding.indent(draw_action_full(child), INDENT_MULTIPLIER)
        for child in action.children
    ]

    return Group(
        header,
        *children,
        Padding.indent(latest_logs, INDENT_MULTIPLIER),
    )


def draw_action(
    action: ActionInfo,
    drawer: Callable[[ActionInfo], RenderableType] = draw_action_partial,
) -> RenderableType:
    """
    Draw action output, choosing output verbosity based on status
    """
    if action.verbose or action.status == ActionStatus.Failure:
        return draw_action_full(action)
    else:
        return drawer(action)


class CliManager:
    """Manager for the CLI.

    Responsible for displaying output during the execution of a recipe step.
    """

    def __init__(self, live: Live) -> None:
        self.__live = live
        self.__should_stop = False

    def stop(self) -> None:
        self.__should_stop = True

    async def run(self, action: ActionSession) -> None:
        """Run the CLI output.

        This runs infinitely, redrawing the output every frame, until it is
        manually cancelled.
        """
        async for _ in hourglass(TIME_PER_CLI_FRAME):
            self.__live.update(draw_action(action.display()))
            if self.__should_stop:
                return
