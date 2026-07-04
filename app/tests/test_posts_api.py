from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.database import close_database, get_session_factory
from app.main import create_app
from app.posts import Post


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

    await close_database()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_create_post_returns_201_and_created_post(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/posts",
        json={
            "title": "First post",
            "content": "Hi everyone!",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "First post"
    assert data["content"] == "Hi everyone!"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_post_returns_existing_post(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/posts",
        json={
            "title": "First post",
            "content": "Hi there!",
        },
    )

    post_id = create_response.json()["id"]

    response = await client.get(f"/posts/{post_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == post_id
    assert data["title"] == "First post"
    assert data["content"] == "Hi there!"


@pytest.mark.asyncio
async def test_get_post_returns_404_when_post_not_found(
    client: AsyncClient,
) -> None:
    response = await client.get("/posts/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Post with id=999999 was not found",
    }


@pytest.mark.asyncio
async def test_update_post_updates_only_provided_fields(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/posts",
        json={
            "title": "Old title",
            "content": "Original content",
        },
    )

    post_id = create_response.json()["id"]

    response = await client.patch(
        f"/posts/{post_id}",
        json={
            "title": "New title",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == post_id
    assert data["title"] == "New title"
    assert data["content"] == "Original content"


@pytest.mark.asyncio
async def test_update_post_returns_404_when_post_not_found(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        "/posts/999999",
        json={
            "title": "New title",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Post with id=999999 was not found",
    }


@pytest.mark.asyncio
async def test_delete_post_returns_204_and_removes_post(
    client: AsyncClient,
) -> None:
    create_response = await client.post(
        "/posts",
        json={
            "title": "Post to delete",
            "content": "Delete me",
        },
    )

    post_id = create_response.json()["id"]

    delete_response = await client.delete(f"/posts/{post_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = await client.get(f"/posts/{post_id}")

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_post_returns_404_when_post_not_found(
    client: AsyncClient,
) -> None:
    response = await client.delete("/posts/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Post with id=999999 was not found",
    }


@pytest.mark.asyncio
async def test_post_id_must_be_positive(
    client: AsyncClient,
) -> None:
    response = await client.get("/posts/0")

    assert response.status_code == 422