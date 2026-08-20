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
| `code-engineer` | Default skill for code-related implementation, review, test, and validation work in the requested mode. |
| `docs-gardener` | Maintain a minimal repository harness and keep its architecture map and compilation knowledge accurate. |

Codex can select a skill from the request automatically. In the CLI or IDE,
invoke one explicitly with `$skill-name`:

```text
$architecture-designer Design the ownership and runtime flow for this controller.
$code-engineer Implement the approved controller interface.
$code-engineer Review this diff for numerical and concurrency issues.
$docs-gardener Create the minimal repository harness.
```

## Sub-agent execution

Default to one agent. Delegate only bounded, independent work with an explicit
mode, deliverable, and non-overlapping write ownership. Delegation does not
expand the user's authority, and the parent agent remains responsible for
integration and the final result.

Review independence is project-specific. A repository may allow self-review or
require review by a separate non-author agent. Follow the closest repository
instructions or explicit user request, and never describe self-review as
independent review.

## Repository harness

These global skills define reusable workflows. Each project keeps its own facts
in a small local harness:

| File | Responsibility |
| --- | --- |
| `AGENTS.md` | Short repository-specific working rules and links to authoritative documents. |
| `docs/ARCHITECTURE.md` | Navigational map of the current accepted codebase: canonical entry points, ownership, dependencies, runtime flow, public boundaries, and intentional absences. |
| `docs/COMMANDS.md` | Source, build, install, and output locations plus exact compilation commands. |

The architecture document is primarily a map of the code that currently exists.
When a migration is incomplete, it should distinguish verified current structure
from the accepted target rather than presenting proposed architecture as current
reality.

Ask `$docs-gardener` to create or maintain this harness for a project. It does
not create `PLANS.md` or `DECISIONS.md` by default.

## Validate context contracts

Run the repository check after changing a skill or reference:

```bash
python3 scripts/validate_context.py
```

It enforces skill word budgets, direct reference discovery, unique section
headings, bounded `Core Contract` sections, complete section maps, and identical
bundled section readers.
