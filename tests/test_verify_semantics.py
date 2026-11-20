"""Tampers the verifier used to accept although truth labels or the books contradict CONTRACT §1-§3.

Each case starts from a valid generated episode, changes the books and/or truth consistently (provenance records
the change, so the reverted books stay clean), and must be rejected by `verify_episode`.
"""

import copy
import unittest
from datetime import datetime

from auditenv.generator import generate
from auditenv.money import convert, parse_offset
from auditenv.verify import line_key, verify_episode

INTERACTING = {"errors": {"fx_error": 1, "duplicate_invoice": 1}, "interacting": {"I1": 1, "I2": 1}}


def inv_rows(ep, iid):
    return [r for r in ep["tables"]["ledger"] if r["invoice_id"] == iid and not r["payment_id"]]


def pay_rows(ep, pid):
    return [r for r in ep["tables"]["ledger"] if r["payment_id"] == pid]


def record_change(ep, journal, before_rows, description):
    """Declare the tamper as an injection so the pre-injection books revert to the clean ones."""
    ep["provenance"]["injections"].append({
        "issue_id": f"TAMPER-{len(ep['provenance']['injections']) + 1}", "type": "tamper", "scenario": "single",
        "description": description, "changes": [{"journal": journal, "before": copy.deepcopy(before_rows),
                                                 "after": None}], "documents_added": []})


def add_issue(ep, typ, affected, amount, evidence_sets):
    ep["truth"]["issues"].append({
        "issue_id": f"ISS-T{len(ep['truth']['issues']) + 1}", "type": typ, "scenario": "single",
        "affected_ids": sorted(affected), "expected_amount_minor": amount,
        "currency": ep["manifest"]["base_currency"], "evidence_sets": evidence_sets})


def booked_invoice(ep, foreign):
    m = ep["manifest"]
    for inv in ep["tables"]["invoices"]:
        rows = inv_rows(ep, inv["invoice_id"])
        if len(rows) == 2 and (inv["currency"] != m["base_currency"]) == foreign \
                and m["period_start"] <= inv["issued_at"][:10] <= m["period_end"]:
            return inv, rows
    raise AssertionError("no candidate invoice")


class FxLabelTest(unittest.TestCase):
    """fx_error = an amount converted with the rate of the wrong date (task text, CONTRACT §3)."""

    def setUp(self):
        self.ep = generate(0, {"errors": {}})
        self.assertEqual(verify_episode(self.ep), [])

    def overbook(self, foreign, delta):
        ep = copy.deepcopy(self.ep)
        inv, rows = booked_invoice(ep, foreign)
        before = copy.deepcopy(rows)
        for r in rows:
            r["debit_minor" if r["account"] == "1200" else "credit_minor"] += delta
        record_change(ep, "inv:" + inv["invoice_id"], before, "tamper: invoice booked at a wrong amount")
        ar = next(r for r in rows if r["account"] == "1200")
        return ep, inv, ar

    def test_base_currency_misbooking_is_not_an_fx_error(self):
        ep, inv, ar = self.overbook(foreign=False, delta=500)
        add_issue(ep, "fx_error", [inv["invoice_id"]], 500, [[inv["doc_id"], ar["row_id"]]])
        self.assertTrue(any("no FX" in p or "no published rate" in p for p in verify_episode(ep)), verify_episode(ep))

    def test_amount_no_published_rate_produces_is_not_an_fx_error(self):
        ep, inv, ar = self.overbook(foreign=True, delta=12345)
        base = ep["manifest"]["base_currency"]
        reachable = {convert(inv["total_minor"], inv["currency"], base, r["rate"]) for r in ep["tables"]["fx"]
                     if (r["source_currency"], r["target_currency"]) == (inv["currency"], base)}
        self.assertNotIn(ar["debit_minor"], reachable)
        tz = parse_offset(ep["manifest"]["timezone"])
        fid = f"{datetime.fromisoformat(inv['issued_at']).astimezone(tz).date()}:{inv['currency']}:{base}"
        add_issue(ep, "fx_error", [inv["invoice_id"]], 12345, [[inv["doc_id"], ar["row_id"], fid]])
        self.assertTrue(any("no published rate" in p for p in verify_episode(ep)), verify_episode(ep))


class UnappliedCashTest(unittest.TestCase):
    """A short allocation moves exactly the unallocated part of the reference to 2900 (CONTRACT §2)."""

    def test_shortfall_cannot_hide_the_whole_reference_in_2900(self):
        ep = copy.deepcopy(generate(0, {"errors": {}}))
        base = ep["manifest"]["base_currency"]
        pay = next(p for p in ep["tables"]["payments"]
                   if p["currency"] != base and p["invoice_refs"] and len(p["invoice_refs"]) == 1
                   and p["amount_minor"] == p["invoice_refs"][0]["amount_minor"]
                   and not any(r["account"] == "2900" for r in pay_rows(ep, p["payment_id"])))
        pid, ref = pay["payment_id"], pay["invoice_refs"][0]
        inv = next(i for i in ep["tables"]["invoices"] if i["invoice_id"] == ref["invoice_id"])
        rows = pay_rows(ep, pid)
        before = copy.deepcopy(rows)
        ar = next(r for r in rows if r["account"] == "1200")
        cash = next(r for r in rows if r["account"] == "1000")
        ar["credit_minor"] -= 1  # declared shortfall: one minor unit
        tz = parse_offset(ep["manifest"]["timezone"])
        day = datetime.fromisoformat(pay["timestamp"]).astimezone(tz).date().isoformat()
        rate = next(r["rate"] for r in ep["tables"]["fx"] if r["fx_id"] == f"{day}:{pay['currency']}:{base}")
        whole = convert(ref["amount_minor"], pay["currency"], base, rate)  # but the whole reference goes to 2900
        ledger = ep["tables"]["ledger"]
        ledger.append({**cash, "row_id": "T2900", "account": "2900", "debit_minor": 0, "credit_minor": whole})
        for r in [r for r in rows if r["account"] == "7900"]:
            ledger.remove(r)
        diff = sum(r["debit_minor"] - r["credit_minor"] for r in pay_rows(ep, pid))
        ledger.append({**cash, "row_id": "T7900", "account": "7900", "debit_minor": max(-diff, 0),
                       "credit_minor": max(diff, 0)})
        ep["manifest"]["counts"]["ledger"] = len(ledger)
        record_change(ep, "pay:" + pid, before, "tamper: 1-unit shortfall, whole reference moved to 2900")
        idate = datetime.fromisoformat(inv["issued_at"]).astimezone(tz).date().isoformat()
        add_issue(ep, "payment_allocation", [inv["invoice_id"], pid], 1,
                  [[pay["doc_id"], inv["doc_id"], ar["row_id"], f"{idate}:{inv['currency']}:{base}"]])
        self.assertTrue(any("incorrect unapplied cash" in p for p in verify_episode(ep)), verify_episode(ep))


class ScenarioLabelTest(unittest.TestCase):
    """I1 = allocation + FX error on one payment, I2 = cutoff + FX error on one invoice (CONTRACT §3)."""

    def setUp(self):
        self.ep = generate(0, INTERACTING)
        self.assertEqual(verify_episode(self.ep), [])
        self.assertEqual(sorted(i["scenario"] for i in self.ep["truth"]["issues"]),
                         ["I1", "I1", "I2", "I2", "single", "single"])

    def relabel(self, mapping):
        ep = copy.deepcopy(self.ep)
        for iss in ep["truth"]["issues"]:
            iss["scenario"] = mapping[iss["scenario"]]
        return verify_episode(ep)

    def test_swapped_labels_are_rejected(self):
        self.assertTrue(any("scenario" in p for p in self.relabel({"I1": "I2", "I2": "I1", "single": "single"})))

    def test_interacting_errors_labelled_single_are_rejected(self):
        self.assertTrue(any("scenario" in p for p in self.relabel({"I1": "single", "I2": "single",
                                                                   "single": "single"})))

    def test_single_errors_labelled_interacting_are_rejected(self):
        self.assertTrue(any("scenario" in p for p in self.relabel({"I1": "I1", "I2": "I2", "single": "I1"})))


class CreditNoteReissueTest(unittest.TestCase):
    """Hard mode: a cancelled invoice is replaced by a new invoice with identical line items (CONTRACT §2)."""

    def test_credit_note_without_replacement_is_rejected(self):
        ep = copy.deepcopy(generate(3, {"difficulty": "hard", "errors": {}}))
        self.assertEqual(verify_episode(ep), [])
        t, pe = ep["tables"], ep["manifest"]["period_end"]
        paid = {r["invoice_id"] for p in t["payments"] for r in p["invoice_refs"] or []}
        keys = {}
        for inv in t["invoices"]:
            keys.setdefault((inv["entity_id"], inv["currency"], line_key(inv["line_items"])), []).append(inv)
        target = next(inv for inv in sorted(t["invoices"], key=lambda i: i["issued_at"])
                      if len(inv_rows(ep, inv["invoice_id"])) == 2 and inv["invoice_id"] not in paid
                      and len(keys[(inv["entity_id"], inv["currency"], line_key(inv["line_items"]))]) == 1
                      and inv["issued_at"][:10] < pe[:8] + "20")
        rows = inv_rows(ep, target["invoice_id"])
        before = copy.deepcopy(rows)
        ar = next(r for r in rows if r["account"] == "1200")
        ts = datetime.fromisoformat(ar["timestamp"]).replace(day=25).isoformat()
        amt = ar["debit_minor"]
        t["ledger"] += [{**ar, "row_id": "TCN1", "timestamp": ts, "account": "4000", "debit_minor": amt,
                         "credit_minor": 0},
                        {**ar, "row_id": "TCN2", "timestamp": ts, "account": "1200", "debit_minor": 0,
                         "credit_minor": amt}]
        ep["manifest"]["counts"]["ledger"] = len(t["ledger"])
        record_change(ep, "inv:" + target["invoice_id"], before, "tamper: revenue reversed, no re-issue")
        self.assertTrue(any("replacement" in p for p in verify_episode(ep)), verify_episode(ep))


class PublicRecordTypesTest(unittest.TestCase):
    """Money is int minor units and timestamps carry an offset (CONTRACT §1, §2)."""

    def setUp(self):
        self.ep = generate(0, {"errors": {}})
        self.base = self.ep["manifest"]["base_currency"]

    def test_fractional_payment_amount_is_rejected(self):
        ep = copy.deepcopy(self.ep)
        pay = next(p for p in ep["tables"]["payments"] if p["invoice_refs"] is None and p["currency"] != self.base)
        pay["amount_minor"] += 0.9 if pay["amount_minor"] > 0 else -0.9
        self.assertTrue(any("amount_minor must be an integer" in p for p in verify_episode(ep)), verify_episode(ep))

    def test_fractional_invoice_ref_is_rejected(self):
        ep = copy.deepcopy(self.ep)
        pay = next(p for p in ep["tables"]["payments"] if p["currency"] != self.base and p["invoice_refs"]
                   and len(p["invoice_refs"]) == 1 and p["invoice_refs"][0]["amount_minor"] == p["amount_minor"])
        pay["amount_minor"] += 0.75
        pay["invoice_refs"][0]["amount_minor"] += 0.75
        self.assertTrue(any("amount_minor must be an integer" in p for p in verify_episode(ep)), verify_episode(ep))

    def test_timestamps_without_offset_are_rejected(self):
        ep = copy.deepcopy(self.ep)
        tz = parse_offset(ep["manifest"]["timezone"])
        pay = next(p for p in ep["tables"]["payments"] if p["invoice_refs"] is None and p["currency"] != self.base)
        naive = datetime.fromisoformat(pay["timestamp"]).astimezone(tz).replace(tzinfo=None).isoformat()
        pay["timestamp"] = naive
        for r in pay_rows(ep, pay["payment_id"]):
            r["timestamp"] = naive
        self.assertTrue(any("timezone offset" in p for p in verify_episode(ep)), verify_episode(ep))


if __name__ == "__main__":
    unittest.main()
