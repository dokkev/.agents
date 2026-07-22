# Control Concurrency

Loading this reference does not authorize tests, validation, or review.

Use this standard when control code crosses execution contexts, including ROS 2
callbacks, hardware I/O threads, real-time loops, background diagnostics, or
user-requested parallel computation.

Also select `control-loop-implementation.md` or
`control-discrete-time-implementation.md` only when the requested work actually
touches those concerns.

## Section Map

- [Core Contract](#core-contract)
- [Keep Concurrency Opt-In](#keep-concurrency-opt-in)
- [Use Concurrency to Isolate Timing Domains](#use-concurrency-to-isolate-timing-domains)
- [Prefer Existing Framework Primitives](#prefer-existing-framework-primitives)
- [Hide Memory Transfer Behind Domain APIs](#hide-memory-transfer-behind-domain-apis)
- [Share Complete Snapshots](#share-complete-snapshots)
- [Use One Coherent World Per Cycle](#use-one-coherent-world-per-cycle)
- [Declare Channel Semantics](#declare-channel-semantics)
- [Treat Time and Identity as Data](#treat-time-and-identity-as-data)
- [Keep Controller History on the Control Thread](#keep-controller-history-on-the-control-thread)
- [Design Overload and Failure Behavior](#design-overload-and-failure-behavior)
- [Keep the Real-Time Path Bounded](#keep-the-real-time-path-bounded)
- [Avoid Custom Concurrency Primitives](#avoid-custom-concurrency-primitives)

## Core Contract

The control loop owns time and controller history. Other execution contexts may
provide data, but they must not control when or how the loop progresses.

Threads exchange complete, timestamped values or events. They do not jointly
edit controller state.

Concurrency isolates unavoidable nondeterminism. It must not introduce hidden
nondeterminism into the control law.

## Keep Concurrency Opt-In

Start with a single-threaded implementation. Do not add `std::thread`,
`std::async`, a thread pool, parallel algorithms, or custom executor behavior
merely to separate components or make the design look scalable.

Introduce concurrency only when at least one of these conditions holds:

- the user explicitly requests multithreading or parallel execution;
- an existing framework creates distinct execution contexts, such as a ROS 2
  subscriber callback and a real-time controller update;
- blocking hardware or network I/O must be isolated from a deadline-sensitive
  loop;
- measured computation cannot meet its deadline sequentially and a bounded
  parallel design is explicitly accepted.

If none of these conditions holds, keep the code single threaded. Prefer a
clear sequential program over speculative concurrency.

Do not add a background worker without making its lifetime, ownership, shutdown,
and failure behavior visible.

## Use Concurrency to Isolate Timing Domains

Create execution boundaries around different timing behavior, not around every
software component.

Reasonable boundaries include:

- blocking device I/O versus a non-blocking control update;
- ROS 2 non-real-time callbacks versus a real-time controller update;
- low-rate diagnostics or file logging versus a high-rate loop;
- an explicitly profiled bounded worker versus its deadline-owning caller.

A class does not need its own thread merely because it has an independent
responsibility. Component boundaries and thread boundaries are different
design decisions.

The control loop must not wait for:

- a subscriber callback;
- a logger or diagnostics consumer;
- a parameter update;
- a network reconnect;
- a background worker with an unbounded completion time.

Synchronize data transfer. Do not synchronize the progress of the control loop
to unrelated execution contexts.

## Prefer Existing Framework Primitives

When ROS 2 callbacks cross into a real-time control path, prefer the established
`realtime_tools` package and the executor already owned by ROS 2. Do not create a
custom subscriber thread.

Choose the primitive from the data semantics:

| Transfer need | Preferred ROS 2 primitive |
| --- | --- |
| only the latest subscriber value matters | `realtime_tools::RealtimeThreadSafeBox` |
| ordered intermediate values must be retained | bounded `realtime_tools::LockFreeQueue` |
| real-time data must be published by a non-real-time path | `realtime_tools::RealtimePublisher` |
| one primitive flag crosses the boundary | `std::atomic<T>` when its contract is sufficient |

Use the non-blocking or best-effort operations required by the real-time path.
Do not assume that every method of a real-time-oriented container is
non-blocking.

`RealtimeBuffer` may be retained when an existing codebase already uses it
correctly. For new ROS 2 controller code, follow the current `realtime_tools`
guidance for the target ROS distribution rather than introducing a private
buffer implementation.

Keep library selection at the adapter boundary. A controller should not depend
on a ROS-specific container merely to read a state or reference.

## Hide Memory Transfer Behind Domain APIs

Synchronization, slot selection, pointer swapping, and buffer lifetime are
implementation details. Expose a domain-level contract to the control law.

```cpp
const RobotState& state = state_source.getSnapshot();

ControllerResult result;
if (!state.valid || state.age > maximum_state_age) {
  result = controller.Fallback(UpdateStatus::kStateUnavailable);
} else {
  const TaskReference& reference = reference_source.getSnapshot();
  result = controller.Step(state, model, reference);
}

command_channel.publish(result.command);
```

In this example:

- `getSnapshot()` acquires the latest complete state into stable control-thread
  storage without allocation or indefinite waiting;
- the returned `const RobotState&` remains stable for the documented cycle or
  accessor lifetime;
- the joint-command controller produces one complete nominal or fallback
  command with status;
- `publish()` transfers an immutable snapshot according to the channel contract;
- the hardware or transport context cannot observe a partially written command.

Do not expose code like this in the control law:

```cpp
// Avoid exposing transfer mechanics to controller code.
const auto* state = state_double_buffer_.ReadActiveSlot();
auto* command = command_buffer_.GetInactiveWriteSlot();
```

Hide memory mechanics, not control-relevant state. Validity, age, sequence,
fallback status, and other facts that affect the control decision must remain
available through the returned data or a small domain-level status.

## Share Complete Snapshots

Give each shared channel one logical writer. The writer constructs or updates a
private object and publishes it only after every field is complete and valid.

Readers consume immutable snapshots. Do not mutate shared Eigen objects,
messages, vectors, or configuration fields in place while another context may
read them.

Prefer:

```cpp
RobotState next_state = DecodeState(message);
next_state.sequence = ++state_sequence;
next_state.receive_time = steady_clock.now();
state_channel.Set(next_state);
```

Avoid publishing a pointer to an object that the callback continues to mutate.
Avoid protecting individual fields with separate locks because a reader may
observe values from different source samples.

If copying a snapshot is too expensive, use preallocated storage with a clear
ownership handoff. The API must still guarantee that a reader sees one complete
version and that storage remains alive for the documented access period.

## Use One Coherent World Per Cycle

Acquire each required input once at the cycle boundary. Use those versions for
the entire update.

```cpp
const RobotState& state = robot.GetState();
const TaskReference& reference = reference_source.GetReference();
const ControllerConfig& config = config_source.GetConfig();

// This update uses only these versions.
```

Do not read a shared reference again halfway through the calculation. Mixing a
new force target with an old pose target is usually worse than using a slightly
older but internally coherent reference.

Apply reset, mode, and configuration requests at a defined cycle boundary.
Never allow a callback to change controller history during an update.

If several channels must be synchronized to the same source sample, define that
relationship explicitly. Independent `GetLatest()` calls do not make values
temporally aligned merely because they occur close together.

## Declare Channel Semantics

Every cross-context channel must declare one of these semantics:

| Semantics | Typical data | Overload behavior |
| --- | --- | --- |
| latest value | robot state, continuous reference, command | replace older unread value |
| ordered event | mode request, discrete workflow command | bounded queue with explicit overflow policy |
| latched state | emergency stop, active fault, enable interlock | remain active until an authorized clear condition |
| sampled telemetry | diagnostics, visualization | lossy latest value or bounded queue |

Do not put a continuous reference into an unbounded FIFO. A 100 Hz reference
consumer should not replay a backlog of obsolete targets.

Do not represent an emergency stop as a transient latest-value message that can
be overwritten by a later benign update. Safety-critical events usually need
latched semantics.

For ordered events, define whether overflow drops the oldest event, rejects the
new event, or raises a fault. Do not rely on the queue never filling.

## Treat Time and Identity as Data

Cross-context data is incomplete without age and identity when freshness
matters.

```cpp
struct StampedRobotState {
  RobotState value;
  SteadyTimePoint receive_time;
  SourceTimePoint source_time;
  std::uint64_t sequence;
};
```

Use the metadata to distinguish:

- a source that stopped producing samples;
- transport delay;
- missed updates;
- duplicate delivery;
- repeated reads of the same valid sample.

Use a monotonic clock for local age and timeout decisions. Preserve a source or
ROS timestamp separately when it is needed for sensor alignment.

Define sequence wraparound behavior if a narrow counter is used. Prefer a wide
unsigned counter for process-lifetime identity.

## Keep Controller History on the Control Thread

The control thread exclusively owns state that changes the next control result,
including:

- integrator and filter history;
- previous controller output when the control algorithm uses it;
- solver warm start;
- mode-transition state;
- contact hysteresis;
- fault and recovery state owned by the controller.

External contexts publish requests. The control loop applies them at a cycle
boundary.

When actuator-facing smoothing is actually required, hardware execution
exclusively owns `previous_tau_sent_` and the associated transmitted-command
history. Do not mirror that history onto the control thread or feed it through
a shared command channel.

```cpp
const ControlRequest& request = request_source.GetRequest();
if (request.reset_sequence != applied_reset_sequence_) {
  ResetDiscreteState();
  applied_reset_sequence_ = request.reset_sequence;
}
```

Do not let a parameter callback call `integrator.Reset()` or replace a solver
warm start while the controller is computing.

## Design Overload and Failure Behavior

For every channel, define:

- capacity or number of retained versions;
- freshness timeout;
- whether the last valid value may be reused;
- behavior when no new value is available;
- overflow behavior;
- diagnostic counters;
- whether loss is a warning, recoverable fault, or latched fault.

Failure to acquire a best-effort container must have a bounded response. Typical
responses include using the previous valid snapshot within its explicit
freshness contract or declaring the input unavailable so the joint-command
controller produces its defined fallback.

Do not spin until a container becomes available. Do not silently use an old
value without updating age and status.

Shutdown must also be bounded. Define which context stops publication, which
controller or hardware-local protection owns the final output, and whether
worker shutdown may block outside the real-time path.

## Keep the Real-Time Path Bounded

Using a lock-free type does not by itself make a path real-time safe. Verify:

- no unbounded lock acquisition or retry loop;
- no allocation, resize, or memory reclamation in the real-time operation;
- stable object lifetime across access;
- bounded queue capacity;
- bounded copy cost;
- finite callback or worker work;
- cache contention and false sharing when measurements show they matter.

Prefer bounded, allocation-free, coherent transfer over a fashionable
synchronization technique.

Non-real-time diagnostics must consume published snapshots. They must not read
or format controller-owned mutable storage directly.

## Avoid Custom Concurrency Primitives

Do not implement a private double buffer, atomic pointer exchange, lock-free
queue, memory reclamation scheme, or synchronization wrapper from scratch when
an established library satisfies the contract.

A custom primitive requires all of the following:

1. the existing framework or library is demonstrably insufficient;
2. the missing requirement is documented;
3. the user approves the custom concurrency work;
4. ownership, lifetime, ordering, and memory-model assumptions are documented;
5. execution, allocation, overflow, race, and shutdown behavior have explicit
   evidence appropriate to the requirement.

Do not replace a small understandable mutex-protected non-real-time section with
custom lock-free code merely to remove the word `mutex`.

Do not claim hard real-time behavior from code inspection alone. Measurement or
validation belongs to an explicitly requested Validate mode.
