# Control Variable Naming

Use this standard for variables, fields, parameters, and intermediate values in
robot control, estimation, planning, optimization, simulation, and hardware
interface code.

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
| `q` | generalized position or joint position |
| `qdot` | generalized velocity or joint velocity |
| `qddot` | generalized acceleration or joint acceleration |
| `tau` | joint torque |
| `x` | task-space position or state when locally unambiguous |
| `wrench` | spatial force and moment |
| `force` | linear force |
| `jacobian` | Jacobian matrix |
| `mass_matrix` | inertia or mass matrix |

Use the repository's established notation consistently. In public APIs, prefer
`qdot` over a generic `v` unless an external library requires `v` internally.

## Pipeline Suffixes

Use a stage suffix when standalone values from different parts of the control
pipeline coexist or when the source of a value would otherwise be ambiguous.

| Suffix | Meaning | Examples |
| --- | --- | --- |
| `_meas` | directly measured by hardware or a sensor | `q_meas`, `tau_meas` |
| `_est` | estimated, filtered, or reconstructed | `qdot_est`, `wrench_est` |
| `_des` | desired target or reference | `q_des`, `force_des` |
| `_sol` | direct solver result before command post-processing | `qddot_sol`, `tau_sol` |
| `_cmd` | value sent to the downstream interface after required processing | `q_cmd`, `tau_cmd` |

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
  Eigen::VectorXd tau;
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
<quantity>_<component>_<stage>
```

Examples:

```cpp
tau_ff_cmd;
tau_fb_cmd;
contact_force_des;
normal_force_meas;
```

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
- hide the physical quantity behind `data`, `result`, `output`, or `value`;
- introduce a new abbreviation where established notation already exists.

Do not recommend a longer name when the signature and surrounding context
already make the meaning clear.