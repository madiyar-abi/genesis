import copy
import unittest

from auditenv.generator import generate
from auditenv.verify import verify_episode, _structure


class ManifestCountsTest(unittest.TestCase):
    def test_original_seed_7_passes(self):
        ep = generate(7)
        self.assertEqual(verify_episode(ep), [])

    def test_seed_7_with_wrong_documents_count_fails(self):
        """Seed 7 has 47 invoices + 21 payments = 68 documents.

        Falsifying manifest counts documents=20 must fail verification.
        """
        ep = generate(7)
        self.assertEqual(ep["manifest"]["counts"]["documents"], 68)
        tampered = copy.deepcopy(ep)
        tampered["manifest"]["counts"]["documents"] = 20
        problems = verify_episode(tampered)
        self.assertTrue(any("manifest count mismatch for documents" in p for p in problems))
        structure_problems = _structure(tampered)
        self.assertIn("manifest count mismatch for documents", structure_problems)

    def test_size_check_applies_to_actual_records(self):
        """Size check must check actual records count, not just the manifest claim."""
        ep = generate(7)
        tampered = copy.deepcopy(ep)
        # Keep only 10 invoices and 5 payments = 15 actual documents (< 20 required)
        tampered["tables"]["invoices"] = tampered["tables"]["invoices"][:10]
        tampered["tables"]["payments"] = tampered["tables"]["payments"][:5]
        tampered["manifest"]["counts"]["invoices"] = 10
        tampered["manifest"]["counts"]["payments"] = 5

        problems = _structure(tampered)
        self.assertTrue(any("outside 200-2000 rows / 20-200 documents" in p for p in problems))

    def test_manifest_missing_documents_key_fails(self):
        ep = generate(7)
        tampered = copy.deepcopy(ep)
        del tampered["manifest"]["counts"]["documents"]
        problems = _structure(tampered)
        self.assertIn("manifest.counts.documents: required", problems)  # manifest.schema.json requires it


if __name__ == "__main__":
    unittest.main()
