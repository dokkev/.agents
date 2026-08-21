# Python Code Examples

Loading this reference does not authorize tests, validation, or review.

Use these examples when choosing between plain Python values, named records,
classes, helpers, wrappers, and public accessors. The goal is not fewer classes
at any cost. The goal is the smallest representation that keeps domain meaning
obvious.

## Core Contract

Use structure to expose meaning, not to add ceremony.

Prefer code whose runtime structure matches the domain structure. Avoid both
unnecessary object machinery and unstructured schemas hidden in dictionaries,
heterogeneous tuples, and magic strings.

## Record-Shaped Dictionaries

Avoid using a dictionary as a stable record when callers depend on a fixed set
of semantic fields.

```python
# Avoid
result = {
    "name": name,
    "depth_mm": depth_mm,
    "clearance_mm": clearance_mm,
    "valid": valid,
}
```

Prefer a named value when those fields form a real domain record.

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

Keep dictionaries for genuine mappings, metadata, or serialization boundaries.

## Heterogeneous Positional Tuples

Avoid positional tuples whose positions carry different semantic meanings.

```python
# Avoid
return name, depth_mm, clearance_mm, valid
```

Prefer a named record when a caller should understand fields by name.

```python
# Prefer
return Result(
    name=name,
    depth_mm=depth_mm,
    clearance_mm=clearance_mm,
    valid=valid,
)
```

Homogeneous tuples remain appropriate collections:

```python
checkpoint_depths_mm = (0.5, 1.0, 1.5)
```

## Magic-String Domain States

Avoid repeating raw strings when a finite vocabulary is part of a real domain
contract.

```python
# Avoid
if state == "contact":
    ...
elif state == "release":
    ...
```

Prefer a small enum when the states cross functions or module boundaries.

```python
# Prefer
from enum import StrEnum


class State(StrEnum):
    CONTACT = "contact"
    RELEASE = "release"
```

Do not create enums for ordinary free-form text or one-off local choices.

## Pass-Through Accessors

Avoid flattening composition with getters or properties that add no behavior.

```python
# Avoid
@property
def post_contact_travel_mm(self) -> float:
    return self.identity.post_contact_travel_mm
```

Prefer the direct ownership path when it is already clear.

```python
# Prefer
mechanics.identity.post_contact_travel_mm
```

Add an accessor only when it owns a meaningful public contract, invariant,
validation, normalization, or derived value.

## Classes Used Only As Namespaces

Avoid a class whose only purpose is grouping stateless functions.

```python
# Avoid
class ResultWriter:
    @staticmethod
    def write(result: Result, path: Path) -> None:
        ...
```

Prefer a module-level function.

```python
# Prefer
def write_result(result: Result, path: Path) -> None:
    ...
```

Use a class when it owns meaningful state, configuration, identity, lifecycle,
or invariants.

## Unnecessary Wrapper Chains

Avoid turning a direct domain operation into a chain of wrappers, adapters, and
intermediate objects without a current requirement.

```python
# Avoid
request = SolveRequest.from_design(design)
solver = SolverFactory.create(config)
result = solver.solve(request)
validated = ResultValidator.validate(result)
artifact = ResultArtifact.from_result(validated)
ArtifactWriter(output_dir).write(artifact)
```

Prefer the direct flow when that is the actual behavior.

```python
# Prefer
result = solve(design, config)
validate_result(result)
write_result(result, output_dir)
```

Introduce a separate object or layer only when it owns real behavior or a real
boundary.

## Do Not Overcorrect Toward Named Types

Avoid introducing a named type when a plain homogeneous collection already says
exactly what the value is.

```python
# Avoid
@dataclass(frozen=True)
class CheckpointDepths:
    first: float
    second: float
    third: float
```

Prefer the collection itself.

```python
# Prefer
checkpoint_depths_mm = (0.5, 1.0, 1.5)
```

The test is semantic, not stylistic: use a named type for a record and a
collection for a collection.
