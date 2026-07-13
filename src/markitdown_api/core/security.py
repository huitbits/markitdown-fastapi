"""Optional bearer token auth, enabled only when MARKITDOWN_FASTAPI_TOKEN is set."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from markitdown_api.core.config import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


async def require_token(
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> None:
    if not settings.auth_required:
        return

    if credentials is None or credentials.credentials != settings.markitdown_fastapi_token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
