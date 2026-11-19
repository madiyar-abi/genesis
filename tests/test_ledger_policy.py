"""The verifier enforces the published `policy.ledger` account usage (REVIEW.md, round 8)."""

import copy
import unittest

from auditenv.generator import generate
from auditenv.verify import verify_episode

CLEAN = {"errors": {}}


def _row(ep, pred):
    return next(r for r in ep["tables"]["ledger"] if pred(ep, r))


def _referenced_remainder(ep, r):
    pay = next((p for p in ep["tables"]["payments"] if p["payment_id"] == r["payment_id"]), None)
    return r["account"] == "2900" and pay is not None and bool(pay["invoice_refs"])


class LedgerPolicyTest(unittest.TestCase):
    def setUp(self):
        self.ep = generate(0, CLEAN)
        self.assertEqual(verify_episode(self.ep), [])

    def _tampered(self, pred, **changes):
        bad = copy.deepcopy(self.ep)
        _row(bad, pred).update(changes)
        return verify_episode(bad)

    def test_referenced_payment_remainder_moved_to_revenue(self):
        problems = self._tampered(_referenced_remainder, account="4000")
        self.assertTrue(any("account 4000 not allowed in payment journal" in p for p in problems), problems)
        self.assertTrue(any("incorrect unapplied cash" in p for p in problems), problems)

    def test_referenced_payment_remainder_amount(self):
        bad = copy.deepcopy(self.ep)
        row = _row(bad, _referenced_remainder)
        row["credit_minor"] += 100  # balanced by an extra FX loss: the journal still balances
        bad["tables"]["ledger"].append({**row, "row_id": "L99999", "account": "7900", "debit_minor": 100,
                                        "credit_minor": 0})
        bad["manifest"]["counts"]["ledger"] += 1
        problems = verify_episode(bad)
        self.assertTrue(any("incorrect unapplied cash" in p for p in problems), problems)

    def test_fx_gain_loss_moved_to_revenue(self):
        problems = self._tampered(lambda ep, r: r["account"] == "7900", account="4000")
        self.assertTrue(any("account 4000 not allowed in payment journal" in p for p in problems), problems)

    def test_expense_booked_to_unknown_account(self):
        problems = self._tampered(lambda ep, r: r["account"] == "6300", account="9999")
        self.assertTrue(any("unknown account 9999" in p for p in problems), problems)

    def test_expense_booked_to_revenue(self):
        problems = self._tampered(lambda ep, r: r["account"] == "6300", account="4000")
        self.assertTrue(any("expense journal" in p for p in problems), problems)

    def test_invoice_journal_entity_swap(self):
        bad = copy.deepcopy(self.ep)
        row = _row(bad, lambda ep, r: r["account"] == "1200" and r["invoice_id"] and not r["payment_id"])
        other = next(i["entity_id"] for i in bad["tables"]["invoices"] if i["entity_id"] != row["entity_id"])
        for r in bad["tables"]["ledger"]:
            if r["invoice_id"] == row["invoice_id"] and not r["payment_id"]:
                r["entity_id"] = other
        problems = verify_episode(bad)
        self.assertTrue(any(f"entity differs from invoice {row['invoice_id']}" in p for p in problems), problems)

    def test_payment_receivable_entity_swap(self):
        bad = copy.deepcopy(self.ep)
        row = _row(bad, lambda ep, r: r["account"] == "1200" and r["payment_id"])
        row["entity_id"] = next(i["entity_id"] for i in bad["tables"]["invoices"] if i["entity_id"] != row["entity_id"])
        problems = verify_episode(bad)
        self.assertTrue(any(f"entity differs from invoice {row['invoice_id']}" in p for p in problems), problems)

    def test_extra_balanced_pair_in_invoice_journal(self):
        bad = copy.deepcopy(self.ep)
        row = _row(bad, lambda ep, r: r["account"] == "1200" and r["invoice_id"] and not r["payment_id"])
        bad["tables"]["ledger"] += [
            {**row, "row_id": "L99998", "account": "6100", "debit_minor": 500, "credit_minor": 0},
            {**row, "row_id": "L99999", "account": "1000", "debit_minor": 0, "credit_minor": 500},
        ]
        bad["manifest"]["counts"]["ledger"] += 2
        problems = verify_episode(bad)
        self.assertTrue(any("not allowed in invoice journal" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
