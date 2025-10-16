from collections.abc import Awaitable, Callable
from typing import Any, Concatenate, ParamSpec, TypeVar

from markten.__action_session import ActionSession

ActionParams = ParamSpec('ActionParams')

ActionResult = Any | dict[str, Any]
"""
Result from a Markten action.

Either a single value or a dict mapping from parameter names to their
corresponding values.

* Single values with no name will be discarded if used directly as a step.
* Dict values will be added to the `context` for future steps.
"""

ResultType = TypeVar("ResultType")

MarktenAction = Callable[
    Concatenate[ActionSession, ActionParams],
    Awaitable[ResultType],
]
"""
A Markten action is an async function which accepts an `ActionSession`, as well
as (optionally) other parameters. It can use this `ActionSession` to register
teardown hooks, and to create child actions.
"""


def markten_action(
    action: MarktenAction[ActionParams, ResultType],
) -> MarktenAction[ActionParams, ResultType]:
    """Decorator to assert that a function satisfies the action type
    definition.

    This performs no validation, but can be used to increase type safety.
    """
    return action
