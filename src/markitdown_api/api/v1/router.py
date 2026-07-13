from fastapi import APIRouter

from markitdown_api.api.v1.endpoints import batch, convert, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(convert.router)
api_router.include_router(batch.router)
