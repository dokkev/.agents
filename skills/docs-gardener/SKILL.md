---
name: docs-gardener
description: Maintain a small, accurate repository harness centered on AGENTS.md, docs/ARCHITECTURE.md, and docs/COMMANDS.md, and create Doxygen-style API documentation when explicitly requested. Use when the user asks to document code direction, ownership, dependencies, runtime flow, compilation commands, source/build/install locations, repo-specific agent guidance, stale documentation, a minimal harness, or Doxygen comments for a repository.
---

# Docs Gardener

Keep repository documentation small enough to remain trustworthy. Document durable
code direction and reproducible build knowledge, not session history.

## Workflow

1. Read the closest `AGENTS.md`. Read only the authoritative documents touched
   by the request: `docs/ARCHITECTURE.md` for code direction and
   `docs/COMMANDS.md` for compilation or build locations.
2. Compare the relevant claims with source layout, build files, scripts,
   configuration, tests, and observed behavior.
3. Classify each gap as stale, missing, duplicated, misplaced, or unverifiable.
4. Update the smallest authoritative document for the knowledge.
5. Verify paths and commands when practical. Never label an unexecuted command as
   verified.
6. Remove obsolete guidance instead of preserving it as history.

## Requested API Documentation

Create or revise Doxygen-style code documentation only when the user explicitly
requests Doxygen, API documentation, or documentation comments. Do not add it as
an automatic follow-up to normal documentation gardening or implementation.

When this mode is requested, read [references/doxygen.md](references/doxygen.md)
as the only skill reference. Preserve the repository's established comment
syntax and document contracts at declarations without duplicating the same
prose at definitions. Do not change program behavior while documenting it.

## What To Maintain

- `AGENTS.md`: short repo-specific rules, entry points, and links to authoritative
  documents.
- `docs/ARCHITECTURE.md`: accepted code direction, component responsibility,
  ownership, dependency direction, runtime flow, and public boundaries. When the
  implementation is mid-migration, distinguish current structure from the target
  direction explicitly.
- `docs/COMMANDS.md`: exact compilation commands and the source, build, install,
  and output locations they use.
- `README.md`: human-facing project introduction and basic usage when the
  repository already uses it for those purposes.
- Optional focused documents such as `docs/TESTING.md` only when the repository
  has enough stable, reusable knowledge to justify them.

Do not create `PLANS.md` or `DECISIONS.md` as part of the default harness.
Short-lived plans belong in the active issue, PR, or task. Durable architectural
choices and their necessary rationale belong next to the affected direction in
`ARCHITECTURE.md`.

## Repo Harness Template

Use the bundled template only when the user explicitly asks to install or create
a repo harness. Normal documentation maintenance does not reinstall the harness.

- Template root: `templates/`
- Installer: `scripts/install_repo_harness.py`
- Current-workspace wrapper: `scripts/install_repo_harness_here.sh`

The template creates:

- `AGENTS.md` at the repository root
- `docs/ARCHITECTURE.md`
- `docs/COMMANDS.md`

Prefer the installer for a new repo:

```bash
python3 "$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness.py" <repo-root>
```

To install into the current workspace:

```bash
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh" --dry-run
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh"
```

Run with `--dry-run` first. The installer creates only missing files and never
overwrites existing repository documentation. After installation, replace the
template prompts with facts from the target repository; do not leave a generic
template as the final result.

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
- Do not create a document solely to fill a standard list.
- Do not use `PLANS.md` as a backlog, status log, or completed-work archive.
- Do not use `DECISIONS.md` as a chronological decision log.
- Keep architectural rationale beside the boundary or direction it explains.
- Keep `COMMANDS.md` focused on compilation and build locations rather than
  turning it into a general operational runbook.
- Do not preserve stale docs just because they are detailed.
- Do not create new docs when a small update to an existing authoritative file is clearer.
- Keep docs specific enough for an agent to act on.
- Prefer links and indexes over duplicated guidance.
- Mark uncertainty explicitly when code behavior cannot be verified.
- Do not update docs for every implementation diff. Update them when code
  direction, a public boundary, ownership, dependency flow, or the compilation
  procedure changes.
- Do not add Doxygen comments unless the user explicitly requests API or
  Doxygen-style documentation.
