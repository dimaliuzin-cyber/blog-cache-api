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
    ## Назначение сервиса

    REST API для управления постами с кешированием часто запрашиваемых данных.

    Сервис предоставляет API для создания, получения, обновления и удаления постов.
    Для оптимизации чтения используется паттерн cache-aside: PostgreSQL остается
    основным источником актуальных данных, а Redis хранит временные копии часто
    запрашиваемых записей.

    ## Хранение данных и кеширование

    - **PostgreSQL** — основное хранилище постов.
    - **Redis** — кеш для ускорения повторных запросов на чтение.
    - **TTL** ограничивает время жизни кешированной записи.
    - **Инвалидация кеша** выполняется при обновлении и удалении поста.

    ## Как работает чтение поста

    При запросе `GET /posts/{post_id}` приложение выполняет следующий сценарий:

    1. Проверяет наличие поста в Redis.
    2. Если запись найдена, возвращает данные из кеша.
    3. Если записи нет, загружает пост из PostgreSQL.
    4. Сохраняет полученный пост в Redis с ограниченным временем жизни.
    5. Возвращает актуальные данные клиенту.

    Такой подход снижает нагрузку на PostgreSQL и ускоряет повторное чтение часто запрашиваемых постов.

    ## Техническая реализация

    Проект запускается через **Docker Compose** и использует миграции **Alembic**
    для управления схемой базы данных. Работа с PostgreSQL построена на
    **SQLAlchemy Async**.

    Код разделен на слои `router / service / repository / cache`, чтобы HTTP-логика,
    бизнес-правила, доступ к базе данных и работа с Redis не смешивались между собой.

    Дополнительно реализованы единый формат ошибок, `request id` для трассировки
    запросов, структурированное логирование и автоматические тесты.
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
