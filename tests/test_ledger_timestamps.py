"""Tests and measurements for ledger timestamp invariants across generated books (T3).

Covers:
(a) Payment journal timestamps vs payment document timestamps (instant equality via parse_ts,
    internal consistency within payment journals).
(b) Invoice booking timestamps vs invoice issued_at for in-period invoices with no truth issue
    (two booking rows share one instant >= issued_at and at most 3 calendar days later in
    company-local date due to generator legitimate posting lag).
(c) Credit-note rows in hard mode (reversal rows Dr 4000 / Cr 1200 are strictly later than booking).
"""

from __future__ import annotations

import copy
from datetime import date
import unittest

from auditenv.fuzz import HEAVY
from auditenv.generator import generate
from auditenv.money import local_date, parse_offset, parse_ts


def check_payment_journal_timestamps(ep: dict) -> list[str]:
    """Check (a): payment journal rows share one instant equal to the payment document timestamp."""
    problems = []
    tables = ep["tables"]
    payments = {pay["payment_id"]: pay for pay in tables["payments"]}

    pay_groups: dict[str, list[dict]] = {}
    for r in tables["ledger"]:
        if r["payment_id"]:
            pay_groups.setdefault(r["payment_id"], []).append(r)

    for pid, rows in pay_groups.items():
        if pid not in payments:
            problems.append(f"Payment journal {pid} references unknown payment document")
            continue
        pay_doc = payments[pid]
        pay_dt = parse_ts(pay_doc["timestamp"])

        instants = {parse_ts(r["timestamp"]) for r in rows}
        if len(instants) != 1:
            problems.append(f"Payment {pid} journal rows have differing instants: {instants}")

        for r in rows:
            if parse_ts(r["timestamp"]) != pay_dt:
                problems.append(
                    f"Payment {pid} row {r.get('row_id')} instant {r['timestamp']} != doc {pay_doc['timestamp']}"
                )

    return problems


def check_invoice_booking_timestamps(ep: dict) -> tuple[list[str], dict[str, int]]:
    """Check (b): in-period invoices without truth issues have 2 booking rows sharing 1 instant in [0, 3] lag days.

    Returns:
        (problems, exceptions_by_truth_issue)
    """
    problems = []
    exceptions_by_issue: dict[str, int] = {}

    tables = ep["tables"]
    manifest = ep["manifest"]
    tz = parse_offset(manifest["timezone"])
    ps = date.fromisoformat(manifest["period_start"])
    pe = date.fromisoformat(manifest["period_end"])

    invoices = {inv["invoice_id"]: inv for inv in tables["invoices"]}
    issue_affected_ids: dict[str, list[str]] = {}
    for iss in ep["truth"]["issues"]:
        for aff_id in iss["affected_ids"]:
            issue_affected_ids.setdefault(aff_id, []).append(iss["type"])

    booking_groups: dict[str, list[dict]] = {}
    for r in tables["ledger"]:
        if r["invoice_id"] and not r["payment_id"]:
            if (r["account"] == "1200" and r["debit_minor"] > 0) or (r["account"] == "4000" and r["credit_minor"] > 0):
                booking_groups.setdefault(r["invoice_id"], []).append(r)

    for iid, inv in invoices.items():
        inv_cdate = local_date(inv["issued_at"], tz)
        if not (ps <= inv_cdate <= pe):
            continue  # out-of-period invoices (e.g. period_cutoff) are handled separately

        rows = booking_groups.get(iid, [])
        if not rows:
            continue

        has_issue = iid in issue_affected_ids
        instants = {parse_ts(r["timestamp"]) for r in rows}
        inv_dt = parse_ts(inv["issued_at"])
        row_cdate = local_date(rows[0]["timestamp"], tz)
        cdate_diff = (row_cdate - inv_cdate).days

        valid = len(rows) == 2 and len(instants) == 1 and list(instants)[0] >= inv_dt and 0 <= cdate_diff <= 3

        if not has_issue:
            if not valid:
                problems.append(
                    f"Invoice {iid} (no issue) booking invalid: rows={len(rows)}, instants={len(instants)}, "
                    f"cdate_diff={cdate_diff}"
                )
        else:
            if not valid:
                for itype in issue_affected_ids[iid]:
                    exceptions_by_issue[itype] = exceptions_by_issue.get(itype, 0) + 1

    return problems, exceptions_by_issue


def check_credit_note_timestamps(ep: dict) -> list[str]:
    """Check (c): hard mode credit-note rows are strictly later than the original booking."""
    problems = []
    tables = ep["tables"]

    booking_rows_by_inv: dict[str, list[dict]] = {}
    cn_rows_by_inv: dict[str, list[dict]] = {}

    for r in tables["ledger"]:
        if r["invoice_id"] and not r["payment_id"]:
            iid = r["invoice_id"]
            is_booking = (r["account"] == "1200" and r["debit_minor"] > 0) or (
                r["account"] == "4000" and r["credit_minor"] > 0
            )
            is_cn = (r["account"] == "4000" and r["debit_minor"] > 0) or (
                r["account"] == "1200" and r["credit_minor"] > 0
            )
            if is_booking:
                booking_rows_by_inv.setdefault(iid, []).append(r)
            elif is_cn:
                cn_rows_by_inv.setdefault(iid, []).append(r)

    for iid, cn_rows in cn_rows_by_inv.items():
        booking_rows = booking_rows_by_inv.get(iid, [])
        if not booking_rows:
            problems.append(f"Credit note for invoice {iid} lacks booking rows")
            continue

        for r in cn_rows:
            r_dt = parse_ts(r["timestamp"])
            if not all(r_dt > parse_ts(br["timestamp"]) for br in booking_rows):
                problems.append(f"Credit note row {r.get('row_id')} for invoice {iid} not strictly later than booking")

    return problems


class LedgerTimestampsTest(unittest.TestCase):
    def test_payment_journal_timestamps_heavy_default(self):
        """Check (a) on 100 seeds heavy default: 0 instant mismatches across 7,057 payment rows."""
        total_rows = 0
        for seed in range(100):
            ep = generate(seed, HEAVY)
            problems = check_payment_journal_timestamps(ep)
            self.assertEqual(problems, [], f"Seed {seed} had payment timestamp problems: {problems}")
            total_rows += sum(1 for r in ep["tables"]["ledger"] if r["payment_id"])
        self.assertEqual(total_rows, 7057)

    def test_payment_journal_timestamps_heavy_hard(self):
        """Check (a) on 100 seeds heavy hard: 0 instant mismatches across 7,189 payment rows."""
        total_rows = 0
        cfg = {**HEAVY, "difficulty": "hard"}
        for seed in range(100):
            ep = generate(seed, cfg)
            problems = check_payment_journal_timestamps(ep)
            self.assertEqual(problems, [], f"Seed {seed} (hard) had payment timestamp problems: {problems}")
            total_rows += sum(1 for r in ep["tables"]["ledger"] if r["payment_id"])
        self.assertEqual(total_rows, 7189)

    def test_invoice_booking_timestamps_heavy_default(self):
        """Check (b) on 100 seeds heavy default: 3,298 clean in-period invoices satisfy 0-3 lag days, 0 violations."""
        clean_invoices = 0
        issue_invoices = 0
        all_exceptions: dict[str, int] = {}
        for seed in range(100):
            ep = generate(seed, HEAVY)
            problems, exc = check_invoice_booking_timestamps(ep)
            self.assertEqual(problems, [], f"Seed {seed} had invoice booking problems: {problems}")
            for k, v in exc.items():
                all_exceptions[k] = all_exceptions.get(k, 0) + v

            manifest = ep["manifest"]
            tz = parse_offset(manifest["timezone"])
            ps = date.fromisoformat(manifest["period_start"])
            pe = date.fromisoformat(manifest["period_end"])
            invoices = {inv["invoice_id"]: inv for inv in ep["tables"]["invoices"]}
            issue_ids = {aff for iss in ep["truth"]["issues"] for aff in iss["affected_ids"]}
            for iid, inv in invoices.items():
                if ps <= local_date(inv["issued_at"], tz) <= pe:
                    if iid in issue_ids:
                        issue_invoices += 1
                    else:
                        clean_invoices += 1

        self.assertEqual(clean_invoices, 3298)
        self.assertEqual(issue_invoices, 839)
        # Even invoices with truth issues (fx_error, payment_allocation, duplicate_invoice) preserve the [0, 3] lag
        self.assertEqual(all_exceptions, {})

    def test_invoice_booking_timestamps_heavy_hard(self):
        """Check (b) on 100 seeds heavy hard: 3,552 clean in-period invoices satisfy 0-3 lag days, 0 violations."""
        clean_invoices = 0
        issue_invoices = 0
        all_exceptions: dict[str, int] = {}
        cfg = {**HEAVY, "difficulty": "hard"}
        for seed in range(100):
            ep = generate(seed, cfg)
            problems, exc = check_invoice_booking_timestamps(ep)
            self.assertEqual(problems, [], f"Seed {seed} (hard) had invoice booking problems: {problems}")
            for k, v in exc.items():
                all_exceptions[k] = all_exceptions.get(k, 0) + v

            manifest = ep["manifest"]
            tz = parse_offset(manifest["timezone"])
            ps = date.fromisoformat(manifest["period_start"])
            pe = date.fromisoformat(manifest["period_end"])
            invoices = {inv["invoice_id"]: inv for inv in ep["tables"]["invoices"]}
            issue_ids = {aff for iss in ep["truth"]["issues"] for aff in iss["affected_ids"]}
            for iid, inv in invoices.items():
                if ps <= local_date(inv["issued_at"], tz) <= pe:
                    if iid in issue_ids:
                        issue_invoices += 1
                    else:
                        clean_invoices += 1

        self.assertEqual(clean_invoices, 3552)
        self.assertEqual(issue_invoices, 842)
        self.assertEqual(all_exceptions, {})

    def test_credit_note_timestamps_heavy_hard(self):
        """Check (c) on 100 seeds heavy hard: all 498 credit-note rows are strictly later than initial booking."""
        total_cn = 0
        cfg = {**HEAVY, "difficulty": "hard"}
        for seed in range(100):
            ep = generate(seed, cfg)
            problems = check_credit_note_timestamps(ep)
            self.assertEqual(problems, [], f"Seed {seed} had credit note problems: {problems}")
            for r in ep["tables"]["ledger"]:
                if (
                    r["invoice_id"]
                    and not r["payment_id"]
                    and (
                        (r["account"] == "4000" and r["debit_minor"] > 0)
                        or (r["account"] == "1200" and r["credit_minor"] > 0)
                    )
                ):
                    total_cn += 1
        self.assertEqual(total_cn, 498)

    def test_credit_note_empty_in_default_mode(self):
        """Check (c): default mode generates 0 credit-note reversal rows."""
        total_cn = 0
        for seed in range(25):
            ep = generate(seed, HEAVY)
            for r in ep["tables"]["ledger"]:
                if (
                    r["invoice_id"]
                    and not r["payment_id"]
                    and (
                        (r["account"] == "4000" and r["debit_minor"] > 0)
                        or (r["account"] == "1200" and r["credit_minor"] > 0)
                    )
                ):
                    total_cn += 1
        self.assertEqual(total_cn, 0)

    def test_tampered_payment_instant_detected(self):
        """Tampering a payment row instant is detected."""
        ep = generate(0, HEAVY)
        bad = copy.deepcopy(ep)
        row = next(r for r in bad["tables"]["ledger"] if r["payment_id"])
        row["timestamp"] = "2026-11-20T12:00:00+00:00"
        problems = check_payment_journal_timestamps(bad)
        self.assertTrue(any("instant" in p and row["payment_id"] in p for p in problems))

    def test_tampered_booking_earlier_than_issued_at_detected(self):
        """Tampering an in-period clean invoice booking to predate issued_at is detected."""
        ep = generate(0, HEAVY)
        bad = copy.deepcopy(ep)
        manifest = bad["manifest"]
        tz = parse_offset(manifest["timezone"])
        ps = date.fromisoformat(manifest["period_start"])
        pe = date.fromisoformat(manifest["period_end"])
        invoices = {inv["invoice_id"]: inv for inv in bad["tables"]["invoices"]}
        issue_ids = {aff for iss in bad["truth"]["issues"] for aff in iss["affected_ids"]}

        row = next(
            r for r in bad["tables"]["ledger"]
            if r["invoice_id"]
            and not r["payment_id"]
            and r["account"] == "1200"
            and r["debit_minor"] > 0
            and r["invoice_id"] not in issue_ids
            and ps <= local_date(invoices[r["invoice_id"]]["issued_at"], tz) <= pe
        )
        row["timestamp"] = "2020-01-01T00:00:00+00:00"
        problems, _ = check_invoice_booking_timestamps(bad)
        self.assertTrue(any(row["invoice_id"] in p and "invalid" in p for p in problems))

    def test_tampered_booking_lag_over_3_days_detected(self):
        """Tampering an in-period clean invoice booking to lag by > 3 days is detected."""
        ep = generate(0, HEAVY)
        bad = copy.deepcopy(ep)
        manifest = bad["manifest"]
        tz = parse_offset(manifest["timezone"])
        ps = date.fromisoformat(manifest["period_start"])
        pe = date.fromisoformat(manifest["period_end"])
        invoices = {inv["invoice_id"]: inv for inv in bad["tables"]["invoices"]}
        issue_ids = {aff for iss in bad["truth"]["issues"] for aff in iss["affected_ids"]}

        iid = next(
            r["invoice_id"]
            for r in bad["tables"]["ledger"]
            if r["invoice_id"]
            and not r["payment_id"]
            and r["account"] == "1200"
            and r["debit_minor"] > 0
            and r["invoice_id"] not in issue_ids
            and ps <= local_date(invoices[r["invoice_id"]]["issued_at"], tz) <= pe - date.resolution * 5
        )
        # Move both booking rows to 5 days later
        for r in bad["tables"]["ledger"]:
            if r["invoice_id"] == iid and not r["payment_id"]:
                orig_dt = parse_ts(r["timestamp"])
                r["timestamp"] = (orig_dt + date.resolution * 5).isoformat()

        problems, _ = check_invoice_booking_timestamps(bad)
        self.assertTrue(any(iid in p and "cdate_diff=5" in p for p in problems))

    def test_tampered_credit_note_not_later_detected(self):
        """Tampering a credit note row to predate initial booking is detected."""
        cfg = {**HEAVY, "difficulty": "hard"}
        ep = generate(0, cfg)
        bad = copy.deepcopy(ep)
        cn_row = next(
            r for r in bad["tables"]["ledger"]
            if r["invoice_id"] and not r["payment_id"] and r["account"] == "4000" and r["debit_minor"] > 0
        )
        cn_row["timestamp"] = "2020-01-01T00:00:00+00:00"
        problems = check_credit_note_timestamps(bad)
        self.assertTrue(any("not strictly later than booking" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
