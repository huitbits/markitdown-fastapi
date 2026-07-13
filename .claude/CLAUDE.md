# markitdown-fastapi — Project Directives

This project wraps Microsoft's [markitdown](https://github.com/microsoft/markitdown) library behind a FastAPI HTTP API. It is open source under the MIT license.

## Language

All code, comments, docstrings, commit messages, PR descriptions, and documentation MUST be written in English (en-us). No exceptions, regardless of the language used in conversation.

## Tooling

- Python 3.10+ (matches markitdown's own minimum supported version).
- Dependency management via `uv`. Use `uv sync` to install, `uv run <cmd>` to execute anything in the project environment. Do not use bare `pip install`.
- Lint and format with `ruff` (`uv run ruff check .`, `uv run ruff format .`). Fix lint issues before considering a change done.
- Type hints are required on all function signatures, including return types. Prefer Pydantic models over raw `dict`/`Any` at any API or service boundary.
- Tests with `pytest` (`uv run pytest`). Every new endpoint or service function needs a corresponding test.

## Architecture

Layered structure, dependencies flow one direction only:

```
api/ (routes)  →  services/ (business logic)  →  core/ (config, markitdown client)
                          ↓
                     schemas/ (Pydantic I/O models, referenced by both api/ and services/)
```

- Route handlers in `api/` stay thin: parse/validate input, call a service, shape the response. No markitdown calls or business logic directly in route handlers.
- `services/` holds conversion logic and orchestrates the markitdown client.
- `core/markitdown_client.py` is the only place that constructs/configures `MarkItDown` instances.
- `core/config.py` centralizes all environment-derived settings via `pydantic-settings`. Never read `os.environ` directly elsewhere.

## Security

markitdown's own docs warn that `convert()` is permissive by design. Since this API accepts user-supplied files and URLs:

- Validate and restrict any user-supplied URL before passing it to markitdown: allow only `http`/`https` schemes, and block requests to private, loopback, and cloud metadata-service IP ranges (SSRF guardrail) before conversion.
- Enforce `MAX_UPLOAD_SIZE_BYTES` on file uploads.
- Never pass user-supplied local file paths straight through — uploads must be written to a controlled temp location, never resolved against attacker-controlled paths.
- Auth is opt-in via `MARKITDOWN_FASTAPI_TOKEN` (see `core/security.py`): when set, it's required as a Bearer token on every router except `health`; when unset, those routes stay open. Any new router besides `health` must include `dependencies=[Depends(require_token)]`.

## Licensing

Project is MIT licensed (see `LICENSE` at repo root). Do not add per-file license headers — the root license covers the whole repository. Do not add or vendor code from sources with incompatible licenses.

## Skills

See `.claude/skills/` for FastAPI and Python convention skills that apply throughout this repo.
