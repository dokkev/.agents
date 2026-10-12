---
name: docs-gardener
description: >-
  Create or maintain a minimal repository harness: AGENTS.md,
  docs/ARCHITECTURE.md, and docs/COMMANDS.md. Use for repository guidance, stale
  documentation, ownership and runtime maps, build commands and locations, or
  explicitly requested Doxygen/API documentation. Do not run as an automatic
  documentation phase after every code edit.
---

# Docs Gardener

Keep durable repository facts in the smallest existing authoritative document.
Do not create documentation merely to fill a template or record session history.

## Workflow

Follow applicable repository instructions and the request. Read only the docs
and source needed for the changed fact. Reuse still-valid prior evidence.
Compare claims with source, configuration, scripts, or existing results; keep
unverified commands and proposed architecture clearly distinguished from facts.

Update or remove stale text at its owner rather than duplicating it elsewhere.
Check changed paths and links. Do not execute builds, tests, simulations, or
hardware just to document commands; execution follows the task/project policy.

Read relevant Markdown sections directly. Use `scripts/read_reference.py` only
when it helps navigate a long document; there is no mandatory pre-read command.
Default to one agent and one editor per document. Delegate only useful bounded
evidence collection, not repeated verification.

## Knowledge Ownership

| Document | Contents |
| --- | --- |
| `AGENTS.md` | Project-specific scope, cost/safety boundaries, review policy, links |
| `docs/ARCHITECTURE.md` | Current entry points, ownership, dependencies, scientific/runtime flow |
| `docs/COMMANDS.md` | Exact compilation commands and source/build/install/output locations |
| Existing `README.md` | Human introduction and usage |

Use source or project-native test configuration when no authoritative document
exists. Do not invent missing facts. Distinguish current and target architecture
during migration. Update the map only when entry points, ownership, flow, or
public boundaries materially change, not for every diff.

Keep rationale beside its boundary. Do not create `PLANS.md`, `DECISIONS.md`, or
additional focused documents unless the request or durable knowledge warrants it.

## Create a Harness

Only when requested, use `templates/AGENTS.md`, `templates/ARCHITECTURE.md`, and
`templates/COMMANDS.md`. Omit irrelevant sections and replace prompts with facts.
Keep root `AGENTS.md` short; other harness documents belong under `docs/`.

Use the existing installer, which creates missing files without overwriting:

```bash
python3 "$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness.py" <repo-root> --dry-run
python3 "$HOME/.agents/skills/docs-gardener/scripts/install_repo_harness.py" <repo-root>
```

`scripts/install_repo_harness_here.sh` targets the current workspace. A template
change does not update already-installed project instructions; reconcile them
explicitly when requested, without overwriting project-specific policy.

## API Documentation

Only for explicitly requested API/Doxygen work, read
[references/doxygen.md](references/doxygen.md). Preserve local syntax and document
contracts at declarations without duplicate definition prose or behavior changes.

## Finish

Report changed documents, the evidence used, and unresolved facts. Do not call
an unexecuted command verified or schedule unsolicited documentation follow-ups.
