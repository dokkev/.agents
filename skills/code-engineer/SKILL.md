---
name: code-engineer
description: >-
  Implement, modify, review, test, or validate C++, robotics, control,
  simulation, hardware, numerical, ROS 2, configuration, and research code.
  Preserve the requested mode: never add tests, run tests, review, or chain
  modes automatically.
---

# Code Engineer

Produce correct, hardware-safe, numerically valid research code within request
scope. Avoid unrequired infrastructure or redesign.

## Select The Mode

Choose the smallest explicit mode satisfying the request.

| User request | Mode | Write scope |
| --- | --- | --- |
| implement, change, fix, refactor, integrate | **Implement** | requested production code and directly required configuration/docs only |
| review, inspect, find issues, assess a diff | **Review** | read-only; separately requested fixes belong to an Implement agent |
| design tests, add tests, improve coverage | **Test** | requested test plan or test files |
| build, run tests, smoke-check, validate | **Validate** | normally read-only; edit only when fixes are requested |

Do not chain modes. Implementation does not authorize tests, review, launch, or
broad validation; the narrow compile exception below is allowed. Review does
not authorize fixes; test or validation does not authorize production fixes.

## Sub-agent Delegation

Default to one agent. Delegate only bounded, independent work with an exact
mode, scope, deliverable, and non-overlapping write ownership. Delegation never
expands user authority; the parent owns integration and the final result. Do not
recursively delegate by default.

An agent must not review or approve production code it authored. Author checks
and corrections remain Implement work, not code review. When implementation and
review are both requested, assign Review to a separate non-author agent. If none
is available, report that independent review was not performed.

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
for a real gap. Never load review/testing guidance for implementation.

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
| YAML, `yaml-cpp`, controller gains, FSM parameters, limits, thresholds, or timeouts | `references/yaml-configuration.md` |
| controller-to-hardware `RobotCommand` handoff, hardware validation, limiting, transmission, or required hardware-owned command smoothing | `references/hardware-command-boundary.md` |
| device or transport I/O, packets, reads/writes, retries, reconnects, or hidden blocking | `references/hardware-io.md` |
| `Update()`, `Step()`, high-frequency callbacks, preallocation, fallback, or command publication | `references/control-loop-implementation.md` |
| linear algebra, geometry, manifolds, optimization, tolerances, normalization, regularization, or Eigen expressions | `references/control-numerical-implementation.md` |
| threads, ROS callbacks, real-time/non-real-time handoff, shared state, queues, or asynchronous publication | `references/control-concurrency.md` |
| `dt`, integrators, derivatives, filters, rate/jerk limits, timeouts, history, mode transitions, multi-rate logic, or warm starts | `references/control-discrete-time-implementation.md` |
| explicit code-review request | `references/review.md` plus only the concern references needed for supported findings |
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

Implement includes no tests or review. Compile only the smallest target with a
safe canonical command that cannot launch software or touch hardware. Other
validation requires an explicit request; otherwise report it unverified.

## Review, Test, And Validate Modes

For review, load `references/review.md`, stay read-only, and send separately
requested fixes to a non-reviewing Implement agent. For test or validation,
load `references/testing.md` and match the request. Report only actions run.

## Final Report

Report behavior and unverified scope for implementation, findings for review,
test protection and run status, or validation commands, results, and gaps.
