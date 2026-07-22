#!/usr/bin/env python3
"""List or print exact H2 sections from a Markdown reference."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def heading_title(raw_title: str) -> str:
    """Remove optional Markdown closing hashes from a heading title."""
    return re.sub(r"\s+#+\s*$", "", raw_title).strip()


def markdown_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return headings outside fenced code as (line index, level, title)."""
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
            headings.append(
                (
                    index,
                    len(heading_match.group(1)),
                    heading_title(heading_match.group(2)),
                )
            )

    return headings


def h2_ranges(
    lines: list[str], headings: list[tuple[int, int, str]]
) -> list[tuple[str, int, int]]:
    """Return each H2 title and its half-open line range."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview a Markdown section map or read exact H2 sections."
    )
    parser.add_argument("reference", type=Path, help="Markdown file to read")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--list", action="store_true", help="print the document title and H2 headings"
    )
    selection.add_argument(
        "--section",
        action="append",
        metavar="TITLE",
        help="print an exact H2 section; repeat to select more than one",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        text = args.reference.read_text(encoding="utf-8")
    except OSError as error:
        print(f"error: cannot read {args.reference}: {error}", file=sys.stderr)
        return 2

    lines = text.splitlines(keepends=True)
    headings = markdown_headings(lines)
    ranges = h2_ranges(lines, headings)

    if args.list:
        title = next((title for _, level, title in headings if level == 1), args.reference.name)
        print(f"# {title}")
        for section_title, _, _ in ranges:
            print(f"- {section_title}")
        return 0

    sections_by_title: dict[str, list[tuple[int, int]]] = {}
    for section_title, start, end in ranges:
        sections_by_title.setdefault(section_title, []).append((start, end))

    selected_text: list[str] = []
    for requested_title in dict.fromkeys(args.section or []):
        matches = sections_by_title.get(requested_title, [])
        if not matches:
            print(f"error: H2 section not found: {requested_title!r}", file=sys.stderr)
            print("available H2 sections:", file=sys.stderr)
            for section_title, _, _ in ranges:
                print(f"  {section_title}", file=sys.stderr)
            return 2
        if len(matches) > 1:
            print(f"error: duplicate H2 section: {requested_title!r}", file=sys.stderr)
            return 2
        start, end = matches[0]
        selected_text.append("".join(lines[start:end]).rstrip())

    print("\n\n".join(selected_text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
