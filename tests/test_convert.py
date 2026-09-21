from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from markitdown_api.core.config import get_settings
from markitdown_api.schemas.convert import ConversionMetadata, ConvertResponse

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


def test_convert_uploaded_html_with_anonymize_redacts_pii(client: TestClient) -> None:
    sample = FIXTURES_DIR / "sample_with_pii.html"
    with sample.open("rb") as f:
        response = client.post(
            "/api/v1/convert",
            files={"file": ("sample_with_pii.html", f, "text/html")},
            params={"anonymize": "true"},
        )

    assert response.status_code == 200
    body = response.json()
    assert "João Silva" not in body["markdown"]
    assert "123.456.789-09" not in body["markdown"]
    assert "joao@example.com" not in body["markdown"]


def test_convert_url_rejects_loopback(client: TestClient) -> None:
    response = client.post("/api/v1/convert/url", json={"url": "http://127.0.0.1/secret"})
    assert response.status_code == 422


def test_convert_url_rejects_non_http_scheme(client: TestClient) -> None:
    response = client.post("/api/v1/convert/url", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422


def test_convert_uploaded_file_force_docintel_without_endpoint_returns_422(
    client: TestClient,
) -> None:
    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = client.post(
            "/api/v1/convert",
            files={"file": ("sample.html", f, "text/html")},
            params={"force_docintel": "true"},
        )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "AZURE_DOCINTEL_ENDPOINT must be configured when force_docintel is true."
    )


def test_convert_url_force_docintel_without_endpoint_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/convert/url",
        json={"url": "https://example.com/doc.pdf", "force_docintel": True},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "AZURE_DOCINTEL_ENDPOINT must be configured when force_docintel is true."
    )


def test_convert_batch_force_docintel_without_endpoint_returns_422(
    client: TestClient,
) -> None:
    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = client.post(
            "/api/v1/convert/batch",
            files=[("files", ("sample.html", f, "text/html"))],
            params={"force_docintel": "true"},
        )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "AZURE_DOCINTEL_ENDPOINT must be configured when force_docintel is true."
    )


def test_convert_uploaded_file_force_docintel_with_endpoint_calls_docintel(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AZURE_DOCINTEL_ENDPOINT", "https://example.cognitiveservices.azure.com/")
    get_settings.cache_clear()

    async def fake_convert_upload(upload, primary, docintel_fallback=None, *, force_docintel=False):
        assert force_docintel is True
        assert primary.extraction_method == "Microsoft Document Intelligence"
        return ConvertResponse(
            markdown="# Extracted with forced DocIntel",
            metadata=ConversionMetadata(
                source_type="upload",
                source=upload.filename or "unknown",
                title="Doc Title",
                extraction_method=primary.extraction_method,
            ),
        )

    monkeypatch.setattr(
        "markitdown_api.api.v1.endpoints.convert.convert_upload_to_markdown",
        fake_convert_upload,
    )

    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = client.post(
            "/api/v1/convert",
            files={"file": ("sample.html", f, "text/html")},
            params={"force_docintel": "true"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["markdown"] == "# Extracted with forced DocIntel"
    assert data["metadata"]["extraction_method"] == "Microsoft Document Intelligence"


def test_convert_url_force_docintel_with_endpoint_calls_docintel(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AZURE_DOCINTEL_ENDPOINT", "https://example.cognitiveservices.azure.com/")
    get_settings.cache_clear()

    async def fake_convert_url(url, primary, docintel_fallback=None, *, force_docintel=False):
        assert force_docintel is True
        assert primary.extraction_method == "Microsoft Document Intelligence"
        return ConvertResponse(
            markdown="# Extracted URL with forced DocIntel",
            metadata=ConversionMetadata(
                source_type="url",
                source=url,
                title="URL Doc",
                extraction_method=primary.extraction_method,
            ),
        )

    monkeypatch.setattr(
        "markitdown_api.api.v1.endpoints.convert.convert_url_to_markdown",
        fake_convert_url,
    )

    response = client.post(
        "/api/v1/convert/url",
        json={"url": "https://example.com/test.pdf", "force_docintel": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["markdown"] == "# Extracted URL with forced DocIntel"
    assert data["metadata"]["extraction_method"] == "Microsoft Document Intelligence"


def test_convert_batch_force_docintel_with_endpoint_calls_docintel(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AZURE_DOCINTEL_ENDPOINT", "https://example.cognitiveservices.azure.com/")
    get_settings.cache_clear()

    async def fake_convert_upload(upload, primary, docintel_fallback=None, *, force_docintel=False):
        assert force_docintel is True
        assert primary.extraction_method == "Microsoft Document Intelligence"
        return ConvertResponse(
            markdown="# Batch item forced",
            metadata=ConversionMetadata(
                source_type="upload",
                source=upload.filename or "unknown",
                title=None,
                extraction_method=primary.extraction_method,
            ),
        )

    monkeypatch.setattr(
        "markitdown_api.api.v1.endpoints.batch.convert_upload_to_markdown",
        fake_convert_upload,
    )

    sample = FIXTURES_DIR / "sample.html"
    with sample.open("rb") as f:
        response = client.post(
            "/api/v1/convert/batch",
            files=[("files", ("sample.html", f, "text/html"))],
            params={"force_docintel": "true"},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["success"] is True
    assert data["results"][0]["markdown"] == "# Batch item forced"
    assert data["results"][0]["extraction_method"] == "Microsoft Document Intelligence"
