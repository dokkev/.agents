---
name: code-engineer
description: >-
  Default skill for any code-related task. Always use when asked to implement,
  modify, fix, debug, refactor, review, inspect, assess, test, validate, build,
  or otherwise work with C++, Python, robotics, control, simulation, hardware,
  numerical, ROS 2, configuration, or research software. Preserve the requested
  mode and do not automatically chain implementation, review, testing, or
  validation unless requested.
---

# Code Engineer

Produce correct, hardware-safe, numerically valid research code within request
scope. Avoid unrequired infrastructure or redesign.

## Select The Mode

Use this skill for every code-related request. Then choose the smallest explicit
mode satisfying the request.

| User request | Mode | Write scope |
| --- | --- | --- |
| implement, change, fix, debug, refactor, integrate | **Implement** | requested production code and directly required configuration/docs only |
| review, inspect, find issues, assess code or a diff | **Review** | read-only unless fixes are explicitly requested |
| design tests, add tests, improve coverage | **Test** | requested test plan or test files |
| build, run tests, smoke-check, validate | **Validate** | normally read-only; edit only when fixes are requested |

Do not chain modes automatically. Implementation does not authorize tests,
review, launch, or broad validation; the narrow compile exception below is
allowed. Review does not authorize fixes; test or validation does not authorize
production fixes unless the current request explicitly includes them.

## Sub-agent Delegation

Default to one agent unless the closest repository instructions, current task,
or explicit user request require delegation.

Delegate only bounded work with an exact mode, scope, deliverable, and
non-overlapping write ownership. Delegation never expands user authority; the
parent owns integration and the final result. Do not recursively delegate by
default.

Review independence is repository- and task-specific. A review may be either a
self-review by the implementation agent or an independent review by a separate
non-author agent. Follow the closest `AGENTS.md`, `INSTRUCTION.md`, or explicit
user request for which form is required.

Do not claim a self-review is independent review. If independent review is
required, assign Review to an agent that did not author the implementation. Do
not create repeated reviewer chains merely to obtain an all-PASS result unless
the repository workflow explicitly requires them.

## Minimal Context Workflow

1. Choose the mode and read the closest `AGENTS.md`.
2. Read `docs/ARCHITECTURE.md` only for relevant direction and
   `docs/COMMANDS.md` only for requested build or validation work.
3. Inspect the smallest owning source surface and direct build, configuration,
   or executable contracts.
4. Load matching references, perform only the authorized mode, and report
   actions actually taken.

## Progressive Reference Loading

Start with no references. Load one for the dominant concern; add another only
for a real gap. Never load review/testing guidance for implementation unless the
current request explicitly includes those modes.

For a reference over 100 lines, use the bundled reader. Resolve paths from this
skill directory; commands are shown from that directory.

```bash
python3 scripts/read_reference.py \
  references/control-discrete-time-implementation.md --list
python3 scripts/read_reference.py \
  references/control-discrete-time-implementation.md \
  --section "Core Contract" \
  --section "Keep Required Hardware Rate-Limit History Local"
```

Read `Core Contract` plus one or two matching H2 sections. Read the full file
only when editing, reviewing, or resolving a cross-section conflict. Apply this
heading-first rule to long repository docs. Safe repository contracts prevail.

| Trigger in the requested work | Read |
| --- | --- |
| control variable names, physical quantities, pipeline stages, or public control data | `references/control-variable-naming.md` |
| units, frames, transforms, signs, joint/motor side, quaternion layout, timestamps, or index maps | `references/control-data-conventions.md` |
| function decomposition, helper boundaries, mutation, outputs, status handling, or Eigen lifetime | `references/control-function-implementation.md` |
| Python API/data modeling, dataclasses, tuple/dict usage, module structure, Python refactoring, PEP 20, or Python readability | `references/python-code-design.md` |
| YAML, `yaml-cpp`, controller gains, FSM parameters, limits, thresholds, or timeouts | `references/yaml-configuration.md` |
| controller-to-hardware `RobotCommand` handoff, hardware validation, limiting, transmission, or required hardware-owned command smoothing | `references/hardware-command-boundary.md` |
| device or transport I/O, packets, reads/writes, retries, reconnects, or hidden blocking | `references/hardware-io.md` |
| `Update()`, `Step()`, high-frequency callbacks, preallocation, fallback, or command publication | `references/control-loop-implementation.md` |
| linear algebra, geometry, manifolds, optimization, tolerances, normalization, regularization, or Eigen expressions | `references/control-numerical-implementation.md` |
| threads, ROS callbacks, real-time/non-real-time handoff, shared state, queues, or asynchronous publication | `references/control-concurrency.md` |
| `dt`, integrators, derivatives, filters, rate/jerk limits, timeouts, history, mode transitions, multi-rate logic, or warm starts | `references/control-discrete-time-implementation.md` |
| code review, implementation inspection, correctness assessment, finding issues, or diff assessment | `references/review.md` plus only the concern references needed for supported findings |
| explicit test design, test implementation, build, test run, smoke check, or validation request | `references/testing.md` |

## Implement Mode

Implement the smallest clear owning diff. Keep safety, units, frames, timing,
ownership, failures, and repeated-path bounds visible.

- Start with the simplest direct implementation satisfying known requirements
  and safety constraints.
- Add abstraction, state, concurrency, caching, retries, reconnects, or timeouts
  only for an explicit requirement, safety invariant, credible hazard, or
  observed problem; use the smallest mechanism with one owner.
- Follow local style; keep lifecycle, control flow, mathematics, mutation, and
  side effects visible.
- Do not turn a local change into reorganization, redesign, concurrency, or a
  generic framework. Surface architectural pressure instead.
- Initialize fixed storage before high-frequency paths. Preserve freshness,
  finite-value, solver, limit, watchdog, and fallback checks.

Implement includes no tests or review unless the current request explicitly
includes those modes. Compile only the smallest target with a safe canonical
command that cannot launch software or touch hardware. Other validation requires
an explicit request; otherwise report it unverified.

## Review, Test, And Validate Modes

For review, load `references/review.md`, stay read-only during the Review pass,
and follow repository/task policy for self-review versus independent review. If
fixes are explicitly requested, perform them in Implement mode according to the
same local policy. For test or validation, load `references/testing.md` and match
the request. Report only actions actually run.

## Final Report

Report behavior and unverified scope for implementation, findings and review
independence for review, test protection and run status, or validation commands,
results, and gaps.
