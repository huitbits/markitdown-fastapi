# markitdown-fastapi

[![Docker publish](https://github.com/huitbits/markitdown-fastapi/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/huitbits/markitdown-fastapi/actions/workflows/docker-publish.yml)

An open source HTTP API that wraps Microsoft's [markitdown](https://github.com/microsoft/markitdown) library, letting you convert files, URLs, and streams to Markdown over a simple REST interface.

## Features

- Convert local file uploads or remote URLs to Markdown
- Batch conversion endpoint
- Optional Azure Document Intelligence integration for higher-fidelity PDF/office parsing
- Optional LLM-based image captioning during conversion
- Optional markitdown plugin support

## Quick start

### With Docker

```bash
cp .env.example .env
docker compose up --build
```

API docs available at `http://localhost:8490/docs`.

### Locally with uv

```bash
uv sync
cp .env.example .env
uv run uvicorn markitdown_api.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

## Usage

Replace `8000` with `8490` if running via Docker.

```bash
curl -F "file=@document.pdf" http://localhost:8000/api/v1/convert
```

```bash
curl -X POST http://localhost:8000/api/v1/convert/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/report.docx"}'
```

## Configuration

All configuration is via environment variables — see [.env.example](.env.example):

| Variable | Description |
|---|---|
| `MARKITDOWN_ENABLE_PLUGINS` | Enable third-party markitdown plugins |
| `MARKITDOWN_FASTAPI_TOKEN` | When set, all endpoints except `/health` require this value as a Bearer token. Unset = no auth. |
| `AZURE_DOCINTEL_ENDPOINT` | Azure Document Intelligence endpoint for enhanced parsing |
| `LLM_PROVIDER` / `LLM_API_KEY` / `LLM_MODEL` | LLM used for image captioning |
| `MAX_UPLOAD_SIZE_BYTES` | Max accepted upload size |

## Authentication

Authentication is opt-in. Set `MARKITDOWN_FASTAPI_TOKEN` to require a matching Bearer token on every endpoint except `/health`:

```bash
curl -H "Authorization: Bearer $MARKITDOWN_FASTAPI_TOKEN" \
  -F "file=@document.pdf" http://localhost:8000/api/v1/convert
```

Leave it unset for unauthenticated access (e.g. local development, or when auth is handled by a reverse proxy in front of this service).

## Security note

This service is intended to run behind your own trust boundary. If exposing conversion of user-supplied URLs, restrict allowed URI schemes and block requests to private/metadata-service network ranges to avoid SSRF, per markitdown's own [security guidance](https://github.com/microsoft/markitdown#security).

## CI/CD

On every push to `main` and on `v*.*.*` tags, GitHub Actions ([.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml)) runs lint + tests, then builds and pushes a multi-arch image to Docker Hub as `huitbits/markitdown-fastapi`. Requires repo secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (a Docker Hub access token, not your password).

```bash
docker pull huitbits/markitdown-fastapi:latest
```

## Development

```bash
uv sync
uv run ruff check .
uv run pytest
```

## License

[MIT](LICENSE)
