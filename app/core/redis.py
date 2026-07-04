from fastapi import Request
from redis.asyncio import Redis
from starlette.applications import Starlette

from app.core.config import get_settings


def create_redis_client() -> Redis:
    settings = get_settings()

    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        health_check_interval=30,
    )


def get_redis_client() -> Redis:
    return create_redis_client()


def get_redis(request: Request) -> Redis:
    redis_client = getattr(request.app.state, "redis", None)

    if redis_client is None:
        raise RuntimeError(
            "Redis client is not initialized"
            "Make sure FastAPI lifespan is running",
        )

    return redis_client


async def close_redis(app: Starlette | None = None) -> None:
    if app is None:
        return

    redis_client: Redis | None = getattr(app.state, "redis", None)

    if redis_client is None:
        return

    await redis_client.aclose()
    app.state.redis = None