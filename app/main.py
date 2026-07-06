from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from textwrap import dedent

from fastapi import FastAPI

from app.api.routers.posts import router as posts_router
from app.api.routers.system import router as system_router
from app.core.config import get_settings
from app.core.database import close_database
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.redis import close_redis, create_redis_client


API_DESCRIPTION = dedent(
    """
    ---
    ### Назначение сервиса

    REST API для управления постами блога с поддержкой кеширования часто запрашиваемых данных.

    Сервис реализует CRUD-операции для постов и использует PostgreSQL как основной
    источник актуальных данных. Redis применяется как быстрый cache-aside слой,
    который ускоряет повторное чтение популярных записей.

    ### Основные возможности

    - создание, получение, обновление и удаление постов;
    - кеширование ответа при `GET /posts/{post_id}`;
    - автоматическая инвалидация кеша при изменении или удалении поста;
    - единый формат ошибок;
    - трассировка запросов через `X-Request-ID`.
    <br>
    <br>
    <br>
    <br>
    # Разделы API: 
    """
).strip()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.redis = create_redis_client()

    try:
        yield
    finally:
        await close_redis(app)
        await close_database()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_title,
        description=API_DESCRIPTION,
        version=settings.app_version,
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "Системные проверки",
                "description": (
                    "Раздел для проверки состояния приложения, готовности сервиса "
                    "и получения версии API."
                ),
            },
            {
                "name": "Управление постами",
                "description": (
                    "Раздел для создания, чтения, обновления и удаления постов."
                ),
            },
        ],
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
        },
    )

    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)

    app.include_router(system_router)
    app.include_router(posts_router)

    return app


app = create_app()
