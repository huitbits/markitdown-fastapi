---
name: branch-creation
description: Use when creating a new development branch. Enforces proper branch naming conventions, sanitization, and step-by-step Git execution workflow.
---

# Branch Creation Skill

This skill establishes the rules and interactive workflow that AI agents must follow whenever the user requests a new development branch for this project.

## 1. Branch Creation Workflow

When the user requests a branch, follow these steps rigorously:

### Step 1: Verify and obtain the issue number

1. Check whether the user provided the GitHub issue number associated with the task.
2. If **not** provided, stop immediately and ask the user for the issue number.

### Step 2: Analyze the issue and context

1. With the issue number, fetch the issue details (via `gh issue view` or context already provided in chat).
2. Analyze the title and description to identify the technical goal and the type of change.

### Step 3: Define the branch name

The branch name must strictly follow these guidelines:

- **Format**: `<type>/<issue-number>/<name-derived-from-title-in-english>`
  - Example: `feat/30/roles-endpoints-authorization`
- **`<type>` definition**: deduced from the issue/task context, one of:
  - `feat`: new functionality.
  - `bug`: bug handling.
  - `fix` or `hotfix`: immediate fixes for production bugs.
  - `enhance`: improvements to existing functionality.
  - `doc`: changes exclusive to documentation (e.g. README, API docs).
  - `ci` or `cicd`: CI/CD configuration and integrations (e.g. workflows, build/deploy scripts).
- **Title sanitization**:
  - The name derived from the title **must be in English**. If the original title is in Portuguese, translate it to English before using it.
  - Keep it concise, words separated exclusively by hyphens (`-`).
  - No special characters or accents. Only alphanumeric characters and `-` are allowed in the final segment of the branch name.

### Step 4: Align on the source branch

Explicitly ask the user in chat:

> _"Should the branch be created from `main` or from the current branch?"_

Depending on the user's choice, run the following Git steps prefixed with `rtk`:

#### If the user chooses `main`:

1. Switch to `main`:
   ```bash
   rtk git checkout main
   ```
2. Pull the latest updates:
   ```bash
   rtk git pull origin main
   ```
3. Create and switch to the new branch from `main`:
   ```bash
   rtk git checkout -b <branch-name>
   ```

#### If the user chooses the current branch:

1. Make sure the current branch is up to date:
   ```bash
   rtk git pull origin <current-branch-name>
   ```
2. Create and switch to the new branch from the current branch:
   ```bash
   rtk git checkout -b <branch-name>
   ```

### Step 5: Create locally and on the remote

After creating the branch locally, push it to the remote for initial sync:

```bash
rtk git push -u origin <branch-name>
```

### Step 6: Error handling

If any Git command fails at any step:

1. **Stop execution immediately**.
2. Do not continue with any subsequent step.
3. Clearly report to the user which command failed and describe the technical error to get further instructions.
