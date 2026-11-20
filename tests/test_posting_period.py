import copy
import unittest

from auditenv.generator import generate
from auditenv.verify import verify_episode


class PostingPeriodTest(unittest.TestCase):
    def test_clean_seed_0_intact_passes(self):
        ep = generate(0, {"errors": {}})
        self.assertEqual(verify_episode(ep), [])

    def test_revenue_credit_moved_to_2099_on_clean_seed_0_fails(self):
        """Moving a revenue credit to 2099 on clean seed 0 must fail verification."""
        ep = generate(0, {"errors": {}})
        bad = copy.deepcopy(ep)
        rev_row = next(r for r in bad["tables"]["ledger"] if r["account"] == "4000" and r["credit_minor"] > 0)
        rev_row["timestamp"] = "2099-06-15T12:00:00+00:00"

        problems = verify_episode(bad)
        self.assertTrue(
            any(f"ledger row {rev_row['row_id']} outside the period" in p for p in problems),
            f"Expected out-of-period error for {rev_row['row_id']}, got: {problems}",
        )

    def test_expense_and_payment_postings_outside_period_fail(self):
        """Expense rows and payment ledger rows outside the period must fail verification."""
        ep = generate(0, {"errors": {}})

        # Corrupt an expense row
        bad_exp = copy.deepcopy(ep)
        exp_row = next(r for r in bad_exp["tables"]["ledger"] if r["invoice_id"] is None and r["payment_id"] is None)
        exp_row["timestamp"] = "2099-01-01T10:00:00+00:00"
        self.assertTrue(any(f"ledger row {exp_row['row_id']} outside the period" in p for p in verify_episode(bad_exp)))

        # Corrupt a payment row
        bad_pay = copy.deepcopy(ep)
        pay_row = next(r for r in bad_pay["tables"]["ledger"] if r["payment_id"] is not None)
        pay_row["timestamp"] = "2099-01-01T10:00:00+00:00"
        self.assertTrue(any(f"ledger row {pay_row['row_id']} outside the period" in p for p in verify_episode(bad_pay)))

    def test_reverted_journal_out_of_period_fails(self):
        """Out-of-period postings in pre-injection (reverted) books must be caught."""
        ep = generate(1)
        bad = copy.deepcopy(ep)
        before_rows = None
        for inj in bad["provenance"]["injections"]:
            for ch in inj["changes"]:
                if ch.get("before"):
                    before_rows = ch["before"]
                    break
            if before_rows:
                break
        self.assertIsNotNone(before_rows)
        self.assertGreater(len(before_rows), 0)
        target_row_id = before_rows[0]["row_id"]
        before_rows[0]["timestamp"] = "2099-05-01T12:00:00+00:00"

        problems = verify_episode(bad)
        self.assertTrue(
            any("pre-injection:" in p and f"ledger row {target_row_id} outside the period" in p for p in problems),
            f"Expected pre-injection out-of-period error for {target_row_id}, got: {problems}",
        )

    def test_boundary_examples_using_company_local_dates(self):
        """Test boundary conditions using company-local dates."""
        ep = generate(0, {"errors": {}})
        expenses = [r for r in ep["tables"]["ledger"] if r["invoice_id"] is None and r["payment_id"] is None]
        journal = [r for r in expenses if r["timestamp"] == expenses[0]["timestamp"]]
        cases = [
            ("2026-08-01T00:00:00-03:00", True),
            ("2026-08-31T23:59:59-03:00", True),
            ("2026-07-31T23:59:59-03:00", False),
            ("2026-09-01T00:00:00-03:00", False),
            ("2026-08-01T02:00:00+00:00", False),  # July 31 in the company timezone
            ("2026-09-01T01:00:00+00:00", True),   # August 31 in the company timezone
        ]
        for timestamp, valid in cases:
            with self.subTest(timestamp=timestamp):
                for row in journal:
                    row["timestamp"] = timestamp
                problems = verify_episode(ep)
                if valid:
                    self.assertEqual(problems, [])
                else:
                    self.assertIn(f"post-injection: ledger row {journal[0]['row_id']} outside the period", problems)


if __name__ == "__main__":
    unittest.main()
