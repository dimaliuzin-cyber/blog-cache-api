from uuid import UUID

from fastapi.testclient import TestClient

from app.main import create_app


def test_response_contains_generated_request_id_header() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_generated_request_id_is_valid_uuid() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    request_id = response.headers["x-request-id"]

    parsed_request_id = UUID(request_id)

    assert str(parsed_request_id) == request_id


def test_response_preserves_incoming_request_id_header() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={
                "X-Request-ID": "test-request-id-123",
            },
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-id-123"


def test_empty_incoming_request_id_is_replaced_with_generated_uuid() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={
                "X-Request-ID": "",
            },
        )

    request_id = response.headers["x-request-id"]

    assert response.status_code == 200
    assert request_id

    parsed_request_id = UUID(request_id)

    assert str(parsed_request_id) == request_id


def test_validation_error_response_contains_request_id_header() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get(
            "/posts/0",
            headers={
                "X-Request-ID": "validation-error-request-id",
            },
        )

    assert response.status_code == 422
    assert response.headers["x-request-id"] == "validation-error-request-id"
