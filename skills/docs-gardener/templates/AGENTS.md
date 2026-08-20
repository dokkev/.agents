# AGENTS.md

Keep this file focused on repository-specific working rules and links to the
authoritative repository documents.

Read detailed sources only when relevant:

- `docs/ARCHITECTURE.md` for the navigational map of the current accepted
  codebase, including canonical entry points, ownership, dependencies, runtime
  flow, public boundaries, and intentional absences.
- `docs/COMMANDS.md` when compilation, validation, environments, or
  build/source/install/output locations matter.

If a document is absent or stale, inspect the repository instead of assuming
its contents.

For documents over 100 lines, inspect H2 headings and read only relevant
sections. Read the full document when editing it or resolving cross-section
contracts.

Task authority:

- Explanation, diagnosis, and review are read-only unless changes are requested.
- Implementation changes only the requested behavior and directly required files.
- Do not add or run tests, broaden validation, or chain modes unless the user or
  current repository workflow explicitly requests that work.
- Architecture work proposes boundaries; it does not authorize implementation.
- Review independence is project-specific. A repository may permit self-review
  or require independent non-author review. Follow the current project rules and
  do not describe self-review as independent review.

Guidelines:

- Keep this file short.
- Put detailed repository structure under `docs/ARCHITECTURE.md`.
- Put exact commands and environment knowledge under `docs/COMMANDS.md`.
- Default to one agent. Delegate only bounded independent work with explicit,
  non-overlapping write ownership; do not recursively delegate by default.
- Delegation does not expand task authority.
- Prefer small, reviewable diffs.
- Preserve existing behavior unless explicitly asked to change it.
- When build or validation is requested, use the documented locations and
  commands from `docs/COMMANDS.md`.
- If validation cannot be run, clearly state what was not verified.
