"""
# Markten / Context

Definition for the `MarktenContext` singleton.
"""
import logging
from os import environ

from markten.__consts import VERBOSE_ENV_VAR


class __MarktenContext:
    def __init__(self) -> None:
        self.__verbosity = int(environ.get(VERBOSE_ENV_VAR, "0"))

    @property
    def verbosity(self) -> int:
        """
        The verbosity of Markten's outputs.
        """
        return self.__verbosity

    @verbosity.setter
    def verbosity(self, new_verbosity: int) -> None:
        self.__verbosity = new_verbosity
        environ[VERBOSE_ENV_VAR] = str(new_verbosity)
        mappings = {
            0: "CRITICAL",
            1: "WARNING",
            2: "INFO",
            3: "DEBUG",
        }
        logging.basicConfig(level=mappings.get(new_verbosity, "DEBUG"))


__ctx = __MarktenContext()


def get_context():
    return __ctx
