---
name: architecture-designer
description: >-
  Design or revise ownership, dependencies, runtime flow, lifecycle, and public
  boundaries in robotics, control, simulation, hardware, or ROS 2 research code.
  Use for a genuine architectural decision or requested redesign, not as a
  mandatory stage of a small implementation or implementation-quality review.
---

# Architecture Designer

Design the smallest structure that a research team can understand and change.
Preserve hardware safety, numerical validity, and demonstrated runtime needs;
do not build infrastructure for hypothetical scale.

## Work on the Actual Decision

Follow applicable repository instructions and the task. Read the relevant part
of `docs/ARCHITECTURE.md` as a map, then inspect affected owners, callers, and
boundaries. Reuse accepted decisions and existing evidence; do not repeat a
repository-wide investigation. Read build commands only when they affect design.

State the unresolved decision and constraints. Give each responsibility and
mutable datum one owner, keep dependency direction clear, and prefer existing
cohesive boundaries. Trace runtime and failure paths when the decision affects
them, not for every class or file change.

Keep current implementation distinct from an accepted target or a new proposal.
Architecture work does not authorize implementation. When both are requested,
implement only the agreed scope and preserve unrelated behavior.

Default to one agent. Delegate only bounded read-only questions that materially
help resolve the decision; keep synthesis with the parent. Do not automatically
add advisors, reviews, tests, or recursive delegation.

## References

Read the sections needed for the decision. Use `scripts/read_reference.py`
optionally for long documents; no reader or heading-list command is required.
Do not load overlapping references simply because they exist.

| Design question | Reference |
| --- | --- |
| Responsibilities, types, state ownership, lifecycle | `references/class.md` |
| Model-based robot state and Pinocchio coherence | `references/robot-system.md` |
| Control cycle, ROS wrappers, command flow, multi-rate boundaries | `references/runtime-dataflow.md` |
| States, transitions, coordination, planning | `references/finite-state-machine.md` |
| ROS 2 package, node, target, deployment boundary | `references/ros2-package.md` |
| C++ headers, type placement, include dependencies | `references/header.md` |

## Design Constraints

Keep scientific or runtime flow visible at its entry point. Centralize
orchestration, not unrestricted mutable access. Pass stable domain values where
appropriate; do not manufacture wrappers around every library type.

Keep control, model, hardware, transport, ROS, and vendor dependencies one-way.
Add an abstraction only for a current ownership, substitution, dependency,
lifecycle, deployment, or reuse need. Preserve explicit failure, units, frames,
timing, and command-stage contracts. Use concurrency only for a demonstrated
execution-context or timing boundary.

## Deliver

Lead with the recommendation and the reasons needed to decide. Include only
relevant ownership, flow, lifecycle, failure, migration, and open questions;
do not fill a standard architecture checklist for its own sake.

Identify documentation updates when canonical entry points or boundaries change.
Do not present proposals as already implemented or verified. Stop at the requested
decision rather than turning it into a larger research or infrastructure project.
