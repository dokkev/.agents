# Python Code Design

Loading this reference does not authorize tests, validation, or review.

Use this reference when Python API design, data modeling, module structure,
refactoring, or readability is a material part of the requested work. This is
not a formatting guide; use the repository formatter and linter for mechanical
style.

## Section Map

- [Core Contract](#core-contract)
- [Python References](#python-references)
- [Prefer the Obvious Python Representation](#prefer-the-obvious-python-representation)
- [Collections Are Not Records](#collections-are-not-records)
- [Keep Dictionaries at Boundaries](#keep-dictionaries-at-boundaries)
- [Functions Before Classes](#functions-before-classes)
- [Use Dataclasses for Meaningful Data](#use-dataclasses-for-meaningful-data)
- [Avoid Pass-Through Accessors](#avoid-pass-through-accessors)
- [Keep One Source of Truth](#keep-one-source-of-truth)
- [Keep Framework Types at Boundaries](#keep-framework-types-at-boundaries)
- [Keep Core Logic Visible](#keep-core-logic-visible)
- [Use Types to Clarify Contracts](#use-types-to-clarify-contracts)
- [Make Mutation and Failure Explicit](#make-mutation-and-failure-explicit)
- [Keep Imports Lightweight](#keep-imports-lightweight)
- [Avoid Speculative Python Machinery](#avoid-speculative-python-machinery)

## Core Contract

Write Python for the reader of the domain logic, not for the machinery around
it.

Prefer explicit, simple, flat code with one obvious representation of each
concept. Use ordinary functions, dataclasses, enums, collections, and modules
before introducing framework-style abstractions.

Do not mechanically translate C++, Java, or framework architecture into
Python. A class, interface, registry, factory, wrapper, or protocol must earn
its existence by owning real state, invariants, polymorphism, lifecycle, or a
required external boundary.

Keep the scientific or application control flow visible. Hide serialization,
framework conversion, hashing, plotting, path construction, and low-level
mechanics rather than hiding the algorithm itself.

Use the official Python guidance as the baseline. This reference focuses on
repository-scale design choices that those documents do not prescribe in
detail.

## Python References

Do not duplicate general Python guidance here. Use the official references:

- PEP 20 — The Zen of Python: https://peps.python.org/pep-0020/
- PEP 8 — Style Guide for Python Code: https://peps.python.org/pep-0008/
- PEP 557 — Data Classes: https://peps.python.org/pep-0557/

This document focuses on representation choice, data modeling, ownership,
framework boundaries, and keeping domain logic visible.

## Prefer the Obvious Python Representation

Choose the smallest Python representation that communicates the semantics.
Do not add ceremony because a concept might become more complicated later.

Prefer direct values and functions for local calculations. Introduce a named
runtime type when names, invariants, identity, or cross-module contracts make
that type easier to understand than positional or unstructured data.

Avoid copying patterns from languages that require classes, interfaces,
getters, builders, or factories for ordinary data flow.

## Collections Are Not Records

Use a tuple when the values form one homogeneous immutable collection:

```python
checkpoint_depths_mm = (0.5, 1.0, 1.5)
```

Do not use positional tuples as unnamed records when positions have different
meanings:

```python
# Avoid
("flat_pad_height", 0.5, 29.5)
```

Prefer a small named object:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    lower: float
    upper: float
```

Use the rule:

> tuple = collection; named object = record

A short-lived local unpacking tuple is fine when its meaning is obvious at the
use site. Do not create a dataclass for every temporary intermediate value.

## Keep Dictionaries at Boundaries

Dictionaries are appropriate for dynamic mappings, serialized data, metadata,
and external-library payloads.

Avoid large `dict[str, Any]` objects as stable internal schemas when callers
must know a fixed set of fields. Prefer a named runtime object for stable data
with known semantics or invariants.

Convert domain objects to dictionaries at JSON, CSV, artifact, configuration,
or framework boundaries rather than carrying serialization-shaped data through
the core implementation.

Use `TypedDict` when a dictionary shape itself is the required interface, not as
a substitute for a domain object that should own behavior or invariants.

## Functions Before Classes

Prefer a function for a stateless calculation or transformation.

Use a class when it owns meaningful state, configuration, identity, lifecycle,
or invariants. A class should make ownership clearer than a collection of free
variables would.

Do not introduce classes solely to namespace functions or imitate an interface
with one implementation. A module is already a namespace.

Prefer composition of small concrete objects over inheritance. Add an abstract
base class or `Protocol` only when a real boundary has multiple implementations
or an external contract requires one.

## Use Dataclasses for Meaningful Data

Use dataclasses for data with stable named fields and meaningful semantics.
`frozen=True` is useful for immutable configuration, identity, and value objects
when immutability is part of the contract.

Put validation where the type owns the invariant, for example in
`__post_init__`, a constructor function, or a dedicated validation function.
Do not hide expensive work, I/O, solver execution, or surprising mutation in a
dataclass constructor.

Do not replace every local tuple, dictionary, or temporary result with a
dataclass. Named types should remove semantic ambiguity, not add ceremony.

## Avoid Pass-Through Accessors

Do not add a public property or getter merely to forward a value that is already
clearly accessible through an owned object.

Prefer the direct composition path when it reflects the actual ownership:

```python
# Prefer
mechanics.identity.post_contact_travel_mm
```

Do not flatten that path with repetitive forwarding accessors:

```python
# Avoid
@property
def post_contact_travel_mm(self) -> float:
    return self.identity.post_contact_travel_mm
```

A forwarding accessor is justified only when it establishes a meaningful public
boundary, preserves an intentionally stable external API, or adds behavior such
as validation, normalization, derivation, or an invariant.

If many forwarding accessors are needed, reconsider ownership instead of hiding
the object structure behind aliases.

## Keep One Source of Truth

Do not independently maintain the same concept as a tuple, set, string,
constant, copied dictionary, and framework-specific object.

Keep one authoritative representation and derive genuinely different forms with
properties, functions, or boundary adapters. A property that only aliases an
already accessible nested field is not a derived representation; prefer direct
access or move ownership to the class that conceptually owns the value.

When a third-party library needs a different representation, convert from the
authoritative domain object at the integration boundary. Do not let two
independently editable representations drift.

## Keep Framework Types at Boundaries

Do not shape core Python objects around an external framework when a neutral
domain representation is clearer.

Examples include converting structured constraints to optimizer strings in an
optimizer adapter, domain objects to JSON dictionaries in artifact writers, and
keeping GPU, solver, ROS, GUI, or database objects behind their owning module.

Framework convenience is not a reason to leak framework-specific types through
the domain model.

If framework behavior is central to the algorithm, keep that dependency
explicit instead of wrapping it in a fake neutral abstraction.

## Keep Core Logic Visible

A reader should encounter the main behavior before helper machinery.

Keep domain decisions, mathematical flow, state transitions, objective or
constraint construction, interpretation of solver outputs, and important
failure decisions visible in the primary function or method.

Move hashing, serialization, path construction, formatting, plotting,
framework conversion, and repetitive mechanical checks out of the way when
they obscure that story.

Before extracting a helper, ask:

> Would a reader need to open this helper to understand what the algorithm
> actually does?

If yes, keep the important logic visible at the call site.

Do not fragment simple code into many tiny private modules merely to reduce file
or function length.

## Use Types to Clarify Contracts

Type hints should clarify public and cross-module contracts. Prefer specific
types over `Any` when they materially improve understanding.

Use `Enum` or `StrEnum` when a finite semantic vocabulary crosses module
boundaries or raw strings would make behavior typo-prone. Do not create enums
for ordinary unconstrained text.

Use `Literal` for small local finite choices when introducing a runtime enum
would add no value.

Prefer concrete collection types when mutation and ownership matter. Use
abstract collection interfaces such as `Sequence` when callers genuinely may
supply multiple compatible representations.

Include physical units in names when ambiguity matters, for example
`radius_mm`, `depth_mm`, `dt_s`, and `force_n`.

Do not make type complexity exceed runtime complexity. Deep generic hierarchies
and type-level machinery need a concrete readability or correctness payoff.

## Make Mutation and Failure Explicit

Make mutation visible in names and ownership. Prefer returning a new value for
pure transformations; mutate an owned object when mutation is the natural
contract.

Validate invariants near the boundary that owns them. Do not silently clamp,
substitute, or coerce invalid scientific or numerical states into plausible
outputs unless that behavior is explicitly part of the contract.

Use exceptions for exceptional failures and small result/status objects when
failure is an expected domain outcome that callers must inspect.

Avoid passing a mutable dictionary through many layers so each layer can append
status, diagnostics, and partial results. Give stable concepts an owner and
classify failures at a clear boundary.

## Keep Imports Lightweight

Importing a domain, configuration, or data-model package should not initialize
GPUs, hardware, solvers, GUI runtimes, network clients, or other expensive
optional dependencies.

Load heavy optional dependencies close to the execution path that requires
them. Keep import-time side effects minimal and deterministic.

Avoid broad package `__init__.py` re-export machinery when it forces heavy
imports or obscures ownership. Re-export a small stable public surface only
when it improves the API.

Prevent local module names from shadowing important third-party packages when
that collision would make imports ambiguous.

## Avoid Speculative Python Machinery

Do not add registries, factories, dependency-injection containers, plugin
systems, metaclasses, descriptor frameworks, decorators with hidden control
flow, generic backend layers, or compatibility wrappers for hypothetical future
requirements.

Introduce such machinery only for a current requirement that cannot be served
clearly by direct Python code.

Prefer migrating repository-owned callers and deleting obsolete internal APIs
over preserving parallel old and new interfaces unless backward compatibility
is explicitly required.
