import logging
import time

from fastapi import FastAPI, Request

from markitdown_api.api.v1.router import api_router
from markitdown_api.core.config import get_settings
from markitdown_api.core.logging import setup_logging

http_logger = logging.getLogger("markitdown_api.http")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="markitdown-fastapi",
        description="HTTP API wrapping Microsoft's markitdown library.",
        version="0.1.0",
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
