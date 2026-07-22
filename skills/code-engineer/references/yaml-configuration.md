# YAML Configuration

Use this reference when implementing or inspecting YAML configuration with
`yaml-cpp`, especially controller gains, WBC tasks, FSM parameters, hardware
limits, thresholds, timeouts, and other runtime settings.

Loading this reference does not authorize tests, validation, or review.

## Contents

- [Core Boundary](#core-boundary)
- [Reuse One Small Parser](#reuse-one-small-parser)
- [Keep Domain Config Typed](#keep-domain-config-typed)
- [Split Validation Responsibility](#split-validation-responsibility)
- [Required, Optional, And Physical Meaning](#required-optional-and-physical-meaning)
- [Runtime And Errors](#runtime-and-errors)
- [Avoid](#avoid)

## Core Boundary

Parse YAML once during initialization, convert it into project-owned typed
configuration, validate it, and pass the trusted result to the owning subsystem.

Do not spread `YAML::Node` traversal and `.as<T>()` calls across controllers,
FSM states, planners, hardware classes, and ROS wrappers.

> Centralize YAML mechanics. Keep configuration meaning with its subsystem.

## Reuse One Small Parser

Prefer one reusable utility such as `YamlParser`. Reuse the repository's
existing equivalent instead of adding another parser or free-function family.

The common parser may own:

- file loading and the root node;
- dotted-key or scoped traversal;
- required and optional typed extraction;
- normalization of `yaml-cpp` exceptions;
- file and full key-path context in errors;
- common scalar, sequence, and shape checks.

```cpp
class YamlParser
{
public:
  static Result<YamlParser> Load(const std::filesystem::path& path);

  template <typename T>
  Result<T> GetRequired(std::string_view key_path) const;

  template <typename T>
  Result<T> GetOptional(
      std::string_view key_path,
      const T& default_value) const;
};
```

Match the repository's `Status`, `Result`, or exception convention. Normalize
library exceptions at this boundary; do not expose raw YAML nodes or
`yaml-cpp` exceptions through control-domain APIs.

## Keep Domain Config Typed

The shared parser does not own every schema. Each subsystem defines a small
typed configuration object and a loader that knows its field meaning.

```cpp
struct TaskGains
{
  Eigen::VectorXd kp;
  Eigen::VectorXd kd;
};

Result<TaskGains> LoadTaskGains(
    const YamlParser& yaml,
    std::string_view key_prefix,
    Eigen::Index task_dimension);
```

Controllers and FSM states receive `TaskGains`, `FsmConfig`, or another
project-owned type. They do not receive a file path, parser, or raw YAML node to
extract settings during execution.

Keep key names and semantic validation near the domain loader. Do not grow the
shared parser into a global configuration singleton that knows every task,
state, controller, and hardware schema.

## Split Validation Responsibility

The common parser validates mechanics:

- file and syntax;
- required-path existence;
- node type and requested conversion;
- common sequence or fixed-size shape.

The subsystem loader validates meaning:

- dimensions and finite values;
- valid gain, threshold, timeout, and limit ranges;
- lower/upper ordering;
- recognized joint, task, frame, or state names;
- expected keys in its owned section when practical;
- consistency between coupled fields.

Do not infer domain rules from a generic key name. Do not make every subsystem
reimplement missing-key and conversion diagnostics.

## Required, Optional, And Physical Meaning

A value is required when silently choosing it could change behavior, safety,
tuning, or experimental meaning. Gains, hardware limits, FSM thresholds, joint
ordering, and model frames are normally required unless a default is an explicit
part of the contract.

Use an optional value only when its default is stable, documented, and safe for
every caller. Avoid scattered `node[key].as<T>(default)` calls that hide typos or
accidental omissions.

Apply `control-data-conventions.md` when units, frames, ordering, or actuator
side matter:

- use canonical SI values internally;
- encode non-canonical boundary units in key names;
- make vector ordering and dimensions explicit;
- do not broadcast scalar gains unless the schema explicitly supports it;
- reject non-finite values before configuration becomes trusted.

## Runtime And Errors

Never open or traverse YAML, allocate configuration vectors, or handle parsing
exceptions in `Update()`, `Step()`, hardware `Read()`/`Write()`, or another
required real-time path.

For live reconfiguration, parse and validate a complete candidate off the
control path, then replace the typed configuration at a defined cycle boundary.
Do not mutate individual fields asynchronously.

An error should identify:

- source file and full key path;
- missing, wrong type/shape, or violated domain constraint;
- expected unit, dimension, or range;
- received value when concise and safe to print.

Fail initialization instead of partially applying a mixture of old, defaulted,
and new fields.

## Avoid

- multiple parser utilities for the same repository;
- mutable process-wide configuration;
- controllers or FSM states that own YAML mechanics;
- passing `YAML::Node` through public domain APIs;
- parsing or allocation in the control loop;
- implicit precedence among YAML, ROS parameters, and environment variables;
- reflection or registration frameworks for a small set of configs.
