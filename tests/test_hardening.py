"""Regression tests for the jury-style review findings."""
import json
import os
import tempfile
import unittest
from unittest import mock

from auditenv.client import RemoteEnv
from auditenv.env import AuditEnv
from auditenv.generator import generate
from auditenv.verify import verify_episode


def dumps(ep):
    return json.dumps(ep, sort_keys=True)


class HardeningTest(unittest.TestCase):
    def test_secret_keys_episode_id_and_content(self):
        public = generate(7345123, {"errors": {"fx_error": 1}})
        with mock.patch.dict(os.environ, {"AUDITENV_SECRET": "grader-only-key"}):
            hidden = generate(7345123, {"errors": {"fx_error": 1}})
            again = generate(7345123, {"errors": {"fx_error": 1}})
        self.assertNotEqual(public["episode_id"], hidden["episode_id"])
        self.assertNotEqual(public["tables"]["ledger"], hidden["tables"]["ledger"])
        self.assertEqual(dumps(hidden), dumps(again))  # still reproducible for the key holder
        self.assertEqual(verify_episode(hidden), [])

    def test_equivalent_configs_same_company(self):
        a = generate(3, {"errors": {"fx_error": 1}})
        b = generate(3, {"errors": {"fx_error": 1, "duplicate_invoice": 0}, "interacting": {}})
        self.assertEqual(dumps(a), dumps(b))
        self.assertEqual(dumps(generate(3, {})), dumps(generate(3, {"distractors": True})))

    def test_crash_config_and_min_documents(self):
        cfg = {"errors": {"duplicate_invoice": 9, "fx_error": 2}, "n_invoices": 10, "distractors": False}
        self.assertEqual(verify_episode(generate(61, cfg)), [])
        for seed in range(30):
            ep = generate(seed, {"errors": {}, "n_invoices": 10, "distractors": False})
            self.assertGreaterEqual(ep["manifest"]["counts"]["documents"], 20)

    def test_malformed_table_never_crashes_or_overruns(self):
        env = AuditEnv()
        env.reset(1, {"errors": {}})
        for i in range(100):
            obs, r, term, trunc, info = env.step({"type": "list_records", "table": ["ledger"]})
            self.assertEqual(obs["error"]["code"], "unknown_table")
        self.assertTrue(trunc)
        obs, r, term, trunc, info = env.step({"type": "submit", "findings": {}})
        self.assertEqual(obs["error"]["code"], "episode_over")

    def test_server_grades_abandoned_episodes(self):
        with tempfile.TemporaryDirectory() as d:
            log, hidden = os.path.join(d, "g.jsonl"), os.path.join(d, "h.json")
            with open(hidden, "w") as fh:
                json.dump({"seeds": [1, 2, 3], "config": {"errors": {"fx_error": 1}}}, fh)
            with RemoteEnv(grader_log=log, episodes=hidden) as env:
                env.reset()
                env.step({"type": "list_records", "table": "ledger"})
                env.reset()  # skip episode 1 mid-way
                env.reset()  # skip episode 2 without a step; episode 3 left open at close
            with open(log) as fh:
                recs = [json.loads(line) for line in fh]
            self.assertEqual([r["end"] for r in recs], ["abandoned"] * 3)
            self.assertTrue(all(r["reward"] < 0 for r in recs))

    def test_validator_matches_published_schema(self):
        from auditenv.schema import validate_findings
        f = {"type": "fx_error", "affected_ids": ["X"], "claimed_amount_minor": 1, "currency": "USD",
             "evidence_ids": []}
        self.assertIsNone(validate_findings({"episode_id": "e", "findings": [f]}, "e"))
        self.assertIsNotNone(validate_findings({"episode_id": "e", "findings": [f], "extra": 1}, "e"))
        for cur in ("ÄÖÜ", "ＵＳＤ", "usd", "US1"):
            self.assertIsNotNone(validate_findings({"episode_id": "e", "findings": [{**f, "currency": cur}]}, "e"))

    def test_server_accepts_config_episode_lists(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "g.jsonl")
            with RemoteEnv(grader_log=log, episodes=os.path.join(root, "configs", "eval_example.json")) as env:
                obs, info = env.reset()
                self.assertEqual(info["mode"], "eval")


if __name__ == "__main__":
    unittest.main()


class AllocationEvidenceTest(unittest.TestCase):
    """REVIEW.md #1: every payment_allocation evidence set must reproduce the amount on its own."""

    CFG = {"errors": {"payment_allocation": 3}, "interacting": {"I1": 1}}

    def test_partial_allocation_needs_the_posted_ar_credit(self):
        seen_partial = seen_full = 0
        for seed in range(40):
            ep = generate(seed, self.CFG)
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            for iss in ep["truth"]["issues"]:
                if iss["type"] != "payment_allocation":
                    continue
                accounts = {rows[i]["account"] for s in iss["evidence_sets"] for i in s if i in rows}
                inv_id, pay_id = sorted(iss["affected_ids"], key=lambda i: i not in {r["invoice_id"] for r in
                                                                                      ep["tables"]["invoices"]})
                posted = any(r["account"] == "1200" and r["payment_id"] == pay_id and r["invoice_id"] == inv_id
                             for r in ep["tables"]["ledger"])
                if posted:  # partial: only the AR-row set reproduces expected - posted
                    seen_partial += 1
                    self.assertEqual(accounts, {"1200"}, (seed, iss["issue_id"]))
                else:
                    seen_full += 1
                    self.assertEqual(accounts, {"2900"}, (seed, iss["issue_id"]))
            self.assertEqual(verify_episode(ep), [], seed)
        self.assertGreater(seen_partial, 10)
        self.assertGreater(seen_full, 10)

    def test_verifier_rejects_an_insufficient_2900_set(self):
        for seed in range(40):
            ep = generate(seed, self.CFG)
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            for iss in ep["truth"]["issues"]:
                s = iss["evidence_sets"][0]
                if iss["type"] != "payment_allocation" or not any(rows.get(i, {}).get("account") == "1200" for i in s):
                    continue
                pay_id = next(i for i in iss["affected_ids"] if i in {p["payment_id"] for p in ep["tables"]["payments"]})
                unapplied = next((r["row_id"] for r in ep["tables"]["ledger"]
                                  if r["account"] == "2900" and r["payment_id"] == pay_id), None)
                if unapplied is None:
                    continue
                iss["evidence_sets"] = [[unapplied if rows.get(i, {}).get("account") == "1200" else i for i in s]]
                self.assertTrue(any("does not reproduce" in p for p in verify_episode(ep)))
                return
        self.fail("no partial allocation with a 2900 row found")
