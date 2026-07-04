from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_name: str = Field(description="Техническое имя сервиса.")
    app_title: str = Field(description="Название приложения для OpenAPI.")
    app_description: str = Field(description="Описание приложения для OpenAPI.")
    app_env: Literal["local", "test", "staging", "production"] = Field(
        description="Окружение, в котором запущено приложение.",
    )
    app_version: str = Field(description="Версия приложения.")
    api_version: str = Field(description="Версия API.")

    database_url: str = Field(description="URL подключения к PostgreSQL.")
    redis_url: str = Field(description="URL подключения к Redis.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()