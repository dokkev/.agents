---
name: code-implementer
description: Use when writing, modifying, refactoring, or integrating code. Especially useful for C++, robotics, control, simulation, hardware interfaces, communication, numerical, and performance-sensitive code where small diffs, beginner-readable flow, memory discipline, safety, and honest validation matter.
---

# Code Implementer

Use this skill when implementing code changes.

## Core Workflow

1. Read the closest `AGENTS.md`.
2. If present, read the repo harness files that matter for the task:
   - `docs/ARCHITECTURE.md`
   - `docs/COMMANDS.md`
   - `docs/DECISIONS.md`
   - `docs/PLANS.md`
3. Inspect the existing implementation before introducing new structure.
4. Identify the smallest set of files needed for the requested change.
5. Preserve existing behavior unless the task explicitly asks for behavior change.
6. Implement the smallest reasonable, reviewable diff.
7. Run the narrowest relevant validation command from `docs/COMMANDS.md` when practical.

If the task is ambiguous, make a minimal reasonable assumption and state it.

## Implementation Priorities

Prioritize, in this order:

1. Correctness
2. Existing behavior preservation
3. Simplicity
4. Readability for beginners
5. Clear data flow
6. Memory discipline in repeated or high-frequency paths
7. Validation

Prefer boring, explicit, locally understandable code. Do not introduce a new abstraction just to make the code look cleaner.

## Real-Time Or High-Frequency Paths

For functions expected to run in a real-time control loop or other high-frequency
loop:

- Avoid repeated initialization checks, model-loaded checks, configuration
  checks, logging, allocation, and exception-oriented validation in the hot path.
- Prefer validating required model/configuration/state shape during
  initialization, `Load*()`, `Initialize()`, setup, or adapter construction.
- Make the hot-path contract explicit: it may assume initialization has already
  succeeded and dimensions have already been made compatible.
- Keep per-loop work focused on the state update or control math. If a runtime
  guard is truly needed for safety, keep it minimal, deterministic, and
  allocation-free.

## When To Read The Reference

For C++, robotics, control, simulation, hardware interface, communication, numerical, parser/protocol, or performance-sensitive work, read:

- `references/robot-control-readability.md`

Use that reference for detailed guidance on:

- Visible controller and algorithm flow
- Helper design
- Naming and mutation clarity
- Output parameters
- Memory reuse in repeated paths
- Utility extraction
- File organization
- Logging
- Safety and validation

Do not duplicate the reference into normal reports. Use it to guide implementation choices.

## Validation

Do not claim validation was performed unless it was actually performed.

For protocol code, parser code, public interfaces, numerical logic, data transformations, command conversion, safety limits, state-machine transitions, and utility functions, prefer deterministic tests with known input/output examples.

If validation cannot be run, clearly state what was not verified.

## Report Format

At the end, report:

1. What changed
2. Why it changed
3. Files touched
4. Validation performed
5. What was not verified
6. Remaining risks or follow-up work
