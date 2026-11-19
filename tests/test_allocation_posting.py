import unittest

from auditenv.generator import generate
from auditenv.verify import verify_episode


class AllocationPostingTest(unittest.TestCase):
    def test_invoice_debit_cannot_prove_unapplied_payment(self):
        ep = generate(1, {"errors": {"payment_allocation": 1}})
        self.assertEqual(verify_episode(ep), [])
        issue = ep["truth"]["issues"][0]
        evidence = issue["evidence_sets"][0]
        ledger = ep["tables"]["ledger"]
        unapplied = next(r for r in ledger if r["row_id"] in evidence and r["account"] == "2900")
        booking = next(r for r in ledger if r["invoice_id"] in issue["affected_ids"]
                       and r["payment_id"] is None and r["account"] == "1200" and r["debit_minor"] > 0)
        evidence[evidence.index(unapplied["row_id"])] = booking["row_id"]
        self.assertTrue(any("does not reproduce" in problem for problem in verify_episode(ep)))
