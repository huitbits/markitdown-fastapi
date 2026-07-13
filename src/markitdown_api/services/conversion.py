"""Conversion business logic, orchestrating the markitdown client."""

import tempfile
from pathlib import Path

from fastapi import UploadFile
from markitdown import MarkItDown
from starlette.concurrency import run_in_threadpool

from markitdown_api.core.url_guard import UnsafeUrlError, ensure_public_http_url
from markitdown_api.schemas.convert import ConversionMetadata, ConvertResponse


class ConversionError(Exception):
    """Raised when markitdown fails to convert a given source."""


async def convert_upload_to_markdown(client: MarkItDown, upload: UploadFile) -> ConvertResponse:
    suffix = Path(upload.filename or "").suffix
    content = await upload.read()

    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(content)
        tmp.flush()
        try:
            result = await run_in_threadpool(client.convert_local, tmp.name)
        except Exception as err:
            raise ConversionError(str(err)) from err

    return ConvertResponse(
        markdown=result.text_content,
        metadata=ConversionMetadata(
            source_type="upload",
            source=upload.filename or "unknown",
            title=getattr(result, "title", None),
        ),
    )


async def convert_url_to_markdown(client: MarkItDown, url: str) -> ConvertResponse:
    ensure_public_http_url(url)  # raises UnsafeUrlError on SSRF-risky destinations

    try:
        result = await run_in_threadpool(client.convert, url)
    except Exception as err:
        raise ConversionError(str(err)) from err

    return ConvertResponse(
        markdown=result.text_content,
        metadata=ConversionMetadata(
            source_type="url",
            source=url,
            title=getattr(result, "title", None),
        ),
    )


__all__ = [
    "ConversionError",
    "UnsafeUrlError",
    "convert_upload_to_markdown",
    "convert_url_to_markdown",
]
