"""
# Markten / consts
"""

from importlib.metadata import version

VERSION = version("markten")
"""
Markten version, determined using importlib metadata (so that I don't need to
constantly remember to update it).
"""


TIME_PER_CLI_FRAME = 0.03
"""30 FPS"""

VERBOSE_ENV_VAR = "MARKTEN_VERBOSITY"
"""Environment variable to determine verbosity from"""
