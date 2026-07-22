# Testing And Validation

Load this reference only when the user explicitly asks to design or add tests,
run tests, compile, validate, or perform a smoke check. Do not use it as an
automatic follow-up to implementation or review.

## Contents

- [Match The Requested Scope](#match-the-requested-scope)
- [Context](#context)
- [Test Design](#test-design)
- [Concern Matrix](#concern-matrix)
- [Validation Selection](#validation-selection)
- [Reporting](#reporting)

## Match The Requested Scope

| Request | Action |
| --- | --- |
| test plan or coverage analysis | inspect and propose tests; do not edit or run |
| add or fix tests | edit the focused test surface; run only if requested |
| run tests | execute the narrowest relevant existing test command |
| build or compile | compile the owning target or package |
| validate or smoke-check | run the smallest check that exercises the requested behavior |
| fix a failing check | diagnose, make the scoped fix, and rerun that check |

Do not expand one requested command into a full suite. Do not change production
code merely to make a weak or obsolete test pass without confirming the actual
contract.

## Context

Read:

- the closest `AGENTS.md`;
- `docs/COMMANDS.md` for compilation commands and build locations;
- project-native build files, test configuration, scripts, or a focused
  `docs/TESTING.md` for test and smoke commands;
- existing nearby tests to match framework, fixture, naming, and assertion style.

Use `docs/ARCHITECTURE.md` only when ownership or integration boundaries affect
test placement.

## Test Design

Prefer the smallest deterministic test that fails for the behavior, regression,
or contract violation the user cares about.

Prioritize relevant cases from:

- expected behavior and boundary inputs;
- invalid input and failure fallback;
- units, frames, signs, ordering, and conversion;
- numerical edge cases and solver rejection;
- parser, serialization, and public config contracts;
- state-machine transition and reset behavior;
- stale state, timeout, overflow, and concurrency handoff;
- public API, command mapping, saturation, and safety limits;
- integration wiring, startup, plugin discovery, fake hardware, or dry-run.

Test public behavior rather than private implementation trivia. Prefer one
precise regression test over a broad test with a vague failure signal. Do not
chase coverage percentage at the expense of useful assertions.

For hardware-facing code, prefer deterministic protocol tests, fake hardware,
simulation, dry-run, log replay, or disabled motors. Use real hardware only when
the user explicitly requests it and the safety boundary is clear.

## Concern Matrix

Select cases from only the concerns in the user's requested test scope.

| Concern | High-value cases |
| --- | --- |
| data conventions | zero/sign/scale, saturation, encode/decode round trip, non-identity ordering, motor/joint conversion, frame and quaternion variants |
| numerical code | nominal expected output, near-zero and wrap boundaries, singular/rank-deficient input, solver failure, non-finite rejection, scale-aware tolerance |
| repeated loop | initialization contract, malformed boundary input, every early-return fallback, recovery reset, allocation guard when no-allocation is claimed |
| discrete time | first update, invalid or excessive `dt`, missed cycle, integrator saturation/anti-windup, filter reset, bumpless transition, warm-start invalidation, rate change |
| concurrency | complete snapshots, mismatched producer/consumer rates, stale/duplicate/overflow behavior, shutdown lifetime, race detector where practical |
| command boundary | structural rejection, atomic handoff, hardware limiting, send failure, transmitted-command diagnostic, no partial application |
| FSM | entry/re-entry/exit order, transition commit boundary, self/invalid/failure transition, complete output on failure |
| YAML | missing key, wrong type/shape, non-finite or unsafe value, contextual error, atomic live replacement |

Derive expected values and tolerances independently from the implementation
when practical. A test that checks only that output is finite is not a numerical
correctness test.

## Validation Selection

Choose the smallest command that matches the requested check:

- library or numerical change: focused unit test or owning target build;
- parser/protocol change: known input/output or config parse check;
- configuration/wiring change: parse, startup, launch, or plugin check;
- CLI/script change: `--help` or one representative invocation;
- build-system change: minimal affected target before dependents;
- hardware path: build or safe fake/dry-run before physical execution.

Use timeouts for commands that may hang. Capture the first actionable failure
and enough context to identify whether its owner is the change, dependency,
environment, stale command, or external system.

## Reporting

For test design or implementation, report:

- scope;
- tests proposed or changed;
- behavior each test protects;
- whether anything was run;
- remaining gaps.

For validation, report:

- validated scope;
- exact commands run;
- result and first actionable failure;
- likely owner;
- unexercised behavior and residual risk.

Never claim a test, build, launch, simulation, dry-run, or hardware run occurred
unless it actually did.
