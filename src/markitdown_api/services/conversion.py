"""Conversion business logic, orchestrating the markitdown client(s)."""

import tempfile
from pathlib import Path

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from markitdown_api.core.markitdown_client import MarkitdownClientBuild
from markitdown_api.core.url_guard import UnsafeUrlError, ensure_public_http_url
from markitdown_api.schemas.convert import ConversionMetadata, ConvertResponse


class ConversionError(Exception):
    """Raised when markitdown fails to convert a given source."""


async def convert_upload_to_markdown(
    upload: UploadFile,
    primary: MarkitdownClientBuild,
    docintel_fallback: MarkitdownClientBuild | None = None,
) -> ConvertResponse:
    suffix = Path(upload.filename or "").suffix
    content = await upload.read()

    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(content)
        tmp.flush()
        markdown, extraction_method, title = await _convert_with_fallback(
            tmp.name, "convert_local", primary, docintel_fallback
        )

    return ConvertResponse(
        markdown=markdown,
        metadata=ConversionMetadata(
            source_type="upload",
            source=upload.filename or "unknown",
            title=title,
            extraction_method=extraction_method,
        ),
    )


async def convert_url_to_markdown(
    url: str,
    primary: MarkitdownClientBuild,
    docintel_fallback: MarkitdownClientBuild | None = None,
) -> ConvertResponse:
    ensure_public_http_url(url)  # raises UnsafeUrlError on SSRF-risky destinations

    markdown, extraction_method, title = await _convert_with_fallback(
        url, "convert", primary, docintel_fallback
    )

    return ConvertResponse(
        markdown=markdown,
        metadata=ConversionMetadata(
            source_type="url",
            source=url,
            title=title,
            extraction_method=extraction_method,
        ),
    )


async def _convert_with_fallback(
    source: str,
    method_name: str,
    primary: MarkitdownClientBuild,
    docintel_fallback: MarkitdownClientBuild | None,
) -> tuple[str, str, str | None]:
    """Try the primary client; auto-retry with Document Intelligence on empty/failed result.

    Document Intelligence is only ever used as a fallback: attempted solely when the
    primary (built-in) extraction raises or comes back with blank markdown, and only if
    a fallback client was configured (use_docintel=True and Azure DI set up).
    """
    primary_result = None
    primary_error: Exception | None = None
    try:
        primary_result = await run_in_threadpool(getattr(primary.client, method_name), source)
    except Exception as err:  # noqa: BLE001 (markitdown raises assorted converter errors)
        primary_error = err

    primary_has_content = (
        primary_result is not None
        and primary_result.text_content
        and primary_result.text_content.strip()
    )
    if primary_has_content:
        return (
            primary_result.text_content,
            primary.extraction_method,
            getattr(primary_result, "title", None),
        )

    if docintel_fallback is None:
        if primary_error is not None:
            raise ConversionError(str(primary_error)) from primary_error
        return (
            primary_result.text_content,
            primary.extraction_method,
            getattr(primary_result, "title", None),
        )

    try:
        fallback_result = await run_in_threadpool(
            getattr(docintel_fallback.client, method_name), source
        )
    except Exception as err:  # noqa: BLE001
        raise ConversionError(str(err)) from err

    reason = "empty extraction" if primary_error is None else "extraction failed"
    extraction_method = f"{docintel_fallback.extraction_method} (fallback after {reason})"
    return fallback_result.text_content, extraction_method, getattr(fallback_result, "title", None)


__all__ = [
    "ConversionError",
    "UnsafeUrlError",
    "convert_upload_to_markdown",
    "convert_url_to_markdown",
]
