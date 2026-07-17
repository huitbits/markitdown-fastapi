---
name: issue-creation
description: Use when creating or suggesting new issues in the repository. Helps guide the interactive interview, template structure, and GitHub CLI creation.
---

# Issue Creation Skill

This skill establishes the format and workflow for AI agents and humans to collaborate on creating new issues in this repository. The goal is to ensure every issue generated is clear and provides a solid basis for the resulting work.

## 1. Issue Naming

Issues do not carry a number in the title (GitHub assigns it automatically).

- Issue title: `[Type]: Descriptive Name` (e.g. `[Fix]: SSRF guard misses IPv6 loopback`)
- Accepted types: `Feat`, `Fix`, `Bug`, `Enhance`, `Doc`, `CI`.

## 2. Issue Template

The standard Markdown template for issues must be read from this skill resource:

- `resources/issue-template.md`

When filling it out, make sure to fill in every placeholder (Context, Requirements, Technical Notes, DoD).

## 3. Interactive Interview Workflow

Before generating and proposing the final issue to the user, the agent must conduct a brief alignment interview in chat:

1. **Initial gathering**: ask objective questions about scope (e.g. _"What's the main goal?", "Which endpoints or layers are affected?"_).
2. **Draft assembly**: consolidate the gathered information into the template above.
3. **User review**: present the Markdown draft in chat and wait for the user's approval or feedback.

## 4. Publishing the Issue via GitHub CLI (`gh`)

If the user approves and requests automatic creation:

1. Use the Bash tool prefixed with `rtk`.
2. Run the command in this format:
   ```bash
   rtk gh issue create --title "[Type]: Issue Title" --body-file /path/to/temp_file.md
   ```
   _Note: save the issue body to a temporary file first (e.g. the scratchpad directory) so `gh` reads it without shell-escaping issues._
