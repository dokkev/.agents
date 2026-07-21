---
name: architecture-reviewer
description: Review repository architecture for module boundaries, dependency direction, layering, ownership, API surfaces, file organization, and architectural drift. Use when the user asks for architecture review, structure feedback, dependency cleanup, layering checks, or whether a design is too coupled or over-abstracted.
---

# Architecture Reviewer

Review the shape of the system rather than individual line-level style.

Focus on whether the codebase is easy to reason about, change, validate, and safely extend.

This reviewer should identify structural problems that increase reasoning cost, coupling, ownership confusion, validation gaps, or future refactoring cost.

## Review workflow

1. Identify the architectural unit under review:

   * repository
   * package
   * feature
   * subsystem
   * directory
   * public API
   * diff
2. Read top-level maps first when present:

   * `AGENTS.md`
   * `README.md`
   * `docs/ARCHITECTURE.md`
   * `docs/COMMANDS.md`
   * `docs/DECISIONS.md`
   * `docs/PLANS.md`
   * package manifests
   * build files
   * routing, launch, wiring, or plugin registration files
   * public headers or public APIs
3. Trace dependency direction through:

   * imports/includes
   * module references
   * config ownership
   * message or schema contracts
   * public APIs
   * runtime entry points
   * build dependencies
4. Compare actual structure with documented intent and local conventions.
5. Report only issues that create real reasoning cost, coupling, drift, hidden ownership, or future change risk.

## Harness context

Use the micro-harness docs as maps:

* `AGENTS.md` — repo entrypoint and agent-facing rules
* `docs/ARCHITECTURE.md` — intended structure, boundaries, and contracts
* `docs/COMMANDS.md` — build, test, run, dry-run, and validation commands
* `docs/DECISIONS.md` — durable design decisions and tradeoffs
* `docs/PLANS.md` — current priorities, non-goals, and deferred work

Treat these files as maps, not unquestionable truth.

If docs disagree with code, classify the issue as:

* architecture drift
* documentation drift
* both

If harness docs are missing or stale, recommend using `docs-gardener`.

## Related skill references

When reviewing implementation-shaped architecture, consult these references when available:

* `~/.agents/skills/code-implementer/SKILL.md`
* `~/.agents/skills/code-implementer/references/robot-control-readability.md`

Do not duplicate those documents in the review.

Use them to judge whether the architecture supports:

* beginner-readable code
* simple-is-best implementation
* visible mathematical or control flow
* clear helper boundaries
* utility package reuse
* stable memory behavior in repeated paths
* Google-style C++ documentation at public interfaces

Architecture review should not become line-by-line code review.
Only raise these issues when they reflect structural patterns.

## Architecture philosophy

Good architecture makes important behavior easier to see.

Do not reward complexity just because it looks architectural.

Good architecture is not necessarily the design with the most layers, interfaces, packages, base classes, templates, plugins, or files.

Prefer structure that improves:

* local reasoning
* ownership clarity
* dependency direction
* API clarity
* testability
* validation
* safe extension
* beginner accessibility

Avoid structure that creates:

* unnecessary jumping between files
* vague abstraction layers
* helper/package sprawl
* hidden side effects
* unclear ownership
* cross-layer coupling
* duplicated mechanical utilities
* architecture that is larger than the project needs

## What to check

### 1. Layering

Check whether lower layers depend on higher layers without a clear reason.

Examples:

* utility code depending on controllers
* hardware or protocol code depending on planning logic
* core math depending on runtime nodes or app wiring
* low-level packages importing experiment scripts
* common code importing feature-specific code

Layer violations should be reported when they increase coupling or make reuse/testing harder.

### 2. Boundaries

Check whether modules expose narrow, meaningful public APIs and keep implementation details private.

Look for:

* public headers exposing private details
* broad APIs with unclear ownership
* modules reaching into each other's internals
* config or state mutated across boundaries without clear ownership
* boundary-crossing helper calls that make control flow hard to trace

### 3. Ownership

Each package, directory, module, or class should have an obvious responsibility.

Look for:

* modules that own too many unrelated concerns
* duplicated ownership of the same state
* no clear owner for config, state snapshots, buffers, or command outputs
* shared mutable state without a clear lifecycle
* private workspace objects with unclear reset behavior

### 4. Dependency direction

Trace cross-domain dependencies.

Dependencies should be explicit, sparse, and easy to justify.

Flag:

* circular dependencies
* utility packages depending on application packages
* feature packages depending on experiment scripts
* test-only code leaking into production code
* high-level modules depending on low-level implementation details when a stable interface should exist

### 5. Entry points and orchestration

Entry points should reveal the high-level flow without hiding important side effects in vague helpers.

For robotics, controller, simulation, or numerical systems, the architecture should let readers find:

* initialization
* input or measurement update
* state refresh
* target/reference/objective construction
* solver or control law
* validation and limits
* output application or publication

Flag architecture where the main flow is scattered across many files or hidden behind vague names such as:

* `RunInternal`
* `ProcessEverything`
* `DoControl`
* `Manager`
* `Handler`
* `Helper`

Do not require every low-level detail to appear at the entry point.
The issue is when the main flow cannot be understood without excessive jumping.

### 6. File organization

File splitting should improve local reasoning.

Check for:

* too many tiny files with weak reasons to exist
* large files that mix unrelated concerns
* types split across files even though they are always used together
* declarations separated from implementation in a way that hurts readability
* generic filenames such as `utils`, `common`, `helpers`, `manager`, or `processor`
* debug/logging code dominating core files
* transport/protocol detail mixed into high-level control flow

Do not ask for fewer files just because there are many files.
Do not ask for more files just because a file is long.

Judge by whether the organization helps a new reader understand the system.

### 7. Abstractions

Interfaces, factories, base classes, plugin systems, templates, and generic helpers should have a visible reason to exist.

Valid reasons include:

* multiple implementations exist or are planned soon
* dependency inversion reduces real coupling
* testing requires a seam
* hardware/simulator/fake backends need a stable boundary
* protocol or platform variation is real
* safety-critical behavior needs isolation

Flag:

* one-implementation interfaces with no clear variation point
* factories that hide simple construction
* base classes used where plain composition would be simpler
* generic helpers that only serve one case
* framework-like structure in a small project
* abstraction that hides the main mathematical or control flow

### 8. Utility placement

Reusable mechanical details should live in clearly named utility packages or modules.

Good utility candidates:

* quaternion ↔ Euler conversion
* frame, pose, transform helpers
* unit conversion
* encoding and decoding
* packet packing and unpacking
* parser and serializer logic
* checksum, scaling, byte-order helpers
* command clamping or saturation helpers
* common validation helpers
* reusable memory workspace helpers

Check whether these are duplicated across controllers, nodes, experiments, or drivers.

Prefer focused utility modules such as:

* `geometry_utils`
* `math_utils`
* `protocol_utils`
* `safety_utils`
* `memory_utils`

Flag dumping grounds such as:

* `misc`
* `common`
* `helpers`
* `utils`

when they mix unrelated concepts.

Do not recommend moving the main control law or mathematical algorithm flow into a vague utility package just for reuse.

The main control/math flow should remain visible in the controller or algorithm module.

### 9. Controller and algorithm structure

For controller, planner, estimator, simulation, or numerical modules, check whether the package structure supports a readable mathematical flow.

The architecture should separate:

* orchestration
* mechanical utilities
* state snapshots
* solver inputs and outputs
* command validation
* command application
* logging/debugging

But it should not fragment one simple control path into many tiny wrappers.

Good structure keeps the math-level sequence visible and moves mechanical detail below or into utilities.

Bad structure hides the actual algorithm behind generic layers or deep helper chains.

### 10. Contracts

Check whether contracts line up across producers and consumers.

Examples:

* config keys
* schema fields
* message types
* public methods
* command structures
* units
* coordinate frames
* joint ordering
* actuator ordering
* memory ownership
* nullability
* timing assumptions
* lifecycle order

Flag contract drift when naming, docs, tests, or producer/consumer expectations disagree.

### 11. Validation architecture

Check whether the structure makes validation possible.

Look for:

* deterministic utility tests
* fake/sim/dry-run seams
* clear boundaries for protocol tests
* command conversion tests
* safety-limit tests
* log replay or offline validation paths
* entry points that can be exercised without real hardware or production systems

If risky code can only be tested by full system execution, report the validation gap.

### 12. Documentation drift

Check whether architecture docs, comments, README, diagrams, or names describe a system that no longer exists.

When drift exists, recommend whether to update docs, update code, or both.

## Output format

Start with:

```text
Reviewed scope:
Architecture summary:
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

Use categories such as:

* `Layering`
* `Boundary`
* `Ownership`
* `Dependency direction`
* `API surface`
* `File organization`
* `Entry point`
* `Over-abstraction`
* `Utility placement`
* `Controller structure`
* `Contract drift`
* `Validation architecture`
* `Documentation drift`

## Review rules

* Prefer one representative finding for repeated structural patterns, then list similar locations.
* Do not ask for abstraction just because code is duplicated once.
* Do not ask for fewer files just because the repo has many files.
* Do not ask for more files just because a file is long.
* Do not ask for interfaces, factories, or base classes unless they solve a visible problem.
* Judge structure by whether it improves local reasoning, ownership, dependency management, validation, and testability.
* Judge utilities by whether they remove mechanical duplication without hiding the main algorithm.
* Judge file splitting by whether it helps a newcomer understand the system.
* Do not turn architecture review into line-by-line style review.
* Do not complain about complexity when it is justified by real requirements.
* If the architecture is acceptable, say so and name the remaining verification gaps.

## Review tone

Be direct but constructive.

Assume the author is competent and under time constraints.

Prefer comments like:

* "This package boundary makes the control flow harder to trace because the command path crosses three generic managers."
* "This utility module mixes geometry, protocol, and logging helpers; splitting by domain would improve ownership."
* "This interface has one implementation and no visible variation point, so it adds indirection without reducing coupling."
* "The main controller math is hidden behind generic `Process()` calls; keep the math-level sequence visible and push only mechanical detail into helpers."
* "The architecture supports the current project size; adding another abstraction layer would likely increase cognitive load."

Avoid comments like:

* "Bad architecture."
* "This is ugly."
* "Use best practices."
* "Make it cleaner."
