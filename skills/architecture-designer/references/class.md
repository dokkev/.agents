# Class and Component Architecture

Use these rules to design class responsibilities, ownership, runtime flow, and
dependency boundaries in robotics and control software.

## Section Map

- [Core Contract](#core-contract)
- [Make the Control Path Visible](#make-the-control-path-visible)
- [Give Each Class One Role](#give-each-class-one-role)
- [Assign Mutable State to One Owner](#assign-mutable-state-to-one-owner)
- [Keep Dependencies One-Way](#keep-dependencies-one-way)
- [Separate Hardware Mechanics from Control Policy](#separate-hardware-mechanics-from-control-policy)
- [Centralize Orchestration, Not Intelligence](#centralize-orchestration-not-intelligence)
- [Keep the Structure Shallow](#keep-the-structure-shallow)
- [Design Small Domain-Oriented APIs](#design-small-domain-oriented-apis)
- [Make Failure and Lifecycle Explicit](#make-failure-and-lifecycle-explicit)
- [Treat Configuration, Timing, and Conventions as Contracts](#treat-configuration-timing-and-conventions-as-contracts)
- [Decision Checklist](#decision-checklist)

## Core Contract

- Make one complete control cycle and its failure decisions visible at the
  orchestration boundary.
- Give every responsibility and mutable datum one owner; pass stable domain
  values across boundaries instead of exposing mutable components.
- Keep control, model, hardware, transport, ROS, and vendor dependencies
  one-way.
- Add a class or abstraction only for a demonstrated ownership, substitution,
  dependency, lifecycle, deployment, or test boundary.
- Keep interfaces domain-oriented, structure shallow, and hardware mechanics
  separate from control policy.
- Treat lifecycle, failure, timing, configuration, units, frames, and command
  stages as explicit contracts.

## Make the Control Path Visible

The top-level runtime or lifecycle entry point must show the order of one cycle.
Internal details such as Pinocchio cache updates, solver assembly, ROS message
conversion, and CAN packing may be hidden, but orchestration must remain visible.

```cpp
const StateUpdateResult state_update =
    robot.updateState(hardware.readState());

if (!state_update.ok()) {
  state_machine.handleStateFailure(state_update.status);
  return;
}

const RobotState state = robot.getState();
robot.setCommand(planner.step(state, goal));
const ControllerResult result =
    controller.step(state, robot.getCommand());

if (!result.ok()) {
  state_machine.handleControllerFailure(result.status);
  return;
}

const HardwareStatus hardware_status = hardware.step(result.command);
diagnostics.record(state, result, hardware_status);
```

The exact API spelling belongs to implementation standards. Architecturally,
the cycle must expose state update, high-level command generation, lower-level
control, hardware handoff, and failure decisions.

- Avoid several layers of trivial forwarding wrappers.
- Reach meaningful behavior within roughly two navigation hops when practical.
- Do not hide orchestration inside a callback, manager, or broad façade.
- Use one coherent state snapshot for the full cycle.
- Keep the controller-facing command separate from hardware-private limiting,
  smoothing, conversion, and transmission state.

## Give Each Class One Role

A class role should be explainable in one sentence. The word `and` is not an
automatic violation, but it is a useful signal that two independent reasons to
change may have been combined.

| Component | Owns | Must not own |
| --- | --- | --- |
| `Controller` | state/current-command-to-final-command policy and controller history | transport, encoder conversion, device lifecycle |
| `Planner` | goal/state-to-command planning and planning history | actuator protocol, command transmission |
| `TrajectoryHandler` | time-parameterized desired-command progression | FSM transitions, device I/O |
| `Robot` or robot control boundary | trusted state and the current controller-facing command | device transport, hardware limiting, transmitted-command history |
| `RobotModel` | kinematics, dynamics, model data, and model cache | command transmission or system mode |
| `StateMachineState` | mode-specific orchestration and simple transition guards | trajectory math, control math, protocol code |
| FSM coordinator | active state, transitions, and state lifecycle order | motion planning, dynamics, hardware policy |
| `Solver` | a defined mathematical solve and warm-start state | system mode or device behavior |
| `RobotHardware` | domain-state/command mapping to the physical robot | planning or control policy |
| `ActuatorDriver` | packets, registers, vendor SDK, and device lifecycle | task-space or joint-space control policy |
| `Runtime` | concrete wiring, lifecycle order, and cycle call order | dynamics, solver assembly, mapping, or planning math |

Keep closely related responsibilities together when separation would only add
navigation. Role separation does not require one class per file or one package
per class.

## Assign Mutable State to One Owner

Every mutable value must have one authoritative owner.

| Mutable state | Owner |
| --- | --- |
| integrator, filter, and controller history | `Controller` |
| active mode and transition state | FSM coordinator |
| state-entry-local behavior | concrete FSM state |
| trajectory time, segment, and waypoint progression | `TrajectoryHandler` |
| planning search state | `Planner` |
| kinematics/dynamics cache | `RobotModel` |
| solver workspace and warm start | `Solver` |
| latest sensor snapshot | hardware/state boundary |
| current controller-facing command | `Robot` or robot control boundary |
| rate-limit and transmitted-command history | hardware boundary |

Do not distribute writes through mutable references, raw pointers, global
objects, service locators, or generic context bags. Cross a boundary with an
immutable snapshot, result object, or explicit validated update operation.

## Keep Dependencies One-Way

Use this conceptual direction:

```text
Runtime / application
    -> Planner, Controller, FSM coordinator
    -> trusted-state and hardware boundaries

Planner, Controller
    -> Domain types, RobotModel, Solver

Hardware boundary
    -> Domain types
    -> ROS, simulator, SDK, CAN, serial, DDS
```

- Controllers and planners must not depend on ROS messages or vendor protocols.
- The control core must not know CAN IDs, serial packets, DDS topics, or SDK
  error codes.
- Hardware must not call a controller to choose control policy.
- Concrete implementations are connected at the top-level runtime.
- Components share domain data, not unrestricted access to one another.
- Break dependency cycles by correcting ownership, not by creating `common/`, a
  singleton, or a service locator.

## Separate Hardware Mechanics from Control Policy

The hardware boundary owns:

- joint ordering and actuator mapping;
- encoder offset and direction;
- motor-side to joint-side conversion;
- gear ratio application;
- raw units and SI conversion;
- packet/register/vendor lifecycle;
- communication timeout and device fault handling;
- absolute position, velocity, torque, and current protection.

The controller decides what the robot should do in domain units. Hardware
decides how that command is safely exchanged with a device.

```text
Controller
    -> RobotState / RobotCommand
RobotHardware
    -> mapping, offset, direction, units, absolute protection
ActuatorDriver
    -> packet, register, SDK
Physical device
```

Small projects may keep `RobotHardware` and `ActuatorDriver` in one cohesive
class or file. Preserve the conceptual boundary even when a file split has no
value.

Hardware reports meaningful success, limiting, rejection, or fault status, but
keeps its working command and transmitted-command history private. Do not create
public accepted, limited, and sent command objects merely to expose internal
hardware stages.

## Centralize Orchestration, Not Intelligence

A thin runtime is desirable. A master, magic, or god class is not.

An acceptable runtime:

- constructs and connects concrete components;
- controls configure, activate, deactivate, and shutdown order;
- shows the calls performed in one cycle;
- routes results and failures to the responsible component.

It must not implement controller math, dynamics, solver assembly, trajectory
generation, hardware mapping, message conversion, or safety policy.

Avoid:

- `RobotSystem&`, `Context&`, or a property bag passed everywhere;
- a `Manager` that owns and mutates all components;
- singletons, service locators, and global mutable state;
- getters exposing every internal component or mutable container;
- methods whose names hide planning, control, safety, and transmission in one
  call;
- constructors or getters that connect devices, create threads, load
  parameters, or perform other surprising side effects.

If a repository uses the name `RobotSystem`, it must choose one cohesive role:

1. a narrow controller-facing robot boundary that owns trusted state, coherent
   model data when needed, and the current `RobotCommand`; or
2. a runtime orchestrator that wires and orders components.

It must not be both, and it must not absorb `RobotModel`, `RobotHardware`,
controller, planner, or FSM responsibilities behind unrestricted getters.

## Keep the Structure Shallow

Prefer composition. Use inheritance only for a real substitution boundary.

Acceptable:

```text
HardwareInterface
    -> CanHardware
```

Avoid:

```text
ControllerBase
    -> TorqueControllerBase
        -> AdaptiveTorqueController
            -> RobotSpecificAdaptiveController
```

- Prefer a pure interface over implementation inheritance.
- Keep interface-to-concrete depth to one level when practical.
- Avoid mixins, CRTP, multiple inheritance, and template metaprogramming unless
  they solve a demonstrated requirement.
- Do not add `IWhatever`, a factory, or a plugin system for one implementation
  and a hypothetical future backend.
- Extract a semantic helper for complex shared math, not for every one-line
  expression.

Useful semantic helpers include `SO(3)`/`SE(3)` error, quaternion ordering,
spatial ordering, frame transforms, generalized-coordinate mapping, actuator
conversion, and unit conversion. Name them by domain meaning; do not create a
miscellaneous `utils.hpp`.

## Design Small Domain-Oriented APIs

Public boundaries should expose:

- `RobotState`, `Reference`, `RobotCommand`, and meaningful result/status types;
- ownership and mutation rules;
- validity, freshness, timestamp, unit, frame, and ordering contracts;
- lifecycle operations and failure outcomes.

They should hide:

- buffer slots, mutexes, and atomics;
- callbacks and executor mechanics;
- model cache and solver workspace;
- matrix assembly temporaries;
- CAN frames, packets, and vendor objects.

Do not expose internally owned mutable state through a non-const reference or
pointer. Use immutable snapshots and explicit validated replacement or update
operations. Keep concrete accessor names and checks in implementation guidance.

Avoid ambiguous vector-only APIs at major boundaries. Use domain structs when a
group of values shares ownership, timestamp, validity, or convention.

## Make Failure and Lifecycle Explicit

Design named outcomes for at least the relevant cases:

- invalid or stale sensor state;
- solver infeasible, rejected, or failed;
- non-finite state or command;
- dimension or convention mismatch;
- command rejection or limiting;
- communication timeout or device fault;
- controller deadline miss.

Do not silently replace a failure with a zero vector, empty command, or previous
value. The state machine or runtime-level policy chooses fallback behavior; a
deep controller or driver reports the failure it owns.

Use explicit lifecycle when a component owns resources or hardware:

```text
Constructed -> Configured -> Active -> Inactive or Fault
```

- Constructors store dependencies and initialize values only.
- Configuration validates fixed dimensions and contracts.
- Activation connects or enables resources in a defined order.
- Deactivation applies the safe command and releases resources explicitly.
- Partial initialization must be safely reversible.
- Do not rely on a destructor as the only shutdown or fault policy.

## Treat Configuration, Timing, and Conventions as Contracts

Load ROS parameters at the application boundary, validate once, and pass plain
C++ configuration to domain components. Do not perform parameter lookup
throughout the control path.

```cpp
ControllerConfig config = LoadControllerConfig(node);
Validate(config);
Controller controller(config, model);
```

Make the following explicit where they cross boundaries:

- SI units and non-SI boundary units;
- reference frames and spatial-vector order;
- quaternion order;
- generalized and actuated dimensions;
- joint order and motor/joint side;
- timestamp clock and freshness;
- the controller-facing command contract and the hardware protection boundary.

Default to single-threaded execution. Add threads only to separate real timing
domains or existing execution contexts. In real-time cycles, exclude heap
allocation, blocking I/O, parameter lookup, file access, unbounded growth,
mutex waits, heavy logging, dynamic loading, and reconnect attempts unless a
measured requirement and bounded design justify them.

## Decision Checklist

Before accepting a class or component boundary, verify:

1. Can its role be stated in one sentence?
2. Does it own exactly the mutable state implied by that role?
3. Are its dependencies explicit and one-way?
4. Are side effects visible at the call site?
5. Is hardware or framework detail stopped at the correct boundary?
6. Are normal, failure, activation, and shutdown paths visible?
7. Is the abstraction justified by a current boundary rather than future reuse?
8. Can the control cycle be understood without navigating a deep call chain?
9. Are units, frames, dimensions, timestamps, and command ownership defined?
10. Would merging or deleting this class make the architecture clearer without
    combining different reasons to change?
