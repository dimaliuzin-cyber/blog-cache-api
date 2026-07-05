from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.posts.cache import PostCache
from app.posts.exceptions import PostNotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.schemas.posts import PostCreate, PostRead, PostUpdate


class PostRepositoryProtocol(Protocol):
    async def create_post(self, post_create: PostCreate) -> Post:
        pass

    async def get_post_by_id(self, post_id: int) -> Post | None:
        pass

    async def update_post(
        self,
        post_id: int,
        post_update: PostUpdate,
    ) -> Post | None:
        pass

    async def delete_post(self, post_id: int) -> Post | None:
        pass


class PostCacheProtocol(Protocol):
    async def get_post(self, post_id: int) -> PostRead | None:
        pass

    async def set_post(self, post: PostRead) -> None:
        pass

    async def delete_post(self, post_id: int) -> None:
        pass


class PostService:
    def __init__(
        self,
        session: AsyncSession | None = None,
        redis_client: Redis | None = None,
        repository: PostRepositoryProtocol | None = None,
        cache: PostCacheProtocol | None = None,
    ) -> None:
        self._session = session

        if repository is not None:
            self._repository = repository
        else:
            if session is None:
                raise ValueError(
                    "session is required when repository is not provided",
                )

            self._repository = PostRepository(session)

        if cache is not None:
            self._cache = cache
        elif redis_client is not None:
            settings = get_settings()
            self._cache = PostCache(
                redis_client=redis_client,
                ttl_seconds=settings.post_cache_ttl_seconds,
            )
        else:
            self._cache = None

    async def create_post(self, post_create: PostCreate) -> Post:
        post = await self._repository.create_post(post_create)

        await self._commit_transaction()
        await self._refresh_instance(post)

        return post

    async def get_post(self, post_id: int) -> PostRead:
        if self._cache is not None:
            cached_post = await self._cache.get_post(post_id)

            if cached_post is not None:
                return cached_post

        post = await self._repository.get_post_by_id(post_id)

        if post is None:
            raise PostNotFoundError(post_id)

        post_read = PostRead.model_validate(post)

        if self._cache is not None:
            await self._cache.set_post(post_read)

        return post_read

    async def update_post(
        self,
        post_id: int,
        post_update: PostUpdate,
    ) -> Post:
        post = await self._repository.update_post(
            post_id=post_id,
            post_update=post_update,
        )

        if post is None:
            raise PostNotFoundError(post_id)

        await self._commit_transaction()
        await self._refresh_instance(post)

        if self._cache is not None:
            await self._cache.delete_post(post_id)

        return post

    async def delete_post(self, post_id: int) -> Post:
        post = await self._repository.delete_post(post_id)

        if post is None:
            raise PostNotFoundError(post_id)

        await self._commit_transaction()

        if self._cache is not None:
            await self._cache.delete_post(post_id)

        return post

    async def _commit_transaction(self) -> None:
        if self._session is None:
            return

        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _refresh_instance(self, post: Post) -> None:
        if self._session is None:
            return

        await self._session.refresh(post)
