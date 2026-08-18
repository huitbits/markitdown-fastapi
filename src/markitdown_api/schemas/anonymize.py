from typing import Any

from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    entity_type: str = Field(
        description="PII category detected, e.g. PERSON, EMAIL_ADDRESS, CPF, CNPJ, RG, "
        "PHONE_NUMBER_BR, ORGANIZATION, LOCATION, CEP, PROCESS_NUMBER_CNJ, VEHICLE_PLATE_BR.",
        examples=["CPF"],
    )
    start: int = Field(description="Start character offset of the match in the original content.")
    end: int = Field(description="End character offset (exclusive) of the match.")
    score: float = Field(description="Detector confidence score, from 0.0 to 1.0.")
    path: str | None = Field(
        default=None, description="Dotted JSON path, only set for /anonymize/json"
    )


class AnonymizeTextRequest(BaseModel):
    text: str = Field(
        description="Plain text to scan for Brazilian PII.",
        examples=["Meu nome é João Silva, CPF 123.456.789-09"],
    )


class AnonymizeHtmlRequest(BaseModel):
    html: str = Field(
        description="HTML content to scan for Brazilian PII. Surrounding markup is preserved "
        "since redaction operates on character offsets."
    )


class AnonymizeMarkdownRequest(BaseModel):
    markdown: str = Field(
        description="Markdown content to scan for Brazilian PII. Surrounding markup is "
        "preserved since redaction operates on character offsets."
    )


class AnonymizeJsonRequest(BaseModel):
    data: Any = Field(
        description="Arbitrary JSON value. Every string leaf is scanned and redacted "
        'recursively, e.g. {"user": {"email": "joao@example.com"}}.'
    )


class AnonymizeResponse(BaseModel):
    anonymized: str = Field(description="Content with detected PII replaced by entity tags.")
    entities_found: list[DetectedEntity] = Field(
        description="Every PII match detected before redaction."
    )


class AnonymizeJsonResponse(BaseModel):
    anonymized: Any = Field(
        description="Input JSON value with every detected PII string leaf redacted."
    )
    entities_found: list[DetectedEntity] = Field(
        description="Every PII match detected before redaction, with dotted path."
    )
