# Hardware I/O

Use this reference for the lowest code that touches a device or transport,
including a `LowIO` class, CAN or serial adapter, packet codec, socket, or
vendor SDK wrapper.

## Section Map

- [Core Contract](#core-contract)
- [Keep the Boundary Mechanical](#keep-the-boundary-mechanical)
- [Start With the Direct Path](#start-with-the-direct-path)
- [Require Evidence for Complexity](#require-evidence-for-complexity)
- [Keep Waiting Explicit](#keep-waiting-explicit)
- [Do Not Hide Recovery](#do-not-hide-recovery)
- [Publish Complete Facts](#publish-complete-facts)
- [Escalate One Problem at a Time](#escalate-one-problem-at-a-time)

## Core Contract

Start with the simplest implementation that satisfies the known device
protocol, timing requirement, and safety boundary. Add complexity only for an
explicit requirement or an observed problem, and add only the smallest
mechanism that addresses it.

Hardware I/O performs the requested communication, validates protocol-level
results, converts representations, and reports what happened. It does not
invent system recovery or safety policy.

An abstraction, mutable state, thread, queue, cache, retry, reconnect, or
additional timeout carries a burden of proof. Do not add one for a failure that
has not occurred and is not required by the device contract.

## Keep the Boundary Mechanical

Keep the lowest I/O layer responsible for mechanics such as:

- packet or frame encoding and decoding;
- byte order, length, checksum, and protocol-required sequence handling;
- the actual device, bus, socket, or SDK call;
- complete-result validation and minimal factual status reporting.

Keep policy above this boundary. Low-level I/O must not independently clamp or
filter domain commands, interpolate stale feedback, choose a fallback, change
motor mode, disable hardware, or run a recovery state machine. The owning
hardware or runtime layer makes those decisions from the reported outcome.

Do not create a generic transport interface for one concrete device merely in
case another transport is added later. Extract shared semantics after a second
real use case demonstrates them.

## Start With the Direct Path

Keep the normal control flow visible:

```text
write: encode request -> perform write -> return outcome
read:  perform read -> validate complete frame -> decode candidate -> publish outcome
```

Decode into a local candidate and make it visible only after the complete frame
passes validation. Add accumulation, reassembly, or ordering state only when
the actual transport can split or reorder the protocol unit.

Prefer a short synchronous path when its caller permits the documented wait.
Do not introduce a worker, queue, callback graph, or asynchronous state machine
only to make a small adapter appear scalable.

## Require Evidence for Complexity

Before adding a mechanism, identify:

1. the explicit requirement or reproduced failure;
2. the layer that owns the problem;
3. why the direct implementation is insufficient;
4. the smallest change that resolves that specific problem.

Reasonable evidence-to-mechanism pairs include:

- documented partial frames -> one bounded frame accumulator;
- a measured control-path stall -> isolation in an existing I/O context;
- a reproducible transient failure with known idempotence -> one bounded retry;
- an operator-required reconnect workflow -> one explicit reconnect operation.

Do not add several hypothetical protections together. Their interaction often
obscures the first failure and makes the path harder to reason about than the
device itself.

## Keep Waiting Explicit

Blocking is not automatically wrong. Hidden or unbounded blocking on a path
with a deadline is wrong.

Use a timeout only at a boundary that owns a real bounded-wait requirement. For
one operation, prefer one visible deadline or budget over separate nested
timeouts for write, response, retry, and cleanup. Do not mix an I/O wait budget
with the upper layer's state-freshness policy.

Add a dedicated thread only when an actual blocking or independent-rate
requirement must be isolated. Make its ownership and shutdown visible, and keep
the deadline-sensitive caller non-blocking. Do not add a thread merely because
the device API offers asynchronous operation.

## Do Not Hide Recovery

Let `Read()` and `Write()` report failure instead of silently reconnecting,
reenabling a device, changing mode, or repeating an operation indefinitely.

Add retry only when it is required or supported by observed evidence, the
operation's repetition semantics are known, and one layer owns a bounded retry
budget. Never let both LowIO and its caller retry the same operation.

Keep reconnect explicit. A failed command must not be delayed and transmitted
later merely because an internal reconnect eventually succeeded.

## Publish Complete Facts

Return the smallest result the caller needs to distinguish success, absence of
new data, malformed input, transport failure, or device-reported failure. Use
the repository's existing status model; do not create a large error hierarchy
for imagined cases.

Never expose a partially decoded state or present cached feedback as new data.
Preserve timestamps or sequence values supplied by the real source. Add
diagnostic counters only when they answer an operational question, and preserve
the first owning failure instead of replacing it with failures from speculative
recovery.

## Escalate One Problem at a Time

Use this progression:

1. implement the direct baseline;
2. observe or reproduce a real problem;
3. locate its cause and owning layer;
4. add the smallest targeted mechanism;
5. confirm that the mechanism resolves that problem.

If a mechanism does not protect a current contract or resolve an observed
failure, remove it. Simple hardware code is code whose communication flow,
mutable state, waits, and side effects can be followed without reconstructing a
hidden protocol of its own.
