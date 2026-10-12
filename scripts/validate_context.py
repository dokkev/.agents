#!/usr/bin/env python3
"""Check skill metadata, entrypoint budgets, and local reference discovery.

This is a static packaging check, not an evaluation of agent behavior.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1] / "skills"
SKILL_WORD_LIMITS = {
    "architecture-designer": 700,
    "code-engineer": 850,
    "docs-gardener": 650,
}
REFERENCE_RE = re.compile(r"\breferences/[\w./-]+\.md\b")


def validate_skill(skill_dir: Path, word_limit: int) -> list[str]:
    """Validate one entrypoint against the references shipped beside it."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill_file}: missing entrypoint"]

    text = skill_file.read_text(encoding="utf-8")
    errors: list[str] = []
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.S)
    if frontmatter is None:
        errors.append(f"{skill_file}: missing YAML frontmatter")
    else:
        # Check the simple metadata format used here; do not implement YAML.
        metadata = frontmatter.group(1)
        for field in ("name", "description"):
            if not re.search(rf"^{field}:[ \t]*\S", metadata, re.M):
                errors.append(f"{skill_file}: missing {field}")

    words = len(text.split())
    if words > word_limit:
        errors.append(f"{skill_file}: {words} words exceeds {word_limit}")

    mentioned = set(REFERENCE_RE.findall(text))
    references = {
        path.relative_to(skill_dir).as_posix()
        for path in (skill_dir / "references").rglob("*.md")
        if path.is_file()
    }
    for path in sorted(mentioned - references):
        errors.append(f"{skill_file}: missing reference {path}")
    for path in sorted(references - mentioned):
        errors.append(f"{skill_dir / path}: not discoverable directly from SKILL.md")
    return errors


def main() -> int:
    errors = [
        error
        for name, limit in SKILL_WORD_LIMITS.items()
        for error in validate_skill(SKILLS_ROOT / name, limit)
    ]
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"validated metadata, budgets, and reference paths for {len(SKILL_WORD_LIMITS)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
