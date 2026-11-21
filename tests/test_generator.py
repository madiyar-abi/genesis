import json
import unittest
from collections import defaultdict
from datetime import datetime

from auditenv.generator import ISSUE_TYPES, generate
from auditenv.money import convert, local_date, parse_offset

ALL = {"errors": {t: 1 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}


def journals(ledger):
    groups = defaultdict(list)
    for r in ledger:
        if r["payment_id"]:
            groups["pay:" + r["payment_id"]].append(r)
        elif r["invoice_id"]:
            groups["inv:" + r["invoice_id"]].append(r)
        else:
            groups["exp:" + r["timestamp"]].append(r)  # expenses: Dr 6xxx / Cr 1000 at one timestamp
    return groups


class GeneratorTest(unittest.TestCase):
    def test_deterministic(self):
        for seed in (0, 7, 123456789):
            a = json.dumps(generate(seed, ALL), sort_keys=True)
            b = json.dumps(generate(seed, ALL), sort_keys=True)
            self.assertEqual(a, b)
        self.assertNotEqual(json.dumps(generate(1, ALL)), json.dumps(generate(2, ALL)))

    def test_sizes_and_formats(self):
        for seed in range(30):
            ep = generate(seed)
            m, t = ep["manifest"], ep["tables"]
            self.assertTrue(200 <= len(t["ledger"]) <= 2000)
            self.assertTrue(20 <= m["counts"]["documents"] <= 200)
            self.assertLessEqual(len(ep["truth"]["issues"]), 12)
            self.assertEqual(m["counts"]["ledger"], len(t["ledger"]))
            for r in t["ledger"]:
                self.assertEqual(r["currency"], m["base_currency"])
                self.assertIsInstance(r["debit_minor"], int)
                self.assertTrue((r["debit_minor"] == 0) != (r["credit_minor"] == 0))
            for inv in t["invoices"]:
                self.assertEqual(inv["total_minor"], sum(li["amount_minor"] for li in inv["line_items"]))
                self.assertIn(inv["issued_at"][-6], "+-")
            ids = [r["row_id"] for r in t["ledger"]] + [d["doc_id"] for d in t["invoices"] + t["payments"]]
            self.assertEqual(len(ids), len(set(ids)))

    def test_journals_balance_after_injection(self):
        for seed in range(40):
            ep = generate(seed, ALL if seed % 2 else None)
            for jid, rows in journals(ep["tables"]["ledger"]).items():
                self.assertEqual(sum(r["debit_minor"] for r in rows), sum(r["credit_minor"] for r in rows), jid)

    def test_clean_company_has_no_issues(self):
        for seed in range(10):
            ep = generate(seed, {"errors": {}})
            self.assertEqual(ep["truth"]["issues"], [])
            self.assertEqual(ep["provenance"]["injections"], [])

    def test_requested_issue_counts(self):
        for seed in range(25):
            ep = generate(seed, ALL)
            types = sorted(i["type"] for i in ep["truth"]["issues"])
            self.assertEqual(types, sorted(list(ISSUE_TYPES) + ["payment_allocation", "fx_error",
                                                                  "period_cutoff", "fx_error"]))

    def test_customer_credit_covers_each_refund(self):
        # A multi-invoice receipt can move to the date of the later payment.
        for difficulty, seed in (("default", 0), ("hard", 16)):
            with self.subTest(difficulty=difficulty, seed=seed):
                books = generate(seed, {"errors": {}, "difficulty": difficulty}, key="")["tables"]
                entities = {r["payment_id"]: r["entity_id"] for r in books["ledger"] if r["account"] == "2900"}
                credits = defaultdict(int)
                for payment in sorted(books["payments"], key=lambda p: datetime.fromisoformat(p["timestamp"])):
                    entity = entities.get(payment["payment_id"])
                    if entity is None:  # unidentified receipts do not fund a customer's refund
                        continue
                    key = (entity, payment["currency"])
                    allocated = sum(ref["amount_minor"] for ref in payment["invoice_refs"] or [])
                    credits[key] += payment["amount_minor"] - allocated
                    self.assertGreaterEqual(credits[key], 0, payment["payment_id"])

    def test_evidence_exists_and_amounts_positive(self):
        for seed in range(40):
            ep = generate(seed, ALL)
            t = ep["tables"]
            ids = {r["row_id"] for r in t["ledger"]} | {d["doc_id"] for d in t["invoices"] + t["payments"]} \
                | {r["fx_id"] for r in t["fx"]}
            for iss in ep["truth"]["issues"]:
                self.assertGreater(iss["expected_amount_minor"], 0)
                self.assertEqual(iss["currency"], ep["manifest"]["base_currency"])
                for s in iss["evidence_sets"]:
                    self.assertTrue(set(s) <= ids, (iss, s))

    def test_duplicate_and_fx_reproduce_from_records(self):
        for seed in range(40):
            ep = generate(seed, ALL)
            m, t = ep["manifest"], ep["tables"]
            tz = parse_offset(m["timezone"])
            fx = {(r["date"], r["source_currency"]): r["rate"] for r in t["fx"]}
            inv = {i["invoice_id"]: i for i in t["invoices"]}
            ar = {r["invoice_id"]: r for r in t["ledger"] if r["account"] == "1200" and not r["payment_id"]}
            for iss in ep["truth"]["issues"]:
                if iss["type"] == "duplicate_invoice":
                    a, b = (inv[i] for i in iss["affected_ids"])
                    self.assertEqual((a["entity_id"], a["currency"], a["line_items"]),
                                     (b["entity_id"], b["currency"], b["line_items"]))
                    self.assertTrue(iss["expected_amount_minor"] in (ar[a["invoice_id"]]["debit_minor"],
                                                                     ar[b["invoice_id"]]["debit_minor"]))
                if iss["type"] == "fx_error" and iss["affected_ids"][0] in inv:
                    i = inv[iss["affected_ids"][0]]
                    d = local_date(i["issued_at"], tz).isoformat()
                    correct = convert(i["total_minor"], i["currency"], m["base_currency"], fx[(d, i["currency"])])
                    self.assertEqual(abs(ar[i["invoice_id"]]["debit_minor"] - correct), iss["expected_amount_minor"])


if __name__ == "__main__":
    unittest.main()
