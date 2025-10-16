"""
# Markten / Action Session

The context for an action, allowing it to update its state, log progress, and
create child actions.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Concatenate, ParamSpec, TypeVar

from markten.__utils import friendly_name

TeardownHook = Callable[[], Awaitable[None] | None]
"""Callback function for cleaning up after an action has completed."""


P = ParamSpec('P')
T = TypeVar('T')


class ActionStatus(Enum):
    """Status of an action"""

    Running = 1
    """Action is running"""
    Success = 2
    """Action resolved successfully"""
    Failure = 3
    """Action resolved, but failed"""


@dataclass
class ActionInfo:
    name: str
    status: ActionStatus
    message: str | None
    progress: float | None
    children: list['ActionInfo']
    output: list[str]
    verbose: bool


class ActionSession:

    def __init__(self, name: str | object) -> None:
        """Create an ActionSession object.

        You shouldn't call this directly unless you intend to display the data
        yourself. Instead, you should create a child of an existing action
        using `action.make_child` so that that action's output is drawn nicely.

        Parameters
        ----------
        name : str | object
            Name of this action. If an object is given, its name will be used
            (if it is a function or class).
        """
        self.__name = name if isinstance(name, str) else friendly_name(name)
        # TODO: Get pretty name of object

        self.__status = ActionStatus.Running
        """Status as enum"""
        self.__message: str | None = None
        """Status message"""
        self.__output: list[str] = []
        """Overall logs"""
        self.__progress: float | None = None
        """Progress percentage (float from 0 to 1)"""

        self.__children: list[ActionSession] = []
        """Child tasks"""

        self.__teardown_hooks: list[TeardownHook] = []

        self.__verbose = False
        """Whether task should always show full output regardless of status"""

    def add_teardown_hook(self, hook: TeardownHook):
        """Register a teardown hook, which will be called during the clean-up
        phase of the action.

        This function can be either synchronous or asynchronous. If it is
        async, its return will be awaited before running earlier hooks.

        Parameters
        ----------
        hook : TeardownHook
            Hook callback function.
        """
        self.__teardown_hooks.append(hook)

    def get_teardown_hooks(self) -> list[TeardownHook]:
        """Returns all registered teardown hooks, both for this hook, and for
        all its children.

        This list of hooks should be returned by a `RecipeStep` once it
        finishes executing. It does not need to be manually run by a Markten
        action.

        The hooks are returned in the order in which they should be executed
        (ie reverse order of creation).

        Returns
        -------
        list[TeardownHook]
            List of teardown hooks.
        """
        hooks = []
        for child in reversed(self.__children):
            hooks.extend(child.get_teardown_hooks())
        hooks.extend(reversed(self.__teardown_hooks))
        return hooks

    def child(
        self,
        action: Callable[Concatenate['ActionSession', P], T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """Register and immediately execute a child action

        This handles the complexity of making a child action and then calling
        it.

        Parameters
        ----------
        action : MarktenAction
            Action function to execute as a child of this action session.

        Returns
        -------
        T
            Return of the given action.
        """
        child_session = self.make_child(action)
        return action(child_session, *args, **kwargs)

    def make_child(self, name: str | object) -> 'ActionSession':
        """Create a child action of this action.

        It's probably simpler to use `ActionSession.child` to create and
        execute the child action immediately.

        Used to indicate when a sub-action is required for the completion of
        this action. The action will not be called automatically, but the
        returned `ActionSession` can be passed to it for logging purposes.

        Parameters
        ----------
        name : str | object
            Name of the child action. If an object is given, its name will be
            used (if it is a function or class).

        Returns
        -------
        ActionSession
            Child task
        """
        child = ActionSession(name)
        self.__children.append(child)
        return child

    def set_verbose(self, new_value: bool = True) -> None:
        """Set verbosity for this action's output.

        This can be used to make actions always show output, regardless of
        failure or success.

        Parameters
        ----------
        new_value : bool, optional
            New verbose value, by default True
        """
        self.__verbose = new_value

    def log(self, line: str) -> None:
        """
        Add message to the actions's output log.

        This is used for detailed output, such as the stdout of a child
        process or debugging info.
        """
        self.__output.append(line.strip())

    def progress(self, progress: float | None) -> None:
        """
        Set the progress percentage of the action.

        If set to `None`, indicates progress is not being measured (a spinner
        will be shown rather than a progress bar).
        """

    def message(self, msg: str | None) -> None:
        """
        Set the overall status message of the action.

        If set, this is always displayed alongside the action's name.

        If `None`, no message is shown, and the previous message is discarded.
        """
        self.__message = msg
        if msg is not None:
            self.log(msg)

    def running(self, msg: str | None = None) -> None:
        """
        Set the action status as `Running`.

        Optionally, a status message can be provided.
        """
        self.__status = ActionStatus.Running
        self.message(msg)

    def succeed(self, msg: str | None = None) -> None:
        """
        Set the action status as `Success`.

        Optionally, a status message can be provided.
        """
        self.__status = ActionStatus.Success
        self.message(msg)

    def fail(self, msg: str | None = None) -> None:
        """
        Set the action status as `Failure`.

        Optionally, a status message can be provided.
        """
        self.__status = ActionStatus.Failure
        self.message(msg)

    def is_resolved(self) -> bool:
        """
        Returns whether the action has resolved, meaning it finished
        successfully, or that it failed.
        """
        return self.__status in [ActionStatus.Success, ActionStatus.Failure]

    def display(self) -> ActionInfo:
        """
        Return info about this action in a format which can be displayed
        easily.
        """
        return ActionInfo(
            self.__name,
            self.__status,
            self.__message,
            self.__progress,
            [child.display() for child in self.__children],
            self.__output,
            self.__verbose,
        )
