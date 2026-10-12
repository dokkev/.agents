# Code Review

Use for a review or assessment included in the task contract from `SKILL.md`.
That contract and project instructions determine review independence, fix
permission, and execution scope; this reference does not impose another gate.

## Scope and Evidence

Review the actual diff and enough direct callers to understand the changed
behavior. Keep the review pass read-only. Classify each supported finding by:

- precise file and location;
- violated behavior or contract;
- concrete input, state, timing condition, or call path;
- consequence and smallest useful correction.

Separate unknown assumptions from demonstrated defects. Treat architecture
docs as a map to check against source, not unquestionable truth. Do not reopen
accepted design decisions or convert a local review into redesign.

## Priorities

Look first for correctness and hardware safety, then failure behavior, numerical
validity, units/frames/timing, and ownership/lifetime. Examine concurrency and
runtime costs only on paths where they matter. Use only the domain references
needed to resolve an actual question.

For Python, notice duplicated calculations or representations, unnecessary
forwarding layers, hidden heavy imports, and abstraction without a current
owner or boundary. Do not demand new types or helpers just for stylistic symmetry.

For control code, preserve complete fallback commands, fresh coherent state,
single-owner history and reset semantics, bounded repeated work, and the
distinction between produced and hardware-applied commands.

| Severity | Meaning |
| --- | --- |
| Critical | Credible unsafe behavior, data loss, or unusable core behavior |
| High | Concrete correctness, numerical, race, or failure-handling defect |
| Medium | Fragile contract with a realistic incorrect-behavior consequence |
| Low | Local clarity issue with limited consequence; not a blocker by default |

Do not inflate severity for a preference or missing speculative infrastructure.
A lack of extra tests is not itself a defect without a concrete unprotected risk.

## Report and Stop

Lead with actionable findings, then unresolved assumptions and unreviewed scope.
State whether review was self-review or independent when relevant. If required
independence was unavailable, report the gap instead of claiming approval.

If no supported finding remains, say so. Do not invent follow-up work. Re-check
only a corrected blocker and its affected path when a re-check is warranted;
do not restart the entire review or repeat valid experiment results.
