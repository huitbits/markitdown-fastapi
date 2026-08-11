from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ConvertUrlRequest(BaseModel):
    url: HttpUrl = Field(
        description="Remote http(s) URL to fetch and convert. Private, loopback, and "
        "cloud metadata-service network ranges are blocked.",
        examples=["https://example.com/report.docx"],
    )
    enable_plugins: bool = Field(
        default=False, description="Enable third-party markitdown plugins for this conversion."
    )
    use_docintel: bool = Field(
        default=False,
        description="Retry with Azure Document Intelligence as a fallback if the built-in "
        "converters fail or return empty markdown. Requires AZURE_DOCINTEL_ENDPOINT.",
    )
    use_llm_captions: bool = Field(
        default=False, description="Caption embedded images using the configured LLM provider."
    )
    anonymize: bool = Field(
        default=False,
        description="Redact Brazilian PII from the resulting markdown before returning it.",
    )


class ConversionMetadata(BaseModel):
    source_type: Literal["upload", "url"] = Field(
        description="Whether the content came from a file upload or a remote URL."
    )
    source: str = Field(description="Original filename or URL")
    title: str | None = Field(default=None, description="Document title, when extractable.")
    extraction_method: str = Field(
        description="Engine(s) used to extract content, e.g. 'Microsoft Document Intelligence' "
        "or 'MarkItDown (built-in converters) + LLM image captioning (OpenAI/gpt-4o-mini)'"
    )


class ConvertResponse(BaseModel):
    markdown: str = Field(description="Converted content in Markdown format.")
    metadata: ConversionMetadata


class BatchItemResult(BaseModel):
    source: str = Field(description="Original filename or URL that produced this result.")
    success: bool = Field(description="Whether this individual item converted successfully.")
    markdown: str | None = Field(
        default=None, description="Converted markdown, present only when success is true."
    )
    extraction_method: str | None = Field(
        default=None,
        description="Engine(s) used to extract content, present only when success is true.",
    )
    error: str | None = Field(
        default=None, description="Error message, present only when success is false."
    )


class BatchConvertResponse(BaseModel):
    results: list[BatchItemResult] = Field(
        description="One result per submitted file/URL, in the order files were provided "
        "followed by URLs."
    )
