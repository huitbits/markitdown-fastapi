from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from markitdown_api.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
