# YAML Configuration

Use this standard when implementing or modifying YAML configuration with
`yaml-cpp`, especially for controller gains, WBC tasks, FSM parameters,
hardware limits, thresholds, timeouts, and other robot runtime settings.

## Contents

- [Core Principle](#core-principle)
- [Use One Parsing Utility](#use-one-parsing-utility)
- [Keep Domain Configuration Typed](#keep-domain-configuration-typed)
- [Separate Mechanical and Semantic Validation](#separate-mechanical-and-semantic-validation)
- [Required and Optional Values](#required-and-optional-values)
- [Preserve Physical Meaning](#preserve-physical-meaning)
- [Keep YAML Out of Runtime Logic](#keep-yaml-out-of-runtime-logic)
- [Report Actionable Errors](#report-actionable-errors)
- [Test the Configuration Boundary](#test-the-configuration-boundary)
- [Avoid Overgeneralization](#avoid-overgeneralization)
- [Review Rules](#review-rules)

## Core Principle

Parse YAML once at an initialization boundary, convert it into project-owned
typed configuration, validate it, and pass the trusted result to the subsystem
that uses it.

Do not spread direct `YAML::Node` traversal and `.as<T>()` calls across
controllers, FSM states, planners, hardware classes, and ROS wrappers.

> Centralize YAML mechanics. Keep configuration meaning with the subsystem that
> owns it. Run control code on typed, validated data.

## Use One Parsing Utility

Prefer one small reusable utility, such as `YamlParser`, for the mechanical
behavior shared by all YAML configuration readers. Reuse the repository's
existing equivalent instead of adding another parser or free-function family.

The utility should normally own:

- loading one file and retaining its root node;
- traversing a key path or scoped subsection;
- required and optional typed extraction;
- normalization of `yaml-cpp` exceptions;
- source file and key-path context in errors;
- common scalar and sequence shape checks.

A minimal API may look like:

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

Match the repository's established `Status`, `Result`, or exception convention.
If `yaml-cpp` throws, catch and normalize its exceptions at this boundary. Do
not let library-specific exceptions or `YAML::Node` become part of controller or
FSM APIs.

## Keep Domain Configuration Typed

The shared parser is not the owner of every configuration schema. Each
subsystem should define a small typed configuration object for the values it
uses.

```cpp
struct TaskGains
{
  Eigen::VectorXd kp;
  Eigen::VectorXd kd;
};

struct ContactFsmConfig
{
  double force_threshold;
  double transition_timeout;
};
```

A domain loader uses `YamlParser` to construct and validate the object:

```cpp
Result<TaskGains> LoadTaskGains(
    const YamlParser& yaml,
    std::string_view key_prefix,
    Eigen::Index task_dimension);
```

Controllers and FSM states should receive `TaskGains`, `ContactFsmConfig`, or
another project-owned type. They should not receive a file path, parser, or raw
YAML node merely to extract their own settings later.

Keep key names and semantic validation near the domain loader. Do not grow the
shared parser into a central class that knows every controller, state, task, and
hardware schema.

## Separate Mechanical and Semantic Validation

`YamlParser` validates YAML mechanics:

- the file can be opened and parsed;
- a required path exists;
- the node has the requested scalar, sequence, or map form;
- conversion to the requested C++ type succeeds;
- a fixed-size sequence has the requested number of values when specified.

The domain loader validates meaning:

- gains and limits have the expected dimensions;
- values are finite;
- lower and upper limits are ordered;
- stiffness, damping, timeout, and thresholds use valid ranges;
- joint, task, frame, and state names are recognized;
- unexpected keys in an owned schema section are rejected when practical;
- coupled fields are mutually consistent.

Do not make the generic parser guess domain rules from a key name. Do not make
each subsystem reimplement missing-key and type-conversion diagnostics.

## Required and Optional Values

Treat a value as required when silently choosing it could change behavior,
safety, tuning, or the meaning of an experiment. Controller gains, hardware
limits, FSM thresholds, joint ordering, and model frame names are normally
required unless the default is an intentional part of the contract.

Use an optional value only when its default is stable, documented next to the
typed field or loader, and safe for every caller.

```cpp
const auto transition_timeout = yaml.GetRequired<double>(
    "fsm.contact.transition_timeout_s");
if (!transition_timeout.ok()) {
  return transition_timeout.status();
}
config.transition_timeout = transition_timeout.value();

const auto log_decimation = yaml.GetOptional<int>(
    "diagnostics.log_decimation", 10);
if (!log_decimation.ok()) {
  return log_decimation.status();
}
config.log_decimation = log_decimation.value();
```

Do not use `node[key].as<T>(default)` throughout the codebase. It obscures
whether a key was misspelled, omitted intentionally, or converted incorrectly.

## Preserve Physical Meaning

Apply `control-data-conventions.md` to configuration values.

- Use canonical SI values internally.
- Encode a non-canonical boundary unit in the YAML key.
- Keep vector ordering and expected dimensions explicit.
- Do not broadcast a scalar gain into a vector unless that shorthand is an
  explicit part of the schema.
- Do not infer frames, joint order, actuator order, or transmission side from
  vector length.
- Reject non-finite values before producing trusted configuration.

Prefer a nested schema that reflects ownership:

```yaml
wbc:
  hand_task:
    kp: [40.0, 40.0, 40.0]
    kd: [4.0, 4.0, 4.0]

fsm:
  contact:
    force_threshold_N: 2.0
    transition_timeout_s: 0.25
```

Do not silently convert a key whose unit is ambiguous. Rename the key or make
the boundary conversion explicit.

## Keep YAML Out of Runtime Logic

Load and validate configuration during initialization, activation, or an
explicit non-real-time reconfiguration step. Never open a file, traverse YAML,
allocate configuration vectors, or handle parsing exceptions in `Update()`,
`Step()`, a hardware `Read()`/`Write()`, or another required real-time path.

After initialization, runtime code should read stable typed members:

```cpp
command.tau =
    gains_.kp.cwiseProduct(position_error)
    + gains_.kd.cwiseProduct(velocity_error);
```

If live reconfiguration is required, parse and validate a complete candidate
off the control path, then replace the active typed configuration at a defined
cycle boundary using the repository's concurrency conventions. Do not mutate
individual gain or FSM fields asynchronously.

## Report Actionable Errors

Configuration failure should identify:

- the source file;
- the full key path;
- whether the value is missing, has the wrong type or shape, or violates a
  domain constraint;
- the expected type, dimension, unit, or range;
- the received value when it is safe and concise to print.

Prefer:

```text
config/hand.yaml: wbc.hand_task.kp expected 3 finite values, received 2
```

Avoid errors such as `bad conversion`, `invalid config`, or a raw `yaml-cpp`
exception without repository context.

Fail initialization instead of partially applying a configuration. A subsystem
should never run with a mixture of old, defaulted, and newly parsed fields.

## Test the Configuration Boundary

Add focused tests for the shared parser and each non-trivial domain loader.
Cover at least the cases relevant to the change:

- valid required and optional values;
- missing required keys;
- wrong scalar or sequence type;
- wrong vector dimension;
- non-finite and out-of-range values;
- unexpected keys and misspelled optional keys when the schema rejects them;
- unknown joint, frame, task, or FSM state names;
- malformed YAML and missing files;
- defaults that are intentionally supported;
- error messages containing the file and key path.

Use small inline YAML fixtures or dedicated test data consistent with the
repository style. Controller tests should construct typed config directly when
the test is about control behavior rather than parsing.

## Avoid Overgeneralization

One parser utility does not imply one global configuration singleton.

Avoid:

- a mutable process-wide configuration object;
- a parser that owns every subsystem schema;
- templated reflection or registration frameworks for a small set of configs;
- caching arbitrary key lookups in runtime code;
- passing `YAML::Node` through public domain APIs;
- duplicating a new parser class in each package;
- coupling ROS parameters, environment variables, and YAML through implicit
  precedence rules.

If multiple configuration sources are required, define the precedence once at
the application boundary and produce one typed candidate before validation.

## Review Rules

Reject or revise an implementation when:

- direct `yaml-cpp` traversal is duplicated across multiple subsystems;
- a controller or FSM owns YAML parsing instead of typed configuration;
- a missing gain, limit, or threshold silently receives an accidental default;
- parsing or configuration allocation occurs in a control loop;
- vector dimension, finite values, units, or names are not validated;
- errors omit the source file or full key path;
- partial configuration can become active after a failure;
- the shared parser becomes a global owner of domain behavior;
- parser and domain-loader failure paths are not tested.
