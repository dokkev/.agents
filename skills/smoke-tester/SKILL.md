---
name: smoke-tester
description: Run focused build, test, launch, startup, CLI, or runtime smoke checks and report actionable failures. Use when the user asks to validate a change, check whether a refactor still works, debug failing local checks, or run the narrowest useful verification loop.
---

# Smoke Tester

Validate changes with the narrowest useful feedback loop.

Expand only when the first failure, dependency graph, or user request requires it.

This skill runs validation commands. It should not design a broad test strategy unless the user asks for that; use `test-designer` for test planning.

## Workflow

1. Identify what changed and which package, app, binary, route, launch file, node, module, or command owns the behavior.
2. Read the repo harness when present:

   * `AGENTS.md`
   * `docs/COMMANDS.md`
   * `docs/ARCHITECTURE.md`
   * `docs/DECISIONS.md`
   * `docs/PLANS.md`
3. Choose the smallest meaningful check:

   * lint
   * typecheck
   * unit test
   * package build
   * CLI invocation
   * config parse
   * app startup
   * launch smoke
   * fake-hardware run
   * dry-run
   * log replay
   * focused integration test
4. Run commands from the correct repo root with the project environment loaded when needed.
5. Use timeouts for commands that may hang.
6. Capture the first actionable failure, not pages of noise.
7. Fix only when the user explicitly asked for fixes.
8. Re-run the narrowest check after a fix.

## Harness context

Use the micro-harness docs as maps:

* `AGENTS.md` — repo setup, local rules, and validation expectations
* `docs/COMMANDS.md` — source of truth for build, test, lint, run, dry-run, and smoke commands
* `docs/ARCHITECTURE.md` — owning package, module boundaries, and runtime wiring
* `docs/DECISIONS.md` — design decisions that may affect validation choice
* `docs/PLANS.md` — current priorities, non-goals, and deferred work

If commands are stale, missing, or too broad, report that and suggest a `docs-gardener` update.

If a repo also has `docs/TESTING.md`, use it as an additional source, but do not require it.

## Check selection

Choose the smallest check that meaningfully exercises the changed behavior.

### Code-only library change

Use:

* targeted unit test
* package build
* typecheck or lint when relevant

### Numerical or utility change

Use:

* deterministic unit test
* known input/output example
* package build
* focused regression test if available

### Parser, encoder, decoder, or protocol change

Use:

* deterministic unit test
* golden input/output test
* config or packet parse check
* package build

### Config or wiring change

Use:

* config parse
* startup
* launch smoke
* route or node registration
* plugin discovery
* dependency injection check

### CLI or script change

Use:

* `--help`
* representative success case
* representative failure-path case when cheap

### Frontend change

Use:

* app startup
* route render
* key interaction
* console error check
* screenshot when tooling exists

### Backend or API change

Use:

* service startup
* handler test
* schema or contract test
* representative request when cheap

### Build-system change

Use:

* minimal build target first
* then dependent package if necessary

### Hardware-facing or physical-system change

Prefer safe validation before real hardware:

* build
* unit test
* fake hardware
* dry-run
* simulation
* log replay
* motors disabled
* limited-power or limited-scope check when explicitly requested

Do not claim hardware validation unless real hardware was actually tested.

## Failure handling

When a command fails:

1. Identify the first actionable error.
2. Preserve enough context to act.
3. Avoid dumping long unrelated logs.
4. Identify the likely owner:

   * changed file
   * package
   * dependency
   * environment
   * stale command
   * missing setup
   * flaky external service
5. Recommend the next smallest check or fix path.

Do not hide command failures behind vague summaries.

## Output format

Always report:

```text
Validated scope:
Commands run:
Result:
First actionable failure:
Likely owner:
Next recommended check:
Residual risk:
```

If everything passes, explicitly say there were no blocking failures and name what was not exercised.

## Rules

* Prefer targeted checks over full-suite runs unless the change is broad or the user asks for full validation.
* Use timeouts for commands that can hang.
* Run commands from the correct repo root.
* Load the project environment when needed.
* Do not treat warnings as failures unless they affect correctness, startup, runtime behavior, or future debugging.
* Keep logs concise; include the first relevant error and enough context to act.
* Do not claim a test, build, launch, simulation, dry-run, or hardware run was performed unless it was actually performed.
* If no meaningful command can be found, say so and recommend updating `docs/COMMANDS.md`.
