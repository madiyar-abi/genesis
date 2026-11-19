import copy
import unittest

from auditenv.generator import ISSUE_TYPES, generate
from auditenv.verify import Books, _sufficient, verify_episode

HEAVY = {"errors": {t: 2 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}


class VerifyTest(unittest.TestCase):
    def test_generated_episodes_verify(self):
        for seed in range(60):
            for cfg in (None, {"errors": {}}, HEAVY, {**HEAVY, "transform_seed": seed}):
                self.assertEqual(verify_episode(generate(seed, cfg)), [], (seed, cfg))

    def test_detects_undeclared_discrepancy(self):
        ep = generate(3, {"errors": {}})
        bad = copy.deepcopy(ep)
        row = next(r for r in bad["tables"]["ledger"] if r["account"] == "1200" and r["debit_minor"] > 0)
        rev = next(r for r in bad["tables"]["ledger"] if r["account"] == "4000" and r["invoice_id"] == row["invoice_id"])
        row["debit_minor"] += 500
        rev["credit_minor"] += 500
        self.assertTrue(any("truth mismatch" in p for p in verify_episode(bad)))

    def test_detects_unbalanced_journal(self):
        bad = copy.deepcopy(generate(4, {"errors": {}}))
        next(r for r in bad["tables"]["ledger"] if r["account"] == "1000" and r["debit_minor"] > 0)["debit_minor"] += 1
        self.assertTrue(any("unbalanced" in p for p in verify_episode(bad)))

    def test_detects_wrong_truth(self):
        ep = generate(5, HEAVY)
        dropped = copy.deepcopy(ep)
        dropped["truth"]["issues"].pop()
        self.assertTrue(verify_episode(dropped))
        wrong_amount = copy.deepcopy(ep)
        wrong_amount["truth"]["issues"][0]["expected_amount_minor"] += 7
        self.assertTrue(verify_episode(wrong_amount))
        bad_evidence = copy.deepcopy(ep)
        bad_evidence["truth"]["issues"][0]["evidence_sets"] = [["NOPE-1"]]
        self.assertTrue(verify_episode(bad_evidence))


if __name__ == "__main__":
    unittest.main()

    def test_nothing_allocated_evidence_must_cover_the_whole_ref(self):
        """D2: the 2900 row is the positive evidence for 'nothing allocated'; for a base-currency payment it
        must carry at least the referenced amount (the missing AR credit is proven by the whole-book check)."""
        ep = generate(1, HEAVY)
        t, m = ep["tables"], ep["manifest"]
        rows = {r["row_id"]: r for r in t["ledger"]}
        docs = {d["doc_id"]: d for d in t["invoices"] + t["payments"]}
        checked = 0
        for iss in ep["truth"]["issues"]:
            s = iss["evidence_sets"][0]
            ev = [rows[i] for i in s if i in rows]
            pay = next((docs[i] for i in s if i in docs and "payment_id" in docs[i]), None)
            if iss["type"] != "payment_allocation" or ev[0]["account"] != "2900" or pay["currency"] != m["base_currency"]:
                continue
            self.assertEqual(_sufficient(Books(m, t), iss, s, rows, docs), [])
            short = copy.deepcopy(rows)
            ref = next(r for r in pay["invoice_refs"] if r["invoice_id"] in iss["affected_ids"])
            short[ev[0]["row_id"]]["credit_minor"] = ref["amount_minor"] - 1
            self.assertTrue(_sufficient(Books(m, t), iss, s, short, docs))
            checked += 1
        self.assertGreater(checked, 0)
