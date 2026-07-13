from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ConvertUrlRequest(BaseModel):
    url: HttpUrl
    enable_plugins: bool = False
    use_docintel: bool = False
    use_llm_captions: bool = False


class ConversionMetadata(BaseModel):
    source_type: Literal["upload", "url"]
    source: str = Field(description="Original filename or URL")
    title: str | None = None
    extraction_method: str = Field(
        description="Engine(s) used to extract content, e.g. 'Microsoft Document Intelligence' "
        "or 'MarkItDown (built-in converters) + LLM image captioning (OpenAI/gpt-4o-mini)'"
    )


class ConvertResponse(BaseModel):
    markdown: str
    metadata: ConversionMetadata


class BatchItemResult(BaseModel):
    source: str
    success: bool
    markdown: str | None = None
    extraction_method: str | None = None
    error: str | None = None


class BatchConvertResponse(BaseModel):
    results: list[BatchItemResult]
