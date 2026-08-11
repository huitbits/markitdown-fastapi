from fastapi import APIRouter, Depends

from markitdown_api.core.security import AUTH_RESPONSES, require_token
from markitdown_api.schemas.anonymize import (
    AnonymizeHtmlRequest,
    AnonymizeJsonRequest,
    AnonymizeJsonResponse,
    AnonymizeMarkdownRequest,
    AnonymizeResponse,
    AnonymizeTextRequest,
)
from markitdown_api.services.anonymization import anonymize_content, anonymize_json_value

router = APIRouter(prefix="/anonymize", tags=["anonymize"], dependencies=[Depends(require_token)])


@router.post(
    "/text",
    response_model=AnonymizeResponse,
    summary="Redact PII from plain text",
    description="Scans plain text for Brazilian PII (names, e-mails, CPF, CNPJ, RG, phone "
    "numbers) and returns the redacted text alongside every match found.",
    responses=AUTH_RESPONSES,
)
async def anonymize_text(body: AnonymizeTextRequest) -> AnonymizeResponse:
    return anonymize_content(body.text)


@router.post(
    "/html",
    response_model=AnonymizeResponse,
    summary="Redact PII from HTML",
    description="Scans HTML for Brazilian PII and returns it redacted, with surrounding "
    "markup preserved since redaction operates on character offsets rather than "
    "re-serializing the content.",
    responses=AUTH_RESPONSES,
)
async def anonymize_html(body: AnonymizeHtmlRequest) -> AnonymizeResponse:
    return anonymize_content(body.html)


@router.post(
    "/markdown",
    response_model=AnonymizeResponse,
    summary="Redact PII from Markdown",
    description="Scans Markdown for Brazilian PII and returns it redacted, with surrounding "
    "markup preserved since redaction operates on character offsets rather than "
    "re-serializing the content.",
    responses=AUTH_RESPONSES,
)
async def anonymize_markdown(body: AnonymizeMarkdownRequest) -> AnonymizeResponse:
    return anonymize_content(body.markdown)


@router.post(
    "/json",
    response_model=AnonymizeJsonResponse,
    summary="Redact PII from a JSON value",
    description="Recursively scans every string leaf of an arbitrary JSON value for "
    "Brazilian PII and returns it redacted, reporting each match's dotted path "
    "(e.g. `user.email`).",
    responses=AUTH_RESPONSES,
)
async def anonymize_json(body: AnonymizeJsonRequest) -> AnonymizeJsonResponse:
    return anonymize_json_value(body.data)
