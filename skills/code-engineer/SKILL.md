---
name: code-engineer
description: >-
  Implement, modify, review, test, or validate code when the user explicitly
  requests the corresponding work. Use for C++, robotics, robot control,
  simulation, hardware interfaces, communication, numerical code, ROS 2
  integration, configuration, and research software. Preserve the user's
  requested mode: do not automatically add tests, run tests, perform a code
  review, or chain implementation into review and validation.
---

# Code Engineer

Handle code work through one skill while preserving the exact scope and authority
of the user's request.

Optimize for a research-lab codebase: correct, hardware-safe, numerically valid,
locally understandable, and practical for another student to modify. Do not add
production-scale infrastructure or invent a new architecture unless the task
requires it.

## Select The Mode

Choose the smallest mode or explicit combination that satisfies the request.

| User request | Mode | Write scope |
| --- | --- | --- |
| implement, change, fix, refactor, integrate | **Implement** | requested production code and directly required configuration/docs only |
| review, inspect, find issues, assess a diff | **Review** | read-only unless fixes are also requested |
| design tests, add tests, improve coverage | **Test** | requested test plan or test files |
| build, run tests, smoke-check, validate | **Validate** | normally read-only; edit only when fixes are requested |

Do not chain modes by habit.

- An implementation request does not authorize writing or running tests, a
  separate code review, or a broad validation campaign.
- A review request does not authorize fixes.
- A test request does not authorize production-code changes unless the user also
  asks to fix what the test exposes.
- A validation request does not authorize fixes unless the user asks for them.
- Use a hybrid flow such as Review -> Implement or Implement -> Test only when
  the user explicitly asks for both parts.

Reading an existing test is allowed when it is the nearest executable
specification for the requested implementation. That does not authorize changing
or running the test.

## Minimal Context Workflow

1. Read the closest `AGENTS.md`.
2. Determine the mode from the user's wording before exploring broadly.
3. Read repository maps only when relevant:
   - read `docs/ARCHITECTURE.md` when the task touches ownership, dependencies,
     runtime flow, public boundaries, or accepted code direction;
   - read `docs/COMMANDS.md` when the task requires compilation, validation, or
     build/source/install locations.
4. Inspect the smallest source surface that owns the requested behavior, plus
   build, configuration, or tests only when they are directly relevant.
5. Select only the detailed references whose triggers match the actual change.
6. Perform only the authorized mode or mode combination.
7. Report the result, actions actually performed, and relevant uncertainty.

Do not read every repo document or every skill reference up front. If the task
can be completed from local instructions and the owning code, load no reference.

## Progressive Reference Loading

The files under `references/` are an indexable library, not a mandatory reading
list.

- Start with zero references.
- Open a reference only after the inspected code reveals its concern.
- Usually one or two references are enough.
- Read three or more only when the task genuinely crosses those independent
  concerns.
- Do not read both implementation and review/testing guidance merely because
  they exist.
- Prefer a repository's explicit local contract over a general preference, but
  never silently violate physical, numerical, concurrency, or safety contracts.

| Trigger in the requested work | Read |
| --- | --- |
| control variable names, physical quantities, pipeline stages, or public control data | `references/control-variable-naming.md` |
| units, frames, transforms, signs, joint/motor side, quaternion layout, timestamps, or index maps | `references/control-data-conventions.md` |
| function decomposition, helper boundaries, mutation, outputs, status handling, or Eigen lifetime | `references/control-function-implementation.md` |
| YAML, `yaml-cpp`, controller gains, FSM parameters, limits, thresholds, or timeouts | `references/yaml-configuration.md` |
| controller-to-hardware `RobotCommand` handoff, hardware validation, limiting, transmission, or hardware-owned command smoothing | `references/hardware-command-boundary.md` |
| `Update()`, `Step()`, high-frequency callbacks, preallocation, fallback, or command publication | `references/control-loop-implementation.md` |
| linear algebra, geometry, manifolds, optimization, tolerances, normalization, regularization, or Eigen expressions | `references/control-numerical-implementation.md` |
| threads, ROS callbacks, real-time/non-real-time handoff, shared state, queues, or asynchronous publication | `references/control-concurrency.md` |
| `dt`, integrators, derivatives, filters, rate/jerk limits, timeouts, history, mode transitions, multi-rate logic, or warm starts | `references/control-discrete-time-implementation.md` |
| explicit code-review request | `references/review.md` plus only the concern references needed for supported findings |
| explicit test design, test implementation, build, test run, smoke check, or validation request | `references/testing.md` |

For a reference longer than 100 lines, preview its `Contents` first and read
only the sections relevant to the requested change. Read the full file only
when the task genuinely crosses most of its concerns.

## Implement Mode

Implement the smallest clear diff that owns the requested behavior.

Prioritize:

1. correctness and hardware safety;
2. the requested behavior and preservation of unrelated contracts;
3. visible ownership, units, frames, timing, and failure behavior;
4. simplicity and newcomer readability;
5. bounded, allocation-conscious repeated paths where required.

Prefer direct code and established libraries. Add a helper, class, or utility
only when it represents a real domain operation, isolates mechanical detail,
improves safety, or removes meaningful duplication.

Follow the established local C++ style. Keep lifecycle and control functions
readable as a top-level story, preserve the visible mathematical flow, and use
precise helper names for mechanical details and side effects. Do not impose a
repo-wide separator, helper package, or formatting convention that the
repository has not adopted.

Do not broaden a local change into package reorganization, public API redesign,
new concurrency, or a generic framework. Surface architectural pressure instead
of resolving it implicitly.

For high-frequency paths, establish fixed structure and storage during
initialization. Keep coherent input acquisition, the control calculation,
runtime safety checks, fallback behavior, and complete command publication
visible. Do not remove freshness, finite-value, solver-status, limit, or watchdog
checks merely to shorten the loop.

Implement mode does not include automatic test creation, test execution, or a
post-implementation code review. A directly relevant compile may be performed
when compilation is explicitly requested or is necessary to complete the stated
build task; do not expand it into unrelated checks.

## Review, Test, And Validate Modes

For an explicit review, load `references/review.md`. Keep the work read-only and
lead with evidence-backed findings unless fixes were also requested.

For explicit test or validation work, load `references/testing.md`. Match the
requested depth: a test plan, test implementation, one command, a focused build,
or a smoke check are different scopes.

Do not claim a build, test, launch, simulation, hardware run, or review was
performed unless it actually was.

## Final Report

Keep the report proportional to the selected mode.

- **Implement:** behavior changed, important decision, files touched, and what
  remains unverified. Do not imply tests or review were performed.
- **Review:** findings first, then assumptions and unreviewed risk.
- **Test:** tests designed or changed, what they protect, and whether they ran.
- **Validate:** commands run, result, first actionable failure, and unexercised
  scope.
