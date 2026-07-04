from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core import database


@pytest_asyncio.fixture(autouse=True)
async def reset_database_state() -> AsyncGenerator[None, None]:
    await database.close_database()
    yield
    await database.close_database()


@pytest.mark.asyncio
async def test_get_engine_returns_async_engine() -> None:
    engine = database.get_engine()

    assert isinstance(engine, AsyncEngine)


@pytest.mark.asyncio
async def test_get_engine_returns_same_instance_between_calls() -> None:
    first_engine = database.get_engine()
    second_engine = database.get_engine()

    assert first_engine is second_engine


@pytest.mark.asyncio
async def test_get_session_factory_returns_async_sessionmaker() -> None:
    session_factory = database.get_session_factory()

    assert isinstance(session_factory, async_sessionmaker)


@pytest.mark.asyncio
async def test_get_session_factory_returns_same_instance_between_calls() -> None:
    first_factory = database.get_session_factory()
    second_factory = database.get_session_factory()

    assert first_factory is second_factory


@pytest.mark.asyncio
async def test_get_db_session_yields_async_session() -> None:
    session_generator = database.get_db_session()

    session = await anext(session_generator)

    try:
        assert isinstance(session, AsyncSession)
    finally:
        await session_generator.aclose()


@pytest.mark.asyncio
async def test_close_database_resets_engine_and_session_factory() -> None:
    first_engine = database.get_engine()
    first_factory = database.get_session_factory()

    await database.close_database()

    second_engine = database.get_engine()
    second_factory = database.get_session_factory()

    assert first_engine is not second_engine
    assert first_factory is not second_factory