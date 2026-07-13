from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from markitdown_api.core.config import Settings, get_settings
from markitdown_api.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_settings] = lambda: Settings(markitdown_fastapi_token="secret")
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_health_never_requires_token(authed_client: TestClient) -> None:
    response = authed_client.get("/api/v1/health")
    assert response.status_code == 200


def test_convert_rejects_missing_token(authed_client: TestClient) -> None:
    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = authed_client.post(
            "/api/v1/convert",
            files={"file": ("sample.html", f, "text/html")},
        )
    assert response.status_code == 401


def test_convert_rejects_wrong_token(authed_client: TestClient) -> None:
    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = authed_client.post(
            "/api/v1/convert",
            files={"file": ("sample.html", f, "text/html")},
            headers={"Authorization": "Bearer wrong"},
        )
    assert response.status_code == 401


def test_convert_accepts_correct_token(authed_client: TestClient) -> None:
    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = authed_client.post(
            "/api/v1/convert",
            files={"file": ("sample.html", f, "text/html")},
            headers={"Authorization": "Bearer secret"},
        )
    assert response.status_code == 200


def test_convert_url_rejects_missing_token(authed_client: TestClient) -> None:
    response = authed_client.post("/api/v1/convert/url", json={"url": "https://example.com"})
    assert response.status_code == 401
