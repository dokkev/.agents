# RobotCommand Ownership and Access

Loading this reference does not authorize tests or review. Apply testing or
review guidance only when the user explicitly requests that mode.

Use this standard when implementing or changing stored robot commands and their
public access API.

## Ownership Contract

Keep ownership of the stored `RobotCommand` inside the robot or command
boundary. Never expose a mutable reference or pointer to internally owned
command state.

Forbidden:

```cpp
RobotCommand& getCommand();
RobotCommand* mutableCommand();
```

Required public shape:

```cpp
[[nodiscard]] RobotCommand getCommand() const;

[[nodiscard]] CommandStatus setCommand(
    const RobotCommand& command);
```

`getCommand()` returns an immutable snapshot or value copy. `setCommand()`
validates one complete replacement and commits it only when every check passes.
Do not provide field-by-field setters that can leave a partially updated command
or bypass whole-command validation.

## Control-Cycle Usage

When a controller updates an existing complete command:

```cpp
RobotCommand command = robot.getCommand();
controller.computeCommand(state, reference, command);

const CommandStatus command_status = robot.setCommand(command);
if (command_status != CommandStatus::kAccepted) {
  state_machine.handleInvalidCommand(command_status);
  return;
}

const SendStatus send_status = robot.sendCommand();
```

When the controller naturally produces a complete value, prefer returning it:

```cpp
const RobotCommand command =
    controller.computeCommand(state, reference);

const CommandStatus command_status = robot.setCommand(command);
if (command_status == CommandStatus::kAccepted) {
  robot.sendCommand();
}
```

Do not let `computeCommand()` retain a mutable alias to the robot's internal
command. The command being computed is caller-owned until `setCommand()` accepts
it.

## setCommand Validation

Before committing, validate at least the fields relevant to the command type:

- joint and actuator dimensions;
- finite values (`NaN` and infinity are rejected);
- command mode and required-field consistency;
- initialized or present fields;
- timestamp or sequence validity when used;
- domain-level ranges and invariants owned by the command boundary.

```cpp
enum class CommandStatus
{
  kAccepted,
  kInvalidDimension,
  kNonFiniteValue,
  kInvalidMode,
  kInvalidTimestamp,
  kOutOfRange,
};
```

On rejection:

- preserve the previously accepted command unchanged;
- return a specific status;
- do not partially commit valid fields;
- do not silently clamp non-finite or structurally invalid input;
- leave fallback selection to the state machine or runtime policy.

Validation must use the full candidate command, then publish or swap the
accepted snapshot once. If concurrency exists, keep mutex, real-time buffer,
double-buffer, or atomic-snapshot mechanics private to the boundary.

## Separate Acceptance from Transmission

`setCommand()` validates and stores the requested command. It does not transmit
to hardware.

| Operation | Meaning |
| --- | --- |
| `getCommand()` | snapshot of the current accepted requested command |
| `setCommand()` | validate and atomically replace the requested command |
| `sendCommand()` | apply hardware protection and transmit to the device |
| `getSentCommand()` | snapshot of the last command actually transmitted |

Hardware-level absolute protection may limit an otherwise valid requested
command. Preserve and distinguish:

```text
requested -> limited -> sent
```

Return a `SendStatus` that reports rejection, communication failure, and whether
limiting changed the command. Make the last actual transmitted command
observable through `getSentCommand()` when diagnostics, fallback, or controller
history needs it.

Do not overwrite the requested command with the limited or sent value. Do not
report a successful send if no device transmission occurred.

## Tests

Test:

- returned snapshots cannot mutate internal storage;
- every invalid dimension, non-finite value, and mode/field mismatch is rejected;
- rejection preserves the previous complete command;
- accepted replacement becomes visible in one complete snapshot;
- `setCommand()` performs no hardware transmission;
- requested, limited, and sent values remain distinguishable;
- concurrent access, when required, never exposes a partial command.
