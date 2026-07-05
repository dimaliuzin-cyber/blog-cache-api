from datetime import datetime, UTC

import pytest

from app.posts import (
    Post,
    PostNotFoundError,
    PostService,
)
from app.schemas.posts import (
    PostCreate,
    PostRead,
    PostUpdate,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakePostRepository:
    def __init__(self) -> None:
        self.posts: dict[int, Post] = {}
        self.next_id = 1

    async def create_post(self, post_create: PostCreate) -> Post:
        now = datetime.now(UTC)

        post = Post(
            title=post_create.title,
            content=post_create.content,
        )

        post.id = self.next_id
        post.created_at = now
        post.updated_at = now

        self.posts[post.id] = post
        self.next_id += 1

        return post

    async def get_post_by_id(self, post_id: int) -> Post | None:
        return self.posts.get(post_id)

    async def update_post(
        self,
        post_id: int,
        post_update: PostUpdate,
    ) -> Post | None:
        post = self.posts.get(post_id)

        if post is None:
            return None

        update_data = post_update.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "title" in update_data:
            post.title = update_data["title"]

        if "content" in update_data:
            post.content = update_data["content"]

        post.updated_at = datetime.now(UTC)

        return post

    async def delete_post(self, post_id: int) -> Post | None:
        return self.posts.pop(post_id, None)


class FakePostCache:
    def __init__(self) -> None:
        self.posts: dict[int, PostRead] = {}
        self.deleted_post_ids: list[int] = []
        self.saved_post_ids: list[int] = []

    async def get_post(self, post_id: int) -> PostRead | None:
        return self.posts.get(post_id)

    async def set_post(self, post: PostRead) -> None:
        self.posts[post.id] = post
        self.saved_post_ids.append(post.id)

    async def delete_post(self, post_id: int) -> None:
        self.posts.pop(post_id, None)
        self.deleted_post_ids.append(post_id)


@pytest.mark.anyio
async def test_create_post_without_database() -> None:
    repository = FakePostRepository()
    service = PostService(repository=repository)

    post = await service.create_post(
        PostCreate(
            title="Title",
            content="Some content",
        ),
    )

    assert post.id == 1
    assert post.title == "Title"
    assert post.content == "Some content"
    assert repository.posts[1] == post


@pytest.mark.anyio
async def test_get_post_returns_post_without_database_and_saves_to_cache() -> None:
    repository = FakePostRepository()
    cache = FakePostCache()

    service = PostService(
        repository=repository,
        cache=cache,
    )

    created_post = await repository.create_post(
        PostCreate(
            title="Cached title",
            content="Some cached content",
        ),
    )

    found_post = await service.get_post(created_post.id)

    assert found_post.id == created_post.id
    assert found_post.title == "Cached title"
    assert found_post.content == "Some cached content"

    assert cache.saved_post_ids == [created_post.id]
    assert cache.posts[created_post.id].title == "Cached title"


@pytest.mark.anyio
async def test_get_post_returns_post_from_cache_without_repository_lookup() -> None:
    repository = FakePostRepository()
    cache = FakePostCache()

    cached_post = PostRead(
        id=10,
        title="From cache",
        content="Cache content",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    cache.posts[cached_post.id] = cached_post

    service = PostService(
        repository=repository,
        cache=cache,
    )

    found_post = await service.get_post(cached_post.id)

    assert found_post.id == 10
    assert found_post.title == "From cache"
    assert found_post.content == "Cache content"
    assert repository.posts == {}


@pytest.mark.anyio
async def test_get_post_raises_error_when_post_not_found_without_database() -> None:
    repository = FakePostRepository()
    service = PostService(repository=repository)

    with pytest.raises(PostNotFoundError) as error:
        await service.get_post(999_999)

    assert error.value.post_id == 999_999


@pytest.mark.anyio
async def test_update_post_invalidates_cache_without_redis() -> None:
    repository = FakePostRepository()
    cache = FakePostCache()

    service = PostService(
        repository=repository,
        cache=cache,
    )

    created_post = await repository.create_post(
        PostCreate(
            title="Old title",
            content="Original content",
        )
    )

    cache.posts[created_post.id] = PostRead.model_validate(created_post)

    updated_post = await service.update_post(
        created_post.id,
        PostUpdate(title="New title"),
    )

    assert updated_post.id == created_post.id
    assert updated_post.title == "New title"
    assert updated_post.content == "Original content"

    assert cache.deleted_post_ids == [created_post.id]
    assert created_post.id not in cache.posts
