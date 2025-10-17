"""Utility to run a background asyncio event loop in a dedicated thread
and provide helpers to schedule coroutines or callables on that loop.

This keeps loop-management centralized so other modules (like Ctx)
don't need to duplicate thread/loop startup logic.
"""

from __future__ import annotations

import asyncio
import threading
from logging import getLogger
from typing import Any, Callable
from concurrent.futures import Future

logger = getLogger("react_tk")


def create_event_loop(trace_name: str) -> asyncio.AbstractEventLoop:

    loop = asyncio.new_event_loop()

    event = threading.Event()

    def _run_loop() -> None:
        try:
            asyncio.set_event_loop(loop)
            loop.call_soon(event.set)
            loop.run_forever()
        except Exception:
            logger.exception("Async loop crashed")

    t = threading.Thread(target=_run_loop, name=trace_name)
    t.start()
    event.wait()
    return loop
