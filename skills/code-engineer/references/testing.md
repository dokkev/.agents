# Focused Testing and Validation

Use when checks or test work are included in the task contract from `SKILL.md`.
That contract owns execution and edit permissions. Reading this reference does
not add a test, build, review, or experiment requirement.

## Choose Evidence

Identify the changed behavior and the specific failure a check should catch.
Reuse existing tests, logs, and artifacts when they already answer that question
and their code, inputs, configuration, and environment assumptions still hold.
Do not present stale evidence as verification of changed behavior.

Use repository-native commands and nearby tests. Read `docs/COMMANDS.md`, test
configuration, or a focused testing document only for the needed command; do
not rediscover the full environment for each task.

| Changed contract | Useful focused evidence |
| --- | --- |
| Calculation or solver adapter | Known expected values, boundary case, solver failure |
| Units, frames, ordering | Independent conversion or non-identity mapping case |
| Parser, configuration, protocol | Valid input plus relevant rejection or round trip |
| State or control history | Transition, reset, stale input, complete fallback |
| Concurrency | Snapshot ownership, overflow, or shutdown on the affected path |
| CLI or build wiring | Representative safe invocation or smallest owning target |
| Hardware boundary | Protocol replay, fake hardware, or approved safe dry-run |

A finite output alone is not numerical correctness. Derive expected values and
tolerances independently where practical. Test public behavior, not private
helper structure, trivial getters, or coverage counts. Import-only or startup
checks are useful when import or startup is the changed contract, not as a
substitute for exercising the algorithm.

## Run and Stop

Execute the smallest authorized check that addresses the risk. Use a timeout
where a command may hang. Record the first actionable failure and distinguish a
change defect from an environment, dependency, or unrelated existing failure.

When fixes are in scope, correct the owning defect and rerun only the checks
whose result the fix invalidated. Do not expand a focused check into a suite,
benchmark, FEA run, optimization campaign, training run, or physical experiment
merely for confidence. Do not execute hardware just because a command is listed.

Do not bend production behavior to satisfy a stale or incorrect test. Report a
contract conflict or unavailable required evidence without silently changing scope.

## Report

State exact commands run, outcomes, reused evidence and why it remains relevant,
and unexercised behavior. For test edits, state the regression protected and
whether execution occurred. Distinguish static checks from runtime or scientific
validation. Stop once the requested evidence is obtained.
