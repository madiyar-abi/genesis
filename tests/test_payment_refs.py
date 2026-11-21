"""Remittance references are document facts: they must be consistent whatever the payment's posting period.

An out-of-period payment is not booked, so the period-dependent checks (cash, AR credits, 2900) skip it; the
reference checks used to be skipped with them (audit f270e4d).
"""

import copy
import unittest

from auditenv.generator import generate
from auditenv.verify import Books, verify_episode

FUTURE, PAST = "2027-01-01T12:00:00+00:00", "2025-01-01T12:00:00+00:00"


def add_payment(ep, timestamp, refs, currency=None):
    """Append an unbooked payment document (copied from a real one) and return its id."""
    tables, counts = ep["tables"], ep["manifest"]["counts"]
    pay = dict(next(p for p in tables["payments"] if p["amount_minor"] > 0), payment_id="P-extra",
               doc_id="D-extra", timestamp=timestamp, invoice_refs=refs)
    if currency:
        pay["currency"] = currency
    tables["payments"].append(pay)
    counts["payments"] += 1
    counts["documents"] += 1
    return pay


def invoice(ep, **match):
    return next(i for i in ep["tables"]["invoices"] if all(i[k] == v for k, v in match.items()))


class OutOfPeriodRefsTest(unittest.TestCase):
    def setUp(self):
        self.ep = generate(2000, {"errors": {}})
        self.assertEqual(verify_episode(self.ep), [])
        self.pay = next(p for p in self.ep["tables"]["payments"] if p["amount_minor"] > 0)
        self.inv = invoice(self.ep, currency=self.pay["currency"])

    def rejected(self, timestamp, refs, words, currency=None):
        ep = copy.deepcopy(self.ep)
        add_payment(ep, timestamp, refs, currency)
        problems = verify_episode(ep)
        self.assertTrue(any("P-extra" in p and words in p for p in problems), problems)

    def test_valid_future_payments_pass(self):
        for refs in (None, [], [{"invoice_id": self.inv["invoice_id"], "amount_minor": self.pay["amount_minor"]}]):
            with self.subTest(refs=refs):
                ep = copy.deepcopy(self.ep)
                add_payment(ep, FUTURE, refs)
                self.assertEqual(verify_episode(ep), [])

    def test_unknown_invoice(self):
        self.rejected(FUTURE, [{"invoice_id": "nonexistent", "amount_minor": 1}], "unknown invoice nonexistent")

    def test_refs_exceed_payment(self):
        self.rejected(FUTURE, [{"invoice_id": self.inv["invoice_id"], "amount_minor": self.pay["amount_minor"] + 1}],
                      "refs exceed amount")

    def test_same_invoice_twice(self):
        ref = {"invoice_id": self.inv["invoice_id"], "amount_minor": 1}
        self.rejected(FUTURE, [ref, dict(ref)], "references an invoice twice")

    def test_non_positive_ref(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                self.rejected(FUTURE, [{"invoice_id": self.inv["invoice_id"], "amount_minor": amount}],
                              "non-positive invoice ref")

    def test_other_currency_invoice(self):
        other = next(i for i in self.ep["tables"]["invoices"] if i["currency"] != self.pay["currency"])
        self.rejected(FUTURE, [{"invoice_id": other["invoice_id"], "amount_minor": 1}],
                      f"other-currency invoice {other['invoice_id']}")

    def test_invoice_issued_after_payment(self):
        self.rejected(PAST, [{"invoice_id": self.inv["invoice_id"], "amount_minor": 1}], "issued after the payment")

    def test_cancelled_invoice(self):
        ep = generate(2000, {"errors": {}, "difficulty": "hard"})
        self.assertEqual(verify_episode(ep), [])
        books = Books(ep["manifest"], ep["tables"])
        books.discrepancies()
        cancelled = invoice(ep, invoice_id=sorted(books.voided)[0])
        add_payment(ep, FUTURE, [{"invoice_id": cancelled["invoice_id"], "amount_minor": 1}], cancelled["currency"])
        problems = verify_episode(ep)
        self.assertTrue(any("P-extra" in p and f"cancelled invoice {cancelled['invoice_id']}" in p
                            for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
