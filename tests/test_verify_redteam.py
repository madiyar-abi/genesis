"""Verifier regressions from the round-8 red-team review (REVIEW.md → "Round 8")."""

import copy
import unittest
from unittest.mock import patch

from auditenv.fuzz import HEAVY
from auditenv.generator import generate
from auditenv.verify import verify_episode

CLEAN = {"errors": {}}


def _recount(ep):
    t, c = ep["tables"], ep["manifest"]["counts"]
    for k in ("ledger", "invoices", "payments", "fx"):
        c[k] = len(t[k])
    c["documents"] = len(t["invoices"]) + len(t["payments"])


def _pay_rows(ep, pid):
    return [r for r in ep["tables"]["ledger"] if r["payment_id"] == pid]


def _inv_rows(ep, iid):
    return [r for r in ep["tables"]["ledger"] if r["invoice_id"] == iid and not r["payment_id"]]


def _has(problems, text):
    return any(text in p for p in problems)


class RedTeamTest(unittest.TestCase):
    def setUp(self):
        self.ep = copy.deepcopy(generate(0, CLEAN))
        self.t = self.ep["tables"]
        self.base = self.ep["manifest"]["base_currency"]
        self.assertEqual(verify_episode(self.ep), [])

    def test_manifest_exponents_cover_used_currencies_as_integers(self):
        with patch.dict("os.environ", {"AUDITENV_SECRET": ""}):
            ep = generate(0, {})
        exponents = ep["manifest"]["amount_exponents"]
        self.assertEqual(exponents.pop("JPY"), 0)
        with self.subTest("missing JPY"):
            self.assertTrue(_has(verify_episode(ep), "amount exponents"))
        exponents["JPY"] = False
        with self.subTest("JSON boolean instead of integer"):  # caught by manifest.schema.json first
            self.assertTrue(_has(verify_episode(ep), "manifest.amount_exponents.JPY: expected integer"))

    def _base_single_ref_payment(self):
        for p in self.t["payments"]:
            refs = p["invoice_refs"] or []
            if len(refs) == 1 and p["currency"] == self.base and refs[0]["amount_minor"] % 2 == 0 \
                    and len(_pay_rows(self.ep, p["payment_id"])) == 2:
                return p
        self.skipTest("no base-currency single-ref payment")

    def test_invoice_listed_twice_in_one_remittance(self):
        p = self._base_single_ref_payment()
        iid, half = p["invoice_refs"][0]["invoice_id"], p["invoice_refs"][0]["amount_minor"] // 2
        p["invoice_refs"] = [{"invoice_id": iid, "amount_minor": half}] * 2
        rows = _pay_rows(self.ep, p["payment_id"])
        cash = next(r for r in rows if r["account"] == "1000")
        next(r for r in rows if r["account"] == "1200")["credit_minor"] = half
        self.t["ledger"].append({**cash, "row_id": "X7900", "account": "7900", "debit_minor": 0, "credit_minor": half})
        _recount(self.ep)
        problems = verify_episode(self.ep)
        self.assertTrue(_has(problems, "references an invoice twice"), problems)
        self.assertTrue(_has(problems, "FX gain/loss on a base-currency payment"), problems)

    def test_unapplied_cash_inflated_on_a_payment_with_a_shortfall(self):
        ep = copy.deepcopy(generate(0, HEAVY))
        pids = {p["payment_id"] for p in ep["tables"]["payments"]}
        for iss in ep["truth"]["issues"]:
            if iss["type"] != "payment_allocation":
                continue
            pid = next(a for a in iss["affected_ids"] if a in pids)
            rows = _pay_rows(ep, pid)
            unapplied = next((r for r in rows if r["account"] == "2900"), None)
            if unapplied is None:
                continue
            cash = next(r for r in rows if r["account"] == "1000")
            unapplied["credit_minor"] += 5_000_000
            ep["tables"]["ledger"].append({**cash, "row_id": "X7900", "account": "7900", "debit_minor": 5_000_000,
                                           "credit_minor": 0})
            _recount(ep)
            problems = verify_episode(ep)
            self.assertTrue(_has(problems, "incorrect unapplied cash"), problems)
            return
        self.fail("no allocation issue with a 2900 row on HEAVY seed 0")

    def test_credit_note_needs_the_hard_mode_policy_rule(self):
        ar = next(r for r in self.t["ledger"] if r["account"] == "1200" and r["invoice_id"] and not r["payment_id"])
        amt = ar["debit_minor"]
        self.t["ledger"] += [{**ar, "row_id": "XCN1", "account": "4000", "debit_minor": amt, "credit_minor": 0},
                             {**ar, "row_id": "XCN2", "account": "1200", "debit_minor": 0, "credit_minor": amt}]
        _recount(self.ep)
        problems = verify_episode(self.ep)
        self.assertTrue(_has(problems, "malformed invoice journal"), problems)

    def test_refund_cannot_reference_an_invoice(self):
        p = next(p for p in self.t["payments"] if p["amount_minor"] < 0)
        inv = self.t["invoices"][0]
        p["invoice_refs"] = [{"invoice_id": inv["invoice_id"], "amount_minor": p["amount_minor"]}]
        row = next(r for r in _pay_rows(self.ep, p["payment_id"]) if r["account"] == "2900")
        row.update(account="1200", invoice_id=inv["invoice_id"], entity_id=inv["entity_id"])
        problems = verify_episode(self.ep)
        self.assertTrue(_has(problems, "non-positive invoice ref"), problems)

    def test_payment_cannot_settle_an_invoice_issued_later(self):
        from auditenv.verify import datetime_key
        p = self._base_single_ref_payment()
        later = next(i for i in self.t["invoices"] if i["currency"] == p["currency"]
                     and datetime_key(i["issued_at"]) > datetime_key(p["timestamp"])
                     and i["entity_id"] == next(x["entity_id"] for x in self.t["invoices"]
                                                if x["invoice_id"] == p["invoice_refs"][0]["invoice_id"]))
        old = p["invoice_refs"][0]["invoice_id"]
        p["invoice_refs"][0]["invoice_id"] = later["invoice_id"]
        for r in _pay_rows(self.ep, p["payment_id"]):
            if r["invoice_id"] == old:
                r["invoice_id"] = later["invoice_id"]
        problems = verify_episode(self.ep)
        self.assertTrue(_has(problems, "issued after the payment"), problems)

    def test_inverted_invoice_journal(self):
        ep = copy.deepcopy(generate(0, HEAVY))
        ids = [a for i in ep["truth"]["issues"] for a in i["affected_ids"]]
        iss = next(i for i in ep["truth"]["issues"] if i["type"] == "fx_error" and ids.count(i["affected_ids"][0]) == 1
                   and i["affected_ids"][0] in {x["invoice_id"] for x in ep["tables"]["invoices"]})
        iid = iss["affected_ids"][0]
        inv = next(i for i in ep["tables"]["invoices"] if i["invoice_id"] == iid)
        from auditenv.verify import Books
        correct = Books(ep["manifest"], ep["tables"]).conv(inv["total_minor"], inv["currency"], inv["issued_at"])
        for r in _inv_rows(ep, iid):  # AR Cr 2C / Rev Dr 2C: |0 - C| would read as an fx_error of C
            r["debit_minor"], r["credit_minor"] = (0, 2 * correct) if r["account"] == "1200" else (2 * correct, 0)
        iss["expected_amount_minor"] = correct
        problems = verify_episode(ep)
        self.assertTrue(_has(problems, "malformed invoice journal"), problems)

    def test_cutoff_evidence_must_be_the_booking_row(self):
        for seed in range(40):
            ep = copy.deepcopy(generate(seed, HEAVY))
            t = ep["tables"]
            docs = {i["invoice_id"]: i["doc_id"] for i in t["invoices"]}
            for iss in ep["truth"]["issues"]:
                if iss["type"] != "period_cutoff":
                    continue
                iid = iss["affected_ids"][0]
                prow = [r for r in t["ledger"] if r["payment_id"] and r["invoice_id"] == iid and r["account"] == "1200"
                        and r["credit_minor"] == iss["expected_amount_minor"]]
                if prow:
                    iss["evidence_sets"] = [sorted([docs[iid], prow[0]["row_id"]])]
                    problems = verify_episode(ep)
                    self.assertTrue(_has(problems, f"{iss['issue_id']}: evidence set"), problems)
                    return
        self.skipTest("no paid cut-off invoice in HEAVY seeds 0-39")

    def test_payment_rows_carry_the_payment_instant(self):
        p = self._base_single_ref_payment()
        row = next(r for r in _pay_rows(self.ep, p["payment_id"]) if r["account"] == "1000")
        row["timestamp"] = self.ep["manifest"]["period_end"] + "T12:00:00" + self.ep["manifest"]["timezone"]
        problems = verify_episode(self.ep)
        self.assertTrue(_has(problems, "not dated at the payment"), problems)

    def test_invoice_cannot_be_booked_before_it_is_issued(self):
        from auditenv.verify import Books, datetime_key
        books = Books(self.ep["manifest"], self.t)
        start = self.ep["manifest"]["period_start"] + "T00:00:00" + self.ep["manifest"]["timezone"]
        inv = next(i for i in self.t["invoices"] if books.in_period(i["issued_at"])
                   and books.cdate(i["issued_at"]).day > 5 and _inv_rows(self.ep, i["invoice_id"]))
        for r in _inv_rows(self.ep, inv["invoice_id"]):
            r["timestamp"] = start
        self.assertLess(datetime_key(start), datetime_key(inv["issued_at"]))
        problems = verify_episode(self.ep)
        self.assertTrue(_has(problems, "booked before it was issued"), problems)

    def test_policy_must_agree_with_manifest_and_contract(self):
        for change in (lambda ep: ep["policy"].update(timezone="+14:00"),
                       lambda ep: ep["policy"]["period"].update(start="2000-01-01"),
                       lambda ep: ep["policy"].update(base_currency="XYZ"),
                       lambda ep: ep["policy"]["ledger"]["accounts"].update({"6900": "Other"}),
                       lambda ep: ep["manifest"]["amount_exponents"].update({self.base: 3})):
            ep = copy.deepcopy(self.ep)
            change(ep)
            problems = verify_episode(ep)
            self.assertTrue(_has(problems, "contradict"), problems)
        ep = copy.deepcopy(self.ep)
        ep["manifest"].update(rounding="ROUND_HALF_EVEN")  # the schema pins the contract's rounding
        self.assertTrue(_has(verify_episode(ep), "manifest.rounding: must be 'ROUND_HALF_UP'"))


if __name__ == "__main__":
    unittest.main()
