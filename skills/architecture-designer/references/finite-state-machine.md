# Finite-State Machine Architecture

Use this reference when a robot has discrete modes or behaviors whose entry,
per-cycle action, exit, transition, and failure semantics must remain coherent.
Do not introduce an FSM when a local enum and a short explicit branch already
describe the complete behavior.

## Contents

- [Preserve Semantics, Not One Class Shape](#preserve-semantics-not-one-class-shape)
- [Lifecycle Contract](#lifecycle-contract)
- [Coordinator Ownership](#coordinator-ownership)
- [Explicit Outputs And Transitions](#explicit-outputs-and-transitions)
- [Keep State Logic Thin](#keep-state-logic-thin)
- [Separate Stateful Behavior Components](#separate-stateful-behavior-components)
- [Cycle, Failure, And Real-Time Boundaries](#cycle-failure-and-real-time-boundaries)
- [Design Checklist](#design-checklist)

## Preserve Semantics, Not One Class Shape

Follow the repository's established interface, names, and ownership model when
they express the required lifecycle safely. A base class, `std::variant`, table,
or explicit switch can all be valid.

Do not require a templated base, an `FSMHandler` class, or exact method names
such as `Initialize()`, `FirstVisit()`, `Step()`, and `LastVisit()` across every
repository. Require the semantic equivalents only when the behavior needs them:

- one-time configuration before activation;
- one entry action per activation;
- one bounded active-state action per logical cycle;
- one exit action before leaving an active state or shutting down;
- a type-safe state identity and explicit transition outcome.

Use the smallest representation that makes those guarantees visible. Do not
pass a generic mutable context, service locator, or unrestricted `RobotSystem&`
to every state merely to simplify signatures.

## Lifecycle Contract

Define the lifecycle and re-entry behavior next to the FSM interface.

| Semantic phase | Typical responsibility |
| --- | --- |
| configure | validate fixed dependencies and configuration; establish storage |
| enter | capture entry conditions; reset state-local behavior; start delegated work |
| step | produce this cycle's output and request a transition or failure outcome |
| exit | stop or finalize delegated behavior and clear entry-local state |

Re-entry normally repeats the entry action but not one-time configuration. An
initialization failure prevents activation. Orderly shutdown runs the active
state's exit behavior when required by its contract.

If a mode has no entry or exit work, an explicit no-op or a representation that
omits the hook is acceptable. Do not create empty methods solely to satisfy a
universal shape.

## Coordinator Ownership

Give one coordinator exclusive ownership of:

- active state identity;
- state registry or dispatch table when one exists;
- lifecycle call ordering;
- pending transition requests;
- transition-target validation;
- shutdown of the active state.

States request transitions; they do not switch the active state or invoke one
another's lifecycle methods. Runtime code outside the coordinator may request a
mode or fault policy, but it must not mutate active-state internals.

The coordinator owns lifecycle, not trajectory generation, control laws,
dynamics, device I/O, or motion policy.

## Explicit Outputs And Transitions

Return the state output and transition/failure outcome explicitly. Avoid hidden
booleans and system-wide mutation.

```cpp
StateStep<ModeId, Reference> MoveMode::Step(const RobotState& state)
{
  const TrajectoryResult result = trajectory_.Step(state);
  if (!result.ok()) {
    return StateStep::Failure(result.status);
  }
  if (result.finished) {
    return StateStep::Transition(ModeId::kHold, result.reference);
  }
  return StateStep::Continue(result.reference);
}
```

Treat the names and types as illustrative. Preserve the important properties:
one input snapshot, one complete output, and one explicit outcome.

Define when a requested transition commits. In a control cycle, do not change
the active mode halfway through planning, control, limiting, or hardware write.
A common policy is to retain the request produced by the current cycle and
commit it at the next cycle boundary, after the current output has been handed
off. Another policy is valid when its atomic boundary and output semantics are
equally explicit.

## Keep State Logic Thin

An FSM state coordinates behavior. Keep its active step short enough to reveal:

- the immutable state and goal or target it consumes;
- delegated planner, trajectory, controller, or handler calls;
- named guards;
- the output and transition/failure outcome.

Keep these outside the state unless the behavior is genuinely trivial:

- interpolation, waypoint timing, and trajectory progression;
- inverse kinematics, optimization, dynamics, or controller equations;
- estimation and complex filtering;
- transport, vendor SDK, and middleware mechanics;
- actuator mapping, offsets, signs, gearing, and unit conversion;
- hardware transmission and system-wide mutation.

Idle, hold, fault, and emergency-stop modes do not need artificial planner
objects merely to satisfy a pattern.

## Separate Stateful Behavior Components

Create only the components required by the behavior:

| Component | Responsibility |
| --- | --- |
| motion planner | choose a path, strategy, or waypoint sequence |
| trajectory component | own time, segments, interpolation, and reference progression |
| controller | convert state and reference into a domain command |
| FSM state | coordinate mode-specific calls, guards, and output |
| FSM coordinator | own active state, transitions, and lifecycle order |

Do not add an empty planner or handler for naming symmetry. Trajectory progress
belongs to the component that owns the trajectory, not to scattered counters
inside the state.

## Cycle, Failure, And Real-Time Boundaries

- Use one coherent input snapshot for a state's logical step.
- Define self-transition behavior; do not accidentally restart lifecycle hooks.
- Reject unknown or unavailable states with an explicit status.
- Route failures to a named hold, fault, disable, or safe-state policy.
- Prevent transition loops or unbounded repeated transitions in one cycle.
- Preserve the state identity and snapshot sequence that caused a transition
  when diagnostics need them.
- Configure state storage and registries before activation.
- Do not allocate states, load plugins, block, or perform device I/O in a
  deadline-sensitive FSM step.

Read `runtime-dataflow.md` when ROS 2 `read-update-write`, command handoff, or a
multi-rate cycle determines the transition boundary.

## Design Checklist

1. Is an FSM more legible than a local branch for this behavior?
2. Is one owner responsible for active state and lifecycle ordering?
3. Are entry, step, exit, re-entry, and shutdown semantics defined where needed?
4. Does each step return one complete output and explicit outcome?
5. Is the transition commit point atomic with respect to the control cycle?
6. Are planning, trajectory, control, and hardware mechanics owned elsewhere?
7. Are failure and safe-state policies named rather than hidden?
8. Are representation and method names adapted to the repository instead of
   imposed globally?
