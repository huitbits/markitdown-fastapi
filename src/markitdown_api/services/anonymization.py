"""PII anonymization business logic, orchestrating the Presidio client."""

from typing import Any

from markitdown_api.core.anonymization_client import analyze_and_anonymize
from markitdown_api.schemas.anonymize import (
    AnonymizeJsonResponse,
    AnonymizeResponse,
    DetectedEntity,
)


def anonymize_content(text: str) -> AnonymizeResponse:
    """Redact PII in raw text, HTML, or Markdown alike (offset-based, markup-preserving)."""
    result = analyze_and_anonymize(text)
    entities = [
        DetectedEntity(entity_type=e.entity_type, start=e.start, end=e.end, score=e.score)
        for e in result.entities
    ]
    return AnonymizeResponse(anonymized=result.text, entities_found=entities)


def anonymize_json_value(data: Any) -> AnonymizeJsonResponse:
    """Recursively redact PII in every string leaf of a JSON-like structure."""
    entities: list[DetectedEntity] = []
    anonymized = _walk(data, path="", entities=entities)
    return AnonymizeJsonResponse(anonymized=anonymized, entities_found=entities)


def _walk(value: Any, path: str, entities: list[DetectedEntity]) -> Any:
    if isinstance(value, str):
        result = analyze_and_anonymize(value)
        entities.extend(
            DetectedEntity(
                entity_type=e.entity_type, start=e.start, end=e.end, score=e.score, path=path
            )
            for e in result.entities
        )
        return result.text
    if isinstance(value, dict):
        return {
            key: _walk(item, f"{path}.{key}" if path else str(key), entities)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_walk(item, f"{path}[{index}]", entities) for index, item in enumerate(value)]
    return value


__all__ = ["anonymize_content", "anonymize_json_value"]
