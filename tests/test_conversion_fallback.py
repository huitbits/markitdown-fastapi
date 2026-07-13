"""Unit tests for the docintel-as-fallback orchestration in services/conversion.py.

Uses stub clients (not real MarkItDown/Azure calls) to isolate the fallback branching logic.
"""

import pytest

from markitdown_api.core.markitdown_client import MarkitdownClientBuild
from markitdown_api.services.conversion import ConversionError, _convert_with_fallback


class _StubResult:
    def __init__(self, text_content: str, title: str | None = None) -> None:
        self.text_content = text_content
        self.title = title


class _StubClient:
    def __init__(self, *, result: _StubResult | None = None, error: Exception | None = None):
        self._result = result
        self._error = error

    def convert_local(self, source: str) -> _StubResult:
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result

    convert = convert_local


def _build(client: _StubClient, method: str) -> MarkitdownClientBuild:
    return MarkitdownClientBuild(client=client, extraction_method=method)


async def test_uses_primary_when_content_present() -> None:
    primary = _build(_StubClient(result=_StubResult("# Hello")), "MarkItDown (built-in converters)")

    markdown, method, _ = await _convert_with_fallback("src", "convert_local", primary, None)

    assert markdown == "# Hello"
    assert method == "MarkItDown (built-in converters)"


async def test_falls_back_when_primary_returns_empty() -> None:
    primary = _build(_StubClient(result=_StubResult("")), "MarkItDown (built-in converters)")
    fallback = _build(
        _StubClient(result=_StubResult("# From Azure")), "Microsoft Document Intelligence"
    )

    markdown, method, _ = await _convert_with_fallback("src", "convert_local", primary, fallback)

    assert markdown == "# From Azure"
    assert method == "Microsoft Document Intelligence (fallback after empty extraction)"


async def test_falls_back_when_primary_raises() -> None:
    primary = _build(_StubClient(error=RuntimeError("boom")), "MarkItDown (built-in converters)")
    fallback = _build(
        _StubClient(result=_StubResult("# From Azure")), "Microsoft Document Intelligence"
    )

    markdown, method, _ = await _convert_with_fallback("src", "convert_local", primary, fallback)

    assert markdown == "# From Azure"
    assert method == "Microsoft Document Intelligence (fallback after extraction failed)"


async def test_no_fallback_configured_returns_empty_result() -> None:
    primary = _build(_StubClient(result=_StubResult("")), "MarkItDown (built-in converters)")

    markdown, method, _ = await _convert_with_fallback("src", "convert_local", primary, None)

    assert markdown == ""
    assert method == "MarkItDown (built-in converters)"


async def test_no_fallback_configured_raises_on_primary_error() -> None:
    primary = _build(_StubClient(error=RuntimeError("boom")), "MarkItDown (built-in converters)")

    with pytest.raises(ConversionError):
        await _convert_with_fallback("src", "convert_local", primary, None)


async def test_fallback_error_raises_conversion_error() -> None:
    primary = _build(_StubClient(result=_StubResult("")), "MarkItDown (built-in converters)")
    fallback = _build(
        _StubClient(error=RuntimeError("azure down")), "Microsoft Document Intelligence"
    )

    with pytest.raises(ConversionError):
        await _convert_with_fallback("src", "convert_local", primary, fallback)
