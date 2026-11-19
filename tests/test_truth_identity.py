import unittest

from auditenv.generator import generate
from auditenv.verify import verify_episode


class TruthIdentityTest(unittest.TestCase):
    def test_clean_truth_belongs_to_manifest_episode(self):
        episode = generate(7, {"errors": {}})
        self.assertEqual(verify_episode(episode), [])
        episode["truth"]["episode_id"] = generate(8, {"errors": {}})["truth"]["episode_id"]
        self.assertIn("truth episode_id differs from manifest", verify_episode(episode))

    def test_distinct_issues_require_distinct_identifiers(self):
        episode = generate(7, {"errors": {"duplicate_invoice": 2}})
        self.assertEqual(verify_episode(episode), [])
        first, second = episode["truth"]["issues"]
        second["issue_id"] = first["issue_id"]
        self.assertIn(f"duplicate truth issue_id {first['issue_id']}", verify_episode(episode))
