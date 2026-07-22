---
name: code-implementer
description: Implement or modify code with small, readable, validated changes. Use for C++, robotics, robot control, simulation, hardware interfaces, communication, numerical code, ROS 2 integration, or other research software where correctness, visible data flow, practical real-time discipline, and newcomer accessibility matter. Do not use this skill to invent a new architecture unless the user requests architectural work.
---

# Code Implementer

Implement the requested behavior with the smallest clear and reviewable change.

## Project Goal

Optimize for a research-lab codebase, not a large-scale production deployment.
The result should be light enough to run and modify in the lab and clear enough
for another student or collaborator to understand without extensive onboarding.

Prefer direct code, established libraries, visible control flow, and a small
number of well-named concepts. Do not add production-scale infrastructure,
frameworks, generic extension systems, background services, or speculative
scalability unless the user or the existing system actually requires them.

This scope does not relax correctness, hardware safety, numerical validity,
determinism on required real-time paths, or honest validation.

## Workflow

1. Read the closest `AGENTS.md`.
2. Read relevant repository maps when present:
   - `docs/ARCHITECTURE.md`
   - `docs/COMMANDS.md`
   - `docs/DECISIONS.md`
   - `docs/PLANS.md`
3. Inspect the existing implementation, tests, and local style before proposing
   new structure.
4. Identify the behavior change and the smallest set of files that owns it.
5. Select and read only the references required by the task using the table
   below.
6. Preserve existing behavior outside the requested scope.
7. Implement a locally understandable diff. Keep important mathematical,
   lifecycle, and failure flow visible.
8. Run the narrowest relevant validation commands. Expand validation in
   proportion to safety and regression risk.
9. Report what changed, validation performed, unverified areas, and remaining
   risks.

Make a small reasonable assumption when it does not change task scope. State it
when it affects behavior. Ask before making a materially different architectural
or concurrency decision.

## Reference Selection

The detailed rules live in `references/`. Do not load every file by default.
Read the files whose trigger matches the change.

| Situation | Read |
| --- | --- |
| non-trivial C++, robotics, control, simulation, hardware, protocol, or performance-sensitive implementation | `references/robot-control-readability.md` |
| naming control variables, physical quantities, pipeline stages, or public control data | `references/control-variable-naming.md` |
| touching units, frames, transforms, spatial ordering, signs, joint/motor side, quaternion layout, timestamps, or index maps | `references/control-data-conventions.md` |
| implementing or refactoring a control/math function, helper boundary, ownership contract, mutation, output, or status API | `references/control-function-implementation.md` |
| adding or changing YAML configuration, `yaml-cpp` parsing, controller gains, FSM parameters, limits, timeouts, or other runtime settings | `references/yaml-configuration.md` |
| implementing stored `RobotCommand` access, validation, replacement, limiting, or transmission through `getCommand()`, `setCommand()`, `sendCommand()`, or `getSentCommand()` | `references/robot-command-access.md` |
| changing `Update()`, `Step()`, a high-frequency callback, initialization/runtime validation, preallocation, fallback, or command publication | `references/control-loop-implementation.md` |
| using linear algebra, geometry, manifolds, optimization, tolerances, normalization, regularization, or Eigen expressions | `references/control-numerical-implementation.md` |
| crossing threads, ROS callbacks, real-time/non-real-time contexts, shared state, queues, or asynchronous publishing | `references/control-concurrency.md` |
| using `dt`, integrators, derivatives, filters, rate or jerk limits, timeouts, previous-cycle commands, mode transitions, multi-rate logic, or warm starts | `references/control-discrete-time-implementation.md` |

When several situations apply, read the corresponding references together. Use
the repository's explicit local conventions when they conflict with a general
preference, but do not silently override physical, numerical, or safety
contracts.

## Implementation Priorities

Prioritize:

1. Correctness and hardware safety
2. Requested behavior and existing contract preservation
3. Simplicity and local understandability
4. Visible data ownership and mathematical flow
5. Newcomer readability
6. Bounded and allocation-conscious repeated paths where required
7. Focused validation

Prefer boring explicit code over clever abstractions. Add a helper, class, or
utility only when it clarifies a real domain operation, isolates mechanical
detail, improves testability or safety, or removes meaningful duplication.

Do not broaden a local implementation task into package reorganization,
dependency inversion, public API redesign, or a new framework. Flag unavoidable
architectural pressure rather than resolving it implicitly.

## Concurrency Decision Gate

Keep new implementation single threaded unless:

- the user explicitly requests multithreading; or
- an existing boundary already creates separate execution contexts, such as a
  ROS 2 subscriber and a real-time controller update.

Do not create a custom thread merely because a ROS subscriber exists. Let the
ROS 2 executor own callbacks. For data crossing into or out of a real-time path,
prefer the established `realtime_tools` primitive whose semantics match the
channel.

Hide synchronization and buffer mechanics behind domain accessors such as
`getState()`, `getCommand()`, `setCommand()`, and `sendCommand()`. Keep
freshness, validity, command acceptance, and fallback decisions visible to the
control loop.

Do not implement synchronization, double buffering, or a lock-free queue from
scratch unless existing libraries are demonstrably insufficient and the user
approves that exception.

## High-Frequency and Control Paths

Initialize fixed structure once. Preallocate reusable storage. Validate fixed
configuration and dimensions during initialization. Validate changing safety
conditions at runtime.

Keep the repeated function focused on:

- acquiring one coherent input snapshot;
- applying pending transition or reset requests at a cycle boundary;
- updating model and controller state;
- showing the control calculation;
- applying limits and runtime safety checks;
- publishing one complete command or an explicit fallback.

Avoid allocation, repeated lookup, logging format work, blocking I/O, unbounded
retry, and exception-driven normal flow in a required real-time path.

Do not remove runtime freshness, finite-value, solver-status, limit, or watchdog
checks merely to shorten a loop.

## Validation

Do not claim validation that was not performed.

Prefer deterministic tests with known inputs and outputs for:

- protocol and message conversion;
- units, frames, ordering, and sign conversion;
- numerical and manifold calculations;
- command limits and discrete-time state;
- failure and fallback behavior;
- mode transitions;
- concurrency handoff and stale or overflow cases.

Use timing, allocation, race, or stress tools only when the relevant requirement
exists. Do not build a production-scale validation system for a small lab change.

If validation cannot run, say exactly what remains unverified.

## Final Report

Report:

1. behavior changed;
2. important implementation decision;
3. files touched;
4. validation performed and result;
5. unverified behavior or remaining risk.

Keep the report proportional to the change.
