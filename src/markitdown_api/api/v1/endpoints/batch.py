from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile

from markitdown_api.core.config import Settings, get_settings
from markitdown_api.core.markitdown_client import (
    build_docintel_fallback_client,
    build_primary_client,
)
from markitdown_api.core.security import AUTH_RESPONSES, require_token
from markitdown_api.schemas.convert import BatchConvertResponse, BatchItemResult
from markitdown_api.services.anonymization import anonymize_content
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
    description="Converts any combination of file uploads and URLs in a single request. "
    "Per-item failures (unsafe URL, conversion error) do not fail the whole request — they "
    "are reported as a `success: false` entry with an `error` message for that item.",
    responses=AUTH_RESPONSES,
)
async def convert_batch(
    settings: Annotated[Settings, Depends(get_settings)],
    files: list[UploadFile] | None = None,
    urls: Annotated[list[str], Form()] = [],  # noqa: B006 (FastAPI Form default pattern)
    enable_plugins: bool = False,
    use_docintel: bool = False,
    use_llm_captions: bool = False,
    anonymize: bool = False,
) -> BatchConvertResponse:
    primary = build_primary_client(
        settings, enable_plugins=enable_plugins, use_llm_captions=use_llm_captions
    )
    docintel_fallback = (
        build_docintel_fallback_client(settings, use_llm_captions=use_llm_captions)
        if use_docintel
        else None
    )

    results: list[BatchItemResult] = []

    for file in files or []:
        source = file.filename or "unknown"
        try:
            response = await convert_upload_to_markdown(file, primary, docintel_fallback)
            markdown = (
                anonymize_content(response.markdown).anonymized if anonymize else response.markdown
            )
            results.append(
                BatchItemResult(
                    source=source,
                    success=True,
                    markdown=markdown,
                    extraction_method=response.metadata.extraction_method,
                )
            )
        except ConversionError as err:
            results.append(BatchItemResult(source=source, success=False, error=str(err)))

    for url in urls:
        try:
            response = await convert_url_to_markdown(url, primary, docintel_fallback)
            markdown = (
                anonymize_content(response.markdown).anonymized if anonymize else response.markdown
            )
            results.append(
                BatchItemResult(
                    source=url,
                    success=True,
                    markdown=markdown,
                    extraction_method=response.metadata.extraction_method,
                )
            )
        except (UnsafeUrlError, ConversionError) as err:
            results.append(BatchItemResult(source=url, success=False, error=str(err)))

    return BatchConvertResponse(results=results)
