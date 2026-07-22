# Runtime Data Flow

Make ownership, data movement, and one complete control cycle visible. Keep ROS
2 as an adapter around ROS-independent control and hardware code. Collapse any
layer that does not represent a real ownership, model, hardware, middleware, or
timing boundary.

## Section Map

- [Core Contract](#core-contract)
- [Show One Direct Cycle](#show-one-direct-cycle)
- [Assign Runtime Boundaries](#assign-runtime-boundaries)
- [Keep the Core ROS-Independent](#keep-the-core-ros-independent)
- [Keep ROS 2 at the Adapter Boundary](#keep-ros-2-at-the-adapter-boundary)
- [Keep State and Model Coherent](#keep-state-and-model-coherent)
- [Make Command and Failure Ownership Explicit](#make-command-and-failure-ownership-explicit)
- [Keep Hardware Orchestration Local](#keep-hardware-orchestration-local)
- [Respect Cycle and Callback Boundaries](#respect-cycle-and-callback-boundaries)
- [Keep Diagnostics Observational](#keep-diagnostics-observational)
- [Anti-Patterns](#anti-patterns)
- [Design Checklist](#design-checklist)

## Core Contract

Let each layer fully own its domain and exchange complete domain values through
narrow contracts.

```text
ROS or application adapter
    -> control core
       -> optional RobotSystem for Pinocchio model/state coherence
       -> WBC / OSC / other joint-command controller
    -> RobotHardware
       -> actuator and LowIO mechanics
```

An owner keeps its mechanism private while reporting meaningful status. Higher
layers do not reach into lower layers to duplicate protection or coordinate
owned objects. Lower layers do not invent control behavior or mode policy.

## Show One Direct Cycle

The runtime entry point should reveal one cycle without a chain of forwarding
wrappers:

```cpp
const StateUpdateResult state_update =
    robot_system.Update(hardware.ReadState());

const ControllerResult result = [&]() -> ControllerResult {
  if (!state_update.ok()) {
    return controller.Fallback(robot_system, state_update.status);
  }

  const RobotState& state = robot_system.state();
  const Reference reference = behavior.Step(state, goal);
  return controller.Step(robot_system, reference);
}();

const HardwareStatus hardware_status = hardware.Step(result.command);
behavior.ObserveControllerStatus(result.status);
diagnostics.Record(result.status, hardware_status);
```

Use `RobotSystem` only when the controller needs the shared Pinocchio
model-and-state boundary. A simpler controller may receive `RobotState` and
`Reference` directly. The essential flow is state acquisition, reference or
behavior selection, complete joint-command production, hardware handoff, and
observable status.

## Assign Runtime Boundaries

| Component | Owns |
| --- | --- |
| runtime/application | concrete wiring, lifecycle order, and cycle call order |
| runtime/FSM behavior layer | active behavior, reference selection, and mode transitions |
| `RobotSystem`, when justified | accepted state plus coherent Pinocchio model data and cache |
| WBC/OSC/controller | nominal or fallback complete joint command and controller history |
| ROS 2 adapter | ROS lifecycle, interface adaptation, and ROS-facing storage |
| `RobotHardware` | subsystem I/O order, mapping, local protection, and hardware lifecycle |
| actuator | actuator-specific state, conversion, limits, and device fault state |
| `LowIO` | transport calls, packets, and protocol facts |

An orchestration object may coordinate several owned components, but it must
not absorb their calculations or expose them through unrestricted getters.

## Keep the Core ROS-Independent

Use project-owned types such as `RobotState`, `Reference`, `RobotCommand`,
`HardwareState`, `Status`, `TimePoint`, and `Duration` in control and hardware
code. Keep ROS messages, `rclcpp`, controller interfaces, and hardware
interfaces at the adapter boundary.

Control decisions, model updates, FSM transitions, actuator mapping, command
protection, and device protocol behavior remain in ROS-independent C++.

A useful check is:

> Removing ROS 2 should replace adapters and wiring, not rewrite control or
> hardware behavior.

Thin means that an adapter owns no domain decision, not merely that it has few
lines.

## Keep ROS 2 at the Adapter Boundary

When `ros2_control` is used, preserve its visible `read -> update -> write`
semantics without turning the skill into a prescribed repository layout.

```text
read
    -> acquire one complete hardware-domain state
    -> adapt it to ROS-facing state storage
update
    -> build one complete controller input snapshot
    -> invoke the ROS-independent control core
    -> publish one complete command to ROS-facing command storage
write
    -> build one hardware-domain command
    -> invoke RobotHardware once
```

The ROS adapter may own middleware-facing storage because ROS interfaces require
it. That storage is not the internal data model of `RobotHardware` and does not
compete with the accepted controller-facing `RobotState`.

The adapter must not implement control laws, solver fallback, FSM policy, CAN
or serial packets, actuator conversion, watchdog behavior, reconnect logic, or
hardware safety policy. It translates lifecycle, time, interfaces, and status.

## Keep State and Model Coherent

Acquire and convert hardware state at the hardware boundary. Build one complete
controller-facing candidate and accept it atomically before the control cycle
uses it.

```text
device feedback
    -> RobotHardware mapping, offsets, signs, and units
    -> complete RobotState candidate
    -> accepted state boundary
    -> optional Pinocchio model update in RobotSystem
    -> one immutable model-and-state view for the cycle
```

Do not let controllers, planners, or FSM states independently retrieve live
fields during one logical cycle. Do not publish partial candidates. When
Pinocchio-based model control is not present, keep the accepted snapshot in the
smallest existing state boundary instead of adding `RobotSystem` by convention.

## Make Command and Failure Ownership Explicit

Prefer a direct command result:

```text
behavior or planner -> Reference
joint-command controller -> ControllerResult { complete command, status }
runtime adapter -> complete handoff
RobotHardware -> validation, local protection, conversion, transmission
```

The controller that produces the joint-level command owns control-level
fallback. Solver failure, stale or invalid control input, and rejected
controller output produce one complete controller-defined fallback command and
an observable status. Never publish partial solver output.

The runtime or FSM may use controller status to choose the next reference,
behavior, mode, or transition. It must not overwrite that controller's command
for the same cycle. `RobotHardware` may reject a structurally invalid command
or apply immediate hardware-local protection, watchdog, and device-fault
responses; it does not choose a task-level fallback.

Stored `setCommand()`/`getCommand()` handoff is optional. Add it only when a
real multi-component or cross-context channel needs persistent complete command
storage. It is not inherent to `RobotSystem` or to ROS 2.

## Keep Hardware Orchestration Local

Expose one intention-level hardware operation for a complete command and one
meaningful outcome. Keep these details private to the hardware subsystem:

- actuator ordering, offsets, signs, gearing, and unit conversion;
- complete-command structural validation and absolute protection;
- device lifecycle, communication health, and watchdog;
- packet/register/vendor calls delegated to LowIO or the actuator;
- hardware rate limiting or smoothing history when the actual system requires
  that mechanism;
- the last successfully transmitted value when such history is required.

Do not add smoothing, retry, reconnect, watchdog state, or a background worker
merely because a hardware class exists. Each mechanism needs an explicit
requirement, safety invariant, credible hazard, or observed problem. Report
protection activation and transmission status without exposing mutable working
commands or transport objects.

## Respect Cycle and Callback Boundaries

One active FSM state or behavior produces one cycle's reference. Commit normal
transitions at a defined cycle boundary so two states cannot contribute to one
command. The controller then produces that cycle's complete nominal or fallback
joint command.

Do not block a deadline-sensitive loop on a planner, UI, logger, ROS callback,
network reconnect, or device API with an unbounded wait. Let slower contexts
publish complete timestamped values and consume them according to an explicit
freshness policy.

Add a thread, queue, or real-time handoff only for an actual execution-context
or rate boundary. A callback must not partially mutate active state, reference,
configuration, controller history, or command. ROS lifecycle is an integration
contract, not the robot's hardware safety mechanism.

## Keep Diagnostics Observational

Useful read-only observations include:

- accepted state sequence, timestamp, validity, and freshness;
- controller nominal/fallback status and owning failure;
- active behavior and requested transition;
- hardware communication, watchdog, protection activation, and transmission
  status;
- cycle duration and deadline misses.

Diagnostics must not become an alternative command path or expose mutable
hardware-private command history.

## Anti-Patterns

Avoid designs in which:

- `RobotSystem` is imposed on a controller with no shared Pinocchio model need;
- `RobotSystem` becomes the runtime, hardware manager, or service locator;
- every command is routed through stored `setCommand()`/`getCommand()` without
  a real handoff requirement;
- a ROS 2 wrapper owns domain decisions or device protocol behavior;
- ROS-facing vectors become the hardware core's internal state model;
- the FSM, controller, and hardware each choose a competing same-cycle
  fallback;
- hardware exposes mutable actuators, transport objects, or working commands;
- callbacks partially mutate a control-cycle snapshot;
- several layers duplicate retry, watchdog, limiting, or recovery logic.

## Design Checklist

1. Is one complete cycle visible at the runtime boundary?
2. Does every mutable runtime datum have one owner?
3. Does one coherent state snapshot feed each logical cycle?
4. Is `RobotSystem` used only when shared Pinocchio model/state coherence is
   required?
5. Does the joint-command controller return a complete nominal or fallback
   command with status?
6. Do the runtime/FSM own later behavior decisions without overwriting the
   same-cycle command?
7. Does hardware apply only hardware-local validation and protection policy?
8. Are ROS 2 wrappers limited to adaptation, lifecycle, storage, and status?
9. Are hardware I/O mechanisms private, direct, and justified by real needs?
10. Can callbacks and slower contexts neither block nor partially mutate a
    cycle?
