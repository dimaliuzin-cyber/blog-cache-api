from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.posts import (
    PostCreate,
    PostListItem,
    PostRead,
    PostUpdate,
)


def test_post_create_valid_data() -> None:
    post = PostCreate(title="First post", content="Hello!")

    assert post.title == "First post"
    assert post.content == "Hello!"


def test_post_create_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        PostCreate(title="", content="Hello!")


def test_post_create_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        PostCreate(title="First post", content="")


def test_post_create_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        PostCreate(id=1, title="First post", content="Hello!")


def test_post_update_allows_only_title() -> None:
    post_update = PostUpdate(title="Updated title")

    assert post_update.title == "Updated title"
    assert post_update.content is None


def test_post_update_rejects_empty_body() -> None:
    with pytest.raises(ValidationError):
        PostUpdate()


def test_post_read_contains_full_post_data() -> None:
    now = datetime(2026, 7, 3, 10, 0, 0)

    post = PostRead(
        id=1,
        title="First post",
        content="Hello!",
        created_at=now,
        updated_at=now,
    )

    assert post.id == 1
    assert post.title == "First post"
    assert post.content == "Hello!"
    assert post.created_at == now
    assert post.updated_at == now


def test_list_item_does_not_contain_content() -> None:
    now = datetime(2026, 7, 3, 10, 0, 0)

    post = PostListItem(
        id=1,
        title="First post",
        created_at=now,
        updated_at=now,
    )

    data = post.model_dump()

    assert "content" not in data


def test_post_read_model_dump_json_converts_datetime_to_string() -> None:
    now = datetime(2026, 7, 3, 10, 0, 0)

    post = PostRead(
        id=1,
        title="First post",
        content="Hello!",
        created_at=now,
        updated_at=now,
    )

    data = post.model_dump(mode="json")

    assert data["created_at"] == "2026-07-03T10:00:00"
    assert data["updated_at"] == "2026-07-03T10:00:00"