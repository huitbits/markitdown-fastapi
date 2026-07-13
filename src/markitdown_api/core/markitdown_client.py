"""The only module allowed to construct MarkItDown instances."""

from markitdown import MarkItDown

from markitdown_api.core.config import Settings


def build_markitdown_client(
    settings: Settings,
    *,
    enable_plugins: bool = False,
    use_docintel: bool = False,
    use_llm_captions: bool = False,
) -> MarkItDown:
    kwargs: dict = {"enable_plugins": enable_plugins}

    if use_docintel and settings.has_docintel_config:
        kwargs["docintel_endpoint"] = settings.azure_docintel_endpoint

    if use_llm_captions and settings.has_llm_config:
        kwargs["llm_client"] = _build_llm_client(settings)
        kwargs["llm_model"] = settings.llm_model

    return MarkItDown(**kwargs)


def _build_llm_client(settings: Settings):
    if settings.llm_provider == "openai":
        from openai import OpenAI

        return OpenAI(api_key=settings.llm_api_key)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
