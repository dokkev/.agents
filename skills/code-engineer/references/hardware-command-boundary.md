# Hardware Command Boundary

Use this reference for the handoff from a controller-produced complete
`RobotCommand` to hardware validation, protection, optional smoothing,
conversion, and transmission.

## Section Map

- [Core Contract](#core-contract)
- [Complete Handoff](#complete-handoff)
- [Keep Fallback and Protection Distinct](#keep-fallback-and-protection-distinct)
- [Add Hardware Smoothing Only When Required](#add-hardware-smoothing-only-when-required)
- [Concurrency](#concurrency)

## Core Contract

Prefer a direct result when one execution context owns the cycle:

```cpp
const ControllerResult result =
    controller.Step(state, model, reference);
const HardwareStatus status = hardware.Step(result.command);
```

Preserve these boundaries:

- the joint-command controller owns nominal calculation, control-level
  fallback, and controller history;
- the runtime or middleware adapter owns visible orchestration and transfer;
- the hardware boundary owns complete-command validation, absolute hardware
  protection, device conversion, transmission, and only the smoothing or
  transmission history actually required by the plant;
- the transport owns packets and communication mechanics.

Stored `setCommand()`/`getCommand()` is optional. Use it only when a real
control-side handoff or cross-context channel requires persistent complete
command storage. It does not validate hardware feasibility, transmit a command,
or prove application to the plant.

## Complete Handoff

Pass one complete command across the boundary. Validate it before any part is
made visible to hardware:

- expected dimension and actuator ordering;
- finite values;
- supported mode and required-field consistency;
- timestamp, sequence, and freshness when part of the interface;
- command-domain invariants owned by the hardware boundary.

Reject a structurally invalid command as a whole. Do not partially apply valid
fields, silently repair `NaN`, mix the candidate with a preceding command, or
report success when no transmission occurred.

Expose one intention-level operation whose local name makes the complete input
and explicit outcome clear:

```cpp
[[nodiscard]] HardwareStatus Step(const RobotCommand& command);
```

Keep the working device command private. Report only useful facts such as
success, rejection, protection activation, transmission failure, or device
fault. Physical response remains authoritative through later feedback.

## Keep Fallback and Protection Distinct

The WBC, OSC, or other controller that produces the joint-level command returns
one complete nominal or fallback command with status. Its solver must not leak a
partial or rejected solution.

`RobotHardware` does not choose a task-level hold, damping behavior, or
recovery mode. It may reject a malformed command and apply the immediate local
response required by absolute limits, watchdogs, drive faults, or the hardware
safety contract. The runtime or FSM may observe controller and hardware status
and choose a later behavior or mode; it does not rewrite the controller command
for the same cycle.

## Add Hardware Smoothing Only When Required

Do not add torque smoothing or transmitted-command history by default. When an
explicit plant requirement, safety invariant, credible hazard, or observed
problem justifies actuator-facing rate limiting, keep its working value and
history private to the hardware boundary.

For a required torque-rate limiter, the hardware subsystem owns the previous
torque it successfully transmitted:

```cpp
class RobotHardware
{
public:
  [[nodiscard]] HardwareStatus Step(const RobotCommand& command);

private:
  Eigen::VectorXd previous_tau_sent_;
  Eigen::VectorXd tau_to_send_;
};
```

Within `Step()`:

1. validate the complete command;
2. apply the required rate limit against `previous_tau_sent_`;
3. apply absolute hardware protection and device conversion;
4. transmit the complete device command;
5. update `previous_tau_sent_` only after successful transmission.

Initialize history from an explicit activation policy. Do not advance it after
a failed send. Controller filters or output shaping own different histories and
must not borrow hardware transmission state. Do not create public requested,
limited, and sent command objects merely to expose internal stages.

## Concurrency

When controller and hardware execution contexts differ, transfer immutable
complete snapshots through one channel with explicit latest-value or ordered
semantics. Keep buffer, slot, lock, and pointer-swap mechanics outside the
control law. Do not add a queue or stored command when direct synchronous
handoff already satisfies the runtime contract.
