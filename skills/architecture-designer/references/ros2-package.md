# ROS 2 Package Architecture

Treat a ROS 2 package as a build, dependency, installation, deployment, plugin,
or stable public-API boundary. Do not use packages merely to organize classes.

## Contents

- [Package Versus Directory or Target](#package-versus-directory-or-target)
- [Strong Reasons to Create a Package](#strong-reasons-to-create-a-package)
- [Common Robot Package Boundaries](#common-robot-package-boundaries)
- [Package Dependency Rules](#package-dependency-rules)
- [Weak Reasons to Create a Package](#weak-reasons-to-create-a-package)
- [Split and Merge Checklist](#split-and-merge-checklist)

## Package Versus Directory or Target

| Need | Prefer |
| --- | --- |
| organize files by topic | directory in the current package |
| compile internal code separately | CMake library target |
| add a node or executable | executable in the current package |
| isolate an external dependency | new package when isolation is meaningful |
| install or deploy independently | new package |
| expose a stable API used by other packages | new package consideration |
| support ROS plugin discovery | plugin-owning package consideration |

A controller class, hardware class, node, enum, test, or additional executable
does not by itself justify a package.

```text
wbc_controller/
├── include/wbc_controller/
│   ├── controller.hpp
│   └── robot_model.hpp
├── src/
│   ├── controller.cpp
│   ├── robot_model.cpp
│   └── controller_node.cpp
└── test/
```

ROS-free control code and its ROS wrapper may remain in one package as separate
targets when no one independently consumes or deploys the core.

```cmake
add_library(control_core ...)
add_library(ros_adapter ...)
add_executable(control_node ...)
```

## Strong Reasons to Create a Package

### Independent dependency set

Separate a dependency when it is large, optional, platform-specific, vendor
specific, or inappropriate for generic consumers.

Strong examples include:

- vendor SDK or device protocol library;
- CAN, serial, or fieldbus backend;
- simulator API;
- GUI or visualization framework;
- GPU or machine-learning runtime;
- optional solver backend;
- plugin framework dependency.

```text
wbc_control        # Eigen, Pinocchio, solver
unitree_hardware   # Unitree SDK, DDS, device protocol
```

Different dependency sets are evidence, not an automatic split. Small code that
is always installed, built, deployed, and changed together can remain one
package with separate targets.

### Demonstrated reuse and stable contract

Create a reusable package when:

- two or more packages or projects actually consume it;
- its public API and conventions are stable enough to support consumers;
- it has meaningful independent tests;
- it is not tied to one robot or application.

Reuse within one package justifies a module or directory, not automatically a
package. Start helpers in the owning package and extract only when the consumer
boundary appears.

### Shared ROS interfaces

A dedicated `*_interfaces` package is appropriate when messages, services, or
actions form a stable contract shared across multiple packages.

```text
clear_hand_interfaces/
├── msg/
├── srv/
└── action/
```

Keep implementation, nodes, hardware logic, and unrelated runtime dependencies
out of an interface-only package. A message used only inside one package may be
generated there until a real shared boundary exists.

Do not replace well-defined in-process C++ domain types with ROS messages merely
because an interface package exists.

### Independent installation or deployment

A package boundary is useful when users need to choose, install, release, or
deploy components independently, for example:

- simulation without physical hardware;
- visualization on a development workstation only;
- controller and hardware on the robot computer;
- one of several hardware backends;
- a separately released robot description;
- a top-level launch/configuration deployment unit.

### Real plugin boundary

Framework-discovered plugins can justify a package:

- `ros2_control` hardware or controller plugin;
- RViz plugin;
- MoveIt plugin;
- behavior-tree plugin.

One package may contain several small plugins when they share dependencies,
lifecycle, release, and users. Do not create a package per plugin mechanically.

## Common Robot Package Boundaries

### `*_description`

Use for independently consumed URDF/Xacro, meshes, SRDF, semantic description,
and visualization configuration. It should not depend on control or hardware.

Create it when simulation, visualization, planning, and control genuinely share
the robot description. Keep generated runtime logic out of it.

### `*_hardware`

Use for:

- joint and actuator mapping;
- encoder offsets, direction, and units;
- motor-side/joint-side conversion;
- vendor SDK and device lifecycle;
- communication and absolute hardware safety;
- a `ros2_control` hardware interface when applicable.

Control must not depend on the concrete hardware implementation.

### `*_control`

Use for:

- control laws and task formulations;
- state/reference-to-command computation;
- controller configuration;
- its necessary ROS wrapper or controller plugin.

Split a generic core from robot-specific control only after actual reuse or a
meaningful independent dependency/test boundary appears.

### `*_bringup`

Use to assemble the running system:

- top-level launch files;
- deployment configuration;
- hardware/simulation selection;
- namespace and remapping;
- lifecycle and startup order.

Bringup wires components together; it does not implement controller math,
hardware conversion, planning, or another package's domain logic.

Do not create empty `description`, `hardware`, `control`, or `bringup` packages
just to match a conventional repository layout. Each needs a real boundary.

## Package Dependency Rules

Prefer this direction:

```text
Bringup / application
    -> Control
    -> Hardware
    -> Description

Control
    -> Domain/model or shared interfaces

Hardware
    -> Shared interfaces
    -> Vendor SDK
```

- Bringup may assemble multiple implementation packages.
- Control must not depend on a hardware implementation.
- Hardware must not call control policy.
- An interface package must not depend on implementation packages.
- Description must not depend on control or hardware.
- Do not allow circular package dependencies.
- Do not create a `common` package to conceal a dependency cycle.
- If two packages always require coordinated changes and cannot expose a stable
  contract, consider merging them.

Package dependencies must match declared `package.xml` and CMake dependencies.
Do not rely on transitive dependencies or include another package's internal
headers.

## Weak Reasons to Create a Package

Do not split merely because:

- a new class, node, executable, controller, or test was added;
- the file count or one header became large;
- namespaces differ;
- a small enum or configuration type is shared;
- a backend or reuse case might exist someday;
- every class seems to deserve an interface;
- the repository would look more architectural;
- separate package names appear cleaner in a diagram.

Try a directory, an internal CMake target, a source-file split, or a clearer
namespace first.

Avoid speculative `core`, `common`, `utils`, `interfaces`, factory, and plugin
packages. These names must correspond to a demonstrated consumer or framework
boundary.

## Split and Merge Checklist

Create a new package only when at least one question has a concrete yes:

1. Does it isolate an external dependency from consumers that do not need it?
2. Must it build, install, release, or deploy independently?
3. Do multiple packages consume a stable public API?
4. Is it a ROS interface or plugin-discovery boundary?
5. Is it an optional hardware, simulator, visualization, or solver backend?
6. Is it already reused by another repository or project?
7. Does it need independent versioning or platform support?

Reconsider an existing split when:

- the packages change together in nearly every PR;
- they include each other's internal headers;
- they require a circular dependency;
- a small `common` package exists only to move types between them;
- one package has no independent meaning, deployment, or consumer;
- configuration plumbing exceeds the useful public API.

Prefer fewer cohesive packages. Split when a real build, dependency,
deployment, plugin, interface, or demonstrated reuse boundary appears.
