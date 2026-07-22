---
name: code-engineer
description: >-
  Implement, modify, review, test, or validate code only when explicitly
  requested. Use for C++, robotics, robot control,
  simulation, hardware interfaces, communication, numerical code, ROS 2
  integration, configuration, and research software. Preserve the user's
  requested mode: do not automatically add tests, run tests, perform a code
  review, or chain implementation into review and validation.
---

# Code Engineer

Produce correct, hardware-safe, numerically valid research code within request
scope. Avoid unrequired infrastructure or redesign.

## Select The Mode

Choose the smallest explicit mode satisfying the request.

| User request | Mode | Write scope |
| --- | --- | --- |
| implement, change, fix, refactor, integrate | **Implement** | requested production code and directly required configuration/docs only |
| review, inspect, find issues, assess a diff | **Review** | read-only unless fixes are also requested |
| design tests, add tests, improve coverage | **Test** | requested test plan or test files |
| build, run tests, smoke-check, validate | **Validate** | normally read-only; edit only when fixes are requested |

Do not chain modes. Implementation does not authorize tests, review, launch, or
broad validation; the narrow compile exception below is allowed. Review does
not authorize fixes; test or validation does not authorize production fixes.

## Minimal Context Workflow

1. Read the closest `AGENTS.md` and determine the mode first.
2. Read `docs/ARCHITECTURE.md` only for relevant code-direction contracts and
   `docs/COMMANDS.md` only for requested build, validation, or locations.
3. Inspect the smallest source surface owning the behavior, plus directly
   relevant build, configuration, or executable-contract files.
4. Load only references whose triggers match the actual work.
5. Perform only the authorized mode and report actions actually taken.

## Progressive Reference Loading

Start with zero references and choose one primary reference for the dominant
concern. Add another only when the primary leaves a real contract gap; a second
trigger match alone is insufficient. Do not load review/testing guidance for
implementation.

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
only to edit/review it, resolve a three-section conflict, perform a broad
safety/consistency audit, or follow an unresolved dependency. Apply the same
heading-first rule to long repository docs; they need no `Core Contract`.

Prefer explicit safe repository contracts over general preferences.

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

Implement the smallest clear owning diff. Prioritize safety and correctness,
unrelated contracts, visible units/frames/timing/ownership/failures, readability,
and bounded repeated paths.

- Start with the simplest direct implementation satisfying known requirements
  and safety constraints.
- Add abstraction, state, concurrency, caching, retries, reconnects, or timeouts
  only for an explicit requirement, safety invariant, credible hazard, or
  observed problem. Use the smallest mechanism with one owner.
- Follow local style; keep lifecycle, control flow, mathematics, mutation, and
  side effects visible.
- Do not broaden a local change into package reorganization, API redesign,
  concurrency, or a generic framework. Surface architectural pressure instead.
- Initialize fixed storage before high-frequency paths. Preserve freshness,
  finite-value, solver, limit, watchdog, and fallback checks.

Implement mode includes neither automatic tests nor review. Compile the
smallest affected target when a safe canonical command neither launches
software nor touches hardware. Tests, launch, simulation, dry-run, and hardware
execution require an explicit request. Otherwise report compilation unverified.

## Review, Test, And Validate Modes

For review, load `references/review.md`, remain read-only, and lead with evidence
unless fixes were requested. For test or validation, load
`references/testing.md` and match the requested depth. Never claim an action ran
unless it did.

## Final Report

Report proportionally: behavior and unverified scope for implementation;
findings for review; protection and run status for tests; commands, results,
first failure, and unexercised scope for validation.
