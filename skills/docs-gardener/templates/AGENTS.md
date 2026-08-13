# AGENTS.md

Use this file as the repository map. Read detailed sources only when relevant:

- `docs/ARCHITECTURE.md` for ownership, dependencies, runtime flow, public
  boundaries, or accepted code direction.
- `docs/COMMANDS.md` when compilation, validation, or build/source/install
  locations matter.

If a document is absent or stale, inspect the repository instead of assuming
its contents.

For documents over 100 lines, inspect H2 headings and read only relevant
sections. Read the full document when editing it or resolving cross-section
contracts.

Task authority:

- Explanation, diagnosis, and review are read-only unless changes are requested.
- Implementation changes only the requested behavior and directly required files.
- Do not add or run tests, perform a separate code review, or broaden validation
  unless the user explicitly requests that work.
- An agent may check and correct its own implementation, but only a separate
  non-author agent may review or approve it.
- When implementation and review are both requested, assign them to different
  agents. If no independent reviewer is available, report review as not performed.
- Architecture work proposes boundaries; it does not authorize implementation.

Guidelines:

- Keep this file short.
- Put detailed project context under `docs/`.
- Default to one agent. Delegate only bounded independent work with explicit,
  non-overlapping write ownership; do not recursively delegate by default.
- Delegation does not expand task authority.
- Prefer small, reviewable diffs.
- Preserve existing behavior unless explicitly asked to change it.
- When build or validation is requested, use the documented locations and
  commands from `docs/COMMANDS.md`.
- If validation cannot be run, clearly state what was not verified.
