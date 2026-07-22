---
name: architecture-designer
description: Design or revise software architecture for robotics, robot control, hardware integration, simulation, and ROS 2 research code. Use when defining class responsibilities, mutable-state ownership, dependency direction, runtime orchestration, finite-state-machine structure, ROS 2 package boundaries, header/type organization, hardware-control separation, lifecycle, failure paths, or real-time boundaries before implementation. Do not use for implementation-only work or implementation-quality review unless the user also requests architectural redesign.
---

# Architecture Designer

Design the smallest architecture that makes ownership, dependency direction,
control flow, lifecycle, and failure behavior obvious to a research-code reader.

Optimize for a laboratory codebase that collaborators can understand and modify
quickly. Preserve correctness, hardware safety, numerical validity, and actual
real-time requirements without importing production-scale infrastructure.

## Workflow

1. Read the closest `AGENTS.md` and relevant repository maps:
   - `docs/ARCHITECTURE.md`
   - `docs/DECISIONS.md`
   - `docs/PLANS.md`
   - `docs/COMMANDS.md`
2. Inspect the existing component graph, public types, runtime entry point,
   build targets, and tests before proposing new boundaries.
3. State the architectural problem and constraints. Distinguish current defects
   from optional improvements.
4. Trace one complete control cycle and the important failure paths.
5. Select and read only the references relevant to the task.
6. Assign each responsibility and mutable state to one owner. Make dependencies
   and external boundaries one-way.
7. Prefer the fewest cohesive classes, packages, interfaces, and files that
   satisfy demonstrated boundaries.
8. Show the proposed runtime flow, responsibilities, dependencies, lifecycle,
   failure policy, and migration impact.
9. Record unresolved choices instead of hiding them behind a generic manager,
   context object, or speculative abstraction.

Do not silently turn an architecture task into a broad implementation rewrite.
When implementation is requested, preserve the approved design and use the
repository's implementation standards.

## Reference Selection

| Design question | Read |
| --- | --- |
| class responsibility, component ownership, runtime flow, hardware boundary, public domain types, lifecycle, failure, or dependency direction | `references/class.md` |
| authoritative robot state, controller-facing state access, state validation, state/model coherence, live versus rollout state, or `RobotSystem` responsibility | `references/robot-system.md` |
| states, modes, transitions, state lifecycle, `FSMHandler`, trajectory generation, or motion planning | `references/finite-state-machine.md` |
| whether to create, merge, or split a ROS 2 package, target, node, interface package, hardware package, description package, or bringup package | `references/ros2-package.md` |
| C++ header boundary, include dependency, forward declaration, nested/shared type placement, template definition, or file split | `references/header.md` |

Read multiple references when a decision crosses concerns. Repository-specific
hardware, timing, frame, unit, and deployment contracts override general
preferences when they are explicit and safe.

## Core Rules

- Make the main control path read like a story at the runtime or lifecycle entry
  point.
- Centralize orchestration, not intelligence, mutable state, or unrestricted
  access.
- Give every class one explainable role and every mutable state one owner.
- Pass stable domain data such as `RobotState`, `Reference`, and `RobotCommand`
  across boundaries instead of exposing live mutable components.
- Keep control, model, hardware, transport, ROS, and vendor dependencies flowing
  in one direction.
- Use composition and shallow interfaces. Add abstractions only for a real
  substitution, dependency, deployment, test, or reuse boundary.
- Make failure, lifecycle, configuration, timing, units, frames, and command
  stages part of the design contract.
- Default to single-threaded execution. Add concurrency only for a demonstrated
  timing or execution-context boundary.
- Keep implementation-specific accessor names and validation mechanics in
  implementation standards. Architecture defines ownership and validation
  boundaries, not a mandatory spelling for every method.

## Deliverable

Lead with the recommended design. Include only the detail needed to implement
or decide it:

1. runtime/control flow;
2. component responsibilities and owned mutable state;
3. dependency and external boundaries;
4. lifecycle, failure, and real-time behavior;
5. package/header changes when relevant;
6. rejected alternatives and why they do not fit current constraints;
7. migration steps and open decisions.

Use a diagram only when topology or lifecycle is materially clearer than a
short table or code sketch. Do not disguise uncertainty with extra layers.
