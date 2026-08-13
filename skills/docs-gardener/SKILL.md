---
name: docs-gardener
description: Maintain a small, accurate repository harness centered on AGENTS.md, docs/ARCHITECTURE.md, and docs/COMMANDS.md, and create Doxygen-style API documentation when explicitly requested. Use when the user asks to document code direction, ownership, dependencies, runtime flow, compilation commands, source/build/install locations, repo-specific agent guidance, stale documentation, a minimal harness, or Doxygen comments for a repository.
---

# Docs Gardener

Keep repository docs small and trustworthy. Record durable direction and
reproducible build knowledge, not session history.

## Workflow

1. Read the closest `AGENTS.md` and only the authoritative documents touched by
   the request: `docs/ARCHITECTURE.md` for code direction and
   `docs/COMMANDS.md` for compilation or build locations.
2. Compare claims with relevant source, builds, scripts, config, tests, and
   observed behavior.
3. Classify each gap as stale, missing, duplicated, misplaced, or unverifiable.
4. Update the smallest authoritative document for the knowledge.
5. Verify paths and commands when practical; never call an unexecuted command
   verified.
6. Remove obsolete guidance instead of preserving it as history.

## Sub-agent Delegation

Default to one agent. Delegate independent evidence collection across
non-overlapping sources with exact facts and paths to verify.
Keep one editor per authoritative document; the parent verifies and integrates.
Do not recursively delegate by default.

For a Markdown document over 100 lines, list its H2 sections before reading it:

```bash
python3 "$DOCS_GARDENER_DIR/scripts/read_reference.py" \
  docs/ARCHITECTURE.md --list
python3 "$DOCS_GARDENER_DIR/scripts/read_reference.py" docs/ARCHITECTURE.md \
  --section "Runtime Flow" --section "Hardware Boundary"
```

Set `DOCS_GARDENER_DIR` to this skill directory, then run from the target repo.
Read the full document only to review or restructure it, reconcile several
sections, or resolve cross-section conflicts.

## Requested API Documentation

Create Doxygen-style docs only when explicitly requested; never add them as an
automatic follow-up.

When requested, read [references/doxygen.md](references/doxygen.md) as the only
skill reference. Preserve local comment syntax, document contracts at
declarations, avoid duplicate prose at definitions, and do not change behavior.

## What To Maintain

- `AGENTS.md`: short repo-specific rules, entry points, and links to authoritative
  documents.
- `docs/ARCHITECTURE.md`: accepted direction, responsibility, ownership,
  dependencies, runtime flow, and public boundaries; distinguish current and
  target structure during migration.
- `docs/COMMANDS.md`: exact compilation commands and their source, build,
  install, and output locations.
- `README.md`: human introduction and basic usage when already authoritative.
- Optional focused documents only when stable reusable knowledge justifies them.

Do not create `PLANS.md` or `DECISIONS.md` by default. Keep temporary plans in
the task and durable rationale beside the architecture.

## Repo Harness Template

Use the bundled template only when explicitly asked to create a repo harness.

Use `templates/`, `scripts/install_repo_harness.py`, and the current-workspace
wrapper `scripts/install_repo_harness_here.sh`. They create root `AGENTS.md`,
`docs/ARCHITECTURE.md`, and `docs/COMMANDS.md`.

Prefer the installer for a new repo:

```bash
python3 "$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness.py" <repo-root>
```

To install into the current workspace:

```bash
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh" --dry-run
"$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness_here.sh"
```

Run `--dry-run` first. The installer creates only missing files and never
overwrites existing docs. Replace template prompts with repository facts.

## Rules

- Do not turn `AGENTS.md` into a large manual. Keep it as a map.
- Keep repo-level `AGENTS.md` at the root.
- Store harness templates in `templates/`; map its `AGENTS.md` to the repo root
  and other templates to `docs/`.
- Generate harness docs under `docs/`, but not a primary `docs/AGENTS.md`.
- Do not create a document solely to fill a standard list.
- Do not use `PLANS.md` as a backlog or status archive, or `DECISIONS.md` as a
  chronological log.
- Keep rationale beside the boundary it explains.
- Keep `COMMANDS.md` focused on compilation and build locations.
- Do not preserve stale docs just because they are detailed.
- Prefer a small update to an existing authority over a new document.
- Keep docs actionable; prefer links and indexes over duplication.
- Mark uncertainty explicitly when code behavior cannot be verified.
- Update docs when code direction, public boundaries, ownership, dependencies,
  or compilation changes—not for every implementation diff.
- Do not add Doxygen comments unless the user explicitly requests API or
  Doxygen-style documentation.

Report the documents examined or changed, evidence, and remaining gaps.
