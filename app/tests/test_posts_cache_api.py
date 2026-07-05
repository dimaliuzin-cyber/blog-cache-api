from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.database import close_database, get_session_factory
from app.core.redis import close_redis, get_redis_client
from app.main import create_app
from app.posts import Post
from app.schemas.posts import PostRead


@pytest_asyncio.fixture(autouse=True)
async def clean_posts_table() -> AsyncGenerator[None, None]:
    session_factory = get_session_factory()

    async with session_factory() as session:
        await session.execute(delete(Post))
        await session.commit()

    yield

    async with session_factory() as session:
        await session.execute(delete(Post))
        await session.commit()

    await close_redis()
    await close_database()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client


@pytest.mark.asyncio
async def test_get_post_stores_post_in_redis(
    client: AsyncClient,
) -> None:
    redis_client = get_redis_client()

    create_response = await client.post(
        "/posts",
        json={
            "title": "Cached post",
            "content": "This post should be cached",
        },
    )

    post_id = create_response.json()["id"]
    cache_key = f"post:{post_id}"

    await redis_client.delete(cache_key)

    try:
        assert await redis_client.get(cache_key) is None

        response = await client.get(f"/posts/{post_id}")
        assert response.status_code == 200

        cached_data = await redis_client.get(cache_key)
        assert cached_data is not None

        cached_post = PostRead.model_validate_json(cached_data)
        assert cached_post.id == post_id
        assert cached_post.title == "Cached post"
        assert cached_post.content == "This post should be cached"
    finally:
        await redis_client.delete(cache_key)
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_update_post_invalidates_redis_cache(
    client: AsyncClient,
) -> None:
    redis_client = get_redis_client()

    create_response = await client.post(
        "/posts",
        json={
            "title": "Old title",
            "content": "Original content",
        },
    )

    post_id = create_response.json()["id"]
    cache_key = f"post:{post_id}"

    try:
        get_response = await client.get(f"/posts/{post_id}")

        assert get_response.status_code == 200
        assert await redis_client.get(cache_key) is not None

        update_response = await client.patch(
            f"/posts/{post_id}",
            json={
                "title": "New title",
            },
        )

        assert update_response.status_code == 200
        assert await redis_client.get(cache_key) is None
    finally:
        await redis_client.delete(cache_key)
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_delete_post_invalidates_redis_cache(
    client: AsyncClient,
) -> None:
    redis_client = get_redis_client()

    create_response = await client.post(
        "/posts",
        json={
            "title": "Post to delete",
            "content": "Delete me",
        },
    )

    post_id = create_response.json()["id"]
    cache_key = f"post:{post_id}"

    try:
        get_response = await client.get(f"/posts/{post_id}")

        assert get_response.status_code == 200
        assert await redis_client.get(cache_key) is not None

        delete_response = await client.delete(f"/posts/{post_id}")

        assert delete_response.status_code == 204
        assert await redis_client.get(cache_key) is None

        get_response_after_delete = await client.get(f"/posts/{post_id}")

        assert get_response_after_delete.status_code == 404
        assert await redis_client.get(cache_key) is None
    finally:
        await redis_client.delete(cache_key)
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_get_post_returns_post_from_redis_when_cache_exists(
    client: AsyncClient,
) -> None:
    redis_client = get_redis_client()

    create_response = await client.post(
        "/posts",
        json={
            "title": "Original title",
            "content": "Original content",
        },
    )

    post_id = create_response.json()["id"]
    cache_key = f"post:{post_id}"

    await redis_client.delete(cache_key)

    try:
        first_response = await client.get(f"/posts/{post_id}")

        assert first_response.status_code == 200
        assert first_response.json()["title"] == "Original title"
        assert await redis_client.get(cache_key) is not None

        session_factory = get_session_factory()

        async with session_factory() as session:
            post = await session.get(Post, post_id)

            assert post is not None

            post.title = "Changed directly in PostgreSQL"
            post.content = "Changed directly in PostgreSQL"

            await session.commit()

        second_response = await client.get(f"/posts/{post_id}")

        assert second_response.status_code == 200

        data = second_response.json()

        assert data["id"] == post_id
        assert data["title"] == "Original title"
        assert data["content"] == "Original content"
    finally:
        await redis_client.delete(cache_key)
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_get_post_after_update_returns_fresh_post_not_stale_cache(
    client: AsyncClient,
) -> None:
    redis_client = get_redis_client()

    create_response = await client.post(
        "/posts",
        json={
            "title": "Old title",
            "content": "Original content",
        },
    )

    post_id = create_response.json()["id"]
    cache_key = f"post:{post_id}"

    try:
        first_get_response = await client.get(f"/posts/{post_id}")

        assert first_get_response.status_code == 200
        assert first_get_response.json()["title"] == "Old title"
        assert await redis_client.get(cache_key) is not None

        update_response = await client.patch(
            f"/posts/{post_id}",
            json={
                "title": "New title",
            },
        )

        assert update_response.status_code == 200
        assert update_response.json()["title"] == "New title"
        assert await redis_client.get(cache_key) is None

        second_get_response = await client.get(f"/posts/{post_id}")

        assert second_get_response.status_code == 200

        data = second_get_response.json()

        assert data["id"] == post_id
        assert data["title"] == "New title"
        assert data["content"] == "Original content"

        assert await redis_client.get(cache_key) is not None
    finally:
        await redis_client.delete(cache_key)
        await redis_client.aclose()
