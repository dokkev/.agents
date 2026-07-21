# Control Function Implementation

Use this standard when implementing or reviewing controller, estimator,
planner, solver, simulation, dynamics, kinematics, and numerical functions.
For repeated high-frequency paths, apply this document together with
`control-loop-implementation.md`; its preallocation and runtime-safety rules
also apply.

## Contents

- [Core Principle](#core-principle)
- [Keep Core Logic Visible](#keep-core-logic-visible)
- [Helper Boundary](#helper-boundary)
- [Equation Comments](#equation-comments)
- [Reading Locality](#reading-locality)
- [Structure Longer Functions with Sections](#structure-longer-functions-with-sections)
- [Make Mutation and Side Effects Visible](#make-mutation-and-side-effects-visible)
- [Review Rules](#review-rules)

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

```cpp
bool Controller::Update(
    const RobotState& state,
    const TaskReference& reference,
    RobotCommand* command)
{
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
  return true;
}
```

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

// Prefer: the control law remains visible.
const Eigen::VectorXd tau =
    gains_.kp.cwiseProduct(reference.q - state.q)
    + gains_.kd.cwiseProduct(reference.qdot - state.qdot)
    + reference.tau_ff;
```

## Equation Comments

Place the corresponding equation immediately above non-trivial control,
dynamics, estimation, or optimization code.

```cpp
// e_x = x_des - x
const Vector6d pose_error = reference.pose - state.pose;

// F = Kp e_x + Kd e_xdot
const Vector6d wrench =
    gains_.kp.cwiseProduct(pose_error)
    + gains_.kd.cwiseProduct(velocity_error);

// tau = J^T F + g(q)
command->tau.noalias() = jacobian.transpose() * wrench + gravity;
```

Document relevant frame, unit, sign, convention, and approximation assumptions.

```cpp
// e_R = Log(R_des^T R), expressed in the local task frame.
const Eigen::Vector3d orientation_error =
    LogRotation(reference.rotation.transpose() * state.rotation);
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

## Review Rules

Flag code when:

- the control law or mathematical contribution is hidden behind a helper;
- understanding one path requires opening several small functions;
- helpers are thin wrappers with no meaningful contract;
- a line-count target caused excessive fragmentation;
- equations, frames, signs, or units are not recoverable from the code;
- important mutation or side effects are hidden;
- low-level protocol or conversion detail overwhelms the main algorithm.

Recommend the smallest change that restores a readable mathematical flow.