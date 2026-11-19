"""The seed sweep (auditenv.fuzz) passes on a few seeds and reports a corrupted episode."""
import unittest
from unittest import mock

from auditenv import fuzz
from auditenv.generator import generate


class SeedSweepTest(unittest.TestCase):
    def test_small_sweep_is_clean(self):
        for hard in (False, True):
            r = fuzz.sweep([0, 1, 2], hard=hard)
            self.assertEqual(r["episodes"], 9)
            self.assertEqual(r["problems"], [])
            self.assertEqual(r["random_positive_dirty"], 0)
            self.assertEqual(r["flag_all_negative"], 9)

    def test_corrupted_ledger_is_reported(self):
        def broken(seed, config=None):
            ep = generate(seed, config)
            row = next(r for r in ep["tables"]["ledger"] if r["debit_minor"])
            row["debit_minor"] += 1  # unbalanced journal
            return ep

        with mock.patch.object(fuzz, "generate", broken):
            r = fuzz.sweep([0], hard=False)
        self.assertEqual({p[2] for p in r["problems"]}, {"verifier"})
        self.assertEqual(len(r["problems"]), 3)


if __name__ == "__main__":
    unittest.main()
