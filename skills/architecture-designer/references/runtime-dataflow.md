# Runtime Data Flow

Make runtime ownership, data movement, and execution order explicit without
exposing subsystem internals. Keep ROS 2 as an integration layer around
ROS-independent C++ control and hardware cores.

The class and member names below are illustrative. Preserve established local
names and collapse layers that do not represent a real ownership, middleware,
hardware, or timing boundary.

## Contents

- [Design Philosophy](#design-philosophy)
- [Runtime Boundaries](#runtime-boundaries)
- [ROS-Independent Core](#ros-independent-core)
- [ROS 2 Control Cycle](#ros-2-control-cycle)
- [Trusted State Flow](#trusted-state-flow)
- [One State Snapshot Per Cycle](#one-state-snapshot-per-cycle)
- [Command Flow](#command-flow)
- [ROS 2 Interface Storage](#ros-2-interface-storage)
- [Hardware Orchestration](#hardware-orchestration)
- [FSM Cycle Semantics](#fsm-cycle-semantics)
- [Failure Ownership](#failure-ownership)
- [Multi-Rate and Asynchronous Data](#multi-rate-and-asynchronous-data)
- [Diagnostics](#diagnostics)
- [Anti-Patterns](#anti-patterns)
- [Design Checklist](#design-checklist)

## Design Philosophy

Let each layer fully own its domain and delegate through a narrow,
intention-level contract.

```text
Controller trusts the accepted-state boundary for coherent controller-facing state.
ROS 2 hardware interface trusts RobotHardware for hardware orchestration.
RobotHardware trusts Actuator and LowIO for their local contracts.
```

Trust does not mean hiding failures. An owner keeps mechanisms private while
making meaningful status and outcomes visible at its boundary. Higher layers
must not reach into lower layers to duplicate protection, coordinate owned
objects, or reinterpret implementation details.

## Runtime Boundaries

Assign each runtime responsibility and mutable datum to one owner.

| Component | Owns |
| --- | --- |
| ROS 2 controller wrapper | loaned interfaces, ROS lifecycle, and adaptation to control-domain types |
| ROS-independent control core | trusted state, FSM, planners, controllers, trajectories, and control-cycle policy |
| trusted-state boundary | latest accepted, coherent `RobotState` used by the control core when a separate owner is needed |
| ROS 2 hardware interface | ROS-facing state, sensor, and command storage plus the robot hardware adapter |
| `RobotHardware` | hardware-subsystem orchestration, `LowIO`, actuators, mapping, watchdog, and local fault handling |
| `Actuator` | actuator state, actuator-specific conversion and limits, and transmitted-command bookkeeping |
| `LowIO` | transport and protocol details |

An orchestration class is justified when a subsystem necessarily coordinates
several owned objects. It coordinates their order and lifecycle without
exposing them or absorbing their local responsibilities.

## ROS-Independent Core

Keep the ROS 2 controller and hardware interface as thin integration wrappers.
Implement control decisions and hardware behavior as ROS-independent C++.

```text
ROS 2 controller wrapper
    -> ROS-independent control core
       -> trusted state, FSM, planners, controllers

ROS 2 hardware interface
    -> RobotHardware instance
       -> LowIO and actuators
```

Core code should use project-owned types such as `RobotState`, `RobotCommand`,
`HardwareState`, `JointImpedanceCommand`, `Status`, `TimePoint`, and `Duration`.
It should not depend on ROS messages, loaned interfaces, `rclcpp`,
`controller_interface`, or `hardware_interface`.

The ROS 2 controller wrapper should only:

- claim and read state and sensor interfaces;
- construct project-owned state and reference inputs;
- invoke the ROS-independent control core;
- write the returned command to command interfaces;
- adapt ROS lifecycle, configuration, time, and status;
- publish optional diagnostics.

The ROS 2 hardware interface should only:

- adapt the ROS hardware lifecycle;
- declare and export ROS state, sensor, and command interfaces;
- maintain ROS-facing interface storage;
- copy hardware-domain state into ROS-facing storage;
- build hardware-domain commands from ROS-facing storage;
- call the intention-level `RobotHardware` API;
- translate hardware status into ROS return values and diagnostics.

It must not implement control laws, FSM transitions, planning, CAN or serial
packets, actuator conversion, watchdog behavior, communication recovery, or
hardware safety policy.

A useful boundary check is:

> Removing ROS 2 should require replacing the wrappers, not rewriting control
> or hardware behavior.

Thin means that a wrapper owns no domain decision, not merely that it has few
lines of code.

## ROS 2 Control Cycle

Preserve the standard `read -> update -> write` structure when using
`ros2_control`.

```text
read()
  RobotHardware acquires and converts hardware state
  ROS 2 hardware interface exports it through state interfaces

controller update()
  controller wrapper builds one complete RobotState candidate
  control core validates and commits it at the trusted-state boundary
  active FSM/controller computes one RobotCommand from one snapshot
  controller wrapper writes the result to command interfaces

write()
  ROS 2 hardware interface builds a hardware-domain command
  RobotHardware applies the selected intention-level command
  RobotHardware coordinates actuators and LowIO
```

State flows upward from the physical subsystem to the control core. Commands
flow downward from the control core to the physical subsystem. No component may
bypass this path by directly accessing an object owned by another layer.

## Trusted State Flow

Keep state acquisition, middleware storage, and controller-facing acceptance
as distinct responsibilities.

```text
Actuators and sensors
    -> RobotHardware HardwareState
    -> ROS 2 hardware-interface state storage
    -> loaned ROS 2 state interfaces
    -> complete RobotState candidate
    -> trusted-state validation and commit
    -> coherent RobotState snapshot
    -> FSM, planner, and controller
```

`RobotHardware` determines how packets, encoder values, signs, offsets, units,
and joint-to-actuator mappings become hardware-domain state. The ROS 2 hardware
interface only adapts that state to exported interfaces. The selected
trusted-state boundary determines whether the completed robot-domain state
satisfies the configured model and controller-facing contract.

Do not make partial updates to the authoritative state. Build a complete
candidate and commit it only after validation succeeds. See `robot-system.md`
for the state contract, acceptance behavior, and model coherence rules.

## One State Snapshot Per Cycle

Obtain the accepted state once and pass that snapshot explicitly through the
active control path.

```cpp
const StateUpdateResult update =
    robot_system_.updateState(candidate_state);

if (!update.ok()) {
  return handleStateFailure(update.status);
}

const RobotState state = robot_system_.getState();
const RobotCommand command = fsm_handler_.step(state);
```

Controllers, planners, and FSM states must not independently retrieve live
state during the same cycle. Otherwise one command can combine observations
from different points in time.

The snapshot may be a value, immutable handle, or real-time-safe view. Preserve
the semantic requirements that consumers cannot mutate the authoritative state
and that the snapshot remains coherent for the whole logical cycle.

## Command Flow

Let the active control path return a normal `RobotCommand` and pass it through
the ROS 2 command interfaces.

```text
FSM and controller RobotCommand
    -> ROS 2 controller command interfaces
    -> ROS 2 hardware-interface command storage
    -> hardware-domain command
    -> RobotHardware intention-level API
    -> actuators and LowIO
```

The trusted-state boundary owns state, not hardware commands. If that boundary
is named `RobotSystem`, do not add command storage or a `setCommand()` API to it.

Do not introduce public lifecycle representations such as candidate, accepted,
finalized, limited, and sent commands. Validation, limiting, and device
conversion are operations at their owning boundary rather than system-wide
command states.

An actuator may privately retain the last command it received and the command
it actually transmitted for diagnostics. This is local bookkeeping, not a
second control input or an alternative command owner. Observe the robot's
physical response through later state feedback, not through the transmitted
command record.

## ROS 2 Interface Storage

Let the ROS 2 hardware interface own the storage exported through ROS state,
sensor, and command interfaces. Keep these middleware-facing values separate
from the domain representation inside `RobotHardware`.

```cpp
class HandHardwareInterface
    : public hardware_interface::SystemInterface
{
private:
  RobotHardware hardware_;

  // ROS 2 joint-state interface storage
  std::vector<double> joint_position_;
  std::vector<double> joint_velocity_;
  std::vector<double> joint_effort_;

  // ROS 2 sensor-state interface storage
  std::vector<double> sensor_state_;

  // ROS 2 command-interface storage
  std::vector<double> position_command_;
  std::vector<double> effort_command_;
  std::vector<double> stiffness_command_;
  std::vector<double> damping_command_;
};
```

The exact containers and export API depend on the `ros2_control` version, but
the ownership rule does not. These values are adapter-side interface storage;
they must not become the internal data model of `RobotHardware`.

During `read()`, update the hardware adapter first and then copy its domain state to
the ROS-facing storage:

```cpp
hardware_interface::return_type HandHardwareInterface::read(...)
{
  if (!hardware_.read().ok()) {
    return hardware_interface::return_type::ERROR;
  }

  copyToRosStateStorage(hardware_.getState());
  return hardware_interface::return_type::OK;
}
```

During `write()`, build the selected domain command from ROS-facing command
storage and delegate it:

```cpp
hardware_interface::return_type HandHardwareInterface::write(...)
{
  const JointImpedanceCommand command =
      buildJointImpedanceCommandFromRosStorage();

  return hardware_.setJointImpedance(command).ok()
      ? hardware_interface::return_type::OK
      : hardware_interface::return_type::ERROR;
}
```

ROS-facing storage, `HardwareState`, and trusted controller-facing state do
not compete as authoritative copies. Each belongs to a different boundary:

- `HardwareState` is the hardware subsystem's latest domain state;
- ROS-facing storage is the snapshot exported during `read()`;
- `RobotState` is the accepted snapshot trusted by the control core.

## Hardware Orchestration

Let the ROS 2 hardware interface exclusively own the hardware adapter for the
complete hardware subsystem. Name its type and instance for the local domain.

```cpp
class HandHardwareInterface
    : public hardware_interface::SystemInterface
{
private:
  RobotHardware hardware_;
};
```

`RobotHardware` owns the low-level I/O and actuator objects it coordinates.

```cpp
class RobotHardware
{
public:
  Status read();
  const HardwareState& getState() const;

  Status setPosition(const JointPositionCommand& command);
  Status setEffort(const JointEffortCommand& command);
  Status setJointImpedance(const JointImpedanceCommand& command);
  HardwareStatus getStatus() const;

private:
  void updateWatchdog();
  void handleCommunicationFault();
  void applySafeCommand();

  LowIO low_io_;
  std::vector<Actuator> actuators_;
};
```

The exact API may follow repository naming, but keep it at the level of joint
intent. `RobotHardware` coordinates:

- communication and actuator update order;
- hardware lifecycle and activation;
- joint-to-actuator mapping and command distribution;
- communication health and watchdog behavior;
- local safe response to hardware faults.

Keep raw transport access, packet construction, mutable actuators, watchdog
reset, retries, encoder conversion, and actuator-specific limits out of the
public runtime API. The hardware interface trusts `RobotHardware` to operate the
subsystem rather than coordinating `LowIO` or individual actuators itself.

Private handling must remain observable. Report meaningful status through
return values, read-only status, state interfaces, or diagnostics without
exposing internal control mechanisms.

## FSM Cycle Semantics

Let one active state own one cycle's command. When a state requests a normal
transition, transmit the current state's command before committing that
transition.

```text
controller cycle N
    -> current state step
    -> publish current state's command interfaces
hardware write N
    -> transmit current state's command
controller cycle N + 1
    -> finish current state
    -> enter next state
    -> next state step
```

In a `ros2_control` runtime, preserve this order by keeping the transition
pending through `write()` and committing it at the beginning of the next
controller update. Do not call both the current and next state's `step()` in
one cycle. This keeps command ownership and state lifecycle deterministic.
Immediate fault handling is a separate runtime path and must not be disguised
as a normal transition.

## Failure Ownership

Handle a failure at the narrowest layer that has enough information and
authority to own the response.

- the trusted-state boundary rejects invalid candidates without partially modifying
  the accepted state.
- The control core decides whether rejected or stale state means hold, Idle,
  fault, or controller deactivation.
- The ROS 2 wrappers adapt core or hardware status to ROS return values and
  diagnostics; they do not invent domain policy.
- `RobotHardware` privately handles communication timeouts, its watchdog, and
  hardware-local safe output.
- `Actuator` handles actuator-specific validation, limiting, conversion, and
  local fault state.
- `LowIO` reports transport outcomes without deciding robot behavior.

If the hardware subsystem rejects a command, do not transmit that rejected
value. Apply the hardware-local safe response, report the failure, and let the
control core select the subsequent system behavior from the observable status.

Lower-level protection and higher-level behavior selection may both exist, but
must not duplicate the same mechanism. For example, hardware may independently
enforce a watchdog while the control FSM observes the reported fault and enters
Idle. The FSM must not manually tick or reset the hardware watchdog.

## Multi-Rate and Asynchronous Data

Do not block a fast control loop while waiting for a slower planner, user
interface, logger, or ROS callback.

Let slower producers publish a complete result. Consume the latest valid result
at a control-cycle boundary according to an explicit timestamp, validity, and
staleness policy. If no new plan is available, continue with the last valid
reference only while that policy allows it.

Do not add threads or buffers unless an actual rate or execution-context
boundary requires them. When ROS callbacks and a real-time loop must exchange
data, prefer the appropriate ROS 2 `realtime_tools` primitive over an ad hoc
concurrency implementation.

An asynchronous callback must never partially mutate the active `RobotState`,
trajectory, reference, or command during a control cycle. Transfer complete
snapshots or requests with explicit ownership.

## Diagnostics

Let diagnostics observe the runtime without becoming part of the control path.
Useful read-only observations include:

- accepted state timestamp, sequence, and freshness;
- active FSM state and requested transition;
- hardware communication and watchdog status;
- last transmitted actuator command;
- control-cycle duration and deadline misses.

Do not feed diagnostic command records back into a controller or expose mutable
subsystem internals through a diagnostic API.

## Anti-Patterns

Avoid designs in which:

- a controller accesses `RobotHardware`, an actuator, or `LowIO` directly;
- a ROS 2 wrapper owns controller, planner, actuator, protocol, watchdog, or
  safety behavior;
- ROS-facing `std::vector<double>` storage becomes the hardware core's domain
  model;
- the trusted-state boundary stores or validates hardware commands;
- several consumers independently retrieve live state in one cycle;
- `RobotHardware` exposes mutable actuators or transport objects;
- a caller manually drives another owner's watchdog or retry mechanism;
- multiple layers duplicate the same validation or protection policy;
- logging or diagnostics form an alternative command path.

## Design Checklist

Before accepting a runtime design, verify:

1. Does every mutable runtime datum have one authoritative owner?
2. Does one coherent `RobotState` snapshot feed each logical control cycle?
3. Are control and hardware behaviors implemented in ROS-independent C++?
4. Do ROS 2 wrappers only adapt interfaces, lifecycle, time, and status?
5. Does the ROS 2 hardware interface own ROS-facing storage separately from
   `RobotHardware` state?
6. Does the ROS 2 hardware interface exclusively own its hardware adapter?
7. Does `RobotHardware` own and coordinate `LowIO` and its actuators?
8. Do public hardware APIs express joint intent rather than device mechanism?
9. Are watchdog, communication, conversion, limiting, and transmitted-command
   bookkeeping private to their proper hardware owners but observable?
10. Does command flow avoid public lifecycle objects and bypass paths?
11. Does one FSM state own each normal control-cycle command?
12. Can slow or asynchronous work neither block nor partially mutate a cycle?
