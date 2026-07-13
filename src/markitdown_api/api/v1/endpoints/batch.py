from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile

from markitdown_api.core.config import Settings, get_settings
from markitdown_api.core.markitdown_client import build_markitdown_client
from markitdown_api.core.security import require_token
from markitdown_api.schemas.convert import BatchConvertResponse, BatchItemResult
from markitdown_api.services.conversion import (
    ConversionError,
    UnsafeUrlError,
    convert_upload_to_markdown,
    convert_url_to_markdown,
)

router = APIRouter(tags=["convert"], dependencies=[Depends(require_token)])


@router.post(
    "/convert/batch",
    response_model=BatchConvertResponse,
    summary="Convert multiple files and/or URLs to Markdown in one call",
)
async def convert_batch(
    settings: Annotated[Settings, Depends(get_settings)],
    files: list[UploadFile] | None = None,
    urls: Annotated[list[str], Form()] = [],  # noqa: B006 (FastAPI Form default pattern)
    enable_plugins: bool = False,
    use_docintel: bool = False,
    use_llm_captions: bool = False,
) -> BatchConvertResponse:
    client = build_markitdown_client(
        settings,
        enable_plugins=enable_plugins,
        use_docintel=use_docintel,
        use_llm_captions=use_llm_captions,
    )

    results: list[BatchItemResult] = []

    for file in files or []:
        source = file.filename or "unknown"
        try:
            response = await convert_upload_to_markdown(client, file)
            results.append(BatchItemResult(source=source, success=True, markdown=response.markdown))
        except ConversionError as err:
            results.append(BatchItemResult(source=source, success=False, error=str(err)))

    for url in urls:
        try:
            response = await convert_url_to_markdown(client, url)
            results.append(BatchItemResult(source=url, success=True, markdown=response.markdown))
        except (UnsafeUrlError, ConversionError) as err:
            results.append(BatchItemResult(source=url, success=False, error=str(err)))

    return BatchConvertResponse(results=results)
