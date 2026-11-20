import unittest
from datetime import datetime, timedelta, timezone

from auditenv.generator import generate
from auditenv.verify import verify_episode


class InvoiceBookingTimeTest(unittest.TestCase):
    def test_invoice_booking_entries_must_share_an_instant(self):
        for difficulty in ("default", "hard"):
            with self.subTest(difficulty=difficulty):
                ep = generate(0, {"errors": {}, "difficulty": difficulty})
                ledger = ep["tables"]["ledger"]
                cancelled = {row["invoice_id"] for row in ledger
                             if row["account"] == "4000" and row["debit_minor"]}
                row = next(row for row in ledger if row["account"] == "4000" and row["credit_minor"]
                           and (difficulty == "default" or row["invoice_id"] in cancelled))
                booking = datetime.fromisoformat(row["timestamp"])
                row["timestamp"] = booking.astimezone(timezone.utc).isoformat()
                self.assertEqual(verify_episode(ep), [])
                row["timestamp"] = (booking + timedelta(seconds=1)).isoformat()
                message = f"invoice {row['invoice_id']}: booking debit and credit dated at different instants"
                self.assertCountEqual(verify_episode(ep), [f"pre-injection: {message}", f"post-injection: {message}"])
