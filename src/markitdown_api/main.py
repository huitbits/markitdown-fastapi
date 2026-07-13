from fastapi import FastAPI

from markitdown_api.api.v1.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="markitdown-fastapi",
        description="HTTP API wrapping Microsoft's markitdown library.",
        version="0.1.0",
    )
    app.include_router(api_router)
    return app


app = create_app()
