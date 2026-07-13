from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from markitdown_api.core.config import Settings, get_settings
from markitdown_api.core.markitdown_client import build_markitdown_client
from markitdown_api.core.security import require_token
from markitdown_api.core.url_guard import UnsafeUrlError
from markitdown_api.schemas.convert import ConvertResponse, ConvertUrlRequest
from markitdown_api.services.conversion import (
    ConversionError,
    convert_upload_to_markdown,
    convert_url_to_markdown,
)

router = APIRouter(tags=["convert"], dependencies=[Depends(require_token)])


@router.post(
    "/convert",
    response_model=ConvertResponse,
    summary="Convert an uploaded file to Markdown",
)
async def convert_file(
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile,
    enable_plugins: bool = False,
    use_docintel: bool = False,
    use_llm_captions: bool = False,
) -> ConvertResponse:
    if file.size is not None and file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, detail="File exceeds max upload size"
        )

    client = build_markitdown_client(
        settings,
        enable_plugins=enable_plugins,
        use_docintel=use_docintel,
        use_llm_captions=use_llm_captions,
    )
    try:
        return await convert_upload_to_markdown(client, file)
    except ConversionError as err:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)) from err


@router.post(
    "/convert/url",
    response_model=ConvertResponse,
    summary="Convert a remote URL to Markdown",
)
async def convert_url(
    settings: Annotated[Settings, Depends(get_settings)],
    body: ConvertUrlRequest,
) -> ConvertResponse:
    client = build_markitdown_client(
        settings,
        enable_plugins=body.enable_plugins,
        use_docintel=body.use_docintel,
        use_llm_captions=body.use_llm_captions,
    )
    try:
        return await convert_url_to_markdown(client, str(body.url))
    except UnsafeUrlError as err:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)) from err
    except ConversionError as err:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)) from err
