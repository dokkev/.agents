# Hardware Command Boundary

Use this reference when implementing the handoff from a controller-facing
`RobotCommand` to hardware validation, smoothing, limiting, conversion, and
transmission.

## Section Map

- [Core Contract](#core-contract)
- [Complete Handoff](#complete-handoff)
- [Hardware-Private Smoothing, Limiting, And Transmission](#hardware-private-smoothing-limiting-and-transmission)
- [Concurrency](#concurrency)

## Core Contract

An upper control component loads one complete command into the robot control
boundary. A lower controller reads that command without mutating its storage,
adjusts a caller-owned copy, and gives the final command to hardware.

```cpp
const RobotState state = robot.getState();
robot.setCommand(trajectory_handler.step(state, goal));

const RobotCommand command =
    controller.step(state, robot.getCommand());
const HardwareStatus status = hardware.step(command);
```

Preserve these boundaries:

- the robot control boundary owns accepted live `RobotState` and the current
  controller-facing `RobotCommand`;
- the controller owns its calculation and discrete history;
- the runtime or middleware adapter owns orchestration and transfer;
- the hardware boundary owns command validation, absolute protection,
  torque-command smoothing, device-side conversion, transmission, and the
  previous successfully transmitted torque command;
- the transport owns packets and communication mechanics.

Use `getCommand()` and `setCommand()` only for the control-side handoff. They do
not validate hardware feasibility, transmit, or report application. Do not add
a control-side `sendCommand()` or expose a mutable reference or pointer to
command storage shared with another execution context.

## Complete Handoff

Pass one complete command across the boundary. Validate it before making any
part visible to hardware:

- expected dimension and actuator ordering;
- finite values;
- supported mode and required-field consistency;
- timestamp, sequence, and freshness when part of the interface;
- command-domain invariants owned by the boundary.

Reject a structurally invalid command as a whole. Do not partially apply valid
fields, silently repair `NaN`, or mix the rejected candidate with a preceding
command. The runtime or explicit hardware safety policy selects hold, fallback,
disable, or fault behavior.

Use an intention-level hardware cycle operation whose name matches the
repository, such as:

```cpp
[[nodiscard]] HardwareStatus step(const RobotCommand& command);
```

The exact class and method names are local choices. The semantic contract is a
single complete input and an explicit outcome.

## Hardware-Private Smoothing, Limiting, And Transmission

Hardware protection may change a valid controller-facing command before it is
transmitted. Keep every working command and transmission-history value private
to the hardware boundary. Do not expose accepted, limited, and sent command
objects as a public lifecycle.

For torque-command smoothing, the hardware subsystem owns the previous torque
that it successfully transmitted:

```cpp
class RobotHardware
{
public:
  [[nodiscard]] HardwareStatus step(const RobotCommand& command);

private:
  Eigen::VectorXd previous_tau_sent_;
  Eigen::VectorXd tau_to_send_;
};
```

Within `step()`:

1. validate the complete command;
2. smooth torque against `previous_tau_sent_`;
3. apply absolute hardware protection and device conversion;
4. transmit the complete device command;
5. update `previous_tau_sent_` only after successful transmission.

Initialize this storage during configuration or activation from the explicit
hardware startup policy. On a failed send, do not advance it as though the plant
received a new torque command. Keep controller filters and controller-output
smoothing separate; they own their own histories and must not borrow
`previous_tau_sent_`.

Return only the status needed for runtime failure policy and diagnostics, such
as success, rejection, protection activation, communication failure, or device
fault. Do not return the working torque vector merely to expose an internal
stage. Physical response remains authoritative through later state feedback.

Do not report a successful send when no device transmission occurred. Keep
packet encoding, bus retries, watchdog mechanics, and actuator conversion below
the intention-level boundary.

## Concurrency

When the controller and hardware run in different execution contexts, transfer
immutable complete snapshots through a channel with explicit latest-value or
ordered semantics. Keep slot, buffer, lock, and pointer-swap mechanics out of
the control law. Read `control-concurrency.md` only when the task actually
crosses execution contexts.
