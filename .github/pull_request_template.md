## Summary

<!-- What does this PR change and why? One or two sentences. -->

## Related issue

<!-- Closes #123, or "N/A" -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change (existing behavior changes or API contract changes)
- [ ] Refactor (no behavior change)
- [ ] Documentation
- [ ] CI/CD / tooling

## Changes

<!-- Bullet list of concrete changes, file/module level is fine. -->

-

## Architecture checklist

- [ ] Route handlers in `api/` stay thin (no markitdown calls or business logic in routes)
- [ ] Business logic lives in `services/`
- [ ] `MarkItDown` instances are only constructed in `core/markitdown_client.py`
- [ ] New env-derived config goes through `core/config.py` (`Settings`), not raw `os.environ`
- [ ] New I/O models are Pydantic models in `schemas/`, not raw `dict`/`Any`

## Security checklist

- [ ] User-supplied URLs are still validated by `ensure_public_http_url` (SSRF guard) before conversion
- [ ] Upload size is still bounded by `MAX_UPLOAD_SIZE_BYTES`
- [ ] No user-supplied path is passed straight to the filesystem (uploads go through a controlled temp file)
- [ ] Any new router besides `health` includes `dependencies=[Depends(require_token)]`
- [ ] No secrets, tokens, or `.env` contents committed or logged

## Quality checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` applied
- [ ] `uv run pytest` passes
- [ ] Type hints on all new/changed function signatures, including return types
- [ ] New endpoint or service function has a corresponding test
- [ ] `README.md` / `.env.example` updated if config, endpoints, or behavior changed
- [ ] Code, comments, and this PR description are in English (en-us)

## Test plan

<!-- How did you verify this? Commands run, manual curl calls, etc. -->

## Screenshots / sample output

<!-- Optional: curl + JSON response, API docs screenshot, etc. -->
