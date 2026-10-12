"""Focused regression checks for the lightweight context validator."""

import tempfile
import unittest
from pathlib import Path

from validate_context import validate_skill


class ContextValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.skill = Path(self.temp.name) / "example"
        (self.skill / "references").mkdir(parents=True)
        self.entry = self.skill / "SKILL.md"
        self.entry.write_text(
            "---\nname: example\ndescription: A focused example.\n---\n"
            "Read `references/example.md` when needed.\n",
            encoding="utf-8",
        )
        (self.skill / "references/example.md").write_text(
            "# Example\n" + "Reference detail.\n" * 110, encoding="utf-8"
        )

    def test_reference_needs_no_section_ritual_or_bundled_reader(self):
        self.assertEqual(validate_skill(self.skill, 100), [])

    def test_deleted_or_renamed_reference_is_reported(self):
        (self.skill / "references/example.md").unlink()
        errors = validate_skill(self.skill, 100)
        self.assertTrue(any("missing reference references/example.md" in e for e in errors))

    def test_undiscoverable_reference_is_reported(self):
        (self.skill / "references/extra.md").write_text("# Extra\n", encoding="utf-8")
        errors = validate_skill(self.skill, 100)
        self.assertTrue(any("extra.md: not discoverable" in e for e in errors))

    def test_metadata_and_budget_remain_required(self):
        self.entry.write_text("# No metadata\n", encoding="utf-8")
        self.assertTrue(any("missing YAML frontmatter" in e for e in validate_skill(self.skill, 100)))
        self.entry.write_text("---\nname: example\n---\n", encoding="utf-8")
        self.assertTrue(any("missing description" in e for e in validate_skill(self.skill, 100)))
        self.assertTrue(any("exceeds 1" in e for e in validate_skill(self.skill, 1)))

    def test_missing_entrypoint_is_reported_without_traceback(self):
        self.entry.unlink()
        self.assertEqual(len(validate_skill(self.skill, 100)), 1)
        self.assertIn("missing entrypoint", validate_skill(self.skill, 100)[0])


if __name__ == "__main__":
    unittest.main()
