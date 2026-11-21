"""Block 2 of the jury's check definitions (D01-D20): each scenario is produced by the generator's documented config
(`auditenv.jury.SCENARIOS`, README "Jury adapter") through `judge_adapter.generate_episode`, read back from disk and
checked by the independent verifier (balanced books before the injection, exactly the declared discrepancy after,
sufficient evidence), plus the scenario's own condition."""

import os
import shutil
import tempfile
import unittest

import judge_adapter as ja
from auditenv import jury
from auditenv.load import load_episode
from auditenv.matcher import public_ids
from auditenv.verify import verify_episode

ja._WARNED = True  # public test seeds: the grader-key warning is tested on its own
os.environ.setdefault("AUDITENV_KEY_FILE", os.path.join(tempfile.mkdtemp(), "grader.key"))  # not ~/.auditenv

SEEDS = range(900, 904)  # stand-ins for the jury's hidden seeds
EXPECTED = {**{f"D{n:02d}": [] for n in range(1, 6)},
            **{f"D{n:02d}": [("duplicate_invoice", "single")] for n in range(6, 9)},
            **{f"D{n:02d}": [("payment_allocation", "single")] for n in range(9, 12)},
            **{f"D{n:02d}": [("fx_error", "single")] for n in range(12, 14)},
            **{f"D{n:02d}": [("period_cutoff", "single")] for n in range(14, 16)},
            **{f"D{n:02d}": [("fx_error", "I1"), ("payment_allocation", "I1")] for n in range(16, 19)},
            **{f"D{n:02d}": [("fx_error", "I2"), ("period_cutoff", "I2")] for n in range(19, 21)}}


def allocated(ep, issue) -> int:
    """AR credit actually posted to the invoice in the payment of a payment_allocation issue."""
    pays = {p["payment_id"] for p in ep["tables"]["payments"]}
    pay = next(i for i in issue["affected_ids"] if i in pays)
    inv = next(i for i in issue["affected_ids"] if i != pay)
    return sum(r["credit_minor"] - r["debit_minor"] for r in ep["tables"]["ledger"]
               if r["payment_id"] == pay and r["account"] == "1200" and r["invoice_id"] == inv)


class JudgeScenariosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.episodes = {}
        for name, cfg in jury.SCENARIOS.items():
            for seed in SEEDS:
                path = os.path.join(cls.tmp, f"{name}-{seed}")
                ja.generate_episode(seed, cfg, path)
                cls.episodes[name, seed] = load_episode(path)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_twenty_documented_scenarios(self):
        self.assertEqual(list(jury.SCENARIOS), [f"D{n:02d}" for n in range(1, 21)])

    def test_every_episode_verifies_and_has_the_declared_truth(self):
        for (name, seed), ep in self.episodes.items():
            with self.subTest(scenario=name, seed=seed):
                self.assertEqual(verify_episode(ep), [])
                got = sorted((i["type"], i["scenario"]) for i in ep["truth"]["issues"])
                self.assertEqual(got, EXPECTED[name])
                known = public_ids(ep["tables"])
                for issue in ep["truth"]["issues"]:
                    self.assertTrue(set(issue["affected_ids"]) <= known)
                    self.assertTrue(all(set(s) <= known for s in issue["evidence_sets"]))

    def test_allocation_variants(self):
        for seed in SEEDS:
            (missing,) = self.episodes["D09", seed]["truth"]["issues"]
            (partial,) = self.episodes["D10", seed]["truth"]["issues"]
            self.assertEqual(allocated(self.episodes["D09", seed], missing), 0)
            self.assertGreater(allocated(self.episodes["D10", seed], partial), 0)

    def test_clean_scenarios_hold_the_legitimate_lookalikes(self):
        for n in range(1, 6):
            for seed in SEEDS:
                t = self.episodes[f"D{n:02d}", seed]["tables"]
                with self.subTest(scenario=f"D{n:02d}", seed=seed):
                    parts = [r["invoice_id"] for p in t["payments"] for r in p["invoice_refs"] or ()]
                    self.assertTrue(any(parts.count(i) >= 2 for i in parts))  # D02: one invoice paid in two parts
                    self.assertTrue(any(p["amount_minor"] < 0 for p in t["payments"]))  # D03: a refund
                    totals = [(i["currency"], i["total_minor"]) for i in t["invoices"]]
                    self.assertLess(len(set(totals)), len(totals))  # D04: equal amounts that are not duplicates
                    self.assertTrue(any(p["invoice_refs"] is None for p in t["payments"]))

    def test_interacting_scenarios_vary_their_parameters(self):
        for names in (("D16", "D17", "D18"), ("D19", "D20")):
            amounts = {tuple(sorted(i["expected_amount_minor"] for i in self.episodes[n, s]["truth"]["issues"]))
                       for n in names for s in SEEDS}
            self.assertGreater(len(amounts), 1)

    def test_allocation_key_is_validated_and_off_by_default(self):
        with self.assertRaises(ValueError):
            ja.generate_episode(1, {"allocation": "some"}, os.path.join(self.tmp, "x"))
        from auditenv.generator import gen_config
        self.assertNotIn("allocation", gen_config({}))


if __name__ == "__main__":
    unittest.main()
