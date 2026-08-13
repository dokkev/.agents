# Code Review

Load this reference only when the user explicitly asks for a code review,
inspection, issue search, or assessment. A normal implementation request does
not trigger a separate review pass.

## Section Map

- [Core Contract](#core-contract)
- [Review Order](#review-order)
- [Evidence Standard](#evidence-standard)
- [Severity](#severity)
- [Control-Specific Checks](#control-specific-checks)
- [Concern Matrix](#concern-matrix)
- [Report](#report)

## Core Contract

- Establish the exact diff, files, subsystem, or behavior under review.
- Require a reviewer who did not author any reviewed production code. An
  author's inspection and corrections are Implement work, not review or
  approval.
- Keep the reviewer read-only. Send separately requested fixes to an Implement
  agent; the same non-author reviewer may re-check fixes it did not author.
- If no independent reviewer is available, report that review was not performed.
- Read only the concern references that match the reviewed code.
- Treat `docs/ARCHITECTURE.md` as accepted direction, not unquestionable truth.
- Do not turn implementation review into architecture redesign unless requested.
- Do not run tests, builds, or smoke checks unless validation is also requested.

Judge a research-lab codebase by correctness, safety, numerical validity,
understandable ownership, and practical maintainability. Do not demand generic
frameworks, production service layers, speculative extensibility, or concurrency
for hypothetical scale.

## Review Order

1. correctness, undefined behavior, and hardware safety;
2. failure and fallback behavior;
3. units, frames, signs, ordering, timing, and numerical validity;
4. state ownership, lifetime, mutation, and concurrency;
5. discrete-time history and transition behavior;
6. maintainability and newcomer readability;
7. complexity or performance that matters on the actual path;
8. meaningful test or diagnostic gaps when tests are within review scope.

Formatting and minor naming preferences are not findings when local style or a
formatter already resolves them.

## Evidence Standard

Every finding must include:

- file and precise location;
- violated behavior or contract;
- concrete input, state, timing condition, or call path;
- likely consequence;
- smallest useful correction direction.

Ask a question when the conclusion depends on an unknown hardware, frame,
timing, or library contract. Do not report a hypothetical race merely because
two threads exist or a performance issue without a relevant repeated cost.

## Severity

| Severity | Meaning |
| --- | --- |
| critical | credible unsafe behavior, data loss, or unusable core behavior without an effective guard |
| high | concrete correctness, race, numerical, or failure-handling defect on a realistic path |
| medium | fragile contract likely to cause incorrect changes, intermittent behavior, or difficult debugging |
| low | local clarity or maintainability problem with limited immediate consequence |

Do not inflate severity because code violates a general preference.

## Control-Specific Checks

When relevant, verify that:

- quantities preserve units, frames, signs, and ordering;
- fixed configuration and storage are established before repeated execution;
- changing freshness, finite-value, solver, and command-safety conditions remain
  checked at runtime;
- the joint-command controller produces its defined complete fallback rather
  than stale or partial output;
- controller history has one owner and explicit reset semantics;
- controller-produced and hardware-applied command outcomes remain
  distinguishable when hardware protection can change or reject a command;
- transitions occur once at a defined cycle boundary;
- retries, queues, iterations, and catch-up work are bounded where deadlines
  matter.

For concurrent code, identify complete-snapshot semantics, writer ownership,
freshness, overflow, lifetime, acquisition bounds, and shutdown. First establish
that concurrency is actually required.

## Concern Matrix

Use only the rows relevant to the reviewed code. The concern reference supplies
the implementation contract; this table supplies the review lens.

| Concern | Look for |
| --- | --- |
| data conventions | mixed units or sides, ambiguous frames/signs/order, unsafe quaternion layout, clock-domain mixing, duplicated conversion |
| functions and naming | hidden mathematical flow, thin helper chains, vague side effects, ambiguous mutation or view lifetime |
| repeated loops | allocation or resizing, unbounded work, stale/partial fallback, missing changing-condition guards, hidden recovery |
| numerical code | unjustified inverse, arbitrary tolerance, unsafe normalization, manifold misuse, unchecked solver/rank failure, invalid Eigen lifetime |
| discrete time | undefined `dt`, reset, limiter stage, mode-entry history, multi-rate hold, stale-sample, or catch-up semantics |
| concurrency | shared mutable snapshots, multiple reads per cycle, missing channel semantics, blocking or unbounded acquisition, unsafe shutdown |
| command boundary | unjustified shared command storage, partial acceptance, competing fallback ownership, unclear protection/transmission result, transport leakage |
| hardware I/O | partial-frame publication, hidden blocking/retry/reconnect, nested timeouts, duplicated recovery, cached feedback presented as new, premature transport abstraction |
| YAML | parsing in runtime paths, raw node leakage, scattered schema logic, unsafe defaults, partial live update, weak error context |

Do not load every concern reference by default. Open only those needed to
support a concrete finding or resolve a plausible ambiguity.

## Report

Lead with findings ordered by severity. Then state open questions, assumptions,
unreviewed areas, and residual risk. If no actionable finding is supported, say
so directly without inventing one.
