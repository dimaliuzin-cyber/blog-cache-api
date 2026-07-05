from pydantic import ValidationError
from redis.asyncio import Redis

from app.schemas.posts import PostRead


class PostCache:
    def __init__(
        self,
        redis_client: Redis,
        ttl_seconds: int,
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    def build_key(self, post_id: int) -> str:
        return f"post:{post_id}"

    async def get_post(self, post_id: int) -> PostRead | None:
        key = self.build_key(post_id)

        cached_data = await self._redis.get(key)

        if cached_data is None:
            return None

        try:
            return PostRead.model_validate_json(cached_data)
        except ValidationError:
            await self.delete_post(post_id)
            return None

    async def set_post(self, post: PostRead) -> None:
        key = self.build_key(post.id)
        payload = post.model_dump_json()

        await self._redis.set(
            key,
            payload,
            ex=self._ttl_seconds,
        )

    async def delete_post(self, post_id: int) -> None:
        key = self.build_key(post_id)

        await self._redis.delete(key)
