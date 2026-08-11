from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness check",
    description='Always returns `{"status": "ok"}` when the service is up. Never '
    "requires authentication, regardless of MARKITDOWN_FASTAPI_TOKEN.",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}
