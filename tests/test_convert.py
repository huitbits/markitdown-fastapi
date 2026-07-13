from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_convert_uploaded_html(client: TestClient) -> None:
    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = client.post(
            "/api/v1/convert",
            files={"file": ("sample.html", f, "text/html")},
        )

    assert response.status_code == 200
    body = response.json()
    assert "Hello Markdown" in body["markdown"]
    assert body["metadata"]["source_type"] == "upload"
    assert body["metadata"]["source"] == "sample.html"
    assert body["metadata"]["extraction_method"] == "MarkItDown (built-in converters)"


def test_convert_url_rejects_loopback(client: TestClient) -> None:
    response = client.post("/api/v1/convert/url", json={"url": "http://127.0.0.1/secret"})
    assert response.status_code == 422


def test_convert_url_rejects_non_http_scheme(client: TestClient) -> None:
    response = client.post("/api/v1/convert/url", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422
