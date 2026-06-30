import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from talentscreen.config import get_settings

_engines: dict[int, AsyncEngine] = {}
_session_factories: dict[int, async_sessionmaker[AsyncSession]] = {}


def _loop_key() -> int:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        return 0


def get_engine() -> AsyncEngine:
    key = _loop_key()
    if key not in _engines:
        _engines[key] = create_async_engine(
            get_settings().database_url,
            echo=False,
            pool_pre_ping=True,
        )
    return _engines[key]


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    key = _loop_key()
    if key not in _session_factories:
        _session_factories[key] = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factories[key]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
