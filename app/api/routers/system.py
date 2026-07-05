from typing import Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.config import get_settings


router = APIRouter(tags=["Системные проверки"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(description="Технический статус приложения.")
    service: str = Field(description="Название сервиса.")
    environment: str = Field(description="Окружение приложения.")


class ReadinessResponse(BaseModel):
    status: Literal["ready"] = Field(description="Готовность принимать трафик.")
    checks: dict[str, str] = Field(description="Список внутренних проверок.")


class VersionResponse(BaseModel):
    service: str = Field(description="Название сервиса.")
    version: str = Field(description="Версия приложения.")
    api_version: str = Field(description="Версия API.")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Проверить, что приложение запущено",
    description=(
        "Проверка, что FastAPI-приложение работает и отвечает на HTTP-запросы. "
        "Используется для базового healthcheck."
    ),
    response_description="Текущий статус приложения.",
)
async def health() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Проверить готовность принимать трафик",
    description=(
        "Проверяет, готово ли приложение принимать входящие запросы. "
        "В реальном проекте здесь проверяются база данных, Redis "
        "и другие внешние зависимости."
    ),
    response_description="Статус готовности приложения.",
)
async def readiness() -> ReadinessResponse:
    return ReadinessResponse(
        status="ready",
        checks={
            "application": "ok",
        },
    )


@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить версию сервиса",
    description=(
        "Возвращает техническую информацию о сервисе: название приложения, "
        "версию приложения и версию API."
    ),
    response_description="Информация о версии сервиса.",
)
async def version() -> VersionResponse:
    settings = get_settings()

    return VersionResponse(
        service=settings.app_name,
        version=settings.app_version,
        api_version=settings.api_version,
    )
