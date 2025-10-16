"""
# Markten / Recipe / Runner

Runner for a single permutation of a recipe.
"""

import traceback
from collections.abc import Awaitable
from datetime import datetime
from typing import Any

import humanize
from rich.console import Console

from markten.__action_session import TeardownHook
from markten.__recipe.step import RecipeStep

console = Console()


class RecipeRunner:
    def __init__(
        self,
        params: dict[str, Any],
        steps: list[RecipeStep],
    ) -> None:
        self.__params = params
        self.__steps = steps

    async def run(self):
        self.__show_current_params()
        start = datetime.now()

        try:
            await self.__do_run()
        except Exception as e:
            console.print(
                "[red]Error while running this permutation of recipe[/]"
            )
            # TODO: Better error handling (pretty-print exceptions)
            traceback.print_exception(e)

        duration = datetime.now() - start
        perm_str = humanize.precisedelta(duration, minimum_unit="seconds")
        print(f"Permutation complete in {perm_str}")
        print()

    async def __do_run(self):
        """Actually run the recipe"""
        context: dict[str, Any] = {}
        teardown: list[list[TeardownHook]] = []

        for step in self.__steps:
            context, teardown_hooks = await step.run(self.__params, context)
            teardown.append(teardown_hooks)

        # Now do clean-up in reverse order
        for teardown_step in reversed(teardown):
            for hook in teardown_step:
                await RecipeRunner.__exec_teardown_hook(hook)

    @staticmethod
    async def __exec_teardown_hook(hook: TeardownHook) -> None:
        value = hook()
        if isinstance(value, Awaitable):
            await value

    def __show_current_params(self):
        """
        Displays the current params to the user.
        """
        print()
        print("Running recipe with given parameters:")
        for param_name, param_value in self.__params.items():
            print(f"  {param_name} = {param_value}")
        print()
