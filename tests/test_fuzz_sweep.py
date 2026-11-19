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


class ConfigSweepTest(unittest.TestCase):
    def test_random_configs_are_valid_varied_and_deterministic(self):
        cfgs = [fuzz.random_config(i)[1] for i in range(200)]
        self.assertEqual(cfgs, [fuzz.random_config(i)[1] for i in range(200)])
        self.assertEqual({c.get("difficulty", "default") for c in cfgs}, {"default", "hard"})
        counts = {fuzz.expected_issues(c) for c in cfgs}
        self.assertIn(0, counts)
        self.assertIn(12, counts)
        self.assertLessEqual(max(n for n in counts if n is not None), 12)
        self.assertIn(None, counts)  # some configs leave the mix to the generator
        self.assertTrue(any("transform_seed" in c for c in cfgs) and any("n_invoices" in c for c in cfgs))

    def test_cli_rejects_nonpositive_case_counts(self):
        for count in ("0", "-1"):
            with self.subTest(count=count), mock.patch("sys.stderr"):
                with self.assertRaises(SystemExit) as error:
                    fuzz.main(["--configs", count])
                self.assertEqual(error.exception.code, 2)

    def test_small_config_sweep_is_clean(self):
        r = fuzz.config_sweep(12)
        self.assertEqual(r["episodes"], 12)
        self.assertEqual(r["problems"], [])
        self.assertLessEqual(r["max_steps"], 100)

    def test_config_sweep_reports_a_corrupted_ledger(self):
        def broken(seed, config=None):
            ep = generate(seed, config)
            row = next(r for r in ep["tables"]["ledger"] if r["debit_minor"])
            row["debit_minor"] += 1
            return ep

        with mock.patch.object(fuzz, "generate", broken):
            r = fuzz.config_sweep(2)
        self.assertEqual({p[3] for p in r["problems"]}, {"verifier"})


if __name__ == "__main__":
    unittest.main()
