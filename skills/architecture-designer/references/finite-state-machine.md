# Finite-State Machine Architecture

Use this standard whenever a finite-state machine controls robot modes or
behaviors.

## Contents

- [Mandatory Structure](#mandatory-structure)
- [Lifecycle Contract](#lifecycle-contract)
- [FSMHandler Ownership](#fsmhandler-ownership)
- [Keep State Logic Thin](#keep-state-logic-thin)
- [Separate Motion and Trajectory Logic](#separate-motion-and-trajectory-logic)
- [Transition and Failure Rules](#transition-and-failure-rules)
- [Real-Time and Testing Rules](#real-time-and-testing-rules)
- [Review Checklist](#review-checklist)

## Mandatory Structure

Every FSM must use a common templated state contract. This requirement means a
small type-safe C++ template shared by all states, not template metaprogramming
or a framework hierarchy.

```cpp
template <typename StateId, typename Snapshot, typename Output>
class FiniteStateMachine
{
public:
  virtual ~FiniteStateMachine() = default;

  virtual void Initialize() = 0;
  virtual void FirstVisit(const Snapshot& snapshot) = 0;
  virtual StateStep<StateId, Output> Step(
      const Snapshot& snapshot) = 0;
  virtual void LastVisit() = 0;

  [[nodiscard]] virtual StateId GetStateId() const = 0;
};
```

Adapt template parameters and result types to the repository, but preserve:

- one common templated base contract;
- exactly the `Initialize()`, `FirstVisit()`, `Step()`, and `LastVisit()`
  lifecycle;
- type-safe state identifiers and transition results;
- no direct transition from one state object to another.

Inject exact dependencies through constructors. Do not use the template to pass
a generic mutable `Context`, `RobotSystem`, property bag, or service locator to
every state.

## Lifecycle Contract

| Method | Invocation | Responsibility |
| --- | --- | --- |
| `Initialize()` | once per state during system configuration | validate dependencies/configuration and establish fixed storage |
| `FirstVisit()` | once on every entry, before the first `Step()` | capture entry snapshot, reset state-local behavior, start delegated trajectory/planning work |
| `Step()` | once per active control cycle | call delegated components, produce the state output, and evaluate simple transition guards |
| `LastVisit()` | once immediately before exit or shutdown | stop or finalize delegated state behavior and clear entry-local state |

Re-entering a state calls `FirstVisit()` again but does not repeat
`Initialize()`. Initialization failure prevents activation. `LastVisit()` is
called for the active state during orderly shutdown.

Lifecycle methods must not be invoked from arbitrary runtime code or from
another state.

## FSMHandler Ownership

Every FSM is created, initialized, stepped, transitioned, and shut down through
an `FSMHandler`. The handler is the sole owner of:

- the active state identifier or pointer;
- the state registry;
- whether initialization and first visit occurred;
- pending transition requests;
- lifecycle call ordering.

```cpp
template <typename StateId, typename Snapshot, typename Output>
class FSMHandler
{
public:
  void Initialize();
  StateStep<StateId, Output> Step(const Snapshot& snapshot);
  void CommitRequestedTransition(const Snapshot& snapshot);
  void Shutdown();

private:
  void TransitionTo(StateId next_state, const Snapshot& snapshot);
  FiniteStateMachine<StateId, Snapshot, Output>* current_state_{nullptr};
};
```

The handler guarantees this order:

```text
Initialize each state once
current.FirstVisit(snapshot)

each cycle:
    commit the transition requested by the preceding completed cycle
    result = current.Step(snapshot)
    if result requests a transition:
        retain the request as pending
    return the current state's output

before the next cycle's Step():
    current.LastVisit()
    current = requested state
    current.FirstVisit(snapshot)

shutdown:
    current.LastVisit()
```

The runtime must issue the current state's output before the handler commits its
pending transition. With `ros2_control`, keep the request pending through the
hardware `write()` and commit it at the beginning of the next controller
update. A fault path may cancel or override a pending normal transition. See
`runtime-dataflow.md` for the cycle boundary and command flow.

The handler coordinates lifecycle only. It does not compute trajectories,
control laws, dynamics, hardware commands, or motion policy.

## Keep State Logic Thin

An FSM state coordinates behavior. It must not contain complex implementation
logic.

Allowed state responsibilities:

- pass the current immutable snapshot and state target to a planner or handler;
- select a preconfigured mode-specific dependency;
- return a `Reference`, behavior output, or explicit failure result;
- evaluate short transition guards from named status values;
- reset or stop a delegated component in `FirstVisit()` or `LastVisit()`.

```cpp
void MoveState::FirstVisit(const RobotState& state)
{
  trajectory_handler_.Reset(state, target_);
}

StateStep<StateId, Reference> MoveState::Step(
    const RobotState& state)
{
  const TrajectoryResult result = trajectory_handler_.Step(state);

  if (!result.ok()) {
    return StateStep::Failure(result.status);
  }
  if (result.finished) {
    return StateStep::Transition(StateId::kHold, result.reference);
  }
  return StateStep::Continue(result.reference);
}

void MoveState::LastVisit()
{
  trajectory_handler_.Stop();
}
```

Forbidden inside FSM state code:

- polynomial, spline, or other interpolation implementation;
- waypoint indexing and time progression;
- inverse kinematics, QP, dynamics, or optimization;
- contact or grasp planning;
- controller equations or solver assembly;
- complex filtering or state estimation;
- CAN, serial, DDS, ROS message, or vendor SDK operations;
- motor/joint mapping, offset, sign, gear, or unit conversion;
- direct calls to another state's lifecycle methods;
- hidden command transmission or system-wide mutation.

Idle, hold, fault, and emergency-stop states do not need a planner merely to
satisfy a pattern. Their `Step()` must still remain short and explicit.

## Separate Motion and Trajectory Logic

Use separate components for behavior complexity:

| Component | Responsibility |
| --- | --- |
| `MotionPlanner` | choose a path, motion strategy, or waypoint sequence from state and goal |
| `TrajectoryHandler` | own time, segment, interpolation, and reference progression |
| `Controller` | convert state and reference into a domain command |
| FSM state | invoke those components and express mode-specific ordering and guards |
| `FSMHandler` | own active state, transitions, and lifecycle calls |

Choose `MotionPlanner`, `TrajectoryHandler`, or both according to the behavior.
Do not create an empty wrapper only to satisfy a name. When planning is trivial
but time progression is stateful, use only a `TrajectoryHandler`. When a planner
returns a complete reference without ongoing trajectory state, use only the
planner.

Trajectory progress belongs to the trajectory component, not to an FSM state's
collection of counters and timestamps.

## Transition and Failure Rules

- A state requests a transition in its `Step()` result; it never performs the
  transition itself.
- `FSMHandler` validates and retains the requested target until the runtime has
  issued the current state's output.
- At the next defined cycle boundary, `FSMHandler` calls `LastVisit()`, switches
  the active state, and calls `FirstVisit()` exactly once before the new
  state's `Step()`.
- Do not change the active state halfway through controller or hardware work.
- Define self-transition behavior explicitly. Prefer no lifecycle restart unless
  restart semantics are requested by a distinct result.
- Reject unknown or unavailable state IDs with an explicit status.
- Do not silently transition on planner, controller, or sensor failure.
- Route failures to a named fault, hold, or safe-state policy owned at the FSM or
  runtime level.
- Prevent transition loops and unbounded multiple transitions in one cycle.
- Preserve the state snapshot that caused the transition for diagnostics.

## Real-Time and Testing Rules

Initialize the state registry and fixed storage before activation. Do not add or
remove states, allocate state objects, load plugins, or perform blocking work in
the control cycle.

Test at least:

- initialization once per state;
- `FirstVisit()` once per entry and on re-entry;
- one `Step()` per active cycle;
- `LastVisit()` exactly once before transition and shutdown;
- normal, self, invalid, and failure transitions;
- no direct state-to-state lifecycle call;
- delegated planner/trajectory reset and stop behavior;
- failure routing without stale or partially updated output.

## Review Checklist

Reject an FSM design when:

1. states do not share the templated lifecycle contract;
2. anything other than `FSMHandler` changes the active state or calls lifecycle
   methods;
3. one of the four required lifecycle methods is absent or ambiguously called;
4. `Step()` implements interpolation, planning, control, estimation, dynamics,
   protocol, or hardware mechanics;
5. trajectory timing or waypoint progression lives in the state;
6. transition and failure outcomes are hidden booleans or side effects;
7. a generic context gives every state unrestricted access to the system;
8. lifecycle calls can repeat, be skipped, or occur midway through a cycle.
