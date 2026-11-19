"""Tests for payment posting entity identity across generated books (T2)."""

from __future__ import annotations

import unittest

from auditenv.fuzz import HEAVY
from auditenv.generator import generate


def check_payment_entity_identity(ep: dict) -> list[str]:
    """Independently compare entity IDs on payment receivables postings with referenced invoices."""
    problems = []
    invoices = {inv["invoice_id"]: inv for inv in ep["tables"]["invoices"]}
    payments = {pay["payment_id"]: pay for pay in ep["tables"]["payments"]}

    for row in ep["tables"]["ledger"]:
        if row["account"] == "1200" and row["credit_minor"] > 0 and row["payment_id"]:
            pid = row["payment_id"]
            iid = row["invoice_id"]
            row_ent = row["entity_id"]

            if pid not in payments:
                problems.append(f"Row {row.get('row_id')} references unknown payment {pid}")
                continue
            pay = payments[pid]

            if not iid:
                problems.append(f"Payment receivables row {row.get('row_id')} on {pid} lacks invoice_id")
                continue

            if iid not in invoices:
                problems.append(f"Payment receivables row {row.get('row_id')} references unknown invoice {iid}")
                continue
            inv = invoices[iid]

            if row_ent != inv["entity_id"]:
                problems.append(
                    f"Payment {pid} row {row.get('row_id')} entity {row_ent} != invoice {iid} entity {inv['entity_id']}"
                )

            refs = [r["invoice_id"] for r in (pay["invoice_refs"] or [])]
            if iid not in refs:
                problems.append(f"Payment {pid} row {row.get('row_id')} invoice {iid} not in payment invoice_refs {refs}")

    return problems


class PaymentEntitiesTest(unittest.TestCase):
    def test_payment_entity_identity_heavy_default(self):
        """100 heavy default seeds have 0 entity mismatches on all payment receivables postings."""
        total_postings = 0
        for seed in range(100):
            ep = generate(seed, HEAVY)
            postings = [
                r for r in ep["tables"]["ledger"] if r["account"] == "1200" and r["credit_minor"] > 0 and r["payment_id"]
            ]
            total_postings += len(postings)
            problems = check_payment_entity_identity(ep)
            self.assertEqual(problems, [], f"Seed {seed} had payment entity identity problems: {problems}")
        self.assertEqual(total_postings, 2565)

    def test_payment_entity_identity_heavy_hard(self):
        """100 heavy hard seeds have 0 entity mismatches on all payment receivables postings."""
        total_postings = 0
        cfg = {**HEAVY, "difficulty": "hard"}
        for seed in range(100):
            ep = generate(seed, cfg)
            postings = [
                r for r in ep["tables"]["ledger"] if r["account"] == "1200" and r["credit_minor"] > 0 and r["payment_id"]
            ]
            total_postings += len(postings)
            problems = check_payment_entity_identity(ep)
            self.assertEqual(problems, [], f"Seed {seed} (hard) had payment entity identity problems: {problems}")
        self.assertEqual(total_postings, 2583)

    def test_payment_entity_identity_clean_seeds(self):
        """Clean seeds also have 0 entity mismatches on all payment receivables postings."""
        for seed in range(25):
            ep = generate(seed, {"errors": {}})
            problems = check_payment_entity_identity(ep)
            self.assertEqual(problems, [], f"Clean seed {seed} had problems: {problems}")

    def test_tampered_entity_id_detected(self):
        """A tampered entity_id on a payment receivables row is caught."""
        ep = generate(0, HEAVY)
        row = next(r for r in ep["tables"]["ledger"] if r["account"] == "1200" and r["credit_minor"] > 0 and r["payment_id"])
        row["entity_id"] = "CUST_TAMPERED"
        problems = check_payment_entity_identity(ep)
        self.assertTrue(any("CUST_TAMPERED" in p for p in problems))

    def test_tampered_invoice_ref_detected(self):
        """A payment receivables row referencing an unlinked invoice is caught."""
        ep = generate(0, HEAVY)
        row = next(r for r in ep["tables"]["ledger"] if r["account"] == "1200" and r["credit_minor"] > 0 and r["payment_id"])
        pay = next(p for p in ep["tables"]["payments"] if p["payment_id"] == row["payment_id"])
        refs = {r["invoice_id"] for r in (pay["invoice_refs"] or [])}
        other_inv = next(i for i in ep["tables"]["invoices"] if i["invoice_id"] not in refs)
        row["invoice_id"] = other_inv["invoice_id"]
        problems = check_payment_entity_identity(ep)
        self.assertTrue(any("not in payment invoice_refs" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
