import copy
import unittest

from auditenv.generator import generate
from auditenv.verify import _structure, verify_episode


class LedgerRefsTest(unittest.TestCase):
    def test_intact_episodes_pass_verification(self):
        for seed in (7, 42, 100):
            ep = generate(seed)
            self.assertEqual(verify_episode(ep), [])
            self.assertEqual(_structure(ep), [])

    def test_seed_7_clean_paired_expense_rows_with_nonexistent_payment_fails(self):
        """Seed 7 clean paired expense rows assigned a nonexistent payment must fail verification."""
        ep = generate(7)
        self.assertEqual(verify_episode(ep), [])

        ledger = ep["tables"]["ledger"]
        # Find clean paired expense rows (invoice_id is None and payment_id is None)
        expense_rows = [r for r in ledger if r["invoice_id"] is None and r["payment_id"] is None]
        self.assertGreater(len(expense_rows), 0)

        ts = expense_rows[0]["timestamp"]
        pair = [r for r in expense_rows if r["timestamp"] == ts]
        self.assertGreaterEqual(len(pair), 2)
        # Verify the pair forms a balanced journal
        self.assertEqual(sum(r["debit_minor"] for r in pair), sum(r["credit_minor"] for r in pair))

        tampered = copy.deepcopy(ep)
        for r in tampered["tables"]["ledger"]:
            if r["timestamp"] == ts and r["invoice_id"] is None and r["payment_id"] is None:
                r["payment_id"] = "PAY-NONEXISTENT"

        # _structure directly detects dangling payment references
        structure_problems = _structure(tampered)
        self.assertTrue(
            any("references unknown payment PAY-NONEXISTENT" in p for p in structure_problems),
            f"Expected unknown payment problem, got: {structure_problems}",
        )

        # Full verify_episode fails verification
        problems = verify_episode(tampered)
        self.assertTrue(
            any("references unknown payment PAY-NONEXISTENT" in p for p in problems),
            f"Expected verify_episode to fail, got: {problems}",
        )

    def test_dangling_invoice_reference_fails(self):
        """A ledger row referencing a nonexistent invoice must fail verification."""
        ep = generate(7)
        tampered = copy.deepcopy(ep)
        # Tamper the first invoice booking row
        inv_row = next(r for r in tampered["tables"]["ledger"] if r["invoice_id"] is not None)
        inv_row["invoice_id"] = "SI-9999-999999"

        structure_problems = _structure(tampered)
        self.assertTrue(any("references unknown invoice SI-9999-999999" in p for p in structure_problems))
        problems = verify_episode(tampered)
        self.assertTrue(any("references unknown invoice SI-9999-999999" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
