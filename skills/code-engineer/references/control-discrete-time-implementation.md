# Control Discrete-Time Implementation

Loading this reference does not authorize tests, validation, or review.

Use this standard for control calculations that depend on elapsed time or retain
state between cycles, including integrators, numerical derivatives, filters,
rate limiters, trajectories, timeouts, mode transitions, and solver warm starts.

Select loop, numerical, or concurrency references separately only when the
requested work actually touches those concerns.

## Contents

- [Core Principle](#core-principle)
- [Choose the Time Model Explicitly](#choose-the-time-model-explicitly)
- [Use a Monotonic Clock](#use-a-monotonic-clock)
- [Validate Timing Without Hiding It](#validate-timing-without-hiding-it)
- [Own Discrete State Explicitly](#own-discrete-state-explicitly)
- [Implement Integrators Deliberately](#implement-integrators-deliberately)
- [Prefer Measured Velocity to Numerical Differentiation](#prefer-measured-velocity-to-numerical-differentiation)
- [Discretize Filters for the Actual Update Contract](#discretize-filters-for-the-actual-update-contract)
- [Define Command Stages and Rate-Limit History](#define-command-stages-and-rate-limit-history)
- [Order Limits Explicitly](#order-limits-explicitly)
- [Make Mode Transitions Bumpless](#make-mode-transitions-bumpless)
- [Treat Warm Starts as Controller State](#treat-warm-starts-as-controller-state)
- [Define Multi-Rate Behavior](#define-multi-rate-behavior)
- [Handle Delayed and Missing Samples](#handle-delayed-and-missing-samples)
- [Keep the Update Bounded](#keep-the-update-bounded)

## Core Principle

Every calculation with memory must state what advances it, what history it
stores, and what resets that history.

Do not let `dt`, a previous value, filter state, or warm start become hidden
ambient state. Their meanings affect the control law and must be visible in the
class contract, initialization, and transition logic.

## Choose the Time Model Explicitly

State whether an algorithm uses a nominal fixed period or measured elapsed time.
They are different models.

Use a fixed nominal period when:

- the controller is designed and tuned as a fixed-rate discrete system;
- the scheduler contract provides that period within the accepted jitter;
- overruns are monitored separately and handled as timing faults.

```cpp
const double dt = config_.nominal_period_s;
```

Use measured elapsed time when:

- the update rate is intentionally variable;
- the algorithm derives coefficients or increments from actual elapsed time;
- accepted minimum and maximum intervals are defined.

```cpp
const double dt = ToSeconds(now - previous_update_time_);
```

Do not silently substitute nominal `dt` after a measured interval becomes
invalid. Do not clamp measured `dt` and then describe the result as integration
over actual elapsed time. If a bounded substitution is part of the algorithm,
name it and document the changed semantics.

Monitor actual cycle timing even when the control law uses nominal `dt`. The
control period and the scheduling measurement serve different purposes.

## Use a Monotonic Clock

Use a monotonic or steady clock for:

- elapsed time;
- controller integration;
- local watchdog age;
- timeouts;
- deadline and overrun measurement.

Wall time and ROS time may jump because of synchronization, simulation reset,
bag replay, or clock configuration. Preserve source and ROS timestamps for
alignment and provenance, but do not use a jumpable clock as an elapsed-time
source unless the component explicitly supports those jumps.

Sample the cycle clock once near the cycle boundary. Reuse that value for all
age and elapsed-time decisions in the update.

```cpp
const SteadyTimePoint cycle_time = steady_clock_.Now();
const double dt = ToSeconds(cycle_time - previous_cycle_time_);
```

Do not call the clock independently in several helpers and create slightly
different versions of the current cycle.

## Validate Timing Without Hiding It

Define an accepted timing interval from control and safety requirements.

```cpp
if (!std::isfinite(dt)
    || dt < config_.minimum_period_s
    || dt > config_.maximum_period_s) {
  SetSafeCommand(command);
  ResetDiscreteState();
  return UpdateStatus::kInvalidPeriod;
}
```

The response may instead hold the previous sent command, skip one state update,
or enter a degraded mode, but it must be explicit and safe for the plant.

Distinguish:

- scheduler jitter inside the accepted interval;
- a missed deadline;
- a large pause requiring state reset;
- a clock discontinuity;
- the first update, which has no previous interval.

Do not feed a one-second pause into an integrator designed for a 1 ms loop.
Do not divide by a nearly zero interval to produce a numerical derivative.

## Own Discrete State Explicitly

Keep control history in a named state object or clearly grouped members owned by
the control thread.

```cpp
struct ControllerHistory {
  Eigen::VectorXd integral_error;
  Eigen::VectorXd filtered_velocity;
  Eigen::VectorXd previous_rate_limited_torque;
  SteadyTimePoint previous_cycle_time;
  bool initialized;
};
```

Initialize storage during controller initialization. Set its runtime values in
`Reset()` or a named mode-entry action.

Define exactly what reset clears:

- integrator state;
- filter state;
- derivative previous sample;
- previous controller-produced command stage used by the algorithm;
- previous hardware-applied outcome only when an explicit feedback or result
  channel provides it;
- trajectory phase;
- contact hysteresis;
- solver warm start;
- previous timestamp.

Do not use one broad `initialized_` flag to hide several unrelated histories
with different validity conditions.

External callbacks may request a reset. The control thread applies the reset at
a cycle boundary. See `control-concurrency.md`.

## Implement Integrators Deliberately

State the integration method. Forward Euler is acceptable when its error and
stability are appropriate; do not use it merely because it is the shortest
formula.

```cpp
integral_error_.array() += dt * position_error.array();
```

For every integrator, define:

- units of the integrated state;
- initial value;
- enable condition;
- reset conditions;
- saturation bounds;
- anti-windup behavior;
- behavior while the actuator or downstream command is saturated;
- behavior during invalid input and timing faults.

Prefer conditional integration or back-calculation with a named gain over
unbounded accumulation.

```cpp
if (!torque_saturated || ErrorDrivesOutOfSaturation(error, torque_error)) {
  integral_error_.array() += dt * error.array();
}
ApplyIntegralLimits(&integral_error_);
```

Do not rely only on clamping the integrator after a long invalid interval.
Prevent invalid history from accumulating in the first place.

If the integral term is disabled by configuration, define whether its state is
held, decayed, or reset. Do not leave it ambiguous across re-enable.

## Prefer Measured Velocity to Numerical Differentiation

Use a trustworthy measured or estimated velocity when available. Numerical
differentiation amplifies noise and makes timing error part of the signal.

When differentiation is required, define:

- the sampled quantity and its frame or unit;
- the actual interval used;
- minimum accepted interval;
- angle or manifold difference convention;
- filter placement and coefficients;
- initialization and reset behavior.

```cpp
const Eigen::VectorXd delta_q = model_.Difference(previous_q_, state.q);
qdot_est_ = delta_q / dt;
```

Confirm the sign and argument order of manifold difference functions. Do not
subtract quaternion coefficient vectors.

On the first valid sample, initialize history and report velocity unavailable or
use an explicitly defined initial estimate. Do not differentiate against zeroed
memory.

## Discretize Filters for the Actual Update Contract

Document filter type, cutoff or time constant, discrete equation, assumed
sample period, and stored state.

For a first-order low-pass filter with measured `dt`:

```cpp
const double alpha = dt / (time_constant_s + dt);
filtered_value_.array() += alpha * (input - filtered_value_).array();
```

This example is not a universal filter prescription. Choose the discretization
that matches the design and validate its frequency and transient behavior.

Do not reuse coefficients designed for one sample rate after changing the
update rate. For fixed-rate filters, compute coefficients during initialization.
For variable-rate filters, update coefficients with bounded, allocation-free
work and reject unsupported intervals.

Define filter initialization. Common choices are:

- initialize to the first valid input to avoid startup transients;
- initialize to a known safe state;
- restore a validated persistent state.

Choose one deliberately. Reset filter history on discontinuous mode, frame,
unit, signal-source, or sampling-contract changes.

## Define Command Stages and Rate-Limit History

Distinguish the command requested by the controller, the command after limits,
and the command actually sent or accepted by the hardware interface.

```cpp
Eigen::VectorXd tau_requested;
Eigen::VectorXd tau_limited;
Eigen::VectorXd tau_sent;
```

Semantic containers may own these stages without repeating suffixes in every
field. The distinction must still be visible in the data model.

A rate limiter must state which previous stage it uses. In most actuator-facing
paths, limit against the previous sent or previously accepted command because
that represents the plant input history.

```cpp
LimitTorqueRate(
    tau_requested,
    previous_tau_sent_,
    maximum_torque_rate,
    dt,
    &tau_limited);
```

Do not call a value `previous_command` if it might mean previous requested,
limited, published, transmitted, or hardware-accepted command.

Update `previous_tau_sent_` only after the send boundary reports the stage
defined by the contract. If transport acceptance is asynchronous, name the
local publication stage separately from confirmed hardware application.

## Order Limits Explicitly

Command constraints do not generally commute. Define and preserve the order in
which they apply.

A typical pipeline may be:

1. compute the requested command;
2. apply mode-specific constraints;
3. apply velocity or acceleration constraints;
4. apply rate or jerk limits relative to the selected command-history stage;
5. apply absolute actuator limits;
6. validate finite values;
7. publish the complete command.

This is not a universal order. The correct order depends on the command type,
plant, and safety boundary. Keep the chosen order visible in the control-loop
function and explain non-obvious interactions.

After applying coupled limits, verify all downstream invariants. A later clamp
can violate a ratio, direction, or equality established by an earlier step.

Do not silently make safety limits dependent on wall-clock timing or callback
arrival order.

## Make Mode Transitions Bumpless

Represent mutually exclusive modes with an enum or state machine, not an
accidental combination of booleans.

```cpp
enum class ControlMode {
  kDisabled,
  kPosition,
  kTorque,
  kFault,
};
```

Apply at most one accepted transition at a defined cycle boundary. Keep
transition guards in one visible location.

Separate:

- transition validation;
- mode-entry action;
- steady-state control calculation;
- mode-exit or fault action when needed.

Mode entry must define relevant history. Depending on the controller, this may
mean:

- initialize a reference from measured state;
- initialize a filter from its current input;
- set previous sent command from the actual last output;
- clear or preload an integrator for bumpless transfer;
- invalidate a warm start;
- reset timing origin.

Do not enter a new mode with history computed under incompatible gains, units,
frames, constraints, or command semantics.

Each mode must define its output when state is unavailable or a calculation
fails. Invalid transitions must return a status or fault; do not silently ignore
them.

## Treat Warm Starts as Controller State

A solver warm start is valid only for a compatible problem.

Define invalidation conditions, including:

- first solve or reset;
- dimension or constraint-structure change;
- mode change;
- contact-set change when it changes the optimization structure;
- large elapsed-time gap;
- previous solver failure or rejected solution;
- configuration change that invalidates the solution meaning.

Initialize warm-start storage during setup and mark validity separately. Never
pass uninitialized or rejected solver output as a warm start.

Bound solver iterations and retries independently of warm-start quality.

## Define Multi-Rate Behavior

When estimation, planning, control, hardware I/O, or publication run at
different rates, state the sample-and-hold behavior between updates.

Define:

- producer and consumer rates;
- whether the consumer uses latest-value or ordered-event semantics;
- zero-order hold, interpolation, or extrapolation policy;
- maximum usable age;
- phase or timestamp alignment;
- behavior when an expected update is missed.

Prefer elapsed-time or sequence-based scheduling over a fragile assumption that
one callback occurs exactly every N control cycles. A cycle counter is
acceptable when the fixed-rate scheduler contract makes the relationship exact
and reset behavior is defined.

Do not replay a backlog of continuous references merely to preserve every
producer sample.

## Handle Delayed and Missing Samples

Keep source time, receive time, and control-cycle time distinct when delay
matters.

For a reused sample, advance controller time only where the algorithm truly
continues. Do not fabricate a new source timestamp.

Define whether a missing sample causes:

- reuse of the previous valid value within a freshness window;
- hold of discrete state;
- prediction or extrapolation with a bounded horizon;
- fallback command;
- mode transition or latched fault.

The choice depends on the signal. Reusing a continuous reference briefly may be
acceptable; reusing an old safety interlock state may not be.

Do not integrate the same measurement repeatedly as though it were new without
making the zero-order-hold model explicit.

## Keep the Update Bounded

Preallocate history, coefficient, and workspace storage. Do not resize a filter,
trajectory, limiter, or warm-start vector in the update loop.

Bound:

- catch-up steps after a delay;
- solver iterations and retries;
- event processing per cycle;
- interpolation search;
- history length.

Do not implement an unbounded loop that repeatedly advances a discrete model
until it catches up with wall time. If catch-up is allowed, cap the steps and
define what happens to the remaining gap.

Keep diagnostics allocation-free on the high-frequency path. Record numeric
counters and statuses; format them outside the control thread.
