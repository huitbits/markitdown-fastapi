import logging
import time
from importlib.metadata import version

from fastapi import FastAPI, Request

from markitdown_api.api.v1.router import api_router
from markitdown_api.core.config import get_settings
from markitdown_api.core.logging import setup_logging

http_logger = logging.getLogger("markitdown_api.http")

OPENAPI_TAGS = [
    {
        "name": "convert",
        "description": "Convert file uploads, remote URLs, or batches of both to Markdown.",
    },
    {
        "name": "anonymize",
        "description": "Redact Brazilian PII (names, e-mails, CPF, CNPJ, RG, phone numbers) "
        "from standalone text, HTML, Markdown, or JSON content.",
    },
    {
        "name": "health",
        "description": "Liveness check, always unauthenticated.",
    },
]


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="markitdown-fastapi",
        description="HTTP API wrapping Microsoft's markitdown library.",
        version=version("markitdown-fastapi"),
        openapi_tags=OPENAPI_TAGS,
    )
    app.include_router(api_router)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        # Never log headers/body here — Authorization tokens and uploaded content
        # must not end up in logs. Content-Length is metadata, not content.
        http_logger.debug(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_content_length": request.headers.get("content-length"),
                "response_content_length": response.headers.get("content-length"),
            },
        )
        return response

    return app


app = create_app()
