from fastapi import APIRouter, Depends

from markitdown_api.core.security import require_token
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


@router.post("/text", response_model=AnonymizeResponse, summary="Redact PII from plain text")
async def anonymize_text(body: AnonymizeTextRequest) -> AnonymizeResponse:
    return anonymize_content(body.text)


@router.post("/html", response_model=AnonymizeResponse, summary="Redact PII from HTML")
async def anonymize_html(body: AnonymizeHtmlRequest) -> AnonymizeResponse:
    return anonymize_content(body.html)


@router.post("/markdown", response_model=AnonymizeResponse, summary="Redact PII from Markdown")
async def anonymize_markdown(body: AnonymizeMarkdownRequest) -> AnonymizeResponse:
    return anonymize_content(body.markdown)


@router.post("/json", response_model=AnonymizeJsonResponse, summary="Redact PII from a JSON value")
async def anonymize_json(body: AnonymizeJsonRequest) -> AnonymizeJsonResponse:
    return anonymize_json_value(body.data)
