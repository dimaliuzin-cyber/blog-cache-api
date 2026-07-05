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


@pytest.mark.asyncio
async def test_cache_integration_create_get_update_invalidate_and_recaches(
    client: AsyncClient,
) -> None:
    redis_client = get_redis_client()
    cache_key: str | None = None

    try:
        create_response = await client.post(
            "/posts",
            json={
                "title": "Old cached title",
                "content": "Original cached content",
            },
        )

        assert create_response.status_code == 201

        created_post = create_response.json()
        post_id = created_post["id"]
        cache_key = f"post:{post_id}"

        await redis_client.delete(cache_key)

        assert await redis_client.get(cache_key) is None

        first_get_response = await client.get(f"/posts/{post_id}")

        assert first_get_response.status_code == 200

        first_get_data = first_get_response.json()

        assert first_get_data["id"] == post_id
        assert first_get_data["title"] == "Old cached title"
        assert first_get_data["content"] == "Original cached content"

        old_cached_payload = await redis_client.get(cache_key)

        assert old_cached_payload is not None

        old_cached_post = PostRead.model_validate_json(old_cached_payload)

        assert old_cached_post.id == post_id
        assert old_cached_post.title == "Old cached title"
        assert old_cached_post.content == "Original cached content"

        update_response = await client.patch(
            f"/posts/{post_id}",
            json={
                "title": "New cached title",
            },
        )

        assert update_response.status_code == 200

        updated_data = update_response.json()

        assert updated_data["id"] == post_id
        assert updated_data["title"] == "New cached title"
        assert updated_data["content"] == "Original cached content"

        assert await redis_client.get(cache_key) is None

        session_factory = get_session_factory()

        async with session_factory() as session:
            db_post = await session.get(Post, post_id)

            assert db_post is not None
            assert db_post.id == post_id
            assert db_post.title == "New cached title"
            assert db_post.content == "Original cached content"

        second_get_response = await client.get(f"/posts/{post_id}")

        assert second_get_response.status_code == 200

        second_get_data = second_get_response.json()

        assert second_get_data["id"] == post_id
        assert second_get_data["title"] == "New cached title"
        assert second_get_data["content"] == "Original cached content"

        new_cached_payload = await redis_client.get(cache_key)

        assert new_cached_payload is not None

        new_cached_post = PostRead.model_validate_json(new_cached_payload)

        assert new_cached_post.id == post_id
        assert new_cached_post.title == "New cached title"
        assert new_cached_post.content == "Original cached content"

    finally:
        if cache_key is not None:
            await redis_client.delete(cache_key)

        await redis_client.aclose()
