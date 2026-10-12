# Repository Instructions

Keep project-specific rules here. Replace template guidance with established
facts and omit irrelevant sections.

## Context

Use `docs/ARCHITECTURE.md` for current entry points, owners, dependencies, and
runtime/scientific flow. Use `docs/COMMANDS.md` for needed compilation commands
and build locations. If absent or stale, inspect the affected source instead.
Read only relevant sections; no document reader or full-repository survey is
required. Reuse established decisions rather than reopening them.

## Scope and Cost

Implement the requested behavior at its existing owner and preserve unrelated
behavior. Explanation, diagnosis, design, and review are read-only unless edits
are requested. Reuse existing APIs and calculations; avoid speculative layers
or parallel implementations.

Do not add tests, a separate review pass, launches, or broad validation merely
because implementation finished. A safe documented compile-only check is
permitted, not required. Explicit task requirements still apply.

For requested checks, use focused canonical commands. Reuse results whose code,
inputs, configuration, and environment assumptions remain valid. Rerun only
checks invalidated by a fix. Do not repeat FEA, optimization, training, or
hardware work for reassurance. Hardware execution needs explicit authorization
and a clear safety boundary.

## Review and Completion

Default to one agent. Require independent review only when the project or task
specifies it; do not call self-review independent or add repeated reviewer chains.
Delegation never expands scope.

Stop and report a false required assumption, missing contract, or need for a
substantially larger redesign. Report actual checks, results, and unverified
scope. Stop when the requested task is complete.
