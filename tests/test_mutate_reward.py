"""Ensure the mutation definitions still target the current reward source."""

import unittest

from scripts.mutate_reward import MUTANTS, ROOT


class RewardMutationTest(unittest.TestCase):
    def test_patterns_match_exactly_once(self):
        self.assertTrue(MUTANTS)
        for module, name, original, replacement in MUTANTS:
            with self.subTest(module=module, mutant=name):
                source = (ROOT / "auditenv" / f"{module}.py").read_text()
                self.assertEqual(source.count(original), 1)
                self.assertNotEqual(original, replacement)
                self.assertNotIn("\n", original)
                self.assertNotIn("\n", replacement)
