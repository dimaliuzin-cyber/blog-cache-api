from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class PostCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Заголовок поста",
        examples=["First post"],
    )
    content: str = Field(
        min_length=1,
        description="Текст поста",
        examples=["This is the content of the post."],
    )


class PostUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Новый заголовок поста",
        examples=["Updated title"],
    )
    content: str | None = Field(
        default=None,
        min_length=1,
        description="Новый текст поста",
        examples=["Updated post content."],
    )

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "PostUpdate":
        if self.title is None and self.content is None:
            raise ValueError("At least one field must be provided for update")

        return self


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Уникальный идентификатор поста", examples=[1])
    title: str = Field(description="Заголовок поста", examples=["First post"])
    content: str = Field(
        description="Текст поста",
        examples=["This is the content of the post."],
    )
    created_at: datetime = Field(description="Дата и время создания поста")
    updated_at: datetime = Field(description="Дата и время последнего обновления поста")


class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime
