"""
# Markten / Actions / process.py

Actions for running subprocesses
"""
from .__process import (
    run,
    run_async,
    run_detached,
    run_in_background,
    stdout_of,
)

__all__ = [
    "run",
    "run_async",
    "run_detached",
    "run_in_background",
    "stdout_of",
]
