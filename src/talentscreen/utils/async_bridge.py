"""Run async coroutines from synchronous LangGraph nodes and tools."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="talentscreen-async")


def run_sync(coro: Coroutine[object, object, T]) -> T:
    """Execute *coro* whether or not an event loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return _executor.submit(asyncio.run, coro).result()
