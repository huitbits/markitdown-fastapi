---
name: fastapi-conventions
description: FastAPI route, dependency-injection, and API design conventions for this project. Use when adding or modifying anything under src/markitdown_api/api/.
---

# FastAPI Conventions

## Routes

- All route handlers are `async def`, even if the body is currently synchronous — markitdown conversion calls that block should be run via `run_in_threadpool` (or made async upstream) rather than blocking the event loop directly in a route.
- One router per resource area under `api/v1/endpoints/`, included into `api/v1/router.py`. Do not add routes directly to the app in `main.py`.
- Route handlers only: parse request, call a service function, return the response model. No conversion logic, no direct `MarkItDown()` construction in route files.
- Every route declares an explicit `response_model` (a Pydantic schema from `schemas/`), not a bare `dict`.

## Dependency injection

- Shared resources (settings, a configured markitdown client) are provided via `Depends`, not module-level globals accessed directly inside handlers.
- Prefer function-based dependencies (`Annotated[Settings, Depends(get_settings)]`) over class-based dependencies unless the dependency itself holds significant state.

## Request/response models

- Every endpoint has a dedicated request and response Pydantic model in `schemas/`, even for simple payloads — do not accept or return raw `dict`.
- Use Pydantic v2 (`model_config`, `Field`, validators via `field_validator`), not v1-style `Config` classes.
- File uploads use `UploadFile`; validate content-type/size before handing off to a service.

## Errors

- Raise `HTTPException` with a specific status code and a machine-readable `detail` at the route layer when a service raises a known error type. Do not let raw exceptions from markitdown leak to the client — catch and translate them.
- Use 422 for validation-shaped failures (unsupported format, bad URL), 502/503 for downstream failures (Azure Document Intelligence unreachable), 413 for oversized uploads.

## OpenAPI hygiene

- Give every route a `summary` and, where non-obvious, a short `description`.
- Tag routers logically (`convert`, `health`) so `/docs` stays organized.
