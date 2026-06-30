import asyncio

from talentscreen.utils.async_bridge import run_sync


async def _sample_coro() -> str:
    return "ok"


def test_run_sync_from_running_loop() -> None:
    async def _inner() -> str:
        return run_sync(_sample_coro())

    assert asyncio.run(_inner()) == "ok"


def test_run_sync_without_loop() -> None:
    assert run_sync(_sample_coro()) == "ok"
