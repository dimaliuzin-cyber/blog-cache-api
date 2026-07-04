from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers.posts import router as posts_router
from app.api.routers.system import router as system_router
from app.core.config import get_settings
from app.core.database import close_database
from app.core.exception_handlers import register_exception_handlers
from app.core.redis import close_redis, create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.redis = create_redis_client()

    try:
        yield
    finally:
        await close_redis(app)
        await close_database()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(system_router)
    app.include_router(posts_router)

    return app


app = create_app()