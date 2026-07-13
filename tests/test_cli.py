import tempfile
import unittest
from pathlib import Path

from toppaperlearn.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_cli_build_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            profile = tmp_path / "toplearn.profile.json"
            guard = tmp_path / "toplearn.guard.json"
            reference = tmp_path / "profile.md"

            self.assertEqual(
                main(
                    [
                        "build",
                        str(ROOT / "examples" / "corpus"),
                        "--profile-out",
                        str(profile),
                        "--guard-out",
                        str(guard),
                        "--common-doc-threshold",
                        "2",
                        "--sections",
                        "abstract,introduction",
                        "--skill-reference",
                        str(reference),
                    ]
                ),
                0,
            )
            self.assertTrue(profile.exists())
            self.assertTrue(guard.exists())
            self.assertTrue(reference.exists())

            code = main(
                [
                    "audit",
                    str(ROOT / "examples" / "drafts" / "introduction.md"),
                    "--profile",
                    str(profile),
                    "--guard",
                    str(guard),
                    "--fail-on",
                    "high",
                ]
            )
            self.assertIn(code, {0, 2})

            markdown = tmp_path / "audit.md"
            self.assertEqual(
                main(
                    [
                        "audit",
                        str(ROOT / "examples" / "drafts" / "introduction.md"),
                        "--profile",
                        str(profile),
                        "--guard",
                        str(guard),
                        "--format",
                        "markdown",
                        "--output",
                        str(markdown),
                        "--fail-on",
                        "none",
                    ]
                ),
                0,
            )

            self.assertEqual(main(["inspect", str(profile), "--guard", str(guard)]), 0)
            self.assertIn("# TopPaperLearn Audit", markdown.read_text(encoding="utf-8"))
            self.assertNotIn("Policy uncertainty shapes firm behavior", markdown.read_text(encoding="utf-8"))

    def test_cli_sections_miss_is_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                main(
                    [
                        "build",
                        str(ROOT / "examples" / "corpus"),
                        "--sections",
                        "nonexistent",
                        "--profile-out",
                        str(Path(tmp) / "profile.json"),
                        "--guard-out",
                        str(Path(tmp) / "guard.json"),
                    ]
                ),
                1,
            )

    def test_cli_requires_guard_unless_style_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "toplearn.profile.json"
            self.assertEqual(
                main(
                    [
                        "build",
                        str(ROOT / "examples" / "corpus"),
                        "--profile-out",
                        str(profile),
                        "--guard-out",
                        str(Path(tmp) / "toplearn.guard.json"),
                        "--common-doc-threshold",
                        "2",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "audit",
                        str(ROOT / "examples" / "drafts" / "introduction.md"),
                        "--profile",
                        str(profile),
                        "--fail-on",
                        "none",
                    ]
                ),
                1,
            )
            self.assertEqual(
                main(
                    [
                        "audit",
                        str(ROOT / "examples" / "drafts" / "introduction.md"),
                        "--profile",
                        str(profile),
                        "--style-only",
                        "--fail-on",
                        "none",
                    ]
                ),
                0,
            )


if __name__ == "__main__":
    unittest.main()
