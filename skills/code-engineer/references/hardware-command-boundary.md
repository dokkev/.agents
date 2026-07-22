# Hardware Command Boundary

Use this reference when implementing the handoff from a controller-produced
`RobotCommand` to hardware validation, limiting, conversion, and transmission.

## Core Ownership

The controller or FSM produces a complete caller-owned command. It does not
borrow mutable storage from `RobotSystem`, hardware, transport, or a shared
command buffer.

```cpp
const RobotState state = robot_system.GetState();
const RobotCommand command = controller.ComputeCommand(state, reference);
const CommandResult result = hardware.ApplyCommand(command);
```

Preserve these boundaries:

- the trusted-state boundary owns accepted live `RobotState`, not commands;
- the controller owns its calculation and discrete history;
- the runtime or middleware adapter owns orchestration and transfer;
- the hardware boundary owns command validation, absolute protection,
  device-side conversion, transmission, and local transmitted-command records;
- the transport owns packets and communication mechanics.

Do not add `RobotSystem::GetCommand()`, `SetCommand()`, or `SendCommand()` merely
to centralize the cycle. Do not expose a mutable reference or pointer to a
command object shared with another execution context.

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

Use an intention-level operation whose name matches the repository, such as:

```cpp
[[nodiscard]] CommandResult ApplyCommand(const RobotCommand& command);
```

The exact class and method names are local choices. The semantic contract is a
single complete input and an explicit outcome.

## Limiting And Transmission

Hardware protection may change a valid controller-produced command before it is
transmitted. Keep the stages conceptually distinguishable at the owning
boundary:

```text
controller-produced -> hardware-limited -> transmitted
```

Do not turn these stages into globally mutable lifecycle objects. Return or
publish only the outcome needed by the caller and diagnostics, for example:

- accepted, limited, rejected, or communication-failure status;
- whether absolute protection changed the command;
- command sequence associated with the result;
- last command actually transmitted when fallback, diagnosis, or controller
  history genuinely depends on it.

An actuator or hardware subsystem may privately retain its last transmitted
command. It must not present that record as measured robot state or as an
alternative control input. Physical response remains authoritative through
later state feedback.

Do not report a successful send when no device transmission occurred. Keep
packet encoding, bus retries, watchdog mechanics, and actuator conversion below
the intention-level boundary.

## Concurrency

When the controller and hardware run in different execution contexts, transfer
immutable complete snapshots through a channel with explicit latest-value or
ordered semantics. Keep slot, buffer, lock, and pointer-swap mechanics out of
the control law. Read `control-concurrency.md` only when the task actually
crosses execution contexts.
