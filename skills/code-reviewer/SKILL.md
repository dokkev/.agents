---
name: code-reviewer
description: Review code for correctness, maintainability, readability, unnecessary complexity, beginner accessibility, and reasonable performance. Use when a user asks for general code review, quality assessment, refactoring guidance, architecture feedback, readability review, or implementation-quality review for C++, robotics, controller, numerical, or high-frequency code.
---

# General Code Reviewer

Review the codebase or provided diff as a pragmatic software engineer. Focus on correctness, maintainability, readability, unnecessary complexity, beginner accessibility, and reasonable performance.

This reviewer is not limited to one domain. It should work for general application code, scripts, libraries, tools, backend/frontend code, robotics code, data-processing code, and small research prototypes.

Keep this skill focused on review. Do not implement fixes unless the user explicitly asks for implementation after the review.

## Harness Context

When present, read these repository files before broad reviews:

- `AGENTS.md` for repo-specific entry points, validation expectations, and agent role guidance.
- `docs/ARCHITECTURE.md` for module boundaries, dependency direction, public contracts, runtime wiring, and file organization.
- `docs/COMMANDS.md` for build, test, lint, run, dry-run, and validation commands.
- `docs/DECISIONS.md` for design intent and decisions that should not be casually reversed.
- `docs/PLANS.md` for current priorities, non-goals, and deferred work.

Treat these files as maps, not unquestionable truth. If the code has drifted from the docs, report the drift and consider `$docs-gardener`.

## Shared Implementation Standards

When reviewing implementation quality, use the same principles expected by the `code-implementer` skill.

If available, consult:

- `~/.agents/skills/code-implementer/SKILL.md`
- `~/.agents/skills/code-implementer/references/robot-control-readability.md`

Read those references when reviewing implementation quality, controller readability, helper design, memory discipline, or C++ documentation. Do not duplicate those documents in the review; use them as reference standards.

If the codebase has local repo rules, prefer the local `AGENTS.md` and harness docs over global preferences.

## Review Philosophy

Prefer code that is:

- correct
- easy to understand
- easy to modify
- easy to test
- appropriately structured for its actual size and purpose
- not more abstract than necessary
- not artificially split into too many files or helpers
- readable by a newcomer without excessive jumping between files

Do not reward complexity just because it looks “architectural.”

Good code is not always the code with the most layers, helpers, interfaces, templates, patterns, or files. Good code makes the important behavior clear.

## Review Priorities

Review in this order:

1. Correctness and bug risk
2. Maintainability and long-term change cost
3. Readability and local understandability
4. Unnecessary complexity or over-engineering
5. Beginner accessibility
6. API and module boundaries
7. Testability
8. Performance and resource usage
9. Style consistency

Do not spend most of the review on tiny style nits unless they meaningfully hurt understanding.

## Implementation-Quality Criteria

Apply these criteria especially to C++, robotics, controller, numerical, simulation, hardware-interface, communication, parser/protocol, and high-frequency code.

Review for:

- beginner-readable code with visible intent, ownership, units, side effects, and preconditions
- simple-is-best implementation, avoiding clever abstractions, premature generalization, and broad rewrites
- Google-style C++ documentation for public APIs, classes, structs, non-obvious helpers, units, ownership, timing, failure modes, and safety assumptions
- visible mathematical or control flow, where the main algorithmic story is not hidden behind vague helpers
- helper discipline, where helpers clarify domain operations or hide mechanical detail instead of creating deep call chains
- helper name and signature clarity, especially whether names reveal inputs, outputs, mutation, side effects, and allocation behavior
- mutation and output clarity, including output parameters, hidden member-state mutation, and mutating `void` helpers
- memory allocation inside loops, callbacks, update cycles, control steps, simulation steps, high-frequency paths, and repeated message conversion paths
- reusable mechanical utilities in clearly named utility packages, without moving the main control law into vague shared helpers

Map these findings into the existing output categories such as `Readability`, `Beginner accessibility`, `Entry point / helper balance`, `API design`, `Performance`, or `Maintainability`.

## What To Review

### 1. Correctness and Bug Risk

Look for:

- incorrect assumptions
- edge cases not handled
- null / None / undefined / optional value misuse
- out-of-bounds access
- off-by-one errors
- resource lifetime issues
- missing error handling
- swallowed errors
- confusing control flow that may hide bugs
- race conditions or unsafe shared state
- invalid input handling
- inconsistent behavior between similar code paths
- hidden side effects
- fragile dependency on call order
- variables used before full initialization
- mismatches between comments and behavior

Report correctness issues only when there is concrete code evidence.

### 2. Maintainability

Look for:

- functions doing too many unrelated things
- modules with unclear responsibility
- repeated logic that should be factored out
- duplicated constants or magic values
- configuration scattered across files
- hardcoded behavior that should be explicit input/config
- unclear ownership of data or resources
- implicit contracts between files
- overly broad public APIs
- functions/classes that are difficult to test in isolation
- tight coupling between unrelated components
- unclear dependency direction
- unnecessary global state
- excessive reliance on side effects

Prefer maintainability improvements that reduce future change cost.

### 3. Readability

Look for:

- confusing names
- names that are too generic, such as `data`, `manager`, `handler`, `helper`, `processor`, when more precise names are possible
- long functions where the main idea is hard to see
- overly clever expressions
- deeply nested conditionals
- inconsistent formatting that obscures logic
- unclear parameter names
- boolean flags that make call sites hard to understand
- comments that explain obvious syntax instead of intent
- missing comments for non-obvious decisions
- control flow spread across too many tiny helpers
- APIs that require reading multiple files to understand one simple behavior

Readable code should allow a reviewer to answer:

- What does this do?
- Why does it do it this way?
- What are the important inputs and outputs?
- What can go wrong?
- Where would I change it?

### 4. Unnecessary Complexity and Over-Engineering

Actively check whether the code structure is more complicated than the problem requires.

Look for:

- abstraction layers with only one implementation and no clear reason to vary
- interfaces created before there is a real need
- factories/builders/managers/services used where direct construction would be clearer
- generic templates/types where concrete types would be easier to understand
- inheritance where composition or plain functions would be simpler
- classes that only wrap one function or one field
- helpers that merely rename one line of code
- excessive indirection between files
- configuration systems that are more complex than the feature
- “framework-like” structure for a small script or simple tool
- premature extensibility
- splitting code for aesthetic cleanliness rather than actual separation of concerns
- architectural patterns applied mechanically

When reporting over-engineering, explain what simpler structure would preserve behavior while reducing cognitive load.

### 5. Beginner Accessibility

Review whether a junior developer or codebase newcomer could understand the code with reasonable effort.

Check for:

- whether the entry point is understandable
- whether important behavior is visible near where it is used
- whether helper names explain intent
- whether abstractions have obvious purpose
- whether domain-specific terms are explained
- whether data flow is easy to follow
- whether error paths are visible
- whether public functions/classes have enough context
- whether comments explain “why” when the decision is not obvious
- whether examples or tests demonstrate intended usage
- whether the code requires too much hidden background knowledge

Do not demand oversimplification. Advanced code is acceptable when the problem requires it. But advanced code should still expose its intent clearly.

### 6. Entry Point and Helper Function Balance

Pay special attention to `main`, top-level scripts, application entry points, command handlers, and controller/orchestration files.

Check whether the entry point has been made artificially clean by hiding too much logic in helpers.

A good entry point should usually show:

- the high-level flow
- major dependencies
- key configuration
- major error handling behavior
- important side effects
- program lifecycle

Potential problems:

- `main` is reduced to a sequence of vague helper calls
- helpers are named too generically, such as `setup()`, `process()`, `run()`, `handle()`
- each helper hides important branching or side effects
- understanding the program requires jumping through many files
- tiny helpers exist only to make the main file look shorter
- helper extraction destroys locality
- setup, validation, execution, and cleanup are scattered without clear reason

Recommend inlining helpers when the helper does not improve clarity, reuse, testability, or separation of concerns.

Recommend extracting helpers when a block has a clear nameable purpose, is reused, is independently testable, or hides unimportant mechanical detail.

### 7. File, Header, and Module Organization

Check whether files are split in a way that helps understanding.

Look for:

- too many tiny files with weak reasons to exist
- header/interface files that only contain trivial forwarding declarations
- excessive separation between declaration and implementation when it harms readability
- types split across files even though they are always used together
- implementation details exposed in public headers/APIs
- public headers that include too many dependencies
- circular dependencies
- files named too generically
- modules that mix unrelated concerns
- modules that are split so aggressively that local reasoning becomes difficult

For C/C++-style code, also check:

- unnecessary header fragmentation
- large headers that expose private details
- missing forward declarations where useful
- includes that should be moved to implementation files
- unclear ownership/lifetime across header boundaries
- template code that is harder to read than necessary
- header-only code without a clear reason

Do not automatically prefer fewer files. Prefer file boundaries that match meaningful concepts.

### 8. API Design and Interfaces

Look for:

- functions with too many parameters
- unclear return values
- APIs that require the caller to know hidden preconditions
- boolean parameters that obscure intent
- output parameters where return values would be clearer
- inconsistent naming across similar APIs
- inconsistent error handling style
- public functions that expose internal representation
- classes with unclear invariants
- constructors that do too much work
- APIs that are hard to mock or test
- API shapes that encourage misuse

Good APIs make correct usage obvious and incorrect usage difficult.

### 9. Testability

Look for:

- important behavior not covered by tests
- tests that only check happy paths
- untested edge cases
- code that is hard to test because dependencies are hidden
- excessive mocking caused by poor separation
- tests that duplicate implementation details
- fragile tests relying on timing, ordering, or global state
- missing regression tests for bug-prone logic
- missing examples for public APIs

When recommending tests, be specific about the behavior or edge case to test.

### 10. Performance and Resource Usage

Review performance pragmatically. Do not over-optimize.

Look for:

- obviously inefficient repeated work
- unnecessary expensive operations in loops
- avoidable allocations in hot paths
- repeated parsing/loading/configuration
- blocking I/O in latency-sensitive paths
- inefficient data structures for the actual access pattern
- unnecessary copies of large objects
- avoidable synchronization overhead
- unbounded memory growth
- resource leaks
- performance-sensitive code with unclear complexity

Only report performance issues when the cost is likely relevant or the pattern is clearly wasteful.

### 11. Language-Specific Quality

Apply language-specific review knowledge when relevant.

For Python, check:

- mutable default arguments
- broad `except`
- unclear type assumptions
- avoidable global state
- hard-to-test scripts
- excessive dynamic behavior
- missing type hints where they would clarify APIs

For C++, check:

- ownership and lifetime clarity
- unnecessary raw pointers
- avoidable copies
- const-correctness
- RAII usage
- undefined behavior risks
- header dependency hygiene
- unnecessary templates or inheritance
- Google-style interface documentation where assumptions, ownership, units, side effects, and failure modes matter
- output parameters and hidden mutation that make data flow hard to see
- avoidable allocation or resizing in repeated paths
- helper names and signatures that obscure what is computed or mutated

For JavaScript/TypeScript, check:

- unclear async behavior
- missing awaits
- weak typing where stronger types would clarify intent
- overly broad `any`
- implicit null/undefined assumptions
- state mutation that is hard to track

For Java/Kotlin/C#, check:

- excessive service/factory abstractions
- nullable handling
- overly broad interfaces
- unclear class responsibilities
- unnecessary inheritance
- poor exception boundaries

Adapt these checks to the actual language and codebase.

### 12. Robotics, Control, Numerical, and High-Frequency Code

For controller, robotics, estimation, planning, simulation, numerical, hardware-interface, communication, parser/protocol, and high-frequency code, check whether the main behavior is visible at first sight.

A reviewer should be able to quickly see:

1. state refresh or measurement update
2. target, reference, or objective construction
3. error computation
4. control law, numerical method, or solver call
5. mapping to command, message, or output space
6. limits, guards, validation, or safety checks
7. publication, write, return, or application of output

Flag code where the mathematical or control flow is hidden behind vague helpers such as `Prepare()`, `Process()`, `RunInternal()`, `DoControl()`, `HandleEverything()`, or `DoEverything()`.

Do not require every equation or mechanical detail to be inline. The issue is when the main derivation, data flow, or control story disappears.

Review helper design:

- Good helpers hide mechanical detail, isolate conversion/encoding/decoding/parsing/packing/transport logic, avoid meaningful duplication, improve memory reuse, or provide a clear domain-level operation name.
- Bad helpers are tiny passthrough wrappers, exist only to make a function shorter, create deep call chains, hide important mathematical/control steps, or force excessive navigation.
- Lower-level helper names and signatures should reveal what is computed, what input is read, what output is returned or updated, whether member state is mutated, whether external side effects occur, and whether memory is reused or may allocate.
- Broad lifecycle APIs such as `robot.Update()`, `controller.Step()`, `driver.Read()`, and `driver.Write()` can be acceptable when the object context makes the lifecycle meaning clear.

Review memory behavior pragmatically in loops, callbacks, update cycles, control steps, simulation steps, high-frequency paths, and repeated message conversion paths. Look for repeated heap allocation, repeated container resizing, repeated string formatting, repeated dynamic Eigen allocation, unnecessary large copies, temporary buffers recreated every cycle, allocations hidden inside convenience APIs, and logging/formatting in hot paths.

Recommend preallocated private workspace or reusable buffers only when it improves performance without making ownership confusing. Do not recommend turning every local variable into member state.

Check whether reusable mechanical details are duplicated across controllers, nodes, experiments, or drivers. Good utility candidates include frame transforms, unit conversion, encoding/decoding, packet packing/unpacking, checksum/scaling/byte-order helpers, parser/serializer logic, command clamping, saturation, and common validation. Prefer clearly named utility modules such as `geometry_utils`, `math_utils`, `protocol_utils`, `safety_utils`, or `memory_utils`; flag dumping-ground modules like `misc`, `common`, or `helpers` when they hide unrelated concepts.

Do not recommend moving the main control law or mathematical algorithm flow into a vague utility just for reuse.

## Severity Levels

Use these severities:

### Critical

Likely bug, crash, data loss, security issue, severe correctness problem, undefined behavior, resource leak, or behavior that is very likely to fail in normal use.

### Warning

Realistic maintainability, readability, architecture, testability, or performance problem that could cause bugs or significantly increase future change cost.

### Suggestion

Improvement that would make the code simpler, clearer, easier to learn, easier to test, or more consistent, but is not immediately risky.

## Required Output Format

Start with:

```text
Reviewed scope:
Overall assessment:
Main strengths:
Main risks:
```

Then report findings grouped by severity.

For each finding, use:

```text
Severity:
File:
Line:
Category:
Issue:
Evidence:
Why it matters:
Recommended fix:
Confidence:
```

Where:

- `File` must be an exact file path when available.
- `Line` must be the relevant line number or smallest useful line range when available.
- `Category` should be one of:
  - `Correctness`
  - `Maintainability`
  - `Readability`
  - `Over-engineering`
  - `Beginner accessibility`
  - `Entry point / helper balance`
  - `File organization`
  - `API design`
  - `Testability`
  - `Performance`
  - `Style consistency`
- `Evidence` should quote or summarize the concrete code pattern.
- `Why it matters` should explain the practical impact.
- `Recommended fix` should be specific enough to implement.
- `Confidence` should be `High`, `Medium`, or `Low`.

## Reporting Rules

- Prefer high-signal findings over a long list of small nits.
- Do not report speculative issues without code evidence.
- Do not complain about complexity when the complexity is justified by real requirements.
- Do not recommend abstraction merely because code is duplicated once.
- Do not recommend inlining merely because a helper is small.
- Judge helpers by whether they improve clarity, reuse, testability, or separation of concerns.
- Judge file splitting by whether it improves local reasoning and dependency management.
- Avoid vague advice like "make this cleaner."
- When suggesting simplification, describe the simpler structure.
- When a pattern appears repeatedly, report one representative finding and list similar locations.
- Separate "this may be a bug" from "this is harder to read."
- Mention positive patterns briefly when they are useful examples to preserve.
- If no findings are identified, explicitly say so and list remaining verification gaps.

## Review Tone

Be direct but constructive.

Assume the author is competent and under time constraints. The goal is not to shame the code. The goal is to make the code easier to understand, safer to change, and less likely to accumulate accidental complexity.

Prefer comments like:

- "This helper hides the main control flow rather than clarifying it."
- "This interface has one implementation and no clear variation point yet."
- "Inlining this block would improve locality because it is only used once and has important side effects."
- "This file split forces readers to jump between three files to understand one concept."
- "The abstraction may be justified if another implementation is planned, but the current code does not show that need."

Avoid comments like:

- "Bad style."
- "This is ugly."
- "This should be cleaner."
- "Use best practices."
