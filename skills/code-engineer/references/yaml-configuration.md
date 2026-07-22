# YAML Configuration

Use this reference when implementing or inspecting YAML configuration with
`yaml-cpp`, especially controller gains, WBC tasks, FSM parameters, hardware
limits, thresholds, timeouts, and other runtime settings.

Loading this reference does not authorize tests, validation, or review.

## Section Map

- [Core Contract](#core-contract)
- [Start With One Typed Loader](#start-with-one-typed-loader)
- [Extract Shared Mechanics Only After Repetition](#extract-shared-mechanics-only-after-repetition)
- [Keep Domain Config Typed](#keep-domain-config-typed)
- [Split Validation Responsibility](#split-validation-responsibility)
- [Required, Optional, And Physical Meaning](#required-optional-and-physical-meaning)
- [Runtime And Errors](#runtime-and-errors)
- [Avoid](#avoid)

## Core Contract

Parse YAML once during initialization, convert it into project-owned typed
configuration, validate it, and pass the trusted result to the owning subsystem.
Start with one direct typed loader for the configuration being added.

Do not spread `YAML::Node` traversal and `.as<T>()` calls across controllers,
FSM states, planners, hardware classes, and ROS wrappers.

> Keep YAML at the initialization boundary. Extract shared mechanics only after
> real duplication appears.

## Start With One Typed Loader

For one configuration surface, prefer one domain loader over a generic parser
class:

```cpp
Result<ControllerConfig> LoadControllerConfig(
    const YAML::Node& root,
    const std::filesystem::path& source_path);
```

Let that loader own the keys, expected shapes, units, defaults, and domain
validation for `ControllerConfig`. Normalize `yaml-cpp` exceptions there and
return the repository's existing `Status`, `Result`, or exception type. Do not
pass raw YAML nodes into the controller.

Reuse an established repository parser when one already exists and remains
smaller than adding a competing path. Do not create `YamlParser`, a registry,
or a free-function family for a hypothetical second configuration.

## Extract Shared Mechanics Only After Repetition

Extract a small shared reader only when two or more real loaders repeat enough
mechanics or diagnostic behavior to justify it. Shared mechanics may include:

- file loading and the root node;
- dotted-key or scoped traversal;
- required and optional typed extraction;
- normalization of `yaml-cpp` exceptions;
- file and full key-path context in errors;
- common scalar, sequence, and shape checks.

Keep the extracted utility mechanical. It must not know controller, task, FSM,
or hardware schemas. A little repeated YAML traversal is preferable to a
premature global configuration framework.

## Keep Domain Config Typed

Each subsystem defines a small typed configuration object and a loader that
knows its field meaning.

```cpp
struct TaskGains
{
  Eigen::VectorXd kp;
  Eigen::VectorXd kd;
};

Result<TaskGains> LoadTaskGains(
    const YAML::Node& root,
    std::string_view key_prefix,
    Eigen::Index task_dimension);
```

Controllers and FSM states receive `TaskGains`, `FsmConfig`, or another
project-owned type. They do not receive a file path, shared reader, or raw YAML
node to extract settings during execution.

Keep key names and semantic validation near the domain loader. Do not grow the
shared parser into a global configuration singleton that knows every task,
state, controller, and hardware schema.

## Split Validation Responsibility

The YAML boundary validates mechanics:

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

- a generic parser or schema registry before real duplication exists;
- competing parser utilities after a shared repository boundary exists;
- mutable process-wide configuration;
- controllers or FSM states that own YAML mechanics;
- passing `YAML::Node` through public domain APIs;
- parsing or allocation in the control loop;
- implicit precedence among YAML, ROS parameters, and environment variables;
- reflection or registration frameworks for a small set of configs.
