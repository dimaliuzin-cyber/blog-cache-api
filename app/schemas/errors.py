from typing import Any

from pydantic import BaseModel, Field


class ErrorData(BaseModel):
    code: str = Field(description="Машинный код ошибки.")
    message: str = Field(description="Понятное сообщение об ошибке.")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorData