---
name: python-conventions
description: General Python style and typing conventions for this project. Use whenever writing or editing any .py file in the repo.
---

# Python Conventions

## Typing

- Every function and method signature has full type hints, including the return type (`-> None` where applicable).
- Use built-in generics (`list[str]`, `dict[str, int]`) over `typing.List`/`typing.Dict` — target Python is 3.10+.
- Avoid `Any` at module boundaries (public functions, service entry points). It's acceptable internally for narrow, well-commented cases only.

## Data structures

- Prefer Pydantic models over raw dicts/tuples for any data that crosses a function boundary between layers (`api` → `service` → `core`). Local, single-function-scope dicts are fine.
- Prefer dataclasses (`@dataclass(slots=True)`) over plain classes for simple internal value objects that don't need Pydantic validation.

## Naming

- `snake_case` for functions, variables, modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for module-level constants.
- Boolean-returning functions/attributes use `is_`/`has_`/`can_` prefixes (`is_supported_format`, `has_docintel_config`).
- File names are lowercase with underscores, matching the primary symbol they define where practical.

## Style and formatting

- Formatting and import sorting are handled by `ruff format` / `ruff check --fix` — don't hand-format or hand-sort imports against its output.
- Line length 100 (see `pyproject.toml`).
- No bare `except:`; catch specific exception types. Re-raise with context (`raise X(...) from err`) when translating an exception across a layer boundary.

## Async

- Don't mix blocking I/O (file reads, network calls, markitdown conversion of large files) into `async def` functions without offloading to a thread — use `starlette.concurrency.run_in_threadpool` or `asyncio.to_thread`.

## Comments and docstrings

- No comments restating what the code does. Only comment non-obvious *why* (a workaround, a constraint from markitdown's API, a security-relevant restriction).
- Public service functions get a one-line docstring describing behavior, not an essay.
