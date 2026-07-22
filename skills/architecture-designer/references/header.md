# C++ Header and Type Architecture

Use these rules to keep headers self-contained, dependencies explicit, type
placement proportional, and navigation shallow.

## Contents

- [Make Headers Self-Contained](#make-headers-self-contained)
- [Use Forward Declarations Deliberately](#use-forward-declarations-deliberately)
- [Place Types Near Their Owner](#place-types-near-their-owner)
- [Do Not Enforce One Type per Header](#do-not-enforce-one-type-per-header)
- [Keep Interfaces Small](#keep-interfaces-small)
- [Handle Templates Without Hiding the Contract](#handle-templates-without-hiding-the-contract)
- [Prevent Dependency Cycles](#prevent-dependency-cycles)
- [File Split Checklist](#file-split-checklist)

## Make Headers Self-Contained

Every header must compile when included first in a translation unit. Include the
headers required for every complete type, base class, inline expression, alias,
and declaration used by the public contract.

- Include what the header uses.
- Do not rely on transitive includes.
- Keep public headers free of vendor, ROS, simulator, or platform headers unless
  those types are part of the intended public API.
- Put implementation-only includes in the `.cpp` file.
- Prefer a stable domain type over exposing a third-party type at a boundary.

Use include guards or the repository's established `#pragma once` convention.
Follow the local include-order and formatting rules.

## Use Forward Declarations Deliberately

Forward declare when the header needs only a pointer or reference and no inline
code requires the complete type.

```cpp
class RobotModel;

class Controller
{
public:
  explicit Controller(RobotModel& model);

private:
  RobotModel& model_;
};
```

Include the complete definition when the header uses:

- a value member;
- inheritance;
- `sizeof`, member access, or another operation requiring completeness;
- an inline function whose body requires the type;
- a standard-library template whose completeness requirements demand it.

Do not forward declare standard-library types. Include their standard headers.
Do not use forward declarations solely to reduce an include count when they make
ownership or template behavior fragile.

Move concrete third-party members behind a private implementation object only
when dependency isolation or build cost is real and worth the extra allocation,
indirection, lifecycle, and implementation complexity. Do not add PImpl by
default.

## Place Types Near Their Owner

Type placement follows ownership and consumer scope.

| Usage | Placement |
| --- | --- |
| one class only | nested type or private declaration |
| one module's public API | representative module header |
| several modules in one package | focused domain header in that package |
| multiple packages with a stable contract | independent public header or package consideration |

```cpp
class Controller
{
public:
  enum class Mode
  {
    kIdle,
    kPosition,
    kTorque,
    kFault,
  };
};
```

Do not create `control_mode.hpp`, `status.hpp`, or `config.hpp` solely because a
small type has a name. Give it an independent header when it is an independent
concept with multiple real consumers.

Keep closely related domain structs together when they form one stable contract
and change together. Split them when they have different ownership, dependencies,
or consumers.

## Do Not Enforce One Type per Header

One-type-one-header is not a goal. File boundaries should reduce coupling and
navigation, not maximize file count.

Keep types together when:

- they form one small API contract;
- one is a result, status, option, or nested concept owned by the other;
- they share consumers and dependencies;
- reading them together makes usage clearer.

Split a type when:

- it has independent consumers;
- it introduces a distinct or heavy dependency;
- it has a different stability or ownership boundary;
- it is large enough that the owning header obscures its primary contract;
- it needs independent tests or reuse.

Do not create separate files for every enum, status, config, or one-line helper.
Do not collect unrelated concepts into `common.hpp`, `types.hpp`, or `utils.hpp`.

## Keep Interfaces Small

A public header should make role, ownership, lifecycle, inputs, outputs, and
failure behavior clear without exposing implementation workspaces.

Expose:

- stable domain types;
- required lifecycle methods;
- const observation and explicit mutation boundaries;
- meaningful status or result types;
- units, frames, dimensions, and thread-safety contracts when relevant.

Hide:

- solver workspace and matrix assembly temporaries;
- model cache details;
- buffer indices, mutexes, and atomics;
- ROS callback and executor mechanics;
- packets, registers, and vendor SDK objects;
- private helper types used by one implementation.

Do not expose mutable containers or component getters merely to avoid writing a
cohesive operation. Avoid large umbrella headers unless the repository has a
stable public library surface that genuinely benefits consumers.

Keep non-trivial method definitions in `.cpp` files. Inline only short accessors,
templates, `constexpr` functions, and operations where inlining or header
visibility is semantically required.

## Handle Templates Without Hiding the Contract

Templates generally require their definitions to be visible at the point of
instantiation. Keep a small template's declaration and implementation together
in its header when that is easiest to read.

For a large template:

```text
finite_state_machine.hpp
finite_state_machine.tpp
```

The header may include the `.tpp` at its end. Treat both files as one component;
do not use `.tpp` merely to imitate a `.cpp` split.

- Keep template parameters semantically meaningful and few.
- Prefer a normal class or virtual interface when compile-time polymorphism has
  no demonstrated value.
- Avoid template metaprogramming, CRTP, and policy stacks for ordinary component
  wiring.
- For the required templated FSM contract, template only the state identifier,
  snapshot, output, or other actual type variation. Do not template every
  dependency.
- Use explicit instantiation in a `.cpp` only when the supported type set is
  intentionally closed and the build/API tradeoff is documented.

## Prevent Dependency Cycles

A header cycle usually signals unclear ownership or an oversized public API.
Resolve it by:

1. identifying which component owns the relationship;
2. passing a stable domain value instead of a live component;
3. forward declaring pointer/reference dependencies when appropriate;
4. moving shared stable contracts to the real owning module;
5. moving implementation details to `.cpp` files.

Do not solve a cycle with:

- a new global `common.hpp`;
- a generic context or service locator;
- duplicated type definitions;
- transitive include ordering;
- merging unrelated components into a god class.

Public include direction should follow component and package dependency
direction. Internal headers must not leak into another package's public API.

## File Split Checklist

Before adding or splitting a header, ask:

1. Is this an independent concept or merely a named implementation detail?
2. Who consumes it, and do those consumers need its dependencies?
3. Can it stay nested or next to its owner?
4. Does the header compile when included first?
5. Are complete types included and incomplete types used legally?
6. Does the split remove a real dependency, ownership, test, or reuse boundary?
7. Does it reduce understanding by forcing extra navigation?
8. Are template definitions visible without creating an opaque file chain?
9. Is a new `common`, `types`, `base`, or `utils` bucket concealing weak design?

A type deserves its own header because it is an independent concept, not merely
because it has a name.
