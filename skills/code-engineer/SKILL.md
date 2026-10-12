---
name: code-engineer
description: >-
  Implement, fix, debug, refactor, review, or test Python and C++ research
  software, including robotics, control, simulation, numerical code, ROS 2,
  hardware integration, and configuration. Use for code changes and code
  assessments; preserve the requested scope rather than automatically adding
  review, testing, or redesign.
---

# Code Engineer

Optimize for code a small research team can understand, change, and delete.
Prefer fewer concepts and less indirection, not merely fewer lines. Preserve
correctness, hardware safety, numerical validity, and required runtime bounds.

## Task Contract

Follow applicable repository instructions and the current task. Use these
fallbacks only where they do not specify a different workflow:

- Implement only the requested behavior and directly required files. Review or
  diagnosis is read-only unless fixes are requested. Test design does not
  implicitly authorize execution or production changes.
- Do not automatically add tests, a separate review pass, launches, or broad
  validation to implementation. A cheap, documented compile-only command that
  cannot start software or touch hardware is permitted, not required.
- When checks are requested, run only those justified by the change. Reuse
  existing results whose code, inputs, configuration, and environment assumptions
  remain valid. After a fix, rerun only affected checks. Do not rerun experiments,
  FEA, optimization, training, or hardware work merely for reassurance.
- Default to one agent. Use independent review only when required by the task
  or project; never call self-review independent. Do not chain reviewers to
  obtain an all-PASS result. Delegation never expands scope.
- Stop and report when a required contract is absent or false, or the task needs
  a substantially larger redesign or new research. Do not silently expand it.

References refine implementation choices; they do not redefine this contract.

## Implement at the Owner

Locate the affected implementation, direct callers, and existing calculation,
conversion, or adapter before adding another. Reuse relevant code and prior
results; do not survey the whole repository or reopen settled decisions.

Change behavior where it is owned. Keep one authoritative representation and
convert at real boundaries. Keep mathematics, state transitions, mutation, and
failure decisions visible. Extract helpers for a meaningful operation or real
reuse, not just to shorten the caller. Avoid speculative factories, registries,
compatibility layers, and parallel implementations.

Preserve existing APIs outside scope. When replacing an internal path is part
of the task, migrate its owned callers rather than retaining duplicate logic.
Keep safety checks and units, frames, freshness, timing, and fallback semantics;
remove neither real contracts nor useful boundaries in the name of simplicity.

## Python Defaults

Apply these to every Python implementation, even without opening a reference:

- Use functions for stateless operations. Use a class for real state, lifecycle,
  invariants, or a required interface, not merely as a namespace.
- Reuse existing domain types. Use named records when shared semantics need
  names; keep obvious local unpacking and genuine collections simple. Do not
  create a dataclass for every intermediate result or turn every dict into one.
- Keep one source of truth. Avoid pass-through properties and wrapper chains
  unless they preserve a real public boundary or add meaningful behavior.
- Convert solver, serialization, and framework payloads at their owning boundary.
  When a framework is intrinsic to the algorithm, use it explicitly rather than
  inventing a neutral interface. Keep optional heavy initialization out of imports.

## References When Needed

Read relevant sections directly; no heading-list command or reader is required.
Use `scripts/read_reference.py` optionally for long documents. Ordinary Python
work should not require extra reading. Consult the Python examples for an
ambiguous design choice; consult domain references when changing their contracts.
Do not load unrelated references or treat their examples as required scaffolding.

| Question in the changed behavior | Reference |
| --- | --- |
| Python representation or boundary trade-off | `references/python-code-design.md` |
| Physical quantities and naming | `references/control-variable-naming.md` |
| Units, frames, signs, ordering, timestamps | `references/control-data-conventions.md` |
| Function contracts, mutation, Eigen lifetime | `references/control-function-implementation.md` |
| YAML schema or parsing boundary | `references/yaml-configuration.md` |
| Controller-to-hardware command ownership | `references/hardware-command-boundary.md` |
| Transport, packets, bounded I/O | `references/hardware-io.md` |
| Repeated control path or fallback | `references/control-loop-implementation.md` |
| Geometry, solvers, numerical tolerances | `references/control-numerical-implementation.md` |
| Shared state or asynchronous handoff | `references/control-concurrency.md` |
| Time steps, history, filters, reset | `references/control-discrete-time-implementation.md` |
| Requested review: evidence and severity | `references/review.md` |
| Requested checks: selection and reuse | `references/testing.md` |

## Finish

Report what changed, checks actually performed and their results, and any
blocker or unverified behavior. Mention review independence only when relevant.
Do not imply unrun checks passed. Stop when the requested outcome is complete.
