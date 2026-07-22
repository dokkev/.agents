# Robot System Architecture

Use this pattern when several control components need one trusted live
robot-state snapshot and one current controller-facing command. A repository
may call the boundary `Robot`, `RobotSystem`, or something domain-specific, or
keep it inside a small runtime when no separate class is justified. It is not a
master object for the entire application or a hardware manager.

## Contents

- [Primary Responsibility](#primary-responsibility)
- [What Trusted State Means](#what-trusted-state-means)
- [State Ownership and Access](#state-ownership-and-access)
- [Command Ownership and Access](#command-ownership-and-access)
- [State Update Flow](#state-update-flow)
- [Model and State Coherence](#model-and-state-coherence)
- [Live State Versus Hypothetical State](#live-state-versus-hypothetical-state)
- [Responsibility Boundaries](#responsibility-boundaries)
- [Failure and Freshness](#failure-and-freshness)
- [Design Checklist](#design-checklist)

## Primary Responsibility

The robot control boundary stores and exposes the latest accepted `RobotState`
and the current complete `RobotCommand` in controller-facing domain
conventions.

The intended direction is:

```text
hardware adapter or estimator
    -> complete RobotState candidate
trusted-state boundary
    -> validate and commit RobotState
Controller, planner, FSM
    -> immutable state snapshot

Planner, trajectory, or upper control layer
    -> setCommand(complete RobotCommand)
Lower controller
    -> getCommand() and produce the command handed to hardware
```

Other components must not independently assemble, own, or mutate competing
copies of the current robot state. They obtain the controller-facing snapshot
from the accepted-state boundary and use the same snapshot for one logical
cycle.

The boundary may also own or wrap the robot model and its cache when that keeps
model queries coherent with the stored state. This does not make it the owner of
the controller, planner, hardware transport, hardware command history, or
application lifecycle.

Do not introduce a separate robot control class merely to satisfy this pattern.
If the existing runtime already provides the same trusted-state and complete
command-handoff contracts without becoming a service locator, preserve the
simpler boundary.

## What Trusted State Means

"Trusted" does not mean that every measurement is physically exact. It means
that the state crossed an explicit acceptance boundary and satisfies the
contracts required by its consumers:

- dimensions match the configured fixed-base or floating-base model;
- values required by the active state representation are finite;
- joint order, generalized-coordinate layout, units, and frames are known;
- base orientation and other constrained representations are valid;
- timestamp, sequence, and source metadata are coherent;
- joint and base data belong to one defined snapshot policy;
- validity and freshness can be determined without guessing.

The controller may rely on these structural guarantees. Sensor accuracy,
estimation uncertainty, and task suitability remain separate questions and
should be represented explicitly when they matter.

## State Ownership and Access

The selected boundary is the authoritative owner of the accepted `RobotState`
snapshot.

When a dedicated class is justified, prefer a small public boundary such as:

```cpp
class Robot
{
public:
  [[nodiscard]] StateUpdateResult updateState(
      const RobotState& candidate);

  [[nodiscard]] RobotState getState() const;

  void setCommand(const RobotCommand& command);
  [[nodiscard]] const RobotCommand& getCommand() const;

private:
  RobotModel model_;
  RobotState state_;
  RobotCommand command_;
};
```

The class name, types, and method spelling follow the repository. Preserve these
semantics:

- `getState()` provides a read-only snapshot, not an externally mutable alias;
- state replacement passes through one validation and commit operation;
- a failed update cannot leave a partially modified state;
- consumers do not receive setters for individual internal fields;
- concurrency mechanisms remain private to the state boundary;
- the returned snapshot has a defined lifetime and consistency policy.

A by-value return, immutable snapshot handle, or bounded real-time buffer view
may all be valid. Choose from measured copy cost and execution context. Do not
expose a non-const reference or pointer to internally owned state.

## Command Ownership and Access

The robot control boundary owns one complete controller-facing command. An
upper control component loads it with `setCommand()`. A lower controller reads
it with `getCommand()`, applies feedback or other local adjustment to a
caller-owned copy, and passes the resulting complete command to hardware.

```cpp
robot.setCommand(trajectory_handler.step(state, goal));

const RobotCommand command =
    controller.step(state, robot.getCommand());
const HardwareStatus status = hardware.step(command);
```

Preserve these semantics:

- `setCommand()` makes one complete controller-facing command visible at once;
- `getCommand()` returns a value, immutable handle, or const view with a defined
  lifetime; a const reference commonly remains valid until the next
  `setCommand()` in the same execution context;
- callers never mutate internal command storage through a writable reference;
- the boundary does not limit, transmit, or record the actually transmitted
  command;
- no public accepted, limited, or sent command lifecycle is created;
- hardware remains the final owner of validation, protection, smoothing,
  conversion, transmission, and transmitted-command history.

The stored command is a control-side handoff point, not measured state and not
proof of physical application. Observe the result through later state updates.
Before the first `setCommand()`, `getCommand()` must follow an explicit
activation precondition or return an unavailable status rather than a
plausible-looking default command.

## State Update Flow

State acquisition and state acceptance are different responsibilities.

```text
Device packets
    -> hardware adapter: decode, map, offset, sign, unit conversion
    -> RobotState candidate in domain units
    -> trusted-state boundary: validate model/state contract
    -> atomically commit RobotState
    -> update state-bound model cache if applicable
```

The hardware adapter owns vendor communication and conversion from device
representation. The trusted-state boundary owns whether the resulting domain
observation is a valid controller-facing state for the configured robot model.

The runtime makes the cycle order visible:

```cpp
const RobotState candidate = hardware.readState();
const StateUpdateResult update = robot.updateState(candidate);

if (!update.ok()) {
  runtimePolicy.handleStateFailure(update.status);
  return;
}

const RobotState state = robot.getState();
robot.setCommand(planner.step(state, goal));
const RobotCommand command =
    controller.step(state, robot.getCommand());
const HardwareStatus hardware_status = hardware.step(command);
```

Do not hide device reads, planning, lower-level control, or hardware transmission
inside `updateState()`, `setCommand()`, or `getCommand()`.

## Model and State Coherence

When the trusted-state boundary owns state-dependent kinematics or dynamics
data, the model cache and `RobotState` must describe the same accepted snapshot.

- Update the cache only from an accepted state.
- Do not publish the new state before its required cache is ready.
- Associate derived data with the state sequence or version when stale cache use
  is otherwise possible.
- Do not let arbitrary callers mutate the shared model or state-dependent cache.
- Keep fixed model configuration separate from per-cycle model data.
- Make generalized position, generalized velocity, and actuated dimensions
  explicit, especially for floating-base systems.

If model calculations have independent workspaces or different update rates,
separate the model service from the state owner rather than weakening state
coherence. The controller should still receive one clear current-state snapshot.

## Live State Versus Hypothetical State

Optimization, MPC, simulation, and rollout code often evaluate hypothetical
states. These must not overwrite the accepted live `RobotState`.

Use one of the following:

- stateless model queries with explicit hypothetical `q` and `qdot`;
- a separate rollout/model workspace;
- a local copied model-data context owned by the solver or planner.

Keep the distinction visible:

```text
accepted live state     = trusted robot snapshot
Rollout state           = hypothetical planning or optimization sample
Simulator internal state = backend-owned simulation state
```

Only the acquisition or estimation path may commit the live state. A controller
must not call `updateState()` merely to evaluate a candidate configuration.

## Responsibility Boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| hardware adapter | device I/O, decoding, actuator mapping, raw-to-domain conversion | controller policy or authoritative model validation |
| robot control boundary | accepted `RobotState`, current controller-facing `RobotCommand`, robot-state contract, state/model coherence | controller, FSM, planner, device transport, hardware limits, transmitted-command history |
| `RobotModel` | fixed model, kinematics/dynamics operations, required workspaces | hardware communication or system mode |
| estimator | estimate generation and estimator history | unrestricted mutation of stored robot state |
| controller | feedback adjustment and controller history | acquisition, state ownership, command transmission |
| runtime | lifecycle, call order, and failure routing | model math or hidden state mutation |

Do not pass a trusted-state object everywhere as a service locator. A component
that only needs state should receive `RobotState`. A component that needs model
operations should depend on the narrow model contract it actually uses.

## Failure and Freshness

State update outcomes must distinguish the failures relevant to the system,
such as:

- invalid dimensions or representation;
- non-finite data;
- inconsistent joint and base snapshots;
- timestamp regression or unacceptable skew;
- stale observation;
- model/state convention mismatch;
- unavailable initial state.

On rejection, preserve the last accepted snapshot for diagnostics but report
that the new candidate failed. Do not silently present the old snapshot as
fresh. The runtime or FSM policy decides whether to hold, degrade, transition to
a fault state, or stop control.

Before the first accepted update, `getState()` must not return plausible-looking
zero data as though it were valid. Use an explicit unavailable result, validity
status, or activation precondition.

## Design Checklist

Before accepting a robot control boundary, verify:

1. Is its primary role to own and expose controller-facing robot state and the
   current controller-facing command?
2. Does every live-state write cross one validation and commit boundary?
3. Do consumers use one coherent snapshot per logical cycle?
4. Are dimensions, joint order, units, frames, timestamps, and validity defined?
5. Are hardware decoding and transport kept outside the state owner?
6. Are state-dependent model results coherent with the snapshot they describe?
7. Are hypothetical rollout states isolated from live robot state?
8. Can stale or rejected updates be distinguished from fresh accepted state?
9. Do `getState()` and `getCommand()` avoid exposing internally mutable state?
10. Does `setCommand()` replace one complete controller-facing command without
    inventing hardware command stages?
11. Has the boundary avoided becoming a controller, planner, FSM, hardware
    manager, or generic dependency container?
