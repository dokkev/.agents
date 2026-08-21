---
name: architecture-designer
description: Design or revise software architecture for robotics, robot control, hardware integration, simulation, reinforcement learning, and ROS 2 research code. Use when defining class responsibilities, mutable-state ownership, dependency direction, runtime orchestration, finite-state-machine structure, RL environment and training workflow, ROS 2 package boundaries, header/type organization, hardware-control separation, lifecycle, failure paths, or real-time boundaries before implementation. Do not use for implementation-only work or implementation-quality review unless the user also requests architectural redesign.
---

# Architecture Designer

Prefer short, direct designs that lead to short, direct Python and C++ code.
Optimize for architecture that an individual or small research team can
understand and modify quickly, not for a commercial codebase that anticipates
every hypothetical future requirement.

Design the smallest clear robotics research architecture. Preserve correctness,
hardware safety, numerical validity, and demonstrated real-time needs without
importing production-scale infrastructure.

## Workflow

1. Read the closest `AGENTS.md`. Read `docs/ARCHITECTURE.md` as the repository's
   navigational map and current accepted architectural state: use it to locate
   canonical entry points, ownership boundaries, dependencies, and runtime flow,
   then verify the affected area against current source before proposing changes.
   Read `docs/COMMANDS.md` only when build or deployment affects the design.
2. Inspect the smallest relevant component graph, public types, runtime entry
   point, build targets, and executable contracts.
3. State the problem and constraints; separate defects from optional changes.
4. Load only the reference contracts needed for the decision.
5. Trace one complete cycle and important failure paths.
6. Give each responsibility and mutable datum one owner, keep dependencies
   one-way, and prefer the fewest cohesive boundaries.
7. Deliver the runtime flow, ownership, dependencies, lifecycle, failure policy,
   migration impact, and unresolved choices.

Architecture work does not authorize implementation. When both are requested,
preserve the approved design and local implementation standards.

Do not present a proposed target architecture as current repository state. Keep
verified current structure and proposed changes explicit when they differ.

## Sub-agent Delegation

Default to one agent. Delegate only bounded, independent inspection that needs
no shared mutation or unresolved upstream decision. Give each sub-agent one
question and read-only scope. Keep architecture synthesis, trade-offs, and final
decisions with the parent. Do not duplicate investigations or recursively
delegate by default.

## Load Context Progressively

Start with zero references. Choose one primary reference for the dominant
concern. Add another only when the primary contract leaves a real gap; do not
load overlapping sections from multiple references.

For a reference over 100 lines, use the bundled reader. Resolve both paths from
this skill directory; commands below are shown from that directory.

```bash
python3 scripts/read_reference.py references/runtime-dataflow.md --list
python3 scripts/read_reference.py references/runtime-dataflow.md \
  --section "Core Contract" --section "Command Flow"
```

Read `Core Contract` plus one or two matching H2 sections. Read a short file in
full. Read a full long reference only when:

- editing or reviewing that reference itself;
- resolving a conflict spanning three or more sections;
- performing a broad architecture, safety, or consistency audit; or
- selected sections expose an unresolved dependency on the rest of the file.

Apply the same heading-first rule to long repository documents; they need not
contain `Core Contract`. Explicit safe repository contracts take precedence.

## Reference Selection

| Design question | Read |
| --- | --- |
| class responsibility, component ownership, public domain types, lifecycle, failure, or dependency direction | `references/class.md` |
| RL project structure, Isaac Lab workflow selection, environment/task ownership, observation/action/reward flow, training/evaluation separation, or policy-learning workflow | `references/rl-workflow.md` |
| Pinocchio-based `RobotSystem`, authoritative model-based robot state, state/model coherence, live versus rollout state, or optional stored command handoff | `references/robot-system.md` |
| control-cycle ordering, ROS 2 `read-update-write` flow, thin ROS wrappers, `RobotHardware` orchestration, ROS interface storage, command flow, or multi-rate runtime boundaries | `references/runtime-dataflow.md` |
| states, modes, transitions, state lifecycle, FSM coordination, trajectory generation, or motion planning | `references/finite-state-machine.md` |
| whether to create, merge, or split a ROS 2 package, target, node, interface package, hardware package, description package, or bringup package | `references/ros2-package.md` |
| C++ header boundary, include dependency, forward declaration, nested/shared type placement, template definition, or file split | `references/header.md` |

## Core Rules

- Make the main cycle visible at the runtime or lifecycle entry point.
- Centralize orchestration, not intelligence or unrestricted mutable access.
- Pass stable domain values across boundaries instead of live components.
- Keep control, model, hardware, transport, ROS, and vendor dependencies one-way.
- Add abstractions only for a real ownership, substitution, dependency,
  deployment, test, or reuse boundary.
- Make failure, lifecycle, configuration, timing, units, frames, and command
  stages explicit.
- Default to single-threaded execution; add concurrency only for a demonstrated
  execution-context or timing boundary.
- Define ownership and validation boundaries without forcing one method spelling.

## Deliverable

Lead with the recommendation, then the needed flow, ownership, dependencies,
lifecycle, failures, migration, rejected alternatives, and open decisions. Show
package/header changes when relevant. Use a diagram only when materially clearer.

When the proposal changes canonical entry points, package ownership, dependency
direction, or runtime flow, identify which parts of `docs/ARCHITECTURE.md` should
be updated after implementation so the repository map remains accurate.
