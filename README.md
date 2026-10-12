# Codex Robotics Skills

Reusable Codex skills for robotics and research-software development. Keep the
ordinary implementation path short; load technical references only when their
contracts matter. These instructions are model-agnostic, not a growing list of
workarounds for one model version.

## Install on Ubuntu

Codex discovers user-level skills under `$HOME/.agents/skills`. If
`$HOME/.agents` does not already exist, clone this repository there:

```bash
git clone https://github.com/dokkev/.agents.git "$HOME/.agents"
```

If `$HOME/.agents` already contains other files, keep this repository in a
separate location and symlink its skill directories:

```bash
git clone https://github.com/dokkev/.agents.git "$HOME/.local/share/dokkev-agents"
mkdir -p "$HOME/.agents/skills"

for skill in "$HOME/.local/share/dokkev-agents"/skills/*; do
  ln -sfnT "$skill" "$HOME/.agents/skills/$(basename "$skill")"
done
```

Codex supports symlinked skill directories. It normally detects skill changes
automatically; restart Codex only if an installed or updated skill does not
appear.

## Update

For the direct installation:

```bash
git -C "$HOME/.agents" pull --ff-only
```

For the separate checkout:

```bash
git -C "$HOME/.local/share/dokkev-agents" pull --ff-only
```

## Included Skills

| Skill | Purpose |
| --- | --- |
| `code-engineer` | Scoped implementation, review, or checks; everyday Python defaults are in the entrypoint. |
| `architecture-designer` | Resolve actual ownership, dependency, lifecycle, and runtime-boundary decisions. |
| `docs-gardener` | Maintain authoritative repository facts and create a minimal harness when requested. |

Invoke a skill explicitly with `$skill-name`, or let Codex match the request:

```text
$code-engineer Implement the approved solver adapter. Reuse the existing result type.
$code-engineer Fix the regression and run only its focused test.
$code-engineer Review this diff without making changes or running experiments.
$architecture-designer Decide which component should own the warm-start state.
$docs-gardener Update the architecture map for the implemented boundary change.
```

## Policy and Reference Ownership

The current task and applicable repository instructions set execution scope,
cost/safety limits, and review requirements. `skills/code-engineer/SKILL.md` supplies
fallbacks: one agent, no automatic validation campaign or separate review pass,
existing evidence reused when still valid, and no speculative abstractions.
An explicitly required independent reviewer or check must still be honored.

The entrypoint holds everyday implementation rules, including Python defaults.
`skills/code-engineer/references/python-code-design.md` supplies examples for ambiguous choices.
Control, numerical, hardware, and other domain references retain their technical
contracts. Review and testing references explain how to assess evidence, not
whether another agent or experiment must be launched.

Read relevant sections directly. The bundled `read_reference.py` remains an
optional navigation tool; neither a heading-list command nor a prescribed
`Core Contract`/`Section Map` layout is required to perform a task.

## Repository Harness

Keep project knowledge separate from these reusable skills:

| File | Responsibility |
| --- | --- |
| `AGENTS.md` | Project-specific working rules, execution boundaries, review policy, and links. |
| `docs/ARCHITECTURE.md` | Current entry points, owners, dependencies, scientific/runtime flow, and intentional absences. |
| `docs/COMMANDS.md` | Exact compilation commands and source/build/install/output locations. |

Ask `docs-gardener` to create a harness when needed. Remove irrelevant template
sections. Distinguish current code from proposed or partially implemented design;
do not create documentation simply to complete a standard checklist.

Updating this checkout changes the skills, not previously installed project
`AGENTS.md` files, global instructions, or task templates. Reconcile conflicting
rules there explicitly; the harness installer never overwrites existing files.
In particular, a task template that mandates an independent reviewer still does
so after this update. Installing this repository does not itself install global
Codex instructions outside the skill directories.

## Focused Static Checks

After changing entrypoints or reference paths, run:

```bash
python3 scripts/validate_context.py
```

This checks required metadata presence, entrypoint word budgets, existing
reference paths, and direct reference discovery. It does not mandate reference
section layouts or compare optional reader copies. It does not prove skill
selection, instruction compliance, token savings, or runtime correctness.

When changing the validator, its focused regression checks are:

```bash
python3 scripts/test_validate_context.py
```

No new model benchmark or experiment suite is required by these instructions.
Evaluate real behavior through ordinary tasks and their existing results rather
than repeatedly rerunning expensive work for reassurance.
