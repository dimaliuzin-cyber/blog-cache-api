from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import close_database, get_session_factory
from app.posts import Post, PostRepository
from app.schemas.posts import PostCreate, PostUpdate


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            await session.execute(delete(Post))
            await session.commit()

            try:
                yield session
            finally:
                await session.rollback()
                await session.execute(delete(Post))
                await session.commit()
    finally:
        await close_database()


@pytest.mark.asyncio
async def test_create_post_returns_saved_post(db_session: AsyncSession) -> None:
    repository = PostRepository(db_session)

    post = await repository.create_post(
        PostCreate(
            title="First post",
            content="Hello!",
        )
    )

    assert post.id is not None
    assert post.title == "First post"
    assert post.content == "Hello!"


@pytest.mark.asyncio
async def test_get_post_by_id_returns_post(db_session: AsyncSession) -> None:
    repository = PostRepository(db_session)

    created_post = await repository.create_post(
        PostCreate(
            title="First post",
            content="Hello!",
        )
    )

    found_post = await repository.get_post_by_id(created_post.id)

    assert found_post is not None
    assert found_post.id == created_post.id
    assert found_post.title == "First post"
    assert found_post.content == "Hello!"


@pytest.mark.asyncio
async def test_get_post_by_id_returns_none_when_post_not_found(
    db_session: AsyncSession,
) -> None:
    repository = PostRepository(db_session)

    post = await repository.get_post_by_id(999_999)

    assert post is None


@pytest.mark.asyncio
async def test_update_post_updates_only_provided_fields(
    db_session: AsyncSession,
) -> None:
    repository = PostRepository(db_session)

    created_post = await repository.create_post(
        PostCreate(
            title="First post",
            content="Original content",
        )
    )

    updated_post = await repository.update_post(
        created_post.id,
        PostUpdate(title="Updated title"),
    )

    assert updated_post is not None
    assert updated_post.id == created_post.id
    assert updated_post.title == "Updated title"
    assert updated_post.content == "Original content"


@pytest.mark.asyncio
async def test_update_post_returns_none_when_post_not_found(
    db_session: AsyncSession,
) -> None:
    repository = PostRepository(db_session)

    post = await repository.update_post(
        999_999,
        PostUpdate(title="Updated title"),
    )

    assert post is None


@pytest.mark.asyncio
async def test_delete_post_removes_post(db_session: AsyncSession) -> None:
    repository = PostRepository(db_session)

    created_post = await repository.create_post(
        PostCreate(
            title="First post",
            content="Hello!",
        )
    )

    deleted_post = await repository.delete_post(created_post.id)
    found_post = await repository.get_post_by_id(created_post.id)

    assert deleted_post is not None
    assert deleted_post.id == created_post.id
    assert found_post is None


@pytest.mark.asyncio
async def test_delete_post_returns_none_when_post_not_found(
    db_session: AsyncSession,
) -> None:
    repository = PostRepository(db_session)

    post = await repository.delete_post(999_999)

    assert post is None