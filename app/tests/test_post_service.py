from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import close_database, get_session_factory
from app.posts import Post, PostNotFoundError, PostRepository, PostService
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
async def test_create_post_returns_created_post(db_session: AsyncSession) -> None:
    service = PostService(db_session)

    post = await service.create_post(
        PostCreate(
            title="First post",
            content="Hello from service!",
        )
    )

    assert post.id is not None
    assert post.title == "First post"
    assert post.content == "Hello from service!"


@pytest.mark.asyncio
async def test_get_post_returns_post(db_session: AsyncSession) -> None:
    repository = PostRepository(db_session)
    service = PostService(db_session)

    created_post = await repository.create_post(
        PostCreate(
            title="First post",
            content="Hello!",
        )
    )

    found_post = await service.get_post(created_post.id)

    assert found_post.id == created_post.id
    assert found_post.title == "First post"
    assert found_post.content == "Hello!"


@pytest.mark.asyncio
async def test_get_post_raises_error_when_post_not_found(
    db_session: AsyncSession,
) -> None:
    service = PostService(db_session)

    with pytest.raises(PostNotFoundError) as error:
        await service.get_post(999_999)

    assert error.value.post_id == 999_999


@pytest.mark.asyncio
async def test_update_post_updates_existing_post(
    db_session: AsyncSession,
) -> None:
    service = PostService(db_session)

    created_post = await service.create_post(
        PostCreate(
            title="Old title",
            content="Original content",
        )
    )

    updated_post = await service.update_post(
        created_post.id,
        PostUpdate(title="New title"),
    )

    assert updated_post.id == created_post.id
    assert updated_post.title == "New title"
    assert updated_post.content == "Original content"


@pytest.mark.asyncio
async def test_update_post_raises_error_when_post_not_found(
    db_session: AsyncSession,
) -> None:
    service = PostService(db_session)

    with pytest.raises(PostNotFoundError) as error:
        await service.update_post(
            999_999,
            PostUpdate(title="New title"),
        )

    assert error.value.post_id == 999_999


@pytest.mark.asyncio
async def test_delete_post_deletes_existing_post(
    db_session: AsyncSession,
) -> None:
    service = PostService(db_session)

    created_post = await service.create_post(
        PostCreate(
            title="Post to delete",
            content="Delete me",
        )
    )

    deleted_post = await service.delete_post(created_post.id)

    assert deleted_post.id == created_post.id

    with pytest.raises(PostNotFoundError):
        await service.get_post(created_post.id)


@pytest.mark.asyncio
async def test_delete_post_raises_error_when_post_not_found(
    db_session: AsyncSession,
) -> None:
    service = PostService(db_session)

    with pytest.raises(PostNotFoundError) as error:
        await service.delete_post(999_999)

    assert error.value.post_id == 999_999
