# Control Data Conventions

Loading this reference does not authorize tests, validation, or review.

Use this standard for units, coordinate frames, state layout, ordering, signs,
time, and hardware-to-model conversion in robot control, estimation, planning,
simulation, and hardware-interface code.

Select naming, function, loop, or numerical references separately only when the
requested work actually touches those concerns.

## Section Map

- [Core Contract](#core-contract)
- [Canonical Units](#canonical-units)
- [Convert Once at Boundaries](#convert-once-at-boundaries)
- [Generalized, Joint-Side, and Motor-Side Quantities](#generalized-joint-side-and-motor-side-quantities)
- [Gear Ratio and Actuator Conversion](#gear-ratio-and-actuator-conversion)
- [Coordinate Frames and Transform Notation](#coordinate-frames-and-transform-notation)
- [Spatial Vector and Jacobian Ordering](#spatial-vector-and-jacobian-ordering)
- [Quaternion and Rotation Conventions](#quaternion-and-rotation-conventions)
- [Joint and Actuator Ordering](#joint-and-actuator-ordering)
- [Signs, Contact, and Limits](#signs-contact-and-limits)
- [Time and Timestamps](#time-and-timestamps)
- [Configuration and Interface Contracts](#configuration-and-interface-contracts)

## Core Contract

Every numerical value that crosses a module boundary must have one recoverable
physical meaning. Its unit, frame, ordering, sign, side of the transmission, and
time basis must be defined by the type, interface contract, schema, or adjacent
documentation.

Use one canonical internal representation. Convert external representations
once at an adapter boundary instead of scattering conversions through control
logic.

> Convert at boundaries. Compute in canonical representations. Never infer a
> convention from vector length or historical behavior.

## Canonical Units

Use SI units in model, controller, estimator, solver, planner, and internal state
interfaces.

| Quantity | Canonical unit |
| --- | --- |
| length and position | meter (`m`) |
| angle | radian (`rad`) |
| linear velocity | `m/s` |
| angular velocity | `rad/s` |
| linear acceleration | `m/s^2` |
| angular acceleration | `rad/s^2` |
| force | newton (`N`) |
| torque and moment | newton meter (`N m`) |
| mass | kilogram (`kg`) |
| rotational inertia | `kg m^2` |
| time and duration | second (`s`) |
| frequency | hertz (`Hz`) |
| translational stiffness | `N/m` |
| rotational stiffness | `N m/rad` |
| translational damping | `N s/m` |
| rotational damping | `N m s/rad` |
| motor torque constant | `N m/A` on the motor side |

Radians are dimensionless in SI but are never semantically interchangeable
with degrees. Do not rely on a bare scalar when a non-SI unit is possible.

Canonical internal names normally do not need a unit suffix. A boundary field,
configuration key, or protocol value that intentionally uses a non-canonical
unit must encode it explicitly.

```cpp
// Boundary values with non-canonical units.
double timeout_ms;
double position_deg;
std::int32_t encoder_count;

// Canonical internal values.
double timeout;
double position;
RobotState state;
```

Do not use comments to excuse mixed units inside one vector or matrix. Use a
typed structure or document each block as part of the interface contract.

## Convert Once at Boundaries

Convert degrees, millimeters, encoder counts, current commands, PWM values,
device ticks, and protocol-specific scales in the adapter that owns the
external interface.

```cpp
bool MotorStateAdapter::Decode(
    const MotorFrame& frame,
    JointState* state)
{
  const double motor_position = DecodeEncoderRadians(frame.encoder_count);
  state->position = MotorToJointPosition(motor_position);
  state->velocity = MotorToJointVelocity(DecodeMotorVelocity(frame));
  state->torque = MotorToJointTorque(DecodeMotorTorque(frame));
  return state->AllFinite();
}
```

The controller receives validated joint-side SI values. It must not know the
CAN scale, encoder resolution, byte order, motor direction bit, or vendor unit.

For each conversion:

- give the scale and offset one owner;
- make direction and transmission side explicit;
- reject invalid or non-finite input before publishing trusted state;
- define zero, sign, scale, saturation, and encode/decode round-trip behavior;
- avoid applying the same conversion in both an adapter and a controller.

Use `_raw`, `_count`, `_tick`, or an explicit unit suffix only for values that
remain in an external representation. Do not call a raw device value `q`,
`qdot`, or `tau`.

## Generalized, Joint-Side, and Motor-Side Quantities

Use these meanings unless a more specific container contract overrides them:

- `q`: generalized configuration, dimension `nq`;
- `qdot`: generalized tangent velocity, dimension `nv`;
- `qddot`: generalized tangent acceleration, dimension `nv`;
- `tau`: generalized or actuated joint effort on the model side declared by the
  container, commonly dimension `nv` or `na`;
- `na`: number of actuated degrees of freedom.

For a fixed-base fully actuated robot, these dimensions may coincide. Do not
write code that assumes they coincide when floating bases, quaternion joints,
mimic joints, passive joints, or underactuation are possible.

For a floating base, `qdot` is the tangent velocity associated with `q`; it is
not an element-wise derivative vector with the same layout as `q`. Use the
model library's manifold `Integrate` and `Difference` operations instead of
adding or subtracting generalized configurations directly.

The public API uses `qdot`. If Pinocchio or another library uses `v`, keep `v`
inside the narrow library adapter or call scope.

```cpp
const Eigen::VectorXd& v = state.qdot;
pinocchio::forwardKinematics(model, data, state.q, v);
```

When both sides of a transmission coexist, use explicit names:

```cpp
motor_position;
joint_position;
motor_velocity;
joint_velocity;
motor_torque;
joint_torque;
```

Never reuse one variable for motor-side and joint-side values, even if the gear
ratio is currently one.

## Gear Ratio and Actuator Conversion

Define the positive gear-ratio magnitude as:

```text
gear_ratio = motor_speed / joint_speed
```

For an ideal transmission with ratio `r > 0` and direction sign `s` in
`{-1, +1}`:

```text
q_joint    = q_joint_zero + s q_motor / r
qdot_joint = s qdot_motor / r
tau_joint  = s r tau_motor
```

Keep the direction sign separate from the positive ratio. Do not hide a sign in
some ratios and in an encoder offset for other actuators.

Efficiency, friction, elasticity, backlash, and torque-sensor location require
separate models. In particular, do not invert a single efficiency factor for
both motoring and backdriving without a validated transmission model.

A motor torque constant is motor-side unless its name and interface explicitly
say otherwise.

```text
tau_motor = motor_torque_constant * current
tau_joint = direction_sign * gear_ratio * tau_motor       # ideal
```

If calibration produces a lumped output-side constant, name it
`joint_torque_per_amp`; do not store it as `motor_torque_constant`.

Document where an encoder and torque sensor are located. An output encoder,
motor encoder, phase-current estimate, and joint torque sensor do not measure
the same quantity.

## Coordinate Frames and Transform Notation

Use named frames at API boundaries and in non-trivial calculations. Recommended
symbols are:

- `W`: world or inertial frame;
- `B`: robot base or body frame;
- `A`, `C`, or descriptive names: other frames.

Use the convention that `R_AB` rotates coordinates from frame `B` into frame
`A`:

```text
p_A = R_AB p_B
```

`p_AB` is the position of the origin of `B`, expressed in `A`. `T_AB` transforms
a point expressed in `B` into `A`:

```text
p_A = R_AB p_B + p_AB
```

For example, `T_WB` is the pose of body frame `B` in world frame `W` and maps
body-frame coordinates into world-frame coordinates.

When a bare name such as `pose`, `velocity`, `jacobian`, or `wrench` could refer
to multiple frames, encode the frame in the type or name and state the
convention at the interface.

```cpp
const Eigen::Vector3d position_error_W =
    reference.position_W - state.position_W;

const Vector6d twist_WB_W = state.base_twist;
```

Before subtraction, dot products, feedback, or matrix multiplication, express
all operands in compatible frames and about compatible reference points. A
correct vector dimension does not prove frame compatibility.

Angular velocity is not Euler-angle rate. Convert explicitly when an interface
requires Euler rates, and document the rotation sequence and singularity.

## Spatial Vector and Jacobian Ordering

Use this project-facing spatial-vector ordering:

```text
twist  = [linear_velocity; angular_velocity]
wrench = [force; moment]
```

A spatial vector must also declare:

- the moving or loaded body;
- the reference body when relevant;
- the expression frame;
- the point about which linear velocity or moment is defined.

Define a Jacobian by the velocity it produces:

```text
twist_A = J_A(q) qdot
```

The row ordering and expression frame of `J_A` must match the twist, error, and
wrench used with it. Consequently:

```text
tau = J_A(q)^T wrench_A
```

is valid only when `wrench_A` uses the dual ordering, frame, and reference point
associated with `J_A`.

External libraries may use a different spatial ordering. Convert once at the
library boundary; never reinterpret the same six coefficients silently.

## Quaternion and Rotation Conventions

Use rotation matrices or quaternion types for orientation math. Avoid raw
four-element vectors except at serialization and model-library boundaries.

When a serialized or generalized-coordinate quaternion requires a declared
order, use:

```text
[x, y, z, w]
```

Do not rely on constructor argument order or memory layout. For example,
`Eigen::Quaterniond(w, x, y, z)` takes constructor arguments in `wxyz` order,
while `quaternion.coeffs()` exposes `xyzw` order. Assign named components or use
an explicit conversion helper.

Normalize quaternions at untrusted-input boundaries and after numerical
integration when required. Reject a near-zero or non-finite quaternion instead
of normalizing it.

Because `q` and `-q` represent the same orientation, enforce sign continuity
before filtering, interpolation, or finite differencing:

```cpp
if (previous.coeffs().dot(current.coeffs()) < 0.0) {
  current.coeffs() *= -1.0;
}
```

State the convention for orientation error next to the control law. Two valid
examples are:

```text
e_R_W = Log(R_WB_des R_WB^T)       # expressed in W
e_R_B = Log(R_WB^T R_WB_des)       # expressed in current B
```

Do not mix either error with an angular-velocity error expressed in another
frame.

## Joint and Actuator Ordering

Choose one canonical model-side joint and actuator order. Store explicit maps
between model, hardware, message, and solver orderings.

During initialization:

- verify that required names exist exactly once;
- reject duplicate, missing, or unexpected entries according to the interface
  contract;
- build index maps in both required directions;
- verify state, command, gain, and limit shapes against the owning order;
- support a non-trivial permutation rather than specializing the identity map.

Do not assume that URDF order, Pinocchio order, ROS message order, CAN ID order,
actuator ID order, and configuration-file order are identical. Do not sort names
to make mismatched interfaces appear compatible.

Each vector-valued container must own and document its ordering. A copied vector
does not carry a new ordering merely because its variable name changed.

## Signs, Contact, and Limits

Positive joint position, velocity, and torque follow the modeled positive joint
axis. Hardware direction differences are corrected in the adapter.

Positive joint torque tends to increase the corresponding modeled joint
coordinate. Gravity is a vector with physical direction, for example
`gravity_W = [0, 0, -9.81] m/s^2`; do not use an unsigned magnitude where a
vector is required.

For contact quantities, encode the affected body and direction when ambiguity
exists:

```cpp
normal_A_to_B;
force_on_A_W;
force_on_B_W;
```

`normal_A_to_B` points from `A` toward `B`. `force_on_A_W` is the force applied
to `A`, expressed in `W`; the corresponding force on `B` has the opposite sign.
Do not use a bare `contact_force` across an interface unless that interface
defines the body, normal direction, frame, and sign.

Use signed distance with:

```text
positive: separated
zero: touching
negative: penetration
```

If a solver or collision library differs, convert at its adapter. Define the
tangential basis and handedness when individual friction components are used.

State whether limits are inclusive and whether they apply to measured,
estimated, desired, solved, or commanded values. Do not use one limit object for
motor-side and joint-side quantities.

## Time and Timestamps

Use a monotonic clock for control periods, deadlines, state age, timeouts, and
watchdogs. Use wall or system time only for human-readable timestamps and
cross-system synchronization that explicitly requires it.

All timestamps compared or subtracted must share a clock domain. Do not compute
state age by subtracting a device tick or wall-clock timestamp from a monotonic
host timestamp.

Use seconds for canonical numeric durations. Prefer `std::chrono` duration and
time-point types where they prevent clock or unit confusion. When a protocol or
configuration uses milliseconds or microseconds, include the unit in the field
name or schema and convert at the boundary.

Use measured timestamps for variable-period estimation. Use a configured fixed
`dt` only when the control design and scheduler contract intentionally define a
fixed-step update. Validate unreasonable or non-positive measured time steps
before using them in division, differentiation, or integration.

## Configuration and Interface Contracts

For every public message, state container, command container, configuration
schema, and solver interface, document:

- dimensions and ordering;
- units;
- coordinate frames and reference points;
- sign and contact convention;
- motor side, joint side, or generalized-model side;
- quaternion and spatial-vector ordering;
- timestamp clock and validity rules;
- valid range and failure behavior.

Validate fixed contracts during initialization and external data at the adapter
boundary. Reject ambiguous configuration instead of selecting a convention from
the numerical value.

Use named conversion constants and give them dimensions in comments or types.
Reject non-finite scales, non-positive gear ratios, invalid limit intervals,
duplicate names, and unsupported convention identifiers before entering the
control loop.
