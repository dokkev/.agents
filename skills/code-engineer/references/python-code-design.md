# Python Design Choices

Use these examples when the Python defaults in `SKILL.md` leave a real design
choice. Follow its task contract; this document adds no execution or review step.
Preserve appropriate local conventions rather than rewriting code to match examples.

## Function or Object

Keep a stateless computation direct:

```python
result = solve(design, config)
write_result(result, output_dir)
```

Do not introduce `SolveRequest`, `SolverFactory`, and `ResultWriter` just to
connect these operations. Retain a solver object when it actually owns a model,
resources, or useful warm-start state. An existing backend API or required
external interface is also a real reason for a class; a hypothetical second
backend is not.

Extract a helper when it gives a meaningful operation a name, removes actual
duplication, or isolates mechanics such as serialization. Do not split each
expression in a short algorithm into a private function or module.

## Collection or Record

A collection or obvious local unpacking needs no new type:

```python
depths_mm = (0.5, 1.0, 1.5)
lower, upper = bounds[name]
```

For a record shared by callers, reuse an existing type first. Otherwise named
fields can remove positional ambiguity:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    lower: float
    upper: float
```

Do not wrap a single value or every temporary result in a dataclass. Choose
immutability because it is a contract, not a decoration. Validate an invariant
at its owner; keep expensive work and I/O out of constructors.

Use dictionaries for real mappings, metadata, and serialized payloads. Use
`TypedDict` when a dictionary-shaped interface is required, not to justify a
second representation. Do not convert an established, clear interface merely
to satisfy a blanket "no dictionaries" rule.

## Boundary or Indirection

Prefer `mechanics.identity.post_contact_travel_mm` to a property that merely
forwards the same field. A property is useful when it derives a value, enforces
an invariant, or preserves an intentional public API. Avoid independently
editable copies of the same concept.

Keep optimizer-specific conversion in the optimizer adapter and serialization
in the writer. Reuse an existing adapter instead of adding a second path.
Conversely, keep NumPy arrays or framework types explicit when they are central
to the computation; do not wrap every library call in a "neutral" interface.

Use an enum for a shared finite domain vocabulary when it prevents mistakes;
a small local `Literal` or clear string may be enough. Do not let type machinery
become more complex than the behavior it describes.

## Failure and Imports

Make mutation and expected failure outcomes explicit. Preserve physical units
in names where ambiguity matters. Do not silently clamp, coerce, or substitute
invalid numerical states unless that behavior is part of the contract.

Keep GPU, hardware, solver, GUI, and network initialization on the execution
path that needs it. Avoid broad package re-exports that initialize optional
systems on import. Preserve useful existing public imports without creating
compatibility aliases for imaginary consumers.
