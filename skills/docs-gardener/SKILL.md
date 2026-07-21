---
name: docs-gardener
description: Keep repository knowledge current by comparing docs, AGENTS.md, plans, comments, examples, and code behavior. Use when the user asks to update docs after code changes, find stale documentation, create agent-readable repo maps, prune obsolete guidance, or turn repeated feedback into durable documentation.
---

# Docs Gardener

Treat repository documentation as an agent-readable knowledge system. Prefer short maps that point to authoritative details over one giant instruction file.

## Workflow

1. Identify the knowledge surface: `AGENTS.md`, `README.md`, `docs/`, examples, comments, runbooks, plans, or generated references.
2. Compare documented claims against current code, tests, config, scripts, and observed behavior.
3. Classify gaps as stale, missing, duplicated, misplaced, too broad, or not machine-actionable.
4. Update the smallest durable document that future agents and humans are likely to read.
5. If a rule is repeated often, suggest whether it should become a lint check, test, script, or skill instruction.

## What To Maintain

- `AGENTS.md`: short map, repo-specific entry points, validation commands, and links to deeper docs.
- `docs/ARCHITECTURE.md`: repository shape, boundaries, runtime wiring, and public contracts.
- `docs/COMMANDS.md`: setup, run, test, lint, build, and smoke-check commands.
- `docs/PLANS.md`: current work, next steps, ideas, completed notes, and follow-ups.
- `docs/DECISIONS.md`: stable choices, tradeoffs, and constraints future sessions should preserve.
- Optional deeper docs: generated references, API details, quality notes, or runbooks only when the project has enough complexity to justify them.

## Repo Harness Template

Use the bundled lightweight template when the user asks to create an agent-readable repo harness. It is meant for small projects, vibe-coding sessions, prototypes, or repositories where documentation overhead should stay minimal.

- Template root: `templates/`
- Installer: `scripts/install_repo_harness.py`
- Current-workspace wrapper: `scripts/install_repo_harness_here.sh`

The template creates:

- `AGENTS.md` at the repository root
- `docs/ARCHITECTURE.md`
- `docs/COMMANDS.md`
- `docs/PLANS.md`
- `docs/DECISIONS.md`

Prefer the installer for a new repo:

```bash
python3 "$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness.py" <repo-root>
```

To install into the current workspace, prefer:

```bash
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh" --dry-run
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh"
```

If the global wrapper is installed, use:

```bash
codex-harness --dry-run
codex-harness
```

The wrapper calls:

```bash
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh" --dry-run
```

Run with `--dry-run` first when the target may already contain docs. Existing files are skipped unless `--overwrite` is passed.

## Output Format

For review-only requests:

```text
Reviewed docs:
Stale or missing knowledge:
Recommended updates:
Rules worth automating:
```

For edit requests, report:

```text
Updated files:
What changed:
Why it belongs there:
Remaining documentation gaps:
```

## Rules

- Do not turn `AGENTS.md` into a large manual. Keep it as a map.
- Keep repo-level `AGENTS.md` at the repository root because Codex expects it there.
- Store harness templates in `templates/`; map `templates/AGENTS.md` to repo-root `AGENTS.md` and all other template files to `docs/`.
- Generate harness documents under `docs/`, but do not generate `docs/AGENTS.md` as the primary agent entrypoint.
- If an extra docs-level guide is useful, name it `docs/HARNESS.md` or `docs/CODEX_GUIDE.md`.
- Do not preserve stale docs just because they are detailed.
- Do not create new docs when a small update to an existing authoritative file is clearer.
- Keep docs specific enough for an agent to act on.
- Prefer links and indexes over duplicated guidance.
- Mark uncertainty explicitly when code behavior cannot be verified.
