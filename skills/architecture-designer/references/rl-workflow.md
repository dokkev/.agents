# RL Workflow Architecture

Use this reference when designing reinforcement-learning project structure,
Isaac Lab task organization, environment ownership, observation/action/reward
flow, training and evaluation boundaries, or policy-learning workflows.

## Core Contract

Treat Isaac Lab as the default foundation for RL research projects unless the
repository explicitly uses another framework.

Before introducing a new RL abstraction, utility, environment mechanism,
wrapper, runner, randomization layer, sensor pipeline, or training workflow,
check the current official Isaac Lab documentation and existing implementations.
Isaac Lab is actively developed; do not rely on remembered APIs, old Orbit
patterns, or stale examples.

Prefer documentation matching the project's installed Isaac Lab version. Use
newer `main` or `develop` documentation only when intentionally investigating a
newer behavior or migration.

Reuse Isaac Lab functionality when it already solves the problem. Do not rebuild
framework features locally unless the existing mechanism cannot satisfy a
concrete project requirement.

Follow the current Isaac Lab external-project and task layout by default. Do not
invent a parallel repository structure merely for stylistic preference.

## Design The Codebase Around The RL Flow

The top-level architecture should make the learning loop easy to trace:

```text
Task / Environment
    -> observation
Policy
    -> action
Task action processing
    -> simulator
Simulator
    -> next physical state
Task / Environment
    -> reward + termination + next observation

Rollout / Runner
    -> trajectories
RL Algorithm
    -> policy update

Evaluation
    -> same task contract
    -> checkpoint + metrics
```

A reader should be able to locate observation, action, reward, termination,
reset, training, and evaluation ownership without following several layers of
registries, wrappers, or forwarding classes.

## Follow Isaac Lab Structure First

For Isaac Lab projects, first inspect the current official external-project
examples, task templates, and built-in tasks. Keep project layout recognizable
to an Isaac Lab user.

Prefer the framework's current conventions for:

- external project and Python package layout;
- task registration and environment configuration;
- Direct or Manager-based environment organization;
- agent configuration;
- training and play entrypoints;
- RL-library wrappers;
- logging, checkpoint, video, and evaluation utilities;
- domain randomization, events, sensors, actuators, commands, and curriculum;
- distributed execution or tuning when the project actually needs it.

Do not hard-code one historical Isaac Lab directory tree into project policy.
The framework evolves. Follow the structure documented for the installed
version unless the repository has an explicit local convention.

## Choose Direct Or Manager-Based Deliberately

Do not select Manager-based environments merely because they appear more
architected. Do not select Direct environments merely to avoid learning Isaac
Lab's existing managers.

Prefer a Direct workflow when a task is research-specific, has one main variant,
changes frequently, or benefits from keeping observation, reward, termination,
and reset logic visible in one direct implementation.

Prefer a Manager-based workflow when the project has real reuse pressure across
task variants, shared observation/reward/action terms, substantial curriculum or
randomization composition, or configuration-driven experiment families.

Use the simplest Isaac Lab workflow that matches the current research problem.
Do not create a custom framework between the project and Isaac Lab.

## Assign Clear Ownership

Keep these responsibilities distinct even when Isaac Lab provides the concrete
base classes or managers:

| Component | Owns |
| --- | --- |
| simulator / scene | physical state, physics stepping, contacts, rendering, and simulated sensors |
| task / environment | MDP semantics: observation, action interpretation, reward, termination, reset, goals, and episode state |
| policy | observation-to-action mapping |
| RL algorithm | losses, returns or advantages, optimization, and policy updates |
| runner / training entrypoint | rollout and update orchestration, checkpoint cadence, and experiment lifecycle |
| evaluator / play workflow | checkpoint loading, evaluation episodes, metrics, and optional recording |
| logger | observation and reporting, not domain decisions |

The task should not know whether PPO, SAC, RSL-RL, RL-Games, SKRL, or another
learning algorithm is updating the policy. The simulator should not own reward,
termination, or task success semantics.

## Keep The MDP Definition Visible

For each task, make it straightforward to find:

```text
observation
policy action
command / action processing
reward
termination
reset
randomization
```

Do not hide a simple task behind project-owned manager frameworks, registries,
term factories, or generic configuration systems when Isaac Lab already
provides the required mechanism or the task is clearer as direct code.

A reward or observation definition should be understandable without opening a
large chain of unrelated files.

## Keep Action And Observation Paths Direct

Each transformation should have one clear owner.

```text
simulated state
    -> task observation
    -> policy
    -> task action interpretation
    -> actuator / controller command
    -> simulator
```

Avoid duplicated normalization, clipping, scaling, filtering, frame conversion,
or command transformation across runners, environments, wrappers, and
actuators. If Isaac Lab or the selected RL-library wrapper owns a transformation,
do not silently duplicate it in project code.

The same rule applies to observations: keep source quantities, normalization,
stacking, history, privileged observations, and policy-visible observations
traceable.

## Keep Episode State With The Task

Task-specific temporal state belongs with the environment or the Isaac Lab
component that semantically owns it, for example:

- episode progress;
- previous action when needed by the task;
- sampled goals or commands;
- success and termination state;
- task-specific curriculum state;
- per-environment randomized task parameters.

Do not spread one episode concept across the simulator, runner, and policy
configuration merely because each layer can access the tensors.

## Training And Evaluation Share One Task Contract

Do not maintain separate copies of task dynamics or MDP logic for training and
evaluation.

Training and evaluation should use the same task definition unless the research
question explicitly requires a different environment. Evaluation may change
runner behavior such as deterministic actions, seeds, environment count,
checkpoint selection, recording, or metric collection without duplicating task
logic.

Prefer Isaac Lab's current train/play workflows and RL-library wrappers before
writing project-specific alternatives.

## Do Not Reinvent Isaac Lab

Before adding project-owned infrastructure, search the current Isaac Lab
reference architecture, API documentation, tutorials, and built-in examples for
an existing solution.

Common areas to check first include:

- scene and asset configuration;
- sensors and actuators;
- observations and actions;
- rewards and terminations;
- events and domain randomization;
- commands and curriculum;
- environment registration;
- RL-library wrappers;
- train and play entrypoints;
- checkpoint and logging utilities;
- multi-GPU, distributed, or Ray workflows.

Use custom infrastructure only when a concrete requirement remains after this
check. Keep the custom layer narrow and visibly connected to the framework
boundary it extends.

## Keep Framework And Research Logic Distinguishable

Framework integration code should make Isaac Lab requirements visible without
letting framework mechanics obscure the research contribution.

Keep task-specific research logic near the task. Keep reusable project-domain
assets, models, or utilities in clearly owned modules. Keep generic training
machinery in Isaac Lab or the chosen learning library when they already own it.

A useful test is:

> If this project-owned RL layer were deleted, would Isaac Lab or the learning
> library already provide the same behavior?

If yes, prefer the framework implementation.

## Scope Boundary

This reference defines the large-scale RL workflow and ownership model. It does
not prescribe PPO/SAC mathematics, distributed execution internals, simulator
backend architecture, or morphology co-design loops.

Add separate references when those concerns become substantial, such as:

- `simulation-workflow.md` for simulation backend and scene architecture;
- `co-design-workflow.md` for morphology/design optimization loops;
- `ray-workflow.md` for distributed execution and tuning.
