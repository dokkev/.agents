# Control Loop Implementation

Use this standard for repeated controller, estimator, planner, simulation, and
hardware-interface update loops, especially in real-time or high-frequency
paths.

Apply this document together with `control-function-implementation.md` and
`control-variable-naming.md`.

## Contents

- [Core Principle](#core-principle)
- [Initialization Responsibilities](#initialization-responsibilities)
- [Loop Responsibilities](#loop-responsibilities)
- [Validate Untrusted Inputs at Boundaries](#validate-untrusted-inputs-at-boundaries)
- [Preserve Per-Cycle Safety Checks](#preserve-per-cycle-safety-checks)
- [Avoid Per-Cycle Allocation](#avoid-per-cycle-allocation)
- [Cache Fixed Work, Recompute State-Dependent Work](#cache-fixed-work-recompute-state-dependent-work)
- [Keep Diagnostics Outside the Critical Path](#keep-diagnostics-outside-the-critical-path)
- [Keep Execution Bounded](#keep-execution-bounded)
- [Verification](#verification)
- [Review Rules](#review-rules)

## Core Principle

Validate fixed structure once, preallocate reusable storage, and keep each loop
iteration focused on state-dependent computation and changing safety
conditions.

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
bool Controller::Initialize(
    const RobotModel& model,
    const ControllerConfig& config)
{
  if (config.kp.size() != model.na()
      || config.kd.size() != model.na()) {
    return false;
  }

  nq_ = model.nq();
  nv_ = model.nv();
  na_ = model.na();

  q_error_.resize(na_);
  qdot_error_.resize(na_);
  command_workspace_.tau.resize(na_);

  task_frame_id_ = model.GetFrameId(config.task_frame);
  return task_frame_id_ >= 0;
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

```cpp
void Controller::Update(
    const RobotState& state,
    const TaskReference& reference,
    RobotCommand* command)
{
  // Initialization guarantees compatible state, reference, and command sizes.

  // e_q = q_des - q
  q_error_.noalias() = reference.q - state.q;

  // e_qdot = qdot_des - qdot
  qdot_error_.noalias() = reference.qdot - state.qdot;

  // tau = Kp e_q + Kd e_qdot + tau_ff
  command->tau.noalias() =
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
q_error_.setZero();
jacobian_workspace_.setZero();
solver_workspace_.ResetValues();
```

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

## Verification

Verify fixed contracts with initialization tests and malformed-input tests at
adapter boundaries. Verify loop behavior with deterministic state/reference
examples, failure-path tests, and safe offline or simulated execution.

For strict no-allocation loops, use an allocation detector, Eigen runtime malloc
guard, or equivalent test when supported by the project. Do not claim the loop
is allocation-free based only on visual inspection.

## Review Rules

Flag repeated-path code when it:

- validates fixed dimensions or configuration every cycle;
- resizes owned storage after successful initialization;
- performs avoidable dynamic allocation or formatting;
- resolves names, frames, parameters, or mappings repeatedly;
- performs blocking or unbounded work;
- removes a changing runtime safety check in the name of performance;
- mixes untrusted external data directly into the control law;
- hides the mathematical loop behind generic helpers.

Require evidence before recommending micro-optimization. Prioritize stable
memory behavior, bounded execution, safety, and readable data flow.