#!/usr/bin/env python3
"""Install the docs-gardener repo harness template into a repository."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def iter_template_files(template_root: Path) -> list[Path]:
    return sorted(path for path in template_root.rglob("*") if path.is_file())


def destination_for_template(target: Path, relative: Path) -> Path:
    if relative == Path("AGENTS.md"):
        return target / "AGENTS.md"
    return target / "docs" / relative


def install_harness(target: Path, dry_run: bool) -> int:
    skill_root = Path(__file__).resolve().parents[1]
    template_root = skill_root / "templates"

    if not template_root.is_dir():
        raise SystemExit(f"Template directory not found: {template_root}")

    target = target.resolve()
    if not target.exists():
        raise SystemExit(f"Target does not exist: {target}")
    if not target.is_dir():
        raise SystemExit(f"Target is not a directory: {target}")

    copied = 0
    skipped = 0

    for source in iter_template_files(template_root):
        relative = source.relative_to(template_root)
        destination = destination_for_template(target, relative)
        output_relative = destination.relative_to(target)

        if destination.exists():
            print(f"skip existing: {output_relative}")
            skipped += 1
            continue

        print(f"create: {output_relative}")
        copied += 1

        if dry_run:
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    print(f"done: {copied} file(s) to write, {skipped} skipped")
    if dry_run:
        print("dry run only; no files were changed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install a lightweight AGENTS.md and docs harness into a repository."
    )
    parser.add_argument(
        "target",
        type=Path,
        help="Repository root to receive AGENTS.md and lightweight docs templates.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing files.",
    )
    args = parser.parse_args()
    return install_harness(args.target, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
