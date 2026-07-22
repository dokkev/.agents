# Codex Robotics Skills

Reusable Codex skills for robotics and research-software development. The
collection keeps repository knowledge separate from reusable workflows and
loads detailed references only when a task needs them.

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

## Included skills

| Skill | Purpose |
| --- | --- |
| `architecture-designer` | Design ownership, dependencies, runtime flow, lifecycle, and ROS 2 or hardware boundaries before implementation. |
| `code-engineer` | Implement, review, test, or validate code in the mode explicitly requested by the user. It selects only relevant references and does not automatically add tests or reviews. |
| `docs-gardener` | Maintain a minimal repository harness and keep code direction and compilation knowledge accurate. |

Codex can select a skill from the request automatically. In the CLI or IDE,
invoke one explicitly with `$skill-name`:

```text
$architecture-designer Design the ownership and runtime flow for this controller.
$code-engineer Implement the approved controller interface.
$code-engineer Review this diff for numerical and concurrency issues.
$docs-gardener Create the minimal repository harness.
```

## Repository harness

These global skills define reusable workflows. Each project keeps its own facts
in a small local harness:

| File | Responsibility |
| --- | --- |
| `AGENTS.md` | Short repository-specific rules and links to authoritative documents. |
| `docs/ARCHITECTURE.md` | Accepted code direction, ownership, dependencies, runtime flow, and public boundaries. |
| `docs/COMMANDS.md` | Source, build, install, and output locations plus exact compilation commands. |

Ask `$docs-gardener` to create or maintain this harness for a project. It does
not create `PLANS.md` or `DECISIONS.md` by default.
