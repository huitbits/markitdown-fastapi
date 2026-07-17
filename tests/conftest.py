from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from markitdown_api.core.config import get_settings
from markitdown_api.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Settings() reads a local .env file if present. Force known-empty values so a
# developer's own .env (e.g. with a real bearer token or Azure/LLM config) never
# leaks into the test suite — env vars take precedence over the dotenv file.
_ISOLATED_ENV_VARS = {
    "MARKITDOWN_ENABLE_PLUGINS": "false",
    "MARKITDOWN_FASTAPI_TOKEN": "",
    "AZURE_DOCINTEL_ENDPOINT": "",
    "LLM_PROVIDER": "",
    "LLM_API_KEY": "",
    "LLM_MODEL": "",
    "LOG_LEVEL": "INFO",
}


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch):
    for name, value in _ISOLATED_ENV_VARS.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
