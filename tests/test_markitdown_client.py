from markitdown_api.core.config import Settings
from markitdown_api.core.markitdown_client import (
    build_docintel_fallback_client,
    build_primary_client,
)


def test_primary_default_extraction_method_is_builtin() -> None:
    build = build_primary_client(Settings())
    assert build.extraction_method == "MarkItDown (built-in converters)"


def test_primary_never_uses_docintel() -> None:
    settings = Settings(azure_docintel_endpoint="https://example.cognitiveservices.azure.com/")
    build = build_primary_client(settings)
    assert build.extraction_method == "MarkItDown (built-in converters)"


def test_docintel_fallback_none_when_not_configured() -> None:
    assert build_docintel_fallback_client(Settings()) is None


def test_docintel_fallback_built_when_configured() -> None:
    settings = Settings(azure_docintel_endpoint="https://example.cognitiveservices.azure.com/")
    build = build_docintel_fallback_client(settings)
    assert build is not None
    assert build.extraction_method == "Microsoft Document Intelligence"


def test_primary_llm_captions_appended_when_configured() -> None:
    settings = Settings(llm_provider="openai", llm_api_key="sk-test", llm_model="gpt-4o-mini")
    build = build_primary_client(settings, use_llm_captions=True)
    assert build.extraction_method == (
        "MarkItDown (built-in converters) + LLM image captioning (OpenAI/gpt-4o-mini)"
    )


def test_docintel_fallback_llm_captions_appended_when_configured() -> None:
    settings = Settings(
        azure_docintel_endpoint="https://example.cognitiveservices.azure.com/",
        llm_provider="openai",
        llm_api_key="sk-test",
        llm_model="gpt-4o-mini",
    )
    build = build_docintel_fallback_client(settings, use_llm_captions=True)
    assert build is not None
    assert build.extraction_method == (
        "Microsoft Document Intelligence + LLM image captioning (OpenAI/gpt-4o-mini)"
    )


def test_primary_plugins_appended_when_enabled() -> None:
    build = build_primary_client(Settings(), enable_plugins=True)
    assert build.extraction_method == "MarkItDown (built-in converters) + third-party plugins"
