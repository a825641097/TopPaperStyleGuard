import unittest
from pathlib import Path

from toppaperlearn.audit import audit_draft
from toppaperlearn.guard import build_guardpack, load_guardpack, write_guardpack
from toppaperlearn.profile import build_profile
from toppaperlearn.text import read_documents


ROOT = Path(__file__).resolve().parents[1]


class ProfileGuardAuditTests(unittest.TestCase):
    def test_profile_does_not_store_source_sentences(self):
        profile = build_profile(ROOT / "examples" / "corpus", field="economics")

        self.assertFalse(profile["privacy"]["stores_source_sentences"])
        self.assertEqual(profile["corpus"]["document_count"], 2)
        self.assertNotIn("Regulatory uncertainty is central", str(profile))
        self.assertNotIn("Unrelated Reference Title", str(profile))

    def test_section_filter_uses_selected_sections_and_strips_references(self):
        documents = read_documents(ROOT / "examples" / "corpus", sections={"introduction"})
        joined = "\n".join(document.text for document in documents)

        self.assertIn("Policy uncertainty shapes firm behavior", joined)
        self.assertNotIn("Regulatory uncertainty is central", joined)
        self.assertNotIn("Unrelated Reference Title", joined)

        profile = build_profile(
            ROOT / "examples" / "corpus",
            field="economics",
            sections={"introduction"},
        )
        self.assertEqual(profile["corpus"]["selected_sections"], ["introduction"])

    def test_guardpack_hashes_source_ngrams_without_source_text(self):
        guardpack = build_guardpack(ROOT / "examples" / "corpus", ngram=8, common_doc_threshold=2)

        self.assertTrue(guardpack["privacy"]["stores_hashes_only"])
        self.assertTrue(guardpack["privacy"]["guardpack_is_sensitive"])
        self.assertEqual(guardpack["fingerprint_format_version"], "salted-aggregate-v1")
        self.assertNotIn("Policy uncertainty shapes firm behavior", str(guardpack))
        self.assertTrue(guardpack["fingerprints"])
        self.assertIn("common_fingerprints", guardpack)
        first_meta = next(iter(guardpack["fingerprints"].values()))
        self.assertIsInstance(first_meta, dict)
        self.assertIn("count", first_meta)
        self.assertIn("document_count", first_meta)

    def test_guardpack_threshold_above_document_count_warns(self):
        guardpack = build_guardpack(ROOT / "examples" / "corpus", ngram=8, common_doc_threshold=5)

        self.assertTrue(guardpack["warnings"])
        self.assertEqual(guardpack["common_fingerprints"], [])

    def test_legacy_guardpack_load_gets_explicit_format(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.guard.json"
            legacy = build_guardpack(ROOT / "examples" / "corpus", ngram=8, common_doc_threshold=2)
            legacy.pop("salt")
            write_guardpack(legacy, path)
            loaded = load_guardpack(path)

        self.assertEqual(loaded["fingerprint_format_version"], "legacy-fixed-salt-v0")
        self.assertEqual(loaded["salt"], "toppaperlearn-v1")

    def test_audit_flags_copied_opening_span(self):
        profile = build_profile(ROOT / "examples" / "corpus", field="economics")
        guardpack = build_guardpack(ROOT / "examples" / "corpus", ngram=8, common_doc_threshold=2)

        result = audit_draft(ROOT / "examples" / "drafts" / "introduction.md", profile, guardpack)

        self.assertIn(result["risk"], {"medium", "high"})
        self.assertGreaterEqual(result["overlap"]["max_contiguous_span_words"], 10)
        self.assertTrue(result["style_feedback"])
        self.assertNotIn("draft_excerpt", result["overlap"]["findings"][0])

    def test_audit_excerpts_are_opt_in(self):
        profile = build_profile(ROOT / "examples" / "corpus", field="economics")
        guardpack = build_guardpack(ROOT / "examples" / "corpus", ngram=8, common_doc_threshold=2)

        result = audit_draft(
            ROOT / "examples" / "drafts" / "introduction.md",
            profile,
            guardpack,
            include_excerpts=True,
        )

        self.assertIn("draft_excerpt", result["overlap"]["findings"][0])

    def test_revised_draft_has_lower_overlap_than_copied_opening(self):
        profile = build_profile(ROOT / "examples" / "corpus", field="economics")
        guardpack = build_guardpack(ROOT / "examples" / "corpus", ngram=8, common_doc_threshold=2)

        copied = audit_draft(ROOT / "examples" / "drafts" / "introduction.md", profile, guardpack)
        revised = audit_draft(
            ROOT / "examples" / "drafts" / "revised-introduction.md",
            profile,
            guardpack,
        )

        self.assertLess(
            revised["overlap"]["max_contiguous_span_words"],
            copied["overlap"]["max_contiguous_span_words"],
        )
        risk_order = {"clear": 0, "low": 1, "medium": 2, "high": 3}
        self.assertLessEqual(risk_order[revised["risk"]], risk_order["low"])


if __name__ == "__main__":
    unittest.main()
