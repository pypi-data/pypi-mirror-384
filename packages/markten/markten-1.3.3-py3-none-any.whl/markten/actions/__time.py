"""
# Markten / Actions / time.py

Actions for managing timing
"""

import asyncio
import time

from markten.__action_session import ActionSession
from markten.actions.__action import markten_action


@markten_action
async def sleep(action: ActionSession, duration: float) -> None:
    """Pause execution for the given duration.

    Equivalent to a `time.sleep()` call, but without blocking other
    actions.

    Parameters
    ----------
    duration : float
        Time to pause, in seconds.
    """
    action.running()

    start_time = time.time()
    now = time.time()

    while now - start_time < duration:
        # Give a countdown
        remaining = duration - (now - start_time)
        action.message(f"{round(remaining)}s remaining...")
        if remaining > 1:
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(remaining)
        now = time.time()

    action.succeed("0s remaining")
