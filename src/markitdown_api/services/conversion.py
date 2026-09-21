"""Conversion business logic, orchestrating the markitdown client(s)."""

import logging
import tempfile
import time
from pathlib import Path

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from markitdown_api.core.markitdown_client import MarkitdownClientBuild
from markitdown_api.core.url_guard import UnsafeUrlError, ensure_public_http_url
from markitdown_api.schemas.convert import ConversionMetadata, ConvertResponse

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Raised when markitdown fails to convert a given source."""


async def convert_upload_to_markdown(
    upload: UploadFile,
    primary: MarkitdownClientBuild,
    docintel_fallback: MarkitdownClientBuild | None = None,
    *,
    force_docintel: bool = False,
) -> ConvertResponse:
    suffix = Path(upload.filename or "").suffix
    content = await upload.read()
    logger.info(
        "upload_received",
        extra={"upload_filename": upload.filename, "size_bytes": len(content), "suffix": suffix},
    )

    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(content)
        tmp.flush()
        markdown, extraction_method, title = await _convert_with_fallback(
            tmp.name,
            "convert_local",
            primary,
            docintel_fallback,
            force_docintel=force_docintel,
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
    *,
    force_docintel: bool = False,
) -> ConvertResponse:
    ensure_public_http_url(url)  # raises UnsafeUrlError on SSRF-risky destinations
    logger.info("url_conversion_requested", extra={"url": url})

    markdown, extraction_method, title = await _convert_with_fallback(
        url,
        "convert",
        primary,
        docintel_fallback,
        force_docintel=force_docintel,
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
    *,
    force_docintel: bool = False,
) -> tuple[str, str, str | None]:
    """Execute document conversion.

    When force_docintel is True, converts directly with primary (configured for Document
    Intelligence), bypassing local converters.
    Otherwise, tries the primary client (built-in converters) and auto-retries with
    Document Intelligence on empty or failed results if docintel_fallback is provided.
    """
    if force_docintel:
        start = time.perf_counter()
        try:
            result = await run_in_threadpool(getattr(primary.client, method_name), source)
        except Exception as err:  # noqa: BLE001
            logger.error(
                "docintel_forced_failed",
                extra={"extraction_method": primary.extraction_method},
                exc_info=True,
            )
            raise ConversionError(str(err)) from err
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "conversion_succeeded",
            extra={"extraction_method": primary.extraction_method, "duration_ms": duration_ms},
        )
        return (
            result.text_content,
            primary.extraction_method,
            getattr(result, "title", None),
        )

    primary_result = None
    primary_error: Exception | None = None
    start = time.perf_counter()
    try:
        primary_result = await run_in_threadpool(getattr(primary.client, method_name), source)
    except Exception as err:  # noqa: BLE001 (markitdown raises assorted converter errors)
        primary_error = err
        logger.error(
            "primary_extraction_failed",
            extra={"extraction_method": primary.extraction_method},
            exc_info=True,
        )
    primary_duration_ms = round((time.perf_counter() - start) * 1000, 2)

    primary_has_content = (
        primary_result is not None
        and primary_result.text_content
        and primary_result.text_content.strip()
    )
    if primary_has_content:
        logger.info(
            "conversion_succeeded",
            extra={
                "extraction_method": primary.extraction_method,
                "duration_ms": primary_duration_ms,
            },
        )
        return (
            primary_result.text_content,
            primary.extraction_method,
            getattr(primary_result, "title", None),
        )

    if docintel_fallback is None:
        if primary_error is not None:
            raise ConversionError(str(primary_error)) from primary_error
        logger.warning(
            "empty_extraction_no_fallback",
            extra={"extraction_method": primary.extraction_method},
        )
        return (
            primary_result.text_content,
            primary.extraction_method,
            getattr(primary_result, "title", None),
        )

    reason = "empty extraction" if primary_error is None else "extraction failed"
    logger.info(
        "docintel_fallback_triggered",
        extra={"reason": reason, "extraction_method": docintel_fallback.extraction_method},
    )
    start = time.perf_counter()
    try:
        fallback_result = await run_in_threadpool(
            getattr(docintel_fallback.client, method_name), source
        )
    except Exception as err:  # noqa: BLE001
        logger.error(
            "docintel_fallback_failed",
            extra={"extraction_method": docintel_fallback.extraction_method},
            exc_info=True,
        )
        raise ConversionError(str(err)) from err
    fallback_duration_ms = round((time.perf_counter() - start) * 1000, 2)

    extraction_method = f"{docintel_fallback.extraction_method} (fallback after {reason})"
    logger.info(
        "conversion_succeeded",
        extra={"extraction_method": extraction_method, "duration_ms": fallback_duration_ms},
    )
    return fallback_result.text_content, extraction_method, getattr(fallback_result, "title", None)


__all__ = [
    "ConversionError",
    "UnsafeUrlError",
    "convert_upload_to_markdown",
    "convert_url_to_markdown",
]
