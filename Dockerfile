FROM python:3.12-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY src/ src/
RUN uv sync --no-dev

RUN useradd --create-home appuser
USER appuser

EXPOSE 8490

CMD ["uv", "run", "uvicorn", "markitdown_api.main:app", "--host", "0.0.0.0", "--port", "8490"]
