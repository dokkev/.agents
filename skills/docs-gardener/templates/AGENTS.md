# AGENTS.md

Use this file as the repository map. Read detailed sources only when relevant:

- `docs/ARCHITECTURE.md` for ownership, dependencies, runtime flow, public
  boundaries, or accepted code direction.
- `docs/COMMANDS.md` when compilation, validation, or build/source/install
  locations matter.

If a document is absent or stale, inspect the repository instead of assuming
its contents.

Task authority:

- Explanation, diagnosis, and review are read-only unless changes are requested.
- Implementation changes only the requested behavior and directly required files.
- Do not add or run tests, perform a separate code review, or broaden validation
  unless the user explicitly requests that work.
- Architecture work proposes boundaries; it does not authorize implementation.

Guidelines:

- Keep this file short.
- Put detailed project context under `docs/`.
- Prefer small, reviewable diffs.
- Preserve existing behavior unless explicitly asked to change it.
- When build or validation is requested, use the documented locations and
  commands from `docs/COMMANDS.md`.
- If validation cannot be run, clearly state what was not verified.
