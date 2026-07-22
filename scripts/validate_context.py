#!/usr/bin/env python3
"""Validate progressive-loading contracts for the repository skills."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"
SKILL_WORD_LIMITS = {
    "architecture-designer": 700,
    "code-engineer": 850,
    "docs-gardener": 650,
}
LONG_REFERENCE_LINES = 100
MAX_CORE_CONTRACT_WORDS = 220
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def markdown_h2_ranges(text: str) -> list[tuple[str, int, int]]:
    lines = text.splitlines(keepends=True)
    headings: list[tuple[int, int, str]] = []
    fence_character: str | None = None
    fence_length = 0

    for index, line in enumerate(lines):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = None
                fence_length = 0
            continue
        if fence_character is not None:
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            title = re.sub(r"\s+#+\s*$", "", heading_match.group(2)).strip()
            headings.append((index, len(heading_match.group(1)), title))

    ranges: list[tuple[str, int, int]] = []
    for position, (start, level, title) in enumerate(headings):
        if level != 2:
            continue
        end = next(
            (
                next_index
                for next_index, next_level, _ in headings[position + 1 :]
                if next_level <= 2
            ),
            len(lines),
        )
        ranges.append((title, start, end))
    return ranges


def validate_skill(skill_name: str) -> list[str]:
    errors: list[str] = []
    skill_dir = SKILLS_ROOT / skill_name
    skill_file = skill_dir / "SKILL.md"
    skill_text = skill_file.read_text(encoding="utf-8")
    skill_words = len(skill_text.split())

    if skill_words > SKILL_WORD_LIMITS[skill_name]:
        errors.append(
            f"{skill_file}: {skill_words} words exceeds "
            f"{SKILL_WORD_LIMITS[skill_name]}"
        )

    references = sorted((skill_dir / "references").glob("*.md"))
    for reference in references:
        relative_reference = f"references/{reference.name}"
        if relative_reference not in skill_text:
            errors.append(f"{reference}: not discoverable directly from SKILL.md")

        reference_text = reference.read_text(encoding="utf-8")
        ranges = markdown_h2_ranges(reference_text)
        duplicate_headings = [
            title
            for title, count in Counter(title for title, _, _ in ranges).items()
            if count > 1
        ]
        if duplicate_headings:
            errors.append(
                f"{reference}: duplicate H2 headings: {', '.join(duplicate_headings)}"
            )

        if len(reference_text.splitlines()) <= LONG_REFERENCE_LINES:
            continue

        sections = {title: (start, end) for title, start, end in ranges}
        for required_section in ("Section Map", "Core Contract"):
            if required_section not in sections:
                errors.append(f"{reference}: missing {required_section!r} H2 section")

        section_map_range = sections.get("Section Map")
        if section_map_range:
            lines = reference_text.splitlines()
            start, end = section_map_range
            section_map_text = "\n".join(lines[start:end])
            for title in sections:
                if title == "Section Map":
                    continue
                if f"[{title}]" not in section_map_text:
                    errors.append(f"{reference}: Section Map omits {title!r}")

        core_range = sections.get("Core Contract")
        if core_range:
            lines = reference_text.splitlines()
            start, end = core_range
            core_words = len("\n".join(lines[start:end]).split())
            if core_words > MAX_CORE_CONTRACT_WORDS:
                errors.append(
                    f"{reference}: Core Contract has {core_words} words; "
                    f"maximum is {MAX_CORE_CONTRACT_WORDS}"
                )

    return errors


def main() -> int:
    errors: list[str] = []
    for skill_name in SKILL_WORD_LIMITS:
        errors.extend(validate_skill(skill_name))

    reader_files = [
        SKILLS_ROOT / skill_name / "scripts" / "read_reference.py"
        for skill_name in SKILL_WORD_LIMITS
    ]
    reader_contents = [reader.read_bytes() for reader in reader_files]
    if len(set(reader_contents)) != 1:
        errors.append("bundled read_reference.py copies differ")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    reference_count = sum(
        1
        for skill_name in SKILL_WORD_LIMITS
        for _ in (SKILLS_ROOT / skill_name / "references").glob("*.md")
    )
    print(f"validated {len(SKILL_WORD_LIMITS)} skills and {reference_count} references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
