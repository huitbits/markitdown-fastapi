from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    markitdown_enable_plugins: bool = False
    markitdown_fastapi_token: str | None = None
    azure_docintel_endpoint: str | None = None
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    max_upload_size_bytes: int = 50 * 1024 * 1024
    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value

    @property
    def auth_required(self) -> bool:
        return bool(self.markitdown_fastapi_token)

    @property
    def has_docintel_config(self) -> bool:
        return bool(self.azure_docintel_endpoint)

    @property
    def has_llm_config(self) -> bool:
        return bool(self.llm_provider and self.llm_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
