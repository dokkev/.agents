# Robot System Architecture

Use `RobotSystem` as the narrow robot-domain boundary that owns the state a
controller is allowed to trust. It is not a master object for the entire
application.

## Contents

- [Primary Responsibility](#primary-responsibility)
- [What Trusted State Means](#what-trusted-state-means)
- [State Ownership and Access](#state-ownership-and-access)
- [State Update Flow](#state-update-flow)
- [Model and State Coherence](#model-and-state-coherence)
- [Live State Versus Hypothetical State](#live-state-versus-hypothetical-state)
- [Responsibility Boundaries](#responsibility-boundaries)
- [Failure and Freshness](#failure-and-freshness)
- [Design Checklist](#design-checklist)

## Primary Responsibility

`RobotSystem` stores and exposes the latest accepted `RobotState` in the
robot-domain conventions used by controllers, planners, and estimators.

The intended direction is:

```text
RobotHardware or estimator
    -> complete RobotState candidate
RobotSystem
    -> validate and commit RobotState
Controller, planner, FSM
    -> getState()
```

Other components must not independently assemble, own, or mutate competing
copies of the current robot state. They obtain the controller-facing snapshot
from `RobotSystem` and use the same snapshot for one logical cycle.

`RobotSystem` may also own or wrap the robot model and its cache when that keeps
model queries coherent with the stored state. This does not make it the owner of
the controller, planner, hardware transport, or application lifecycle.

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

`RobotSystem` is the authoritative owner of the accepted `RobotState` snapshot.

Prefer a small public boundary such as:

```cpp
class RobotSystem
{
public:
  [[nodiscard]] StateUpdateResult updateState(
      const RobotState& candidate);

  [[nodiscard]] RobotState getState() const;

private:
  RobotModel model_;
  RobotState state_;
};
```

The exact types and spelling may follow the repository, but preserve these
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

## State Update Flow

State acquisition and state acceptance are different responsibilities.

```text
Device packets
    -> RobotHardware: decode, map, offset, sign, unit conversion
    -> RobotState candidate in domain units
    -> RobotSystem: validate model/state contract
    -> atomically commit RobotState
    -> update state-bound model cache if applicable
```

`RobotHardware` owns vendor communication and conversion from device
representation. `RobotSystem` owns whether the resulting domain observation is
a valid controller-facing state for the configured robot model.

The runtime makes the cycle order visible:

```cpp
const RobotState candidate = hardware.readState();
const StateUpdateResult update = robot.updateState(candidate);

if (!update.ok()) {
  runtimePolicy.handleStateFailure(update.status);
  return;
}

const RobotState state = robot.getState();
const Reference reference = planner.computeReference(state, goal);
const RobotCommand command = controller.computeCommand(state, reference);
```

Do not hide device reads, planning, control, and command transmission inside
`updateState()` or `getState()`.

## Model and State Coherence

When `RobotSystem` owns state-dependent kinematics or dynamics data, the model
cache and `RobotState` must describe the same accepted snapshot.

- Update the cache only from an accepted state.
- Do not publish the new state before its required cache is ready.
- Associate derived data with the state sequence or version when stale cache use
  is otherwise possible.
- Do not let arbitrary callers mutate the shared model or state-dependent cache.
- Keep fixed model configuration separate from per-cycle model data.
- Make generalized position, generalized velocity, and actuated dimensions
  explicit, especially for floating-base systems.

If model calculations have independent workspaces or different update rates,
separate `RobotModel` from `RobotSystem` rather than weakening state coherence.
The controller should still receive one clear current-state snapshot.

## Live State Versus Hypothetical State

Optimization, MPC, simulation, and rollout code often evaluate hypothetical
states. These must not overwrite the live `RobotState` stored by `RobotSystem`.

Use one of the following:

- stateless model queries with explicit hypothetical `q` and `qdot`;
- a separate rollout/model workspace;
- a local copied model-data context owned by the solver or planner.

Keep the distinction visible:

```text
RobotSystem state       = accepted live robot snapshot
Rollout state           = hypothetical planning or optimization sample
Simulator internal state = backend-owned simulation state
```

Only the acquisition or estimation path may commit the live state. A controller
must not call `updateState()` merely to evaluate a candidate configuration.

## Responsibility Boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| `RobotHardware` | device I/O, decoding, actuator mapping, raw-to-domain conversion | controller policy or authoritative model validation |
| `RobotSystem` | accepted `RobotState`, robot-state contract, state/model coherence | controller, FSM, planner, device transport, goals, references |
| `RobotModel` | fixed model, kinematics/dynamics operations, required workspaces | hardware communication or system mode |
| estimator | estimate generation and estimator history | unrestricted mutation of stored robot state |
| controller | state/reference-to-command policy and controller history | acquisition, state ownership, command transmission |
| runtime | lifecycle, call order, and failure routing | model math or hidden state mutation |

Do not pass `RobotSystem&` everywhere as a service locator. A component that only
needs state should receive `RobotState`. A component that needs model operations
should depend on the narrow model contract it actually uses.

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

Before accepting a `RobotSystem` design, verify:

1. Is its primary role to own and expose controller-facing robot state?
2. Does every live-state write cross one validation and commit boundary?
3. Do consumers use one coherent snapshot per logical cycle?
4. Are dimensions, joint order, units, frames, timestamps, and validity defined?
5. Are hardware decoding and transport kept outside the state owner?
6. Are state-dependent model results coherent with the snapshot they describe?
7. Are hypothetical rollout states isolated from live robot state?
8. Can stale or rejected updates be distinguished from fresh accepted state?
9. Does `getState()` avoid exposing internally mutable state?
10. Has `RobotSystem` avoided becoming a controller, planner, FSM, hardware
    manager, or generic dependency container?
