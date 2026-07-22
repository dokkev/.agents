# Runtime Data Flow

Make runtime ownership, data movement, and execution order explicit without
exposing subsystem internals. Keep ROS 2 as an integration layer around
ROS-independent C++ control and hardware cores.

The class and member names below are illustrative. Preserve established local
names and collapse layers that do not represent a real ownership, middleware,
hardware, or timing boundary.

## Section Map

- [Core Contract](#core-contract)
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

## Core Contract

Let each layer fully own its domain and delegate through a narrow,
intention-level contract.

```text
Control components trust the robot boundary for coherent state and command access.
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
| ROS-independent control core | robot control boundary, FSM, planners, controllers, trajectories, and control-cycle policy |
| robot control boundary | latest accepted `RobotState` and current controller-facing `RobotCommand` |
| ROS 2 hardware interface | ROS-facing state, sensor, and command storage plus the robot hardware adapter |
| `RobotHardware` | hardware-subsystem orchestration, `LowIO`, actuators, mapping, watchdog, and local fault handling |
| `Actuator` | actuator state and actuator-specific conversion and limits |
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
       -> robot boundary, FSM, planners, controllers

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
- construct and commit one project-owned state candidate;
- invoke the upper command producer and lower controller;
- write the resulting complete command to command interfaces;
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
  control core validates and commits it at the robot boundary
  upper control layer calls setCommand() with one complete RobotCommand
  lower controller reads getCommand() and produces the hardware-facing command
  controller wrapper writes that command to command interfaces

write()
  ROS 2 hardware interface builds a hardware-domain command
  RobotHardware step() validates, smooths, limits, converts, and transmits it
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
robot_system_.setCommand(fsm_handler_.step(state));
const RobotCommand command =
    controller_.step(state, robot_system_.getCommand());
```

Controllers, planners, and FSM states must not independently retrieve live
state during the same cycle. Otherwise one command can combine observations
from different points in time.

The snapshot may be a value, immutable handle, or real-time-safe view. Preserve
the semantic requirements that consumers cannot mutate the authoritative state
and that the snapshot remains coherent for the whole logical cycle.

## Command Flow

Let the upper control layer load one complete `RobotCommand` into the robot
control boundary. Let the lower controller read that command, adjust a
caller-owned copy, and pass the result through the ROS 2 command interfaces.

```text
Planner, trajectory, or FSM
    -> robot.setCommand(RobotCommand)
Lower controller
    -> robot.getCommand()
    -> adjusted RobotCommand
    -> ROS 2 controller command interfaces
    -> ROS 2 hardware-interface command storage
    -> hardware-domain command
    -> RobotHardware step()
    -> actuators and LowIO
```

The robot control boundary owns the current controller-facing command, but it
does not own any hardware-applied command or transmission result. `setCommand()`
loads the control-side handoff; it does not send anything.

Do not introduce public lifecycle representations such as accepted, limited,
and sent commands. Hardware validation, rate smoothing, absolute protection,
device conversion, and transmission remain private operations inside the
hardware boundary.

`RobotHardware` may privately retain the last torque it successfully
transmitted so the next hardware step can perform torque-command smoothing.
That history is not a controller input or diagnostic command object. Observe
the robot's physical response through the next accepted state update.

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
  const RobotCommand command = buildRobotCommandFromRosStorage();

  return hardware_.step(command).ok()
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

  HardwareStatus step(const RobotCommand& command);
  HardwareStatus getStatus() const;

private:
  void updateWatchdog();
  void handleCommunicationFault();
  void applySafeCommand();

  LowIO low_io_;
  std::vector<Actuator> actuators_;
  Eigen::VectorXd previous_tau_sent_;
};
```

The exact API may follow repository naming, but keep it at the level of joint
intent. `RobotHardware` coordinates:

- communication and actuator update order;
- hardware lifecycle and activation;
- joint-to-actuator mapping and command distribution;
- command validation, absolute protection, and torque-command smoothing;
- communication health and watchdog behavior;
- updating `previous_tau_sent_` only after successful transmission;
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
transition, hand off the current state's complete output before the next state
may run.

```text
controller cycle N
    -> current state step
    -> hand off current state's complete output
cycle boundary
    -> exit current state
    -> commit requested transition once
    -> enter next state
controller cycle N + 1
    -> next state step
```

The commit may occur at the end of controller cycle N after its output handoff,
or at the beginning of controller cycle N + 1. It does not need to wait for a
particular hardware `write()` call. The invariant is that cycle N has exactly
one state output and the next state's `step()` cannot run before the transition
commits at a defined cycle boundary. Immediate fault handling is a separate
runtime path and must not be disguised as a normal transition.

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
- hardware communication, watchdog, protection, and smoothing status;
- control-cycle duration and deadline misses.

Do not expose hardware-private command history or mutable subsystem internals
through a diagnostic API.

## Anti-Patterns

Avoid designs in which:

- a controller accesses `RobotHardware`, an actuator, or `LowIO` directly;
- a ROS 2 wrapper owns controller, planner, actuator, protocol, watchdog, or
  safety behavior;
- ROS-facing `std::vector<double>` storage becomes the hardware core's domain
  model;
- the robot control boundary performs hardware limiting or transmission;
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
9. Are watchdog, communication, conversion, limiting, smoothing, and
   transmitted-command history private to the hardware boundary?
10. Does command flow avoid public lifecycle objects and bypass paths?
11. Does one FSM state own each normal control-cycle command?
12. Can slow or asynchronous work neither block nor partially mutate a cycle?
