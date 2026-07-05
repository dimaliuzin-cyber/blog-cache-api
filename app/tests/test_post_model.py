from sqlalchemy import DateTime, String, Text

from app.core.database import Base
from app.posts import Post


def test_post_model_registered_in_metadata() -> None:
    assert "posts" in Base.metadata.tables


def test_post_model_has_expected_table_name() -> None:
    assert Post.__tablename__ == "posts"


def test_post_model_has_expected_coulums() -> None:
    table = Post.__table__

    assert "id" in table.c
    assert "title" in table.c
    assert "content" in table.c
    assert "created_at" in table.c
    assert "updated_at" in table.c


def test_post_model_id_is_primary_key() -> None:
    table = Post.__table__

    assert table.c.id.primary_key is True


def test_post_model_title_is_string_200_and_required() -> None:
    table = Post.__table__

    assert isinstance(table.c.title.type, String)
    assert table.c.title.type.length == 200
    assert table.c.title.nullable is False


def test_post_model_content_is_text_and_required() -> None:
    table = Post.__table__

    assert isinstance(table.c.content.type, Text)
    assert table.c.content.nullable is False


def test_post_model_datetime_columns_are_timezone_aware() -> None:
    table = Post.__table__

    assert isinstance(table.c.created_at.type, DateTime)
    assert isinstance(table.c.updated_at.type, DateTime)

    assert table.c.created_at.type.timezone is True
    assert table.c.updated_at.type.timezone is True
