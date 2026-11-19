"""Hard mode (`{"difficulty": "hard"}`): additive, valid, solvable from the records, harder than default."""

import unittest

from auditenv.env import AuditEnv
from auditenv.generator import gen_config, generate
from auditenv.matcher import match
from auditenv.policies.reconcile import reconcile_findings
from auditenv.verify import verify_episode

HARD = {"difficulty": "hard"}
HARD_CLEAN = {"difficulty": "hard", "errors": {}}
HARD_DUPS = {"difficulty": "hard", "errors": {"duplicate_invoice": 3}}


def _credit_noted(ep):
    return {r["invoice_id"] for r in ep["tables"]["ledger"]
            if r["account"] == "1200" and r["credit_minor"] and r["invoice_id"] and not r["payment_id"]}


class HardModeTests(unittest.TestCase):
    def test_default_is_unchanged_and_bad_values_rejected(self):
        self.assertNotIn("difficulty", gen_config({}))
        self.assertEqual(generate(3), generate(3, {"difficulty": "default"}))
        self.assertNotEqual(generate(3)["episode_id"], generate(3, HARD)["episode_id"])
        with self.assertRaises(ValueError):
            generate(3, {"difficulty": "extreme"})

    def test_policy_and_task_describe_hard_rules_only_in_hard_mode(self):
        default, hard = generate(4), generate(4, HARD)
        self.assertNotIn("credit_note", default["policy"]["ledger"])
        self.assertIn("credit_note", hard["policy"]["ledger"])
        self.assertTrue(hard["task"].startswith(default["task"]))
        self.assertIn("Hard mode", hard["task"])
        self.assertNotIn("Hard mode", default["task"])

    def test_hard_episodes_pass_the_verifier_and_are_larger(self):
        for seed in range(15):
            for cfg in (HARD, HARD_CLEAN, HARD_DUPS, {**HARD, "interacting": {"I1": 1, "I2": 1}}):
                ep = generate(seed, cfg)
                self.assertEqual(verify_episode(ep), [], (seed, cfg))
                self.assertGreaterEqual(len(ep["tables"]["ledger"]), 900)
                self.assertLessEqual(len(ep["tables"]["ledger"]), 2000)

    def test_credit_note_reissue_is_legitimate_but_trips_default_rules(self):
        tripped = 0
        for seed in range(10):
            ep = generate(seed, HARD_CLEAN)
            self.assertEqual(ep["truth"]["issues"], [])
            self.assertGreaterEqual(len(_credit_noted(ep)), 2)
            self.assertEqual(reconcile_findings(ep["manifest"], ep["tables"], hard=True), [])
            plain = reconcile_findings(ep["manifest"], ep["tables"])
            tripped += any(f["type"] == "duplicate_invoice" for f in plain)
        self.assertGreaterEqual(tripped, 8)

    def test_retyped_duplicates_are_truth_and_need_the_hard_rule(self):
        retyped = 0
        for seed in range(10):
            ep = generate(seed, HARD_DUPS)
            invoices = {i["invoice_id"]: i for i in ep["tables"]["invoices"]}
            for iss in ep["truth"]["issues"]:
                a, b = (invoices[i] for i in iss["affected_ids"])
                retyped += a["line_items"] != b["line_items"]
            hard = match(ep["truth"]["issues"], reconcile_findings(ep["manifest"], ep["tables"], hard=True))
            self.assertEqual(hard["f1"], 1.0, seed)
        self.assertGreater(retyped, 5)
        plain_tp = sum(match(generate(s, HARD_DUPS)["truth"]["issues"],
                             reconcile_findings(generate(s, HARD_DUPS)["manifest"],
                                                generate(s, HARD_DUPS)["tables"]))["tp"] for s in range(10))
        self.assertLess(plain_tp, 30)

    def test_env_accepts_difficulty_and_hides_nothing_new(self):
        env = AuditEnv()
        obs, _ = env.reset(5, {"difficulty": "hard", "mode": "eval"})
        self.assertIn("credit_note", obs["policy"]["ledger"])
        self.assertNotIn("truth", obs)


if __name__ == "__main__":
    unittest.main()
