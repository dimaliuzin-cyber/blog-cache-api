from fastapi.testclient import TestClient

from app.main import create_app


def test_response_contains_generated_request_id_header() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


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
