# Robot System Architecture

Use `RobotSystem` when a Pinocchio-based WBC, OSC, or other model-based
controller needs one accepted live robot state and coherent kinematics or
dynamics data. Do not introduce it merely to share a command, wrap the runtime,
or give every component access to the application.

## Section Map

- [Core Contract](#core-contract)
- [When the Boundary Is Justified](#when-the-boundary-is-justified)
- [Accept One Trusted State](#accept-one-trusted-state)
- [Keep Model and State Coherent](#keep-model-and-state-coherent)
- [Expose a Narrow Model-and-State API](#expose-a-narrow-model-and-state-api)
- [Keep Command Storage Optional](#keep-command-storage-optional)
- [Separate Live and Hypothetical State](#separate-live-and-hypothetical-state)
- [Responsibility Boundaries](#responsibility-boundaries)
- [Failure and Freshness](#failure-and-freshness)
- [Design Checklist](#design-checklist)

## Core Contract

`RobotSystem` is the controller-facing model-and-state boundary. It keeps the
accepted `q` and `qdot` coherent with the Pinocchio model data and cache used by
model-based control.

```text
hardware adapter or estimator
    -> complete RobotState candidate
RobotSystem
    -> validate and accept q, qdot, and metadata
    -> update Pinocchio model data for that accepted state
WBC / OSC / model-based controller
    -> read one coherent model-and-state view
    -> return one complete nominal or fallback joint command with status
```

It does not own the controller, planner, FSM, hardware transport, actuator
mapping, transmitted-command history, or application lifecycle. Controllers
that do not need a shared robot model should receive their required state and
reference directly instead of being forced through `RobotSystem`.

## When the Boundary Is Justified

Use a dedicated `RobotSystem` when several model-based calculations must agree
on:

- the accepted generalized position and velocity;
- fixed-base or floating-base dimensions and ordering;
- Pinocchio kinematics, dynamics, frame, Jacobian, or centroidal quantities;
- the sequence or version of state represented by the model cache.

Keep the boundary inside a small controller or runtime when only one component
uses the model and a separate class adds no ownership value. Do not turn a
single PD controller, device adapter, or simple state-feedback loop into a
model framework preemptively.

## Accept One Trusted State

"Trusted" means that the state crossed an explicit acceptance boundary and
satisfies the structural contract required by its consumers. It does not mean
that every measurement is physically exact.

Validate the relevant properties before acceptance:

- configured `nq`, `nv`, and actuated dimensions;
- finite values and valid constrained representations;
- generalized-coordinate layout, joint order, units, and frames;
- base and joint snapshot coherence;
- timestamp, sequence, source, validity, and freshness metadata.

Build a complete candidate and commit it atomically. A failed update must not
partially replace the accepted state or model cache. Sensor uncertainty and
task suitability remain separate explicit inputs when they matter.

## Keep Model and State Coherent

The stored state and state-dependent Pinocchio data must describe the same
accepted snapshot.

- Update model data only from an accepted state.
- Do not publish the new state before the required model update is complete.
- Associate derived data with the state sequence when stale-cache use is
  otherwise possible.
- Keep fixed model configuration separate from per-cycle model data.
- Prevent arbitrary callers from mutating the shared model or cache.
- Make `nq`, `nv`, and actuated dimensions explicit for floating-base systems.

If calculations require independent workspaces or rates, give those consumers
their own model-data workspace rather than weakening live-state coherence.

## Expose a Narrow Model-and-State API

Follow local names and types, but keep the public role small:

```cpp
class RobotSystem
{
public:
  [[nodiscard]] StateUpdateResult Update(
      const RobotState& candidate);

  [[nodiscard]] const RobotState& state() const;
  [[nodiscard]] const RobotModelView& model() const;

private:
  RobotState state_;
  PinocchioModel model_;
};
```

Preserve these semantics:

- state replacement passes through one validation and commit operation;
- returned state and model views are read-only and share a defined version;
- the access lifetime is explicit and safe for the execution context;
- buffer, lock, and cache mechanics remain private;
- callers cannot retrieve unrestricted mutable Pinocchio data or hardware
  objects.

A by-value snapshot, immutable handle, or bounded real-time view can all be
valid. Choose from measured copy cost and actual concurrency, not fashion.

## Keep Command Storage Optional

Command storage is not inherent to `RobotSystem`. Prefer direct flow when one
runtime call already owns the cycle:

```cpp
const RobotState& state = robot_system.state();
const Reference reference = behavior.Step(state, goal);
const ControllerResult result =
    controller.Step(robot_system, reference);
const HardwareStatus status = hardware.Step(result.command);
```

Add a stored command only when a real handoff requires it, such as separate
upper and lower control components, multiple consumers, or different execution
contexts. If `setCommand()` and `getCommand()` are used, treat them as an
explicit command-channel contract:

- replace one complete controller-facing value atomically;
- expose no writable alias;
- define lifetime, initial availability, freshness, and concurrency semantics;
- do not limit, transmit, or record hardware-applied commands there.

Keeping that channel inside `RobotSystem` may be convenient in one codebase,
but it is a project data-flow choice independent of the Pinocchio model
abstraction.

## Separate Live and Hypothetical State

MPC, optimization, simulation, and rollout code must not overwrite accepted
live state to evaluate a candidate.

Use one of:

- stateless model queries with explicit hypothetical `q` and `qdot`;
- a solver- or planner-owned copied model-data workspace;
- a separate rollout model instance.

Keep accepted live state, rollout state, and simulator-internal state visibly
distinct. Only the acquisition or estimation path may commit live state.

## Responsibility Boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| hardware adapter | device I/O, decoding, actuator mapping, raw-to-domain conversion | control policy or model validation |
| `RobotSystem` | accepted live state, Pinocchio model data, state/model coherence | controller, FSM, planner, hardware, generic application context |
| controller | model/state/reference-to-joint-command calculation, control-level fallback, controller history | acquisition, transport, hardware-local protection |
| solver | one mathematical solve and its workspace or warm start | system mode or fallback behavior |
| runtime/FSM | call order, reference/behavior choice, mode transition, lifecycle | same-cycle joint-command fallback or model math |
| `RobotHardware` | command handoff to the plant and hardware-local protection | planning or control fallback policy |

Pass `RobotState` when a component only needs state. Pass a narrow model view
when it needs model quantities. Do not pass unrestricted `RobotSystem&` to every
class as a service locator.

## Failure and Freshness

Report state rejection reasons such as invalid dimensions, non-finite data,
timestamp regression, stale observation, representation mismatch, or
unavailable initial state. Preserve the last accepted state for diagnostics,
but never present it as a fresh successful update.

The joint-command-producing controller owns the same-cycle control fallback.
It returns one complete fallback command and status when its solver, model
input, or accepted state is unusable under its contract. The runtime or FSM may
react to that status by changing the next reference, behavior, or mode.
`RobotHardware` independently applies only hardware-local validation,
protection, watchdog, and device-fault response.

Before the first accepted update, do not return plausible zero state as valid.
Use an explicit unavailable result or require a valid initial-state activation
precondition.

## Design Checklist

1. Does this controller actually require a shared Pinocchio model-and-state
   boundary?
2. Does every live-state write cross one validation and atomic commit point?
3. Do the accepted state and model cache describe the same sequence?
4. Are dimensions, ordering, units, frames, timestamps, and validity explicit?
5. Are hardware decoding, transport, and protection outside `RobotSystem`?
6. Are hypothetical rollout states isolated from accepted live state?
7. Does the controller return a complete nominal or fallback joint command?
8. Is any stored command justified by a real handoff and kept separate from
   hardware-applied command history?
9. Have non-model-based controllers avoided an unnecessary `RobotSystem`?
10. Has the boundary avoided becoming a runtime, hardware manager, controller,
    FSM, planner, or generic dependency container?
