# General Code Guideline

Loading this reference does not authorize tests, validation, or review.

Use this reference when code structure, abstraction, ownership, or readability is
the main concern. It applies across languages. Language-specific references may
add stricter rules.

## Core Contract

Write code for individuals and small research teams who need to understand,
change, debug, and delete it quickly.

Prefer the smallest direct structure that expresses the real domain behavior.
Do not optimize for hypothetical future scale, integrations, compatibility, or
reuse unless the current repository actually requires them.

Every abstraction must pay for itself. A class, helper, wrapper, adapter,
property, intermediate type, or layer should make domain meaning clearer,
preserve correctness or safety, or remove substantial real complexity. If it
does none of those things, remove it.

Do not confuse fewer classes with simpler code. Unstructured data and magic
conventions can be just as difficult to maintain as excessive abstraction. Use
the representation that makes meaning obvious.

## Keep The Main Flow Direct

Avoid hiding a short domain operation behind layers that add no behavior.

```python
# Avoid
request = SolveRequest.from_design(design)
solver = SolverFactory.create(config)
result = solver.solve(request)
validated = ResultValidator.validate(result)
artifact = ResultArtifact.from_result(validated)
ArtifactWriter(output_dir).write(artifact)
```

```python
# Prefer
result = solve(design, config)
validate_result(result)
write_result(result, output_dir)
```

Add a layer only when it owns a real boundary, state, invariant, or alternate
implementation that exists now.

## Do Not Fragment Simple Logic

Avoid extracting helpers only to make the caller shorter.

```python
# Avoid
def update_force(state):
    error = _compute_error(state)
    command = _compute_command(error)
    return _apply_limits(command)
```

when each helper contains only one obvious expression.

```python
# Prefer
def update_force(state):
    error = state.force_des - state.force_meas
    command = state.kp * error
    return clamp(command, -state.max_force, state.max_force)
```

Extract a helper when it names a meaningful operation, removes substantial
repetition, isolates low-level mechanics, or has an independently useful
contract.

## Keep Ownership Visible

Avoid forwarding accessors that merely flatten composition.

```python
# Avoid
@property
def post_contact_travel_mm(self) -> float:
    return self.identity.post_contact_travel_mm
```

```python
# Prefer
mechanics.identity.post_contact_travel_mm
```

If many forwarding accessors seem necessary, reconsider ownership instead of
hiding the object structure.

## Do Not Create Namespace-Only Classes

Avoid classes whose only purpose is grouping stateless functions.

```python
# Avoid
class ResultWriter:
    @staticmethod
    def write(result, path):
        ...
```

```python
# Prefer
def write_result(result, path):
    ...
```

Use a class when it owns meaningful state, configuration, identity, lifecycle,
invariants, or polymorphic behavior.

## Prefer One Obvious Representation

Avoid carrying the same concept through several interchangeable wrapper types
without a real boundary.

```python
# Avoid
design -> DesignRequest -> SolverInput -> InternalDesign -> ArtifactDesign
```

```python
# Prefer
design -> solver boundary conversion -> result
```

Convert representations at actual boundaries. Do not invent intermediate
representations just to make layers look isolated.

## Do Not Encode Records As Loose Data

In Python, avoid stable record schemas hidden in dictionaries or heterogeneous
positional tuples.

```python
# Avoid
result = {
    "name": name,
    "depth_mm": depth_mm,
    "clearance_mm": clearance_mm,
    "valid": valid,
}

return name, depth_mm, clearance_mm, valid
```

```python
# Prefer
from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    name: str
    depth_mm: float
    clearance_mm: float
    valid: bool
```

Dictionaries remain appropriate for real mappings, metadata, configuration, and
serialization. Tuples remain appropriate for homogeneous collections or short
local unpacking whose meaning is obvious.

## Avoid Magic Domain Strings

Avoid repeated raw strings when a finite vocabulary is part of the domain.

```python
# Avoid
if state == "contact":
    ...
elif state == "release":
    ...
```

```python
# Prefer
from enum import StrEnum


class State(StrEnum):
    CONTACT = "contact"
    RELEASE = "release"
```

Do not create an enum for ordinary free-form text or a one-off local choice.

## Do Not Overcorrect Toward Types

A named type is not automatically simpler.

```python
# Avoid
@dataclass(frozen=True)
class CheckpointDepths:
    first: float
    second: float
    third: float
```

```python
# Prefer
checkpoint_depths_mm = (0.5, 1.0, 1.5)
```

Use a named type for a record. Use a collection for a collection.

## Avoid Speculative Generality

Do not add factories, registries, plugin systems, generic interfaces,
compatibility shims, retry frameworks, or configuration switches because they
might be useful later.

```python
# Avoid
backend = BackendRegistry.create(config.backend_name)
```

when the repository has one backend and no current requirement for another.

```python
# Prefer
backend = NewtonBackend(config)
```

Generalize after a second real case creates pressure, not before.

## Prefer Deletion Over Preservation

When repository-owned callers can be migrated safely, prefer deleting an old
internal path over maintaining old and new APIs in parallel.

```text
Avoid:   new API + compatibility wrapper + legacy alias + deprecation state
Prefer:  migrate callers -> delete obsolete internal API
```

Keep compatibility machinery only when an external contract actually requires
it.

## Review Test

When comparing two implementations with equivalent behavior, prefer the one
with fewer concepts and less indirection, not merely fewer lines.

Ask:

> If this class, helper, wrapper, property, adapter, or intermediate type were
> removed, would the code become less correct, less safe, or materially harder
> to understand?

If not, do not add it.