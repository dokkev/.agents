# Control Function Implementation

Loading this reference does not authorize tests, validation, or review.

Use this standard when implementing or reviewing controller, estimator,
planner, solver, simulation, dynamics, kinematics, and numerical functions.
For a repeated high-frequency path, select `control-loop-implementation.md`
separately when its trigger applies.

## Contents

- [Core Principle](#core-principle)
- [Keep Core Logic Visible](#keep-core-logic-visible)
- [Name Functions by Observable Behavior](#name-functions-by-observable-behavior)
- [Helper Boundary](#helper-boundary)
- [Equation Comments](#equation-comments)
- [Reading Locality](#reading-locality)
- [Structure Longer Functions with Sections](#structure-longer-functions-with-sections)
- [Make Ownership and Data Flow Explicit](#make-ownership-and-data-flow-explicit)
- [Make Mutation and Side Effects Visible](#make-mutation-and-side-effects-visible)

## Core Principle

Keep the mathematical and decision-making flow visible in the main function.
Use helpers to hide mechanical detail, not algorithmic meaning.

A reader who is new to the repository should be able to understand the core
algorithm without repeatedly jumping between functions or files.

## Keep Core Logic Visible

Keep these operations in the main function when they define the behavior being
implemented:

- state and reference selection;
- error computation;
- control laws;
- objective and constraint construction;
- solver input assembly;
- interpretation of solver outputs;
- command-space mapping;
- important mode transitions;
- safety-critical decisions and fallback selection.

Avoid vague helpers that hide the algorithm.

```cpp
// Avoid
bool Controller::Update()
{
  UpdateState();
  ComputeError();
  ComputeControl();
  ApplyOutput();
  return true;
}
```

Prefer code that presents the mathematical story directly.

The example below assumes Euclidean actuated-joint coordinates. Use the model's
manifold difference operation when `q` contains a floating base or another
non-Euclidean joint.

```cpp
bool Controller::Step(
    const RobotState& state,
    const TaskReference& reference,
    RobotCommand* command)
{
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
  return true;
}
```

## Name Functions by Observable Behavior

Use short lifecycle names when the class or interface supplies the context:

```cpp
Initialize();
Reset();
Start();
Stop();
Step();
Update();
Read();
Write();
```

For other functions, prefer a specific verb followed by the domain noun. Do not
repeat the class name, narrate the full parameter list, or add `Internal`,
`Impl`, or `Helper` merely to distinguish an implementation detail.

```cpp
// Avoid
controller.ComputeCommand(state, reference);
ComputeEndEffectorPoseFromJointPositions(q);
ProcessData();
HandleInput();
ComputeControlInternal();

// Prefer
robot.setCommand(trajectory_handler.step(state, goal));
const RobotCommand command =
    controller.step(state, robot.getCommand());
ComputeEndEffectorPose(q);
DecodeState(frame);
ApplyCommandLimits(command);
```

Use verbs consistently:

| Verb | Expected behavior |
| --- | --- |
| `Step` | Advance one stateful planner, trajectory, controller, or hardware cycle |
| `Compute` | Optionally calculate a pure mathematical result without changing persistent semantic state |
| `Build` | Construct a value or problem description from inputs |
| `Update` | Refresh owned state or a cache from new input |
| `Apply` | Mutate the named target according to a rule |
| `Set` | Replace an owned property or configuration value |
| `Validate` | Inspect a contract without modifying the input |
| `Encode` / `Decode` | Convert between representations |
| `Read` / `Write` | Interact with a device or stateful interface |
| `Publish` / `Send` | Produce an external communication side effect |

Do not require a generic `ComputeCommand()` layer merely because a component
returns a value. A stateful trajectory or planner may return the next desired
command from `Step()`, and the caller may load it directly with `setCommand()`.
Use `Compute` only when purity is real and the name clarifies a mathematical
operation such as a pose, Jacobian, or gravity term.

Name Boolean queries with `Is`, `Has`, `Can`, or `Should` when it improves
readability. A function name must not imply purity when it changes internal or
external state.

## Helper Boundary

Use a helper when its implementation is not required to understand the core
algorithm. Good helper responsibilities include:

- quaternion, rotation, pose, and coordinate conversion;
- frame transformation;
- unit conversion;
- message conversion;
- encoding, decoding, packing, parsing, byte order, and checksums;
- command clamping and saturation;
- repetitive shape or configuration validation outside the hot path;
- logging and diagnostic formatting;
- buffer initialization and mechanical workspace management;
- file and configuration parsing;
- low-level transport operations.

Examples:

```cpp
const Eigen::Vector3d rpy = QuaternionToRpy(state.orientation);
const double torque = DecodeTorque(frame);
ApplyCommandLimits(command);
PublishCommand(*command);
```

Before extracting a helper, ask:

> Would a reader need to open this helper to understand how this controller or
> algorithm works?

If yes, keep the logic visible at the call site.

```cpp
// Avoid: the control law is hidden.
const Eigen::VectorXd tau = ComputeControlTorque(state, reference);

// Prefer: the control law remains visible and uses preallocated command storage.
command->tau =
    gains_.kp.cwiseProduct(reference.q - state.q)
    + gains_.kd.cwiseProduct(reference.qdot - state.qdot)
    + reference.tau_ff;
```

## Equation Comments

Place the corresponding equation immediately above non-trivial control,
dynamics, estimation, or optimization code.

```cpp
// e_p_W = p_W_des - p_W
const Eigen::Vector3d position_error_W =
    reference.position_W - state.position_W;

// e_R_W = Log(R_WB_des R_WB^T), expressed in the world frame.
const Eigen::Vector3d orientation_error_W =
    LogRotation(reference.rotation_WB * state.rotation_WB.transpose());

// Task-vector ordering: [linear; angular], expressed in the world frame.
Vector6d task_error_W;
task_error_W << position_error_W, orientation_error_W;

// wrench_W = Kp e_task_W + Kd e_twist_W
const Vector6d wrench_W =
    gains_.kp.cwiseProduct(task_error_W)
    + gains_.kd.cwiseProduct(velocity_error_W);

// tau = J_W^T wrench_W + g(q)
command->tau.noalias() =
    jacobian_W.transpose() * wrench_W + gravity;
```

Document relevant frame, unit, sign, convention, and approximation assumptions.

```cpp
// e_R_B = Log(R_WB^T R_WB_des), expressed in the current body frame.
const Eigen::Vector3d orientation_error_B =
    LogRotation(state.rotation_WB.transpose() * reference.rotation_WB);
```

Do not add comments that merely translate an obvious line into prose. Keep an
equation comment adjacent to its implementation so they are updated together.

## Reading Locality

Optimize for reading locality rather than minimum function length.

- Keep one algorithm understandable from one function or one source file.
- Avoid helper chains deeper than one meaningful hop from the main function.
- Keep a single-use block inline unless it isolates substantial mechanical
  detail, a safety boundary, or a separately testable contract.
- Do not create a helper solely to reduce the line count of another function.
- Keep related calculations next to each other.
- Order private helper definitions by their first use when practical.
- Do not create a new file for one small helper.
- Prefer a somewhat longer coherent function over many tiny wrappers.

Do not enforce an arbitrary function-length limit. Split only when the split
creates a real conceptual or ownership boundary.

## Structure Longer Functions with Sections

Use blank lines and short section comments to expose the phases of a longer
algorithm.

```cpp
bool Controller::Update(...)
{
  // State and reference
  ...

  // Task-space error
  ...

  // Impedance control law
  ...

  // Joint-space command
  ...

  // Safety limits
  ...

  return true;
}
```

Do not replace these sections with vague `Compute...()` or `Process...()`
helpers when doing so would hide the important calculations.

## Make Ownership and Data Flow Explicit

Use function signatures to reveal which values are read, produced, and
modified.

- Pass read-only non-trivial inputs by `const&`.
- Pass small scalar and enum values by value.
- Return a value when the function naturally produces one result and the call is
  not a preallocated repeated path.
- Use an explicit non-owning output pointer for caller-owned storage that is
  filled or modified, especially for reusable control-loop workspaces.
- Return a status alongside an output pointer when failure is part of the
  contract.
- Use smart pointers only when ownership or lifetime is actually transferred or
  shared. Do not use a raw pointer to imply ownership.

```cpp
Pose ComputePose(const Eigen::VectorXd& q);

UpdateStatus Controller::Update(
    const RobotState& state,
    const TaskReference& reference,
    RobotCommand* command);
```

An output pointer that is required by the contract must be non-null. Validate
that contract outside a high-frequency path, or enforce it with the project's
assertion or contract mechanism; do not add a redundant null check every cycle.

Do not alias inputs and outputs unless the API is explicitly documented as an
in-place operation. Do not reuse state or reference storage as command
workspace. Views, spans, maps, and references must not outlive the storage they
refer to.

Avoid hidden ownership and hidden inputs:

- no mutable global or thread-local control state;
- no helper that reads an unrelated singleton or implicit current robot;
- no silent replacement of caller-owned buffers;
- no cached reference, pointer, or view without an explicit lifetime contract;
- no semantic state mutation disguised as workspace reuse.

Reusable scratch buffers may be members for allocation control, but they must
not change the controller's mathematical behavior or become undocumented inputs
to the next update.

## Make Mutation and Side Effects Visible

Avoid helpers that silently change unrelated member state.

```cpp
// Avoid: inputs and modified state are unclear.
UpdateKinematics();

// Prefer: the data flow is visible.
kinematics_.Update(state.q, state.qdot);
const Eigen::MatrixXd& jacobian = kinematics_.TaskJacobian();
```

Use names such as `Update`, `Apply`, `Publish`, `Send`, `Encode`, and `Decode`
consistently with their side effects. Prefer explicit outputs when a helper
fills reusable storage.

```cpp
ComputeTaskJacobian(state.q, &jacobian_workspace_);
```
