from fastapi.testclient import TestClient

from app.core import database
from app.main import create_app


def test_app_lifespan_closes_database_on_shutdown() -> None:
    app = create_app()

    with TestClient(app):
        first_engine = database.get_engine()
        first_factory = database.get_session_factory()

        assert first_engine is database.get_engine()
        assert first_factory is database.get_session_factory()

    second_engine = database.get_engine()
    second_factory = database.get_session_factory()

    assert second_engine is database.get_engine()
    assert second_factory is database.get_session_factory()
