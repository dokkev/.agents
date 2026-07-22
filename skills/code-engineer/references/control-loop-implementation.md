# Control Loop Implementation

Loading this reference does not authorize tests, validation, or review.

Use this standard for repeated control, estimation, planning, simulation, and
hardware-interface update loops, especially in real-time or high-frequency
paths.

Select other references separately only when their triggers apply: data
conventions for units or frames, numerical guidance for solver or geometry work,
concurrency guidance for cross-context data, and discrete-time guidance for
history or elapsed time.

## Section Map

- [Core Contract](#core-contract)
- [Initialization Responsibilities](#initialization-responsibilities)
- [Loop Responsibilities](#loop-responsibilities)
- [Validate Untrusted Inputs at Boundaries](#validate-untrusted-inputs-at-boundaries)
- [Consume Coherent Snapshots](#consume-coherent-snapshots)
- [Preserve Per-Cycle Safety Checks](#preserve-per-cycle-safety-checks)
- [Avoid Per-Cycle Allocation](#avoid-per-cycle-allocation)
- [Cache Fixed Work, Recompute State-Dependent Work](#cache-fixed-work-recompute-state-dependent-work)
- [Keep Diagnostics Outside the Critical Path](#keep-diagnostics-outside-the-critical-path)
- [Keep Execution Bounded](#keep-execution-bounded)
- [Handle Failures by Contract](#handle-failures-by-contract)

## Core Contract

Validate fixed structure once, preallocate reusable storage, and keep each loop
iteration focused on state-dependent computation and changing safety
conditions.

The WBC, OSC, or other controller that produces the joint-level command must
leave one complete nominal or controller-defined fallback command on every
recoverable return path and report which path was used.

Do not repeat dimension, model, configuration, or resource checks when the
lifecycle guarantees that those properties cannot change during operation.

## Initialization Responsibilities

Perform these operations during construction, configuration, loading, or
`Initialize()`:

- verify that required models and configuration exist;
- validate `nq`, `nv`, `na`, and other fixed dimensions;
- validate gain, limit, state, reference, and command shapes;
- validate joint names, joint order, actuator order, and frame identifiers;
- resolve joint, frame, parameter, and message indices;
- validate constant units and conversion factors;
- compute constant mappings, transforms, and selection matrices;
- resize Eigen vectors and matrices;
- reserve container capacity;
- initialize solver structures and reusable workspaces;
- establish adapter and protocol mappings.

Fail initialization with a useful diagnostic when a fixed contract is invalid.
Do not defer a known configuration error to the control loop.

```cpp
InitializeStatus Controller::Initialize(
    const RobotModel& model,
    const ControllerConfig& config)
{
  if (config.kp.size() != model.na()
      || config.kd.size() != model.na()) {
    return InitializeStatus::kInvalidGainDimension;
  }

  nq_ = model.nq();
  nv_ = model.nv();
  na_ = model.na();

  q_error_.resize(na_);
  qdot_error_.resize(na_);
  command_workspace_.tau.resize(na_);

  task_frame_id_ = model.GetFrameId(config.task_frame);
  if (task_frame_id_ < 0) {
    return InitializeStatus::kMissingTaskFrame;
  }

  return InitializeStatus::kOk;
}
```

## Loop Responsibilities

Keep each update focused on work that depends on current state or reference:

- acquire or receive the latest valid state snapshot;
- read the active reference;
- update state-dependent kinematics and dynamics;
- compute errors and the control law;
- update and solve the numerical problem;
- check solver and numerical status;
- map the result into command space;
- apply safety and rate limits;
- publish or return the command.

Do not repeat fixed dimension checks or resize owned workspaces in the loop.

The example below assumes Euclidean actuated-joint coordinates. Use the model's
manifold difference operation when `q` includes a floating base or another
non-Euclidean joint.

```cpp
void Controller::Step(
    const RobotState& state,
    const TaskReference& reference,
    RobotCommand* command)
{
  // Initialization guarantees compatible state, reference, and command sizes.

  // e_q = q_des - q
  q_error_ = reference.q - state.q;

  // e_qdot = qdot_des - qdot
  qdot_error_ = reference.qdot - state.qdot;

  // tau = Kp e_q + Kd e_qdot + tau_ff
  command->tau =
      gains_.kp.cwiseProduct(q_error_)
      + gains_.kd.cwiseProduct(qdot_error_)
      + reference.tau_ff;

  ApplyCommandLimits(command);
}
```

Treat an unexpected internal dimension change as a lifecycle or ownership
contract violation, not as a normal per-cycle condition.

## Validate Untrusted Inputs at Boundaries

Validate variable-size messages, packets, files, and external inputs at the
adapter boundary before they become trusted internal state.

```cpp
bool RobotStateAdapter::Decode(
    const RobotStateMessage& message,
    RobotState* state)
{
  if (message.position.size() != expected_joint_count_) {
    return false;
  }

  CopyState(message, state);
  return true;
}
```

Pass only validated, fixed-contract objects into the controller.

> Validate untrusted data at the boundary. Do not repeatedly revalidate trusted
> internal state.

## Consume Coherent Snapshots

Read state, reference, mode, and configuration through coherent snapshots. Do
not read individual fields from a concurrently changing object throughout the
control calculation.

```cpp
const StateSnapshotHandle state_snapshot = state_buffer_.AcquireLatest();
const ReferenceSnapshotHandle reference_snapshot =
    reference_buffer_.AcquireLatest();

const RobotState& state = state_snapshot.state();
const TaskReference& reference = reference_snapshot.reference();
```

The concrete handoff may use a real-time buffer, double buffer, bounded lock, or
another mechanism appropriate to the platform. Its contract must guarantee that
the controller never combines fields from different publications.

Avoid blocking mutex acquisition, allocation, callback execution, and
destruction of unpredictable objects in the critical path. If copying a large
snapshot is too expensive, use an immutable preallocated buffer with an
explicit lifetime and ownership protocol; do not retain a view that the
producer can overwrite during the update.

Apply parameter or mode changes at a defined cycle boundary. If a change
invalidates dimensions, solver structure, mapping, or allocation, leave the
active loop and reinitialize instead of rebuilding those resources in place.

## Preserve Per-Cycle Safety Checks

Do not confuse structural validation with runtime safety. Check conditions that
can change during operation at the frequency required by the safety design.

Typical per-cycle checks include:

- state timestamp freshness;
- communication watchdog state;
- emergency stop and hardware enable state;
- measurement and command finite-value checks;
- solver success and numerical status;
- position, velocity, effort, and command-rate limits;
- mode transition conditions;
- sensor validity when it can change at runtime.

```cpp
if (state.age > maximum_state_age_) {
  SetSafeCommand(command);
  return;
}

if (!solver_status.success || !command->tau.allFinite()) {
  SetSafeCommand(command);
  return;
}
```

Keep required safety checks deterministic and allocation-free.

## Avoid Per-Cycle Allocation

Allocate or resize dynamic storage before entering the repeated path. Reuse
member workspaces for dynamic Eigen objects, solver storage, message buffers,
and containers whose size is fixed after initialization.

Prefer:

```cpp
q_error_ = reference.q - state.q;
values_.clear();  // Retains previously reserved capacity.
solver_workspace_.ResetValues();
```

Do not clear or zero storage that the next operation fully overwrites. Clear
only the entries required by the called API or by partial assembly.

Avoid in repeated paths:

```cpp
Eigen::VectorXd error = Eigen::VectorXd::Zero(na_);
Eigen::MatrixXd jacobian = Eigen::MatrixXd::Zero(6, nv_);
std::vector<double> values;
values.push_back(sample);
```

Also avoid:

- repeated `resize()` or capacity growth;
- repeated dynamic Eigen allocation and unnecessary large copies;
- string creation and formatting;
- exception-driven normal control flow;
- parameter-server or configuration lookup;
- file access and blocking network I/O;
- unbounded logging or message construction.

Keep cheap scalars and fixed-size stack objects local. Do not turn every
temporary into member state. Preallocate only when it provides stable memory
behavior or clear ownership in the repeated path.

## Cache Fixed Work, Recompute State-Dependent Work

Compute fixed values once:

- joint and frame indices;
- actuator mappings;
- gear ratios and unit scaling;
- fixed transforms;
- constant selection matrices;
- solver structure and sparsity patterns;
- command limit shapes.

Recompute values that depend on the current state:

```cpp
model_.UpdateKinematics(state.q, state.qdot);
model_.ComputeTaskJacobian(task_frame_id_, &jacobian_workspace_);
```

Do not cache a state-dependent quantity unless its invalidation rule is explicit
and correct.

## Keep Diagnostics Outside the Critical Path

Avoid expensive logging and formatting in the loop. Update a compact,
preallocated diagnostic snapshot or counters and publish them from a lower-rate,
non-critical context.

```cpp
diagnostics_.maximum_error = q_error_.lpNorm<Eigen::Infinity>();
diagnostics_.solver_failed = !solver_status.success;
```

Throttle unavoidable diagnostics and ensure disabled logging does not still
construct strings or dynamic messages.

## Keep Execution Bounded

Avoid unbounded or blocking work in the control path:

- unlimited solver iterations or retries;
- blocking mutex acquisition;
- synchronous disk or network operations;
- input-dependent container growth;
- reconnection loops;
- waiting for user input or external services.

Set explicit solver iteration, retry, and timeout limits. Use coherent state
snapshots, bounded synchronization, or non-blocking handoff mechanisms where
the architecture requires concurrency.

## Handle Failures by Contract

Classify failures by when they can occur and whether operation can continue:

- **Invalid fixed configuration:** For a wrong gain dimension, missing frame,
  or duplicate joint, refuse initialization with a specific diagnostic.
- **Recoverable runtime fault:** For stale state, a temporary solver failure,
  or an invalid sensor sample, let the joint-command controller write its
  predefined complete fallback and return a specific status.
- **Programming or lifecycle contract violation:** For an internal dimension
  change or update before initialization, assert or enter a controlled fault or
  shutdown according to the deployment policy.

Do not turn a fixed configuration error into a per-cycle branch, resize, or
warning. Do not continue from a programming contract violation as though it
were a noisy sensor sample.

Every update path must leave the output command in a defined state. In
particular:

- never leave a partially updated command;
- never resend a previous command accidentally;
- never use a failed solver's output merely because its buffer contains values;
- never clamp NaN or infinity and continue;
- never catch an exception and silently report success.

Holding the last valid command is allowed only when it is an explicit, bounded
fallback with its own watchdog and expiry. It is not a default error response.

Define the control-level fallback for each joint-command controller during
design and initialization. Depending on the mechanism and hardware safety
layer, it may be zero effort, damped motion, gravity compensation, a bounded
position hold, or a request to disable. There is no universally safe numeric
command.

```cpp
UpdateStatus Controller::Step(
    const RobotState& state,
    const TaskReference& reference,
    RobotCommand* command)
{
  if (state.age > maximum_state_age_) {
    SetSafeCommand(command);
    return UpdateStatus::kStaleState;
  }

  const SolverStatus solver_status = solver_.Solve(&solution_);
  if (!solver_status.success || !solution_.tau.allFinite()) {
    SetSafeCommand(command);
    return UpdateStatus::kInvalidSolution;
  }

  command->tau = solution_.tau;
  ApplyCommandLimits(command);

  if (!command->tau.allFinite()) {
    SetSafeCommand(command);
    return UpdateStatus::kInvalidCommand;
  }

  return UpdateStatus::kOk;
}
```

The example shows control flow, not permission to allocate or resize dynamic
vectors in a high-frequency implementation. Use preallocated storage and the
solver's allocation-free API when required.

The runtime or FSM may observe the returned status and choose the next
reference, behavior, or mode. It must not overwrite the controller's command
for the same cycle. Hardware applies its separate local validation, protection,
watchdog, and device-fault response.

Return or record a specific status that identifies the first owning failure.
Update compact counters or fault state in the loop and format diagnostics in a
non-critical context.

Define recovery explicitly:

- whether a fault is transient or latched;
- how many consecutive failures are tolerated;
- what condition permits re-entry to active control;
- whether integrators, filters, warm starts, and rate limiters must reset;
- which hardware watchdog remains responsible if software stops updating.

Bound retries and escalation. Repeated transient failures must not create an
infinite retry loop or indefinite operation in an undocumented degraded mode.
