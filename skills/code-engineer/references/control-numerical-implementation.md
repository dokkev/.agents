# Control Numerical Implementation

Loading this reference does not authorize tests, validation, or review.

Use this standard for linear algebra, geometry, optimization, filtering,
integration, and other numerical work in robot control, estimation, planning,
simulation, and hardware-interface code.

Select the data, function, loop, or discrete-time references separately only
when their triggers apply.

## Section Map

- [Core Contract](#core-contract)
- [Solve Systems Without Explicit Inverses](#solve-systems-without-explicit-inverses)
- [Use Meaningful Tolerances](#use-meaningful-tolerances)
- [Validate Finite Values](#validate-finite-values)
- [Normalize Safely](#normalize-safely)
- [Implement Rotation and Manifold Math Explicitly](#implement-rotation-and-manifold-math-explicitly)
- [Handle Rank and Conditioning](#handle-rank-and-conditioning)
- [Use Regularization Deliberately](#use-regularization-deliberately)
- [Preserve Matrix Structure](#preserve-matrix-structure)
- [Use Eigen Deliberately](#use-eigen-deliberately)
- [Check Solver Results](#check-solver-results)
- [Keep Repeated Numerics Deterministic and Bounded](#keep-repeated-numerics-deterministic-and-bounded)

## Core Contract

Make numerical assumptions visible and testable. Choose an algorithm that
matches the mathematical structure, validate the result that the controller
will consume, and define failure behavior before runtime.

Do not turn a numerical failure into a plausible-looking command through silent
clamping, normalization, regularization, or fallback to stale data.

## Solve Systems Without Explicit Inverses

Do not form a matrix inverse only to multiply it by a vector or matrix.

```cpp
// Avoid
const Eigen::VectorXd x = matrix.inverse() * rhs;

// Prefer when matrix is symmetric positive definite.
const Eigen::LLT<Eigen::MatrixXd> factorization(matrix);
if (factorization.info() != Eigen::Success) {
  return SolveStatus::kFactorizationFailed;
}
const Eigen::VectorXd x = factorization.solve(rhs);
```

Choose a decomposition that matches the known structure:

| Problem structure | Typical Eigen approach |
| --- | --- |
| symmetric positive definite | `LLT` |
| suitable symmetric semidefinite system | `LDLT`, after checking its contract |
| general square system | pivoted `LU` |
| overdetermined least squares | pivoted `QR` |
| rank-deficient or diagnostic analysis | `SVD` or rank-revealing `QR` |

The table is guidance, not permission to assume structure. Validate or derive
the required property from the model and algorithm. Prefer a factorization
object that can expose status, rank, or reuse where appropriate.

An explicit inverse is acceptable only when the inverse itself is the required
output and its conditioning and validation are addressed.

## Use Meaningful Tolerances

Do not compare floating-point results with exact equality when roundoff is
expected.

```cpp
// Avoid
if (residual == 0.0) {
  ...
}

// Prefer
if (std::abs(residual) <= residual_tolerance) {
  ...
}
```

A tolerance must have a name, physical unit, and scope. Distinguish absolute
and relative tolerance when scale varies.

```cpp
const bool converged =
    residual_norm <= absolute_residual_tolerance
    + relative_residual_tolerance * reference_norm;
```

Do not use one global epsilon for joint position, force, quaternion norm,
solver feasibility, and matrix rank. Machine epsilon is not an application
tolerance.

When comparing vectors or matrices, state the norm and scaling rule. Use
`isApprox()` only when its relative comparison semantics match the contract.

## Validate Finite Values

Reject NaN and infinity at untrusted-input boundaries and before a command
crosses into a downstream or hardware interface. Also check intermediate values
whose failure can be introduced by a solver, division, factorization,
normalization, or integration step.

```cpp
if (!state.q.allFinite() || !state.qdot.allFinite()) {
  SetSafeCommand(command);
  return UpdateStatus::kInvalidState;
}

if (!solution.tau.allFinite()) {
  SetSafeCommand(command);
  return UpdateStatus::kInvalidSolution;
}
```

Do not clamp, saturate, or cast a non-finite value and then continue. Determine
which boundary owns the fault and invoke the defined failure policy.

Avoid redundant full-vector scans at several layers in one cycle. Validate
untrusted input once, validate numerically risky results where they are created,
and validate the final command at the safety boundary.

## Normalize Safely

Check magnitude and finiteness before dividing by a norm.

```cpp
if (!axis.allFinite()) {
  return NormalizeStatus::kInvalidInput;
}

const double axis_norm = axis.norm();
if (!std::isfinite(axis_norm) || axis_norm <= minimum_axis_norm) {
  return NormalizeStatus::kDegenerateInput;
}

axis /= axis_norm;
```

The threshold must be appropriate to the quantity and scale. Do not add an
epsilon to every denominator because doing so changes the model and can hide a
singularity.

For quaternions:

- reject non-finite and near-zero input;
- normalize at the defined boundary or integration step;
- maintain quaternion sign continuity before filtering or interpolation;
- do not compare quaternion coefficients directly to determine orientation
  equality.

For normalized contact directions, axes, and gradients, define the degenerate
case explicitly: failure status, zero contribution, previous valid direction,
or another algorithm-specific fallback. Do not select one silently.

## Implement Rotation and Manifold Math Explicitly

Use `SO(3)` and `SE(3)` operations for rotations and poses. Do not subtract
rotation matrices, quaternion coefficient vectors, or pose storage vectors to
construct a control error.

State the orientation-error sign and expression frame adjacent to the code.

```cpp
// e_R_W = Log(R_WB_des R_WB^T), expressed in W.
const Eigen::Vector3d orientation_error_W =
    LogRotation(reference.rotation_WB * state.rotation_WB.transpose());
```

The angular-velocity error, gain, Jacobian, and wrench used with this error must
use the same frame convention.

For generalized configurations that include manifold joints:

```cpp
const Eigen::VectorXd q_error =
    model.Difference(state.q, reference.q);

const Eigen::VectorXd q_next =
    model.Integrate(state.q, dt * state.qdot);
```

Confirm the library's argument order and sign. Some APIs define
`Difference(q0, q1)` as the tangent displacement from `q0` to `q1`; do not infer
it from the function name.

Wrap scalar periodic-angle errors at the boundary chosen by the project.
Document the interval, including the behavior at `pi`.

```cpp
const double angle_error = std::remainder(angle_des - angle, kTwoPi);
```

Do not wrap a generalized configuration indiscriminately; continuous joints,
bounded joints, and quaternion joints require different treatment.

## Handle Rank and Conditioning

Numerical success from a library call does not guarantee that the result is
useful for control. When the algorithm can approach singularity or rank loss,
define:

- the expected rank;
- the rank or conditioning threshold;
- how scale affects that threshold;
- the allowed response: damping, task reduction, fallback, or failure.

Check decomposition and solver status. When practical, check a residual in the
same norm and units used by the algorithm's acceptance criterion.

```cpp
residual_workspace_.noalias() = matrix * solution;
residual_workspace_ -= rhs;
if (residual_workspace_.norm() > residual_tolerance) {
  return SolveStatus::kResidualTooLarge;
}
```

Do not compute a condition number with an expensive decomposition in every
control cycle unless the design requires it and the runtime budget includes it.
Use offline analysis, bounded diagnostics, or a cheaper algorithm-specific
indicator when appropriate.

## Use Regularization Deliberately

Regularization changes the solved problem. Give every regularization term a
name, unit, documented purpose, and configuration or derivation.

```cpp
// lambda has units that make H and lambda I dimensionally compatible.
hessian.diagonal().array() += hessian_regularization;
```

Avoid unexplained literals such as `1e-6` inside matrix assembly. Scale-aware
regularization is preferred when the problem magnitude varies, but its rule must
remain deterministic and bounded.

Do not use regularization to conceal a wrong frame, wrong unit, incorrect
Jacobian, missing constraint, or invalid model. Report when a fallback or
regularized mode is active if it changes controller behavior materially.

## Preserve Matrix Structure

Use and preserve known matrix structure such as symmetry, positive definiteness,
sparsity, and block layout.

- Fill the triangle expected by the selected factorization.
- Keep mass matrices and Hessians symmetric by construction when possible.
- Reuse fixed sparsity patterns in repeated optimization.
- Do not read uninitialized triangles or blocks.
- Initialize all entries that a downstream library may inspect.

Symmetrization may remove roundoff after a derivation that is known to be
symmetric:

```cpp
matrix = 0.5 * (matrix + matrix.transpose().eval());
```

Do not apply symmetrization automatically to hide an assembly error. If the
antisymmetric component exceeds a meaningful tolerance, treat it as a defect or
numerical fault.

## Use Eigen Deliberately

Use fixed-size Eigen types for small dimensions known at compile time, such as
3D vectors, quaternions, and 6D spatial vectors. Use dynamic types for
model-dependent dimensions.

In repeated paths, resize dynamic objects and initialize solver storage before
the loop. See `control-loop-implementation.md` for allocation rules.

Use `noalias()` only when the destination does not alias any operand and the
expression is an appropriate matrix product assignment. It is a correctness
promise as well as an optimization hint.

```cpp
// Valid only when command->tau does not alias jacobian or wrench.
command->tau.noalias() = jacobian.transpose() * wrench;
```

Use `.eval()` when an expression would otherwise overwrite data that is still
needed, as in an in-place transpose or symmetrization. Do not add `.eval()` or
`noalias()` mechanically.

Treat `Eigen::Map`, `Eigen::Ref`, blocks, and expression templates as
non-owning views. Their storage, stride, alignment, and lifetime must remain
valid for the entire use. Do not return a view into a temporary.

Avoid implicit scalar narrowing and silent row/column convention changes. Make
transposes and representation conversions visible.

## Check Solver Results

For every IK, QP, nonlinear optimization, factorization, or estimator solve:

1. check the library status;
2. verify iteration or timeout bounds;
3. rely on dimensions verified during initialization and treat any unexpected
   change as a contract violation;
4. verify finite outputs;
5. check feasibility, residual, or constraint violation when the library status
   alone is insufficient;
6. map the result into command space only after acceptance;
7. report rejection so the owning joint-command controller produces its
   defined complete fallback.

Do not use an unsuccessful solver's output merely because its buffer contains
numbers. A best-effort or partially feasible result is allowed only when the
solver contract, acceptance thresholds, and safety analysis explicitly permit
it.

Warm starts are state. Define when they are valid, reset after mode or structure
changes, and never use an uninitialized previous solution.

## Keep Repeated Numerics Deterministic and Bounded

In a control loop:

- bound iterations, retries, and line-search steps;
- preallocate factorization and solver workspaces when supported;
- avoid input-dependent allocation and algorithm selection;
- initialize every value before use;
- make the random seed explicit when reproducible sampling is required;
- separate expensive diagnostics from the critical path;
- record enough status to diagnose fallback activation without formatting logs
  in the loop.

Determinism does not require identical floating-point bits across all hardware
and libraries unless the project states that requirement. It does require a
bounded algorithm, initialized state, controlled randomness, and explicit
failure behavior.
