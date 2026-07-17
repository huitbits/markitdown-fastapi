import json
import logging

import pytest
from fastapi.testclient import TestClient

from markitdown_api.core.config import Settings
from markitdown_api.core.logging import JsonFormatter


def test_json_formatter_emits_valid_json_with_expected_fields() -> None:
    record = logging.LogRecord(
        name="markitdown_api.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="something_happened",
        args=(),
        exc_info=None,
    )
    record.duration_ms = 12.3

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "markitdown_api.test"
    assert payload["message"] == "something_happened"
    assert payload["duration_ms"] == 12.3
    assert "timestamp" in payload


def test_json_formatter_includes_exception_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="markitdown_api.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="conversion_failed",
            args=(),
            exc_info=__import__("sys").exc_info(),
        )

    payload = json.loads(JsonFormatter().format(record))

    assert "ValueError: boom" in payload["exception"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("debug", "DEBUG"), ("INFO", "INFO"), ("Warning", "WARNING")],
)
def test_log_level_is_case_insensitive(raw: str, expected: str) -> None:
    assert Settings(log_level=raw).log_level == expected


def test_log_level_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):  # noqa: PT011 (pydantic ValidationError subclasses ValueError)
        Settings(log_level="verbose")


def test_debug_middleware_logs_request_without_leaking_authorization(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG, logger="markitdown_api.http"):
        response = client.get(
            "/api/v1/health", headers={"Authorization": "Bearer super-secret-token"}
        )

    assert response.status_code == 200
    http_records = [r for r in caplog.records if r.name == "markitdown_api.http"]
    assert len(http_records) == 1

    record = http_records[0]
    assert record.method == "GET"
    assert record.path == "/api/v1/health"
    assert record.status_code == 200
    assert isinstance(record.duration_ms, float)

    serialized = json.dumps(record.__dict__, default=str)
    assert "super-secret-token" not in serialized
    assert "authorization" not in serialized.lower()
