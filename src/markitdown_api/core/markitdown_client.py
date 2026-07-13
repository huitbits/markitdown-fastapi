"""The only module allowed to construct MarkItDown instances."""

from dataclasses import dataclass

from markitdown import MarkItDown

from markitdown_api.core.config import Settings

_LLM_PROVIDER_LABELS = {"openai": "OpenAI"}


@dataclass(slots=True)
class MarkitdownClientBuild:
    client: MarkItDown
    extraction_method: str


def build_primary_client(
    settings: Settings,
    *,
    enable_plugins: bool = False,
    use_llm_captions: bool = False,
) -> MarkitdownClientBuild:
    """Build the default client (built-in converters only, never Document Intelligence)."""
    kwargs: dict = {"enable_plugins": enable_plugins}
    methods: list = ["MarkItDown (built-in converters)"]

    if use_llm_captions and settings.has_llm_config:
        kwargs["llm_client"] = _build_llm_client(settings)
        kwargs["llm_model"] = settings.llm_model
        methods.append(_llm_caption_label(settings))

    if enable_plugins:
        methods.append("third-party plugins")

    client = MarkItDown(**kwargs)
    return MarkitdownClientBuild(client=client, extraction_method=" + ".join(methods))


def build_docintel_fallback_client(
    settings: Settings,
    *,
    use_llm_captions: bool = False,
) -> MarkitdownClientBuild | None:
    """Build a Document Intelligence client for fallback use, or None if unconfigured."""
    if not settings.has_docintel_config:
        return None

    kwargs: dict = {"enable_plugins": False, "docintel_endpoint": settings.azure_docintel_endpoint}
    methods = ["Microsoft Document Intelligence"]

    if use_llm_captions and settings.has_llm_config:
        kwargs["llm_client"] = _build_llm_client(settings)
        kwargs["llm_model"] = settings.llm_model
        methods.append(_llm_caption_label(settings))

    client = MarkItDown(**kwargs)
    return MarkitdownClientBuild(client=client, extraction_method=" + ".join(methods))


def _llm_caption_label(settings: Settings) -> str:
    provider_label = _LLM_PROVIDER_LABELS.get(settings.llm_provider, settings.llm_provider)
    return f"LLM image captioning ({provider_label}/{settings.llm_model})"


def _build_llm_client(settings: Settings):
    if settings.llm_provider == "openai":
        from openai import OpenAI

        return OpenAI(api_key=settings.llm_api_key)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
