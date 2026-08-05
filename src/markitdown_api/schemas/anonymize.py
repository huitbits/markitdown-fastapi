from typing import Any

from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
    path: str | None = Field(
        default=None, description="Dotted JSON path, only set for /anonymize/json"
    )


class AnonymizeTextRequest(BaseModel):
    text: str


class AnonymizeHtmlRequest(BaseModel):
    html: str


class AnonymizeMarkdownRequest(BaseModel):
    markdown: str


class AnonymizeJsonRequest(BaseModel):
    data: Any


class AnonymizeResponse(BaseModel):
    anonymized: str
    entities_found: list[DetectedEntity]


class AnonymizeJsonResponse(BaseModel):
    anonymized: Any
    entities_found: list[DetectedEntity]
