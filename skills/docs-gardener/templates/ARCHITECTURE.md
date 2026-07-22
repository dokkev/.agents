# Architecture

This document records the accepted direction of the codebase. Keep current
implementation and intended direction distinct when a migration is incomplete.

## Scope

Describe what this repository owns and what remains outside its boundary.

## Code direction

State the few durable principles that should guide implementation and review.

- Describe the intended ownership model.
- Describe the intended dependency direction.
- Describe important constraints on control flow, hardware access, or middleware.

## Components and ownership

| Path | Role |
| --- | --- |
| Replace with a real path | Describe its responsibility and owned state |

## Dependency direction

Describe which layers may depend on which other layers. Call out dependencies
that are intentionally forbidden.

## Runtime or data flow

Describe the main runtime path at the level needed to preserve code direction.

```text
input or state source
-> owning subsystem
-> computation or coordination
-> output boundary
```

## Public boundaries

| Interface | Producer | Consumer | Notes |
| --- | --- | --- | --- |
| Replace with a real interface | | | |

## Constraints and rationale

Record only rationale needed to preserve a code direction or boundary. Keep it
beside the rule it explains rather than maintaining a chronological decision log.

## Current deviations

List only known places where current code has not yet reached the accepted
direction. Remove entries when they are resolved; do not use this section as a
general backlog.

## Related documents

* `docs/COMMANDS.md`
