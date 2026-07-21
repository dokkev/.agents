# Robot Control Readability Guideline

Use this reference for C++, robotics, control, simulation, hardware interface, communication, numerical, and performance-sensitive code.

## Primary Goal

Implement the requested change with the smallest reasonable, reviewable diff.

Prioritize, in this order:

1. Correctness
2. Existing behavior preservation
3. Simplicity
4. Readability for beginners
5. Clear data flow
6. Memory discipline in repeated or high-frequency paths
7. Validation

The code should be easy to understand for someone reading the repository for the first time.

Prefer code where the reader can understand what happens before needing to inspect how every detail works.

## Before Editing

Before making non-trivial edits:

1. Read the closest `AGENTS.md`.
2. If present, read:
   - `docs/ARCHITECTURE.md`
   - `docs/COMMANDS.md`
   - `docs/DECISIONS.md`
   - `docs/PLANS.md`
3. Inspect the existing implementation before introducing new structure.
4. Identify the smallest set of files needed for the task.
5. Preserve existing behavior unless the task explicitly asks for behavior change.
6. If the task is ambiguous, make a minimal reasonable assumption and state it.

Do not start by inventing a new architecture.

## Implementation Principles

### Simple Is Best

Prefer boring, explicit, locally understandable code.

Avoid:

- Clever abstractions
- Premature generalization
- Framework-like designs
- Excessive templates
- Hidden state
- Deep inheritance
- Unnecessary callbacks
- Generic utilities with only one real use case
- Broad rewrites when a local change solves the task

Do not introduce a new abstraction just to make the code look cleaner.

A helper, class, or utility should exist because it clarifies intent, isolates real mechanical detail, avoids meaningful duplication, improves safety, or improves memory behavior.

### Optimize For The Next Beginner

Write code for the next person who has to debug it under time pressure.

Prefer:

- Descriptive names
- Clear data flow
- Clear ownership
- Clear units
- Clear side effects
- Clear preconditions
- Straight-line control flow when possible

Avoid abbreviations unless they are conventional in the local codebase or domain.

### Preserve Local Style

Follow the existing project style unless it is clearly broken or the task explicitly asks for cleanup.

Prefer consistency with nearby code over introducing a new style.

## C++ Style And Documentation

For C++ code, follow the spirit of Google C++ Style.

Documentation should explain what an interface does, how to use it, and what assumptions matter.

Document these when relevant:

- Inputs
- Outputs
- Ownership
- Nullability
- Units
- Side effects
- Threading or synchronization assumptions
- Timing assumptions
- Failure modes
- Safety assumptions
- Hardware assumptions

Prefer documenting:

- Public APIs
- Classes
- Structs
- Non-obvious helpers
- Important state transitions
- Functions with side effects
- Functions with output parameters
- Functions that rely on units, frames, conventions, or timing assumptions

Do not add comments that merely restate the code.

Bad:

```cpp
// Increment i.
++i;
```

Better:

```cpp
// Clamp before publishing so downstream hardware never receives values outside
// the configured command limits.
LimitCommand(command);
```

Keep comments synchronized with code when behavior changes.

## Control Code Readability

For robot control, estimation, planning, hardware interface, communication, or simulation code, the main behavior should be visible at first sight.

Top-level lifecycle functions such as:

- `Initialize()`
- `Reset()`
- `Read()`
- `Update()`
- `Compute()`
- `Write()`
- `Step()`

should primarily describe orchestration.

They should show the sequence of actions, not every low-level mechanism.

Good:

```cpp
bool Controller::Step()
{
  if (!UpdateMeasurements()) {
    return false;
  }

  RefreshStateSnapshot();
  ProcessModeTransitions();

  const ControlPlan plan = BuildControlPlan();
  if (!plan.ready) {
    HandlePreconditionFailure(plan);
    return true;
  }

  return ExecuteControlPlan(plan);
}
```

Top-level lifecycle functions should usually stay short. As a rule of thumb, 5 to 20 lines is a good target.

However, do not make functions short by creating many meaningless wrappers.

The goal is readable structure, not maximum function count.

## Keep The Mathematical Flow Visible

In controller code, the reader should be able to see the mathematical or algorithmic flow directly.

Helpers should hide mechanical detail, not mathematical intent.

The control code should show the math story:

1. Read or refresh state.
2. Build target, reference, or objective.
3. Compute error.
4. Compute control law.
5. Map to command space.
6. Apply limits.
7. Publish or apply command.

Good:

```cpp
RefreshStateSnapshot();

const TaskTarget target = BuildTaskTarget(state_);
const TaskError error = ComputeTaskError(target, state_);
const WrenchCommand wrench = ComputeImpedanceWrench(error, gains_);
JointCommand command = MapWrenchToJointCommand(jacobian_, wrench);

ApplyCommandLimits(command_limits_, &command);
PublishCommand(command);
```

Avoid hiding the main algorithm behind vague wrappers:

```cpp
Prepare();
Compute();
Finalize();
Send();
```

Also avoid deep helper chains:

```text
Step()
  -> ComputeControl()
    -> ComputeControlInternal()
      -> ComputeControlTerms()
        -> ComputeActualCommand()
```

For control algorithms, prefer code that reads like the derivation.

For mechanical details, use helpers to keep the derivation clean.

## Helper Policy

Use helpers to clarify meaningful operations, not to hide every small block of code.

A helper is good when it:

- Gives a meaningful name to a domain-level operation
- Removes distracting mechanical detail
- Isolates low-level conversion, encoding, decoding, parsing, or transport logic
- Avoids repeated boilerplate with real semantic meaning
- Improves memory reuse in repeated paths
- Makes the caller easier to understand without forcing excessive navigation

Use helpers for mechanical details such as:

- Quaternion to Euler conversion and Euler to quaternion conversion
- Rotation, pose, frame, and transform utilities
- Unit conversion
- Message encoding and decoding
- Packet packing and unpacking
- Parser and serializer logic
- Checksum, scaling, byte-order, and protocol helpers
- Memory preallocation and reusable workspace management
- Buffer resizing, reserving, and clearing
- Log formatting
- Common validation helpers
- Saturation and safety-limit utilities

Do not use helpers to hide the main mathematical or control flow.

Avoid helpers that:

- Are only 1 to 3 line wrappers around another helper
- Add only one trivial guard, one log, or one passthrough call
- Exist only because short functions are good
- Create deep call chains
- Force the reader to jump across many locations to understand one control path
- Split one simple idea into many tiny fragments
- Hide an important mathematical step behind a vague name

As a rule of thumb:

- One or two helper hops from a lifecycle function is usually enough.
- If understanding one control path requires opening three or more helper levels, the decomposition is probably too deep.
- If a helper name does not add meaning beyond the code inside it, inline it.
- If a helper only forwards arguments to another helper, remove it.
- If a helper is called only once, prefer keeping the logic at the call site and
  add a short intent comment when the block needs explanation.
- Do not extract a single-use helper merely to give a block of code a name.
  Extract it only when it isolates substantial mechanical detail, a safety or
  synchronization boundary, reusable behavior, or a separately testable
  contract.
- Comments should explain why the block exists or what domain operation it
  performs, not restate each line.

Prefer:

```cpp
// Publish only complete snapshots so readers never observe mixed DDS frames.
{
  std::lock_guard<std::mutex> lock(state_mutex_);
  latest_state_ = state;
  state_watchdog_.Feed();
}
```

Avoid a single-use wrapper with no additional contract:

```cpp
StoreState(state);
```

## Abstraction Level And Naming Strictness

Naming strictness depends on abstraction level.

High-level lifecycle or object APIs may use broad names when the object context makes the meaning clear.

Acceptable high-level examples:

```cpp
robot.Initialize();
robot.Reset();
robot.Read();
robot.Update();
robot.Write();

controller.Initialize();
controller.Reset();
controller.Step();

estimator.Update();
planner.Plan();
driver.Read();
driver.Write();
```

These are acceptable because the object name provides the domain context, and the method represents a lifecycle action.

The stricter naming rules apply mainly to lower-level helper functions, private helpers, utility functions, and functions with side effects.

For helpers, the name and signature should reveal:

- What is computed
- What input is read
- What output is returned or updated
- Whether member state is mutated
- Whether external side effects occur
- Whether memory is reused or may be allocated

Bad helper:

```cpp
void ApplyForwardKinematics();
```

This hides too much:

- What input is used?
- What output changes?
- Does it update a member variable?
- Does it publish something?
- Does it allocate?
- Does it modify cached state?

Better helper options:

```cpp
Pose ComputeForwardKinematics(const JointVector& q);
void ComputeForwardKinematics(const JointVector& q, Pose* x);
void UpdateForwardKinematicsCache(const JointVector& q);
void RefreshKinematicsSnapshot(const JointVector& q);
```

Use broad lifecycle names at high levels.

Use precise data-flow names at helper levels.

Do not over-police names like `robot.Update()` or `controller.Step()` when they are public lifecycle methods. Instead, make sure their implementations clearly show the high-level flow.

## Function Naming Conventions

Use function names that indicate behavior and side effects.

Recommended meanings:

- `Compute...` returns a value or writes a clearly provided output.
- `Fill...` writes into caller-provided storage.
- `Update...` mutates existing state.
- `Refresh...Snapshot` rebuilds a coherent cached state.
- `Apply...` should be reserved for commands, limits, or effects that are actually applied.
- `Publish...` or `Send...` should imply external side effects.
- `Encode...` converts typed data into raw data.
- `Decode...` converts raw data into typed data.
- `Validate...` checks correctness or readiness.
- `Clamp...` or `Limit...` modifies a value to satisfy bounds.

Avoid vague names like:

- `Do...`
- `Handle...` unless the domain action is clear
- `Process...` unless the domain action is clear
- `Apply...` when nothing externally meaningful is applied
- `Update...` without saying what state is updated
- `Run...Internal`
- `Compute...Internal`
- `Helper...`

The name should describe the semantic operation, not just the implementation phase.

## Output Parameters And Mutation Clarity

A function signature should make data flow visible.

Readable pure-return style:

```cpp
Pose ComputeForwardKinematics(const JointVector& q);
```

This is easiest to read, especially for low-frequency code or small return types.

Memory-conscious output style:

```cpp
void ComputeForwardKinematics(const JointVector& q, Pose* x);
```

This makes the mutation target visible at the call site:

```cpp
ComputeForwardKinematics(q, &x);
```

For C++ output parameters, prefer pointer outputs over non-const reference outputs when practical, because `&x` at the call site makes mutation explicit.

Avoid this unless the local project strongly prefers reference outputs:

```cpp
void ComputeForwardKinematics(const JointVector& q, Pose& x);
```

At the call site, mutation is less obvious:

```cpp
ComputeForwardKinematics(q, x);  // Does x change? Not obvious.
```

If member state is mutated, say so in the function name:

```cpp
void UpdateForwardKinematicsCache(const JointVector& q);
void RefreshKinematicsSnapshot(const JointVector& q);
```

Do not use vague `void` helpers that mutate hidden state without making that mutation clear.

## Per-Step Memory And Workspace Policy

Be careful with memory and repeated work in:

- Loops
- Callbacks
- Update cycles
- Control steps
- Simulation steps
- High-frequency paths
- Repeated message conversion paths

Before adding variables or allocations inside a repeated path, ask:

- Is this object cheap and stack-only?
- Does it allocate memory internally?
- Is it resized every cycle?
- Can this buffer be reused?
- Can this object be a private workspace?
- Does moving it outside the loop make ownership clearer or more confusing?
- Does preallocation improve performance without making the code harder to read?
- Is this logging or formatting happening every iteration?

Prefer:

- Reusing workspaces for repeated numerical computation
- Preallocating buffers when size is known
- Reserving container capacity when size is known
- Avoiding repeated string formatting in hot paths
- Avoiding repeated container growth in hot paths
- Avoiding repeated dynamic Eigen allocation in hot paths
- Passing non-trivial inputs by `const&`
- Passing small scalar values by value
- Keeping loop bodies small and readable

Do not optimize blindly.

For normal low-frequency code, prefer local variables near first use for readability.

For high-frequency paths, prefer stable memory behavior.

## Private Member Workspace Policy

For values recomputed every step and reused as part of controller state or temporary workspace, consider preallocated private member storage.

Good candidates:

- State snapshots
- Kinematics results
- Jacobians
- Command vectors
- Temporary Eigen matrices or vectors
- Solver inputs and outputs
- Message buffers
- Encoding and decoding buffers
- Saturated command storage
- Diagnostic summaries that are reused

Example:

```cpp
class Controller {
 public:
  bool Step();

 private:
  void RefreshStateSnapshot();
  void UpdateKinematicsCache(const JointVector& q);

  StateSnapshot state_;
  Pose end_effector_pose_;
  Jacobian task_jacobian_;
  JointCommand raw_command_;
  JointCommand limited_command_;
};
```

Then the step flow can stay readable:

```cpp
bool Controller::Step()
{
  RefreshStateSnapshot();
  UpdateKinematicsCache(state_.q);

  BuildTaskTarget(state_, &target_);
  ComputeImpedanceCommand(state_, target_, &raw_command_);
  ApplyCommandLimits(raw_command_, &limited_command_);

  return PublishCommand(limited_command_);
}
```

Use private member workspace when it avoids repeated allocation or clarifies ownership.

Do not turn every temporary variable into member state.

Member state should have a clear lifecycle, reset behavior, and ownership meaning.

## Utility Package Policy

Reusable mechanical details should live in utility packages or clearly named utility modules.

Prefer extracting reusable utilities for:

- Quaternion to Euler conversion and Euler to quaternion conversion
- Rotation, pose, frame, and transform helpers
- Unit conversion
- Numeric clamping and saturation helpers
- Message encoding and decoding
- Packet packing and unpacking
- Parser and serializer logic
- Checksum, scaling, byte-order, and protocol helpers
- Common validation helpers
- Common logging or formatting helpers
- Reusable memory buffer or workspace helpers

Do not duplicate these utilities across controllers, nodes, experiments, or drivers.

If the same mechanical helper appears in more than one place, consider moving it into a shared utility package.

However, do not move the main control law or mathematical algorithm flow into a vague utility just for reuse.

Good utility extraction:

```cpp
const Eigen::Vector3d rpy = geometry_utils::QuaternionToRollPitchYaw(quat);
const double torque = protocol_utils::DecodeTorque(frame);
safety_utils::ApplyCommandLimits(limits, &command);
```

Bad utility extraction:

```cpp
const JointCommand command = control_utils::DoEverything(state, target, config);
```

Utilities should remove distracting mechanics, not hide the controller's mathematical intent.

Utility package rules:

- Prefer small, focused utility functions.
- Prefer domain-specific utility names such as `geometry_utils`, `math_utils`, `protocol_utils`, `safety_utils`, or `memory_utils`.
- Avoid dumping grounds like `misc`, `common`, or `helpers`.
- Keep utility functions deterministic and easy to test.
- Add deterministic tests for utilities that handle math, units, encoding, decoding, limits, or protocol behavior.
- Avoid hidden global state.
- Avoid unexpected allocation in hot paths.

## File Organization

When editing a `.cpp`, prefer this order when practical:

1. Construction and initialization
2. Public lifecycle functions
3. High-level private helpers
4. Low-level algorithmic helpers
5. Low-level transport, protocol, conversion, or numerical helpers
6. Logging, printing, and debug utilities

The first screen or two of a file should reveal the main behavior.

Do not bury the control flow under matrix math, protocol details, logging, or debug utilities.

In `.cpp` files, place a consistent slash separator immediately before every
function definition, including constructors, destructors, member functions,
and anonymous-namespace helpers:

```cpp
////////////////////////////////////////////////////////////////////////////////
LowLevelIo::LowLevelIo() = default;

////////////////////////////////////////////////////////////////////////////////
bool LowLevelIo::Start(...)
{
  // ...
}
```

Use the separator only as a visual boundary. It does not replace API
documentation or an intent comment when the function has a non-obvious
contract, side effect, synchronization assumption, or safety requirement.

## Logging

Logging should not dominate control flow.

If formatting or conditional logging makes the main path hard to read, move it into a helper.

Prefer:

```cpp
LogPlanFailureIfNeeded(plan);
```

Avoid large logging blocks inside top-level lifecycle functions.

In high-frequency code, avoid expensive logging, formatting, or string construction unless throttled, disabled, or clearly justified.

## Safety And Risk

Treat hardware-facing, production-facing, data-changing, or user-impacting code conservatively.

Do not remove:

- Safety checks
- Limits
- Guards
- Validation steps
- Timeout handling
- Watchdog behavior
- Rollback paths

unless explicitly requested.

If a change could affect physical systems, deployed systems, data integrity, or user-visible behavior, describe a safe validation path.

## Testing And Validation

After implementation, run the narrowest relevant check from `docs/COMMANDS.md` when practical.

If no command is known, inspect the repository for likely build or test commands.

Do not claim validation was performed unless it was actually performed.

For these areas, prefer deterministic tests with known input/output examples:

- Protocol code
- Parser code
- Public interfaces
- Numerical logic
- Data transformations
- Command conversion
- Safety limits
- State-machine transitions
- Utility functions

If tests cannot be run, clearly state what was not verified.

## Report Format

At the end, report:

1. What changed
2. Why it changed
3. Files touched
4. Validation performed
5. What was not verified
6. Remaining risks or follow-up work
