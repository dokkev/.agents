---
name: test-designer
description: Design or implement focused tests for changed behavior, edge cases, regressions, failure paths, contracts, and integration risks. Use when the user asks for a test plan, missing test analysis, regression tests, coverage improvement, or validation strategy after a change.
---

# Test Designer

Design tests that protect behavior, contracts, and regressions, not implementation trivia.

Prefer the smallest deterministic test that would fail for the bug, regression, or contract violation the user cares about.

This skill designs tests. It may implement tests when explicitly asked, but it should not replace `smoke-tester` for running validation commands.

## Workflow

1. Identify the behavior under test and the user-visible, contract-level, or safety-relevant expectation.
2. Read the repo harness when present:

   * `AGENTS.md`
   * `docs/ARCHITECTURE.md`
   * `docs/COMMANDS.md`
   * `docs/DECISIONS.md`
   * `docs/PLANS.md`
3. Read existing tests to match framework, naming, fixture, assertion, and file-location style.
4. Identify the owning package, module, class, or public interface.
5. Map realistic risk areas:

   * happy path
   * boundary inputs
   * invalid inputs
   * failure paths
   * contract mismatches
   * numerical edge cases
   * unit or frame convention errors
   * parser/serializer errors
   * state-machine transitions
   * timing or concurrency assumptions
   * resource cleanup
   * integration wiring
6. Prioritize tests that catch realistic regressions with clear failure signals.
7. When implementing, keep tests focused, deterministic, and close to the owning package.

## Harness context

Use the micro-harness docs as maps:

* `AGENTS.md` — repo entrypoint and local rules
* `docs/ARCHITECTURE.md` — module boundaries, owning packages, public contracts, and integration points
* `docs/COMMANDS.md` — build, test, lint, smoke, dry-run, and validation commands
* `docs/DECISIONS.md` — design decisions that tests should preserve
* `docs/PLANS.md` — current priorities, non-goals, and deferred work

If commands, fixtures, or validation guidance are missing or stale, recommend a `docs-gardener` update.

If a repo also has `docs/TESTING.md`, use it as an additional source, but do not require it.

## Related skill references

When designing tests for implementation quality, utility behavior, controller readability, helper boundaries, memory discipline, or C++ documentation-sensitive APIs, consult when available:

* `~/.agents/skills/code-implementer/SKILL.md`
* `~/.agents/skills/code-implementer/references/robot-control-readability.md`

Do not duplicate those documents in the test plan.

Use them to identify behaviors worth locking down with tests, such as:

* utility functions with known input/output behavior
* command conversion
* safety limits
* parser/serializer behavior
* numerical calculations
* state transitions
* expected ownership or mutation behavior

## Test categories

### Correctness

Test expected outputs, state transitions, calculations, parsing, serialization, API behavior, and command conversion.

### Edge cases

Test empty inputs, null or missing values, limits, malformed data, duplicate data, unusual ordering, non-finite values, and boundary values.

### Failure paths

Test errors, retries, cleanup, partial writes, invalid permissions, unavailable dependencies, stale state, invalid config, and timeout behavior.

### Regression

A specific previous or likely bug should have a direct test with a clear failure signal.

Prefer one precise regression test over broad tests that fail vaguely.

### Contract

Test producer/consumer agreements for:

* APIs
* config keys
* schemas
* messages
* files
* CLI flags
* units
* coordinate frames
* ordering conventions
* ownership conventions
* mutation behavior

### Numerical and control logic

For numerical, robotics, control, estimation, planning, simulation, or hardware-interface code, prefer deterministic tests with known inputs and expected outputs.

Good candidates:

* unit conversion
* quaternion / Euler / transform helpers
* Jacobian or kinematic helper behavior
* command mapping
* command saturation
* parser and encoder behavior
* state-machine transitions
* desired / computed / applied command separation
* stale or invalid state handling

Avoid tests that duplicate every implementation step unless the step itself is the contract.

### Utility functions

Utility functions should usually be easy to test.

Prioritize tests for utilities that handle:

* math
* units
* transforms
* encoding / decoding
* parsing / serialization
* clamping / saturation
* safety limits
* byte order
* scaling constants
* reusable buffer behavior

### Integration smoke

Design integration smoke checks for:

* launch or startup behavior
* plugin loading
* route or node registration
* config parsing
* dependency injection
* fake hardware
* dry-run mode
* log replay
* representative CLI execution

Integration smoke tests should be narrow and fast when possible.

### Maintainability and examples

Tests can also serve as public examples.

Prefer tests that make intended usage obvious, especially for public APIs, utilities, command structures, and configuration.

## Test design rules

* Do not chase coverage percentage at the expense of useful assertions.
* Do not test private implementation trivia unless it is the only stable seam for important behavior.
* Do not duplicate implementation details unless the detail is the public contract.
* Prefer deterministic tests over timing-sensitive tests.
* Prefer one clear regression test over a broad vague test.
* Include failure-path tests when code handles external inputs, persistence, network calls, hardware, subprocesses, permissions, or user data.
* For hardware-facing code, prefer fake hardware, dry-run, log replay, or deterministic protocol tests before real hardware.
* If behavior is ambiguous, recommend clarifying the contract before adding brittle tests.
* Keep tests close to the owning package unless the repo has a clear test layout convention.
* Match existing test framework, fixture, naming, and assertion style.

## Output format

For planning requests, report:

```text
Test scope:
Existing coverage observed:
Highest-risk gaps:
Recommended tests:
```

For each recommended test, include:

```text
Priority:
Target file/function:
Test type:
Scenario:
Expected result:
Why it matters:
```

For implementation requests, report:

```text
Modified test files:
What each test verifies:
Commands to run:
Commands run:
Results:
Remaining gaps:
```

Do not claim tests were run unless they were actually run.
