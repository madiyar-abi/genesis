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

    def test_refund_clears_the_unapplied_cash_it_returns(self):
        # A foreign refund used to debit 2900 at the refund-date rate, after its receipt credited 2900 at the
        # receipt-date rate, so clean books left the customer's unapplied cash below zero in base currency
        # (round 21, balance re-derivation checker: D01 seed 41006, E0342). It is the receipt's carrying amount now;
        # the cash difference is realised FX (7900).
        # Default seeds 255 and 284 used to merge two overpayments into one receipt, so no refund matched it.
        from auditenv.jury import SCENARIOS
        cases = [(s, {**SCENARIOS["D03"], "difficulty": d}) for s in range(40) for d in ("default", "hard")]
        foreign = with_fx = 0
        for seed, config in cases + [(255, {}), (284, {})]:
            difficulty = config.get("difficulty", "default")
            ep = generate(seed, config, key="")
            base, tables = ep["manifest"]["base_currency"], ep["tables"]
            rows = defaultdict(list)
            for r in tables["ledger"]:
                if r["payment_id"]:
                    rows[r["payment_id"]].append(r)
            balance = defaultdict(int)
            for pay in sorted(tables["payments"], key=lambda p: datetime.fromisoformat(p["timestamp"])):
                entity = rows[pay["payment_id"]][0]["entity_id"]
                for r in rows[pay["payment_id"]]:
                    if r["account"] == "2900":
                        balance[entity] += r["credit_minor"] - r["debit_minor"]
                with self.subTest(seed=seed, difficulty=difficulty, payment=pay["payment_id"]):
                    self.assertGreaterEqual(balance[entity], 0)
                if pay["amount_minor"] < 0:  # the receipt it returns exists (CONTRACT §2), no refund-date fallback
                    receipts = [p for p in tables["payments"] if p["payment_id"] in rows
                                and rows[p["payment_id"]][0]["entity_id"] == entity and p["currency"] == pay["currency"]
                                and p["amount_minor"] - sum(r["amount_minor"] for r in p["invoice_refs"] or [])
                                == -pay["amount_minor"]
                                and datetime.fromisoformat(p["timestamp"]) < datetime.fromisoformat(pay["timestamp"])]
                    with self.subTest(seed=seed, difficulty=difficulty, refund=pay["payment_id"]):
                        self.assertTrue(receipts)
                if pay["amount_minor"] < 0 and pay["currency"] != base:
                    foreign += 1
                    with_fx += any(r["account"] == "7900" for r in rows[pay["payment_id"]])
        self.assertGreater(foreign, 10)
        self.assertGreater(with_fx, 0)

    def test_nothing_allocated_evidence_closes_the_payment_journal(self):
        # With nothing allocated the set cited only the 2900 row: the missing AR credit could not be read from the
        # set (round 23, provenance rebuild checker: D09 default seed 72000, PAY-453849; merged receipts
        # also allocate to other invoices). Every row of the payment's journal is in the set now, so the set
        # alone shows the journal balances without an AR credit for the invoice.
        from auditenv.jury import SCENARIOS
        checked = 0
        for seed in range(30):
            for config in (SCENARIOS["D09"], {**SCENARIOS["D09"], "difficulty": "hard"}, {}):
                ep = generate(seed, config, key="")
                rows = defaultdict(list)
                for r in ep["tables"]["ledger"]:
                    if r["payment_id"]:
                        rows[r["payment_id"]].append(r)
                payments = {p["payment_id"]: p for p in ep["tables"]["payments"]}
                for issue in ep["truth"]["issues"]:
                    if issue["type"] != "payment_allocation":
                        continue
                    pid = next(i for i in issue["affected_ids"] if i in payments)
                    inv = next(i for i in issue["affected_ids"] if i != pid)
                    journal = rows[pid]
                    if any(r["account"] == "1200" and r["invoice_id"] == inv for r in journal):
                        continue  # partial: the AR credit actually posted is in the set
                    checked += 1
                    with self.subTest(seed=seed, config=config, payment=pid):
                        for evidence in issue["evidence_sets"]:
                            self.assertLessEqual({r["row_id"] for r in journal}, set(evidence))
                            self.assertLessEqual(len(evidence), 10)
        self.assertGreater(checked, 20)

    def test_fully_paid_invoice_closes_its_receivable(self):
        # Each cash application used to be converted and rounded on its own, so an invoice paid in foreign parts
        # kept a minor unit in 1200 (18 % of clean D02 episodes, default and hard, seeds 0-299). The application that
        # completes the invoice now credits the rest of the booked amount; the cash difference is realised FX.
        from auditenv.jury import SCENARIOS
        closed = 0
        for seed in range(40):
            for difficulty in ("default", "hard"):
                tables = generate(seed, {**SCENARIOS["D02"], "difficulty": difficulty}, key="")["tables"]
                paid, parts = defaultdict(int), defaultdict(int)
                for p in tables["payments"]:
                    for ref in p["invoice_refs"] or []:
                        paid[ref["invoice_id"]] += ref["amount_minor"]
                        parts[ref["invoice_id"]] += 1
                ar, booked = defaultdict(int), set()
                for r in tables["ledger"]:
                    if r["account"] == "1200" and r["invoice_id"]:
                        ar[r["invoice_id"]] += r["debit_minor"] - r["credit_minor"]
                        if not r["payment_id"]:
                            booked.add(r["invoice_id"])
                for inv in tables["invoices"]:
                    i = inv["invoice_id"]
                    if i in booked and parts[i] >= 2 and paid[i] == inv["total_minor"]:
                        closed += 1
                        with self.subTest(seed=seed, difficulty=difficulty, invoice=i):
                            self.assertEqual(ar[i], 0)
        self.assertGreater(closed, 40)

    def test_cash_is_applied_after_the_invoice_is_posted(self):
        # A posting lag used to let a receipt settle a receivable that the ledger had not booked yet
        # (D01 default seed 30010: RCPT0548981 credits 1200 for 2608-742998 a day before its booking).
        from auditenv.jury import SCENARIOS
        cases = [(30010, SCENARIOS["D01"]), (30033, SCENARIOS["D01"])]
        cases += [(s, {"errors": {}, "difficulty": d}) for s in range(60) for d in ("default", "hard")]
        for seed, config in cases:
            with self.subTest(seed=seed, config=config):
                ledger = generate(seed, config, key="")["tables"]["ledger"]
                posted = {}
                for r in ledger:
                    if r["account"] == "1200" and r["invoice_id"] and not r["payment_id"] and r["debit_minor"]:
                        t = datetime.fromisoformat(r["timestamp"])
                        posted[r["invoice_id"]] = min(t, posted.get(r["invoice_id"], t))
                for r in ledger:
                    if r["account"] == "1200" and r["payment_id"] and r["invoice_id"] in posted:
                        self.assertGreaterEqual(datetime.fromisoformat(r["timestamp"]), posted[r["invoice_id"]],
                                                (r["row_id"], r["invoice_id"], r["payment_id"]))

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
