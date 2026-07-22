# Control Variable Naming

Loading this reference does not authorize tests or review. Use Review Rules only
in an explicitly requested Review mode.

Use this standard for variables, fields, parameters, and intermediate values in
robot control, estimation, planning, optimization, simulation, and hardware
interface code.

For units, frames, ordering, signs, transmission side, and time conventions,
select `control-data-conventions.md` separately when that trigger applies.

## Contents

- [Core Principle](#core-principle)
- [Standard Quantities](#standard-quantities)
- [Pipeline Suffixes](#pipeline-suffixes)
- [Context-Owned Semantics](#context-owned-semantics)
- [Compound Names](#compound-names)
- [Naming Length and Context](#naming-length-and-context)
- [Review Rules](#review-rules)

## Core Principle

Name a value by its physical quantity and, when needed, its stage in the control
pipeline. Do not encode information that is already clear from the type,
container, function signature, or surrounding class.

Prefer concise names that remain unambiguous in their local scope.

## Standard Quantities

Use established mathematical and robotics notation when it is already familiar
to the project.

| Name | Meaning |
| --- | --- |
| `q` | generalized configuration, normally dimension `nq` |
| `qdot` | generalized tangent velocity, normally dimension `nv` |
| `qddot` | generalized tangent acceleration, normally dimension `nv` |
| `tau` | generalized or actuated joint effort as defined by its container |
| `x` | task-space position or state when locally unambiguous |
| `wrench` | spatial force and moment |
| `force` | linear force |
| `moment` | moment component of a wrench |
| `pose` | rigid pose with an explicitly defined frame convention |
| `twist` | spatial velocity with defined ordering and frame |
| `jacobian` | Jacobian matrix |
| `mass_matrix` | inertia or mass matrix |

Use the repository's established notation consistently. In public APIs, prefer
`qdot` over a generic `v` unless an external library requires `v` internally.
For a floating base, do not assume `qdot` has the same dimension or storage
layout as `q`.

Use `x` only in a short mathematical scope where its meaning is obvious. At
module boundaries, prefer the physical quantity such as `position`, `pose`,
`twist`, or `task_state`.

When generalized, actuated-joint, and motor quantities coexist, add the
semantic qualifier rather than relying on dimension:

```cpp
q;
q_actuated;
motor_position;
joint_position;
motor_torque;
joint_torque;
```

## Pipeline Suffixes

Use a stage suffix when standalone values from different parts of the control
pipeline coexist or when the source of a value would otherwise be ambiguous.

| Suffix | Meaning | Examples |
| --- | --- | --- |
| `_meas` | directly measured by hardware or a sensor | `q_meas`, `tau_meas` |
| `_est` | estimated, filtered, or reconstructed | `qdot_est`, `wrench_est` |
| `_des` | desired target or reference | `q_des`, `force_des` |
| `_sol` | raw solver result | `qddot_sol`, `tau_sol` |
| `_cmd` | processed downstream value | `q_cmd`, `tau_cmd` |

Use `_raw`, an explicit device quantity such as `_count`, or a non-SI unit
suffix only at an interface boundary. A raw encoder or protocol value is not a
measured model-side quantity until it has been decoded and converted.

Do not use `_meas` for a filtered or model-corrected value. Use `_est` after
estimation, filtering, sensor fusion, or reconstruction.

Do not use `_sol` for a generic result. State the solved physical quantity.

```cpp
// Avoid
const auto solution = solver.Solve(problem);

// Prefer
const Eigen::VectorXd qddot_sol = solver.Solve(problem);
```

## Context-Owned Semantics

Let a semantic container own the pipeline stage. Do not repeat the container's
meaning in every field.

```cpp
struct RobotState {
  Eigen::VectorXd q;
  Eigen::VectorXd qdot;
  Eigen::VectorXd tau;
};

struct RobotCommand {
  Eigen::VectorXd q;
  Eigen::VectorXd qdot;
  Eigen::VectorXd tau_ff;
  Eigen::VectorXd kp;
  Eigen::VectorXd kd;
};

struct SolverSolution {
  Eigen::VectorXd qddot;
  Eigen::VectorXd tau;
  Eigen::VectorXd contact_force;
};
```

Prefer:

```cpp
state.q;
command.q;
solution.qddot;
```

Avoid redundant field names:

```cpp
state.q_meas;
command.q_cmd;
solution.qddot_sol;
```

Use stage suffixes again after extracting several values into a flat scope.

```cpp
const Eigen::VectorXd q_meas = hardware.ReadPosition();
const Eigen::VectorXd q_des = trajectory.EvaluatePosition(time);
const Eigen::VectorXd q_cmd = LimitPositionCommand(q_des, q_meas);
```

## Compound Names

Use this order:

```text
<quantity>_<component-or-role>_<frame-or-side>_<stage>
```

Omit fields that add no information. When present, the pipeline stage remains
last.

Examples:

```cpp
tau_ff_cmd;
tau_fb_cmd;
wrench_contact_des;
force_normal_meas;
force_normal_W_meas;
```

Add a frame qualifier when otherwise-compatible quantities from different
frames coexist or cross an interface.

```cpp
position_error_W;
twist_WB_W;
wrench_W;
jacobian_W;
```

Frame notation and spatial-vector ordering are defined in
`control-data-conventions.md`. Do not add a frame suffix without knowing what it
means.

Treat `_meas`, `_est`, `_des`, `_sol`, and `_cmd` as mutually exclusive stages.
Do not combine stages in one name.

```cpp
// Avoid
q_des_cmd;
tau_sol_cmd;

// Prefer
q_des;
q_cmd;
tau_sol;
tau_cmd;
```

Represent the transition with separate variables when both stages matter.

```cpp
const Eigen::VectorXd tau_sol = solver.Solve(problem);
Eigen::VectorXd tau_cmd = tau_sol;
ApplyTorqueLimits(&tau_cmd);
```

## Naming Length and Context

Express the primary semantic operation or quantity. Let parameters, return
types, classes, and namespaces carry secondary information.

```cpp
// Avoid
ComputeEndEffectorPoseFromJointPositions(q);
UpdateForwardKinematicsCacheFromGeneralizedCoordinates(q);
ApplyConfiguredJointTorqueAndVelocitySafetyLimits(&command);

// Prefer
ComputeEndEffectorPose(q);
UpdateKinematicsCache(q);
ApplyCommandLimits(&command);
```

Do not impose a rigid character limit. Prefer a short name when it communicates
the same meaning. Add qualifiers only when they distinguish real alternatives
in the same scope or API.

## Review Rules

Flag names that:

- repeat their class or container context;
- narrate the complete function signature;
- use a pipeline suffix with the wrong meaning;
- combine multiple pipeline stages;
- hide whether a value is generalized, actuated-joint, or motor side when more
  than one can exist;
- omit a required frame or attach a frame suffix without a defined convention;
- name raw or non-SI interface data like canonical model-side state;
- hide the physical quantity behind `data`, `result`, `output`, or `value`;
- introduce a new abbreviation where established notation already exists.

Do not recommend a longer name when the signature and surrounding context
already make the meaning clear.
