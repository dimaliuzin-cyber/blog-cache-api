from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.posts.exceptions import PostNotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.schemas.posts import PostCreate, PostUpdate, PostRead
from app.core.config import get_settings
from app.posts.cache import PostCache


class PostService:
    def __init__(
        self,
        session: AsyncSession,
        redis_client: Redis | None = None,
    ) -> None:
        self._session = session
        self._repository = PostRepository(session)
        self._cache: PostCache | None = None

        if redis_client is not None:
            settings = get_settings()
            self._cache = PostCache(
                redis_client=redis_client,
                ttl_seconds=settings.post_cache_ttl_seconds,
            )

    async def create_post(self, post_create: PostCreate) -> Post:
        post = await self._repository.create_post(post_create)

        await self._commit_transaction()
        await self._session.refresh(post)

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
        await self._session.refresh(post)

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
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
