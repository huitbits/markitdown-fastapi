import pytest
from fastapi.testclient import TestClient

from markitdown_api.core.config import Settings, get_settings
from markitdown_api.main import app


def test_anonymize_text(client: TestClient) -> None:
    response = client.post("/api/v1/anonymize/text", json={"text": "Contato: joao@example.com"})
    assert response.status_code == 200
    body = response.json()
    assert "joao@example.com" not in body["anonymized"]
    assert any(e["entity_type"] == "EMAIL_ADDRESS" for e in body["entities_found"])


def test_anonymize_html(client: TestClient) -> None:
    response = client.post("/api/v1/anonymize/html", json={"html": "<p>joao@example.com</p>"})
    assert response.status_code == 200
    body = response.json()
    assert body["anonymized"].startswith("<p>")
    assert "joao@example.com" not in body["anonymized"]


def test_anonymize_markdown(client: TestClient) -> None:
    response = client.post(
        "/api/v1/anonymize/markdown", json={"markdown": "# Contato\n\njoao@example.com"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["anonymized"].startswith("# Contato")
    assert "joao@example.com" not in body["anonymized"]


def test_anonymize_json(client: TestClient) -> None:
    response = client.post(
        "/api/v1/anonymize/json",
        json={"data": {"user": {"email": "joao@example.com"}}},
    )
    assert response.status_code == 200
    body = response.json()
    assert "joao@example.com" not in body["anonymized"]["user"]["email"]
    assert body["entities_found"][0]["path"] == "user.email"


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_settings] = lambda: Settings(markitdown_fastapi_token="secret")
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_anonymize_text_rejects_missing_token(authed_client: TestClient) -> None:
    response = authed_client.post("/api/v1/anonymize/text", json={"text": "joao@example.com"})
    assert response.status_code == 401


def test_anonymize_text_accepts_correct_token(authed_client: TestClient) -> None:
    response = authed_client.post(
        "/api/v1/anonymize/text",
        json={"text": "joao@example.com"},
        headers={"Authorization": "Bearer secret"},
    )
    assert response.status_code == 200
