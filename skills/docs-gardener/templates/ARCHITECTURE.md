# Architecture

This document is the navigational map of the current accepted codebase.

Its primary purpose is to let a new contributor or agent understand the
repository quickly enough to know:

- what the repository owns;
- how the main runtime, scientific, or data flow works;
- where the important code lives;
- which package owns each responsibility;
- which files or symbols are canonical entry points;
- which dependencies are allowed or forbidden;
- which architecture is intentionally absent.

Describe the code that actually exists.

When a migration is incomplete, distinguish clearly between the current
implementation and the accepted target architecture. Do not silently describe
a desired future structure as if it already exists.

## At a glance

Summarize the repository in one short paragraph.

Then show the primary production flow at package or subsystem level.

Prefer scientific or runtime concepts over low-level implementation detail.

~~~text
input or morphology
-> representation
-> computation
-> observation
-> evaluation
-> output or optimization
~~~

Keep validation, reporting, development tools, GUI, offline analysis, and other
consumers outside this production flow when they are not production
dependencies.

## Repository map

Give the reader a compact view of the important top-level areas.

| Path | Purpose | Notes |
| --- | --- | --- |
| path/to/domain | Primary domain model | Add only useful ownership context |
| path/to/runtime | Runtime or solver implementation | Identify important backend if relevant |
| path/to/evaluation | Evaluation or orchestration | Distinguish production from validation |
| path/to/validation | Scientific or regression validation | Must not become a production dependency |

Include only directories that materially help someone understand the codebase.
Do not turn this into a complete directory listing.

## Code map

Give readers direct starting points for common questions.

| If you need to understand... | Start here | Then inspect |
| --- | --- | --- |
| domain representation | path/to/module | related construction or validation |
| public runtime API | path/to/file.py | owning implementation |
| primary computation | path/to/backend.py | local helpers or adapters |
| configuration or protocol | path/to/config.py | consumers |
| objective or scoring | path/to/objective.py | evaluator or optimizer |
| optimization campaign | path/to/adapter.py | design space and registry |
| scientific validation | path/to/validation | production APIs it consumes |

Use real paths and stable symbols.

Prefer canonical entry points over exhaustive lists of helper files.

A reader should normally know where to start after reading this section.

## Package ownership

Describe what each package owns and, when useful, what it intentionally does
not own.

| Package or path | Owns | Does not own |
| --- | --- | --- |
| package_a | domain parameters and invariants | solver execution |
| package_b | discretization and representation | scientific scoring |
| package_c | runtime computation | optimization policy |
| package_d | orchestration and evaluation | backend implementation |

Ownership should answer where new code for a responsibility belongs, which
package is authoritative for a concept, and which neighboring package should
not absorb that responsibility.

Avoid duplicating implementation details already obvious from source code.

## Important execution paths

Describe the small number of execution paths that are essential for
understanding the system.

For each path, identify:

- the public or readable entry point;
- the implementation that owns the behavior;
- important state transitions or conversions;
- where expensive or optional dependencies enter;
- where results leave the subsystem.

Prefer concrete paths and stable symbols.

### Primary runtime path

Describe the main production execution path.

~~~text
public entry point
-> owning implementation
-> backend or numerical stage
-> result
~~~

Explain only the transitions that matter architecturally.

### Additional important paths

Add subsections only for genuinely important flows, such as contact
registration, simulation or mechanics, optical or sensor processing, hardware
command flow, evaluation, optimization, persistence, or artifact generation.

Do not create a subsection for every package merely for symmetry.

## Current runtime or scientific contract

Record current behavior that materially changes how the codebase should be
understood.

Examples include:

- evaluation dimensions;
- protocol structure;
- continuous versus independent trajectories;
- lifecycle stages;
- authoritative configuration sources;
- checkpoint semantics;
- identity and provenance rules;
- cache semantics;
- important numerical or physical contracts.

Point to the authoritative implementation or configuration source.

Do not duplicate every numerical value here when doing so would create a second
source of truth. It is useful to state the structure of a protocol even when
exact values remain owned by code.

## Public boundaries

Document important interfaces between packages or subsystems.

| Interface or artifact | Owner | Consumer | Contract |
| --- | --- | --- | --- |
| public function or type | package | package | units, state, semantics |
| persisted artifact | package | package | identity and provenance |
| configuration object | package | package | authoritative settings |

Include units, coordinate frames, ownership, mutability, identity, or lifecycle
semantics when misunderstanding them would create bugs.

Do not list every public function.

## Data and representation boundaries

Describe important representation changes when they matter to correctness.

~~~text
domain object
-> framework representation
-> computation
-> domain result
~~~

State which side owns each conversion.

Keep framework-specific representations at the boundary that requires them when
possible.

## Failure semantics

Document failure categories when downstream code interprets them differently.

Separate expected domain or candidate outcomes from shared infrastructure
failures.

| Failure | Meaning | Handling |
| --- | --- | --- |
| invalid_input | domain constraints are violated | reject before expensive work |
| domain_incompatible | requested condition is unsupported | reject as expected domain outcome |
| computation_failure | candidate-dependent runtime failure | record against candidate |
| infrastructure_failure | shared dependency or runtime unavailable | abort campaign or run |

Do not classify a shared dependency failure as if it were evidence about one
candidate.

Use repository-specific names rather than preserving these examples
mechanically.

## Artifact, cache, and provenance semantics

If the repository persists scientific or evaluation results, describe:

- what identifies a result;
- which configuration contributes to identity;
- which geometry or model provenance is retained;
- what may be cached;
- what may not be reused across incompatible configurations;
- which fields are raw scientific results versus display-only transforms.

Keep display or reporting transforms out of scientific identity unless they are
actually part of the computation.

## Dependency rules

State the important dependency direction explicitly.

~~~text
domain
-> representation
-> runtime
-> observation
-> orchestration
~~~

Then list the important forbidden dependencies.

Examples:

- production packages do not import validation or tests;
- low-level domain packages do not depend on execution frameworks;
- runtime packages do not depend on reporting or GUI code;
- validation consumes production APIs rather than becoming a production layer;
- heavy optional dependencies load only at execution boundaries.

Keep these rules consistent with Package ownership.

## External dependencies

List only external dependencies that materially affect architecture.

For each important dependency, state which package owns the integration,
whether it is required or optional, whether it must remain lazy, and whether it
is a runtime, build, hardware, or validation dependency.

Exact installation commands belong in docs/COMMANDS.md rather than here.

## Validation boundary

Describe how validation relates to production code.

Validation should normally consume production APIs rather than define reusable
production behavior.

State clearly which reference implementations or persisted artifacts are
validation-only, which regression paths are intentionally outside production,
and which dependency directions are allowed between validation and production.

## Intentionally absent architecture

List structures that are deliberately not part of the current architecture when
an agent or contributor might otherwise recreate them.

Examples include removed compatibility packages, deprecated backends, generic
abstraction layers that are intentionally avoided, historical implementations
available only through version control, or deferred subsystems that should not
be rebuilt during unrelated work.

This is not a repository history section. Include only absences that help
prevent incorrect new work.

## Current deviations

List verified places where the current implementation does not yet match the
accepted architecture.

For each deviation, state the current location or behavior, the accepted
direction, and whether the deviation is intentional, temporary, or blocked.

Remove entries when they are resolved. Do not use this section as a backlog or
session log.

## Reading guidance

When changing a subsystem:

1. Start from the relevant entry in Code map.
2. Read the owning package before neighboring consumers.
3. Follow the execution path through one complete operation.
4. Check the relevant public and data boundaries.
5. Confirm dependency direction before adding a new import or abstraction.

Do not infer architecture from stale tests, deleted compatibility code, or
historical naming when this document and the current implementation agree on a
different structure.

## Related documents

- AGENTS.md: repository-specific agent behavior and working rules.
- docs/COMMANDS.md: environments, build and validation commands, external
  runtime requirements, and generated-output locations.

Keep general coding and language-design rules in the applicable reusable skills
rather than duplicating them here.
