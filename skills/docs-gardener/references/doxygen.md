# Doxygen API Documentation

Load this reference only for an explicit request to create, revise, or audit
Doxygen-style API documentation.

## Scope

1. Inspect the repository for a `Doxyfile`, generated API-doc target, existing
   comment syntax, and documented visibility policy.
2. Follow the established `///` or `/** ... */` style and the established `@tag`
   or `\tag` convention. Do not reformat unrelated comments for consistency.
3. Prioritize public and protected declarations, extension points, non-obvious
   types, configuration structures, and APIs that cross package or hardware
   boundaries.
4. Document private helpers only when they enforce a non-obvious invariant or
   lifecycle rule. Do not comment every symbol.
5. Place the authoritative contract at the declaration, normally in the header.
   Do not copy the same documentation to the definition.

Do not run Doxygen, change a `Doxyfile`, or add a documentation build target
unless the user also requests validation or documentation-tool setup.

## Useful Contract Content

Document only details that callers or maintainers need:

- purpose and semantics not already obvious from the symbol name;
- parameter meaning, units, coordinate frame, valid range, and nullability;
- return meaning, units, frame, ownership, and sentinel or error values;
- preconditions, postconditions, invariants, and state transitions;
- lifetime and ownership of referenced objects or buffers;
- observable side effects and mutation;
- exceptions or error-reporting behavior;
- thread-safety, blocking behavior, allocation, and real-time restrictions;
- numerical conventions and singular or invalid cases.

Use `@brief`, `@param`, `@tparam`, `@return`, `@retval`, `@throws`, `@pre`,
`@post`, `@note`, and `@warning` only when they add applicable information.
Omit empty or redundant sections.

## Quality Rules

- Describe the contract, not the implementation sequence.
- Do not restate a function signature in prose.
- Do not invent guarantees that the code, tests, or existing documentation do
  not support. Mark unresolved behavior or ask the user when it matters.
- Keep terminology aligned with `ARCHITECTURE.md` and the public API.
- Preserve exact units and frame names. Never replace them with vague words such
  as "value," "position," or "velocity" when ambiguity is possible.
- Keep comments current with the declaration in the same change.
- Use `@warning` for genuine hazards, not ordinary usage notes.
- Prefer a short useful contract over a long generic block.
- Do not change logic, signatures, visibility, or build configuration unless the
  user separately requests those changes.

## Example

```cpp
/**
 * @brief Computes the commanded joint torque for one control cycle.
 *
 * @param state Accepted state in model order and canonical joint-side SI units.
 * @param[out] tau_cmd Caller-owned joint-side torque storage, in newton-meters.
 * @retval UpdateStatus::kOk `tau_cmd` contains a complete command.
 * @retval UpdateStatus::kInvalidState `state` violates the controller contract;
 *         `tau_cmd` is unchanged.
 * @pre `tau_cmd.size()` equals the configured actuated-joint dimension.
 */
UpdateStatus ComputeTorque(
    const RobotState& state,
    Eigen::Ref<Eigen::VectorXd> tau_cmd);
```

Use the example as a quality bar, not a mandatory template. Short accessors may
need no comment, while stateful, numerical, concurrent, or hardware-facing APIs
may require more precise contracts. Claim allocation-free, non-blocking, thread-
safe, or real-time behavior only when the implementation and lifecycle actually
establish that guarantee.
