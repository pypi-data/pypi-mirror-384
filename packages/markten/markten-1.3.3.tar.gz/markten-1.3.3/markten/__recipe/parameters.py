"""
# Markten / Recipe / Parameters

Parameter manager for Markten
"""

from collections.abc import Iterable, Iterator, Mapping
from typing import Any


class ParameterManager:
    """
    Collect parameters for a recipe, and then allow for iterating over all
    permutations of those parameters.
    """

    def __init__(self) -> None:
        self.__params: dict[str, Iterable[Any]] = {}

    def add(self, name: str, values: Iterable[Any]) -> None:
        """Add the given iterable of parameters to the parameter set

        Parameters
        ----------
        name : str
            name to use for this parameter.
        values : Iterable[Any]
            All values of this parameter.

        Raises
        ------
        ValueError
            The parameter was already added.
        """
        if name in self.__params:
            raise ValueError(
                f"Cannot add parameter '{name}', as it has already been added"
            )

        self.__params[name] = values

    @staticmethod
    def __do_dict_permutations_iterator(
        keys: list[str],
        params_dict: Mapping[str, Iterable[Any]],
    ) -> Iterator[dict[str, Any]]:
        """
        Recursively iterate over the given keys, producing a dict of values.
        """
        keys_head = keys[0]
        # Base case: this is the last remaining key
        if len(keys) == 1:
            for value in params_dict[keys_head]:
                yield {keys_head: value}
            return

        # Recursive case, other keys remain, and we need to iterate over those
        # too
        keys_tail = keys[1:]

        for value in params_dict[keys_head]:
            # Iterate over remaining keys
            for (
                current_params
            ) in ParameterManager.__do_dict_permutations_iterator(
                keys_tail, params_dict
            ):
                # Overall keys is the union of the current key-value pair with
                # the params yielded by the recursion
                yield {keys_head: value} | current_params

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """
        Iterate over all possible parameter values.
        """
        return self.__do_dict_permutations_iterator(
            list(self.__params.keys()), self.__params
        )
