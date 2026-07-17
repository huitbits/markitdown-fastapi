---
name: pull-request-creation
description: Use when creating or suggesting Pull Requests (PRs). Enforces title guidelines, description structure, issue linking, local verification, and GitHub CLI PR creation.
---

# Pull Request Creation Skill

This skill defines the guidelines, checklist, and technical workflow for opening and filling out Pull Requests (PRs) in this project. The goal is to ensure every change is documented transparently, easing code review and historical traceability.

## 1. Pull Request Guidelines

### PR Title

The PR title must follow **Conventional Commits** format:

- Format: `<type>(<scope>): <short lowercase description>`
- Examples:
  - `feat(api): add docx conversion endpoint`
  - `fix(core): resolve SSRF bypass on redirect`
  - `docs(readme): document MARKITDOWN_FASTAPI_TOKEN`
- Accepted types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

### PR Description

- **Golden rule**: the mandatory canonical PR template is [.github/pull_request_template.md](../../../.github/pull_request_template.md). GitHub pre-fills it automatically when opening a PR through the web UI; when opening via `gh pr create --body-file`, read that template and fill it in fully yourself.
- Fill in every section: `Type of change`, `Changes`, `Architecture checklist`, `Security checklist`, `Quality checklist`, and `Test plan`. Check off only items you actually verified.

### Relation to Issues (Auto-linking)

Always explicitly link the corresponding GitHub issue in the PR body using GitHub keywords (e.g. `Closes #XX` or `Fixes #XX`) so the issue closes automatically on merge.

## 2. Pre-PR Checklist (Local Validation)

Before opening the Pull Request, run and confirm:

- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format .` applied.
- [ ] `uv run pytest` passes.
- [ ] No secrets, passwords, or tokens exposed in the diff.
- [ ] No changes outside the planned scope were included.

## 3. Creating the PR via GitHub CLI (`gh`)

When asked to open a PR automatically:

1. Make sure the branch's changes are committed and pushed.
2. Save the PR body to a temporary file in the scratchpad directory to avoid shell-escaping issues.
3. Use the Bash tool prefixed with `rtk`.
4. Run the command in this format:
   ```bash
   rtk gh pr create --title "<type>(<scope>): pr title" --body-file /path/to/pr_body.md
   ```
5. Report the created PR link to the user.
