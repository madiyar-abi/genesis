"""Rule-based reconciliation baseline policy (CONTRACT §2-3, §7).

Implements:
1. `reconcile_findings(manifest, tables) -> list[dict]`: pure function auditing
   ledger against invoices, payments and FX rates.
2. `Reconcile`: policy class that pages all tables and documents in `AuditEnv`,
   then submits findings.
"""

from __future__ import annotations

import collections
from datetime import date, datetime
from decimal import Decimal

from ..money import convert, local_date, parse_offset


def _line_key(items: list[dict]) -> tuple:
    """Lines compared without order, case or punctuation (re-typed copies in hard mode)."""
    return tuple(sorted(("".join(ch for ch in li["description"].lower() if ch.isalnum()), li["quantity"],
                         li["unit_price_minor"], li["amount_minor"]) for li in items))


def reconcile_findings(manifest: dict, tables: dict, hard: bool = False) -> list[dict]:
    """Audit public records and return detected financial misstatements.

    `hard=True` adds the hard-mode rules from the policy: line items match regardless of order,
    case and punctuation, and an invoice reversed by a full credit note is not a duplicate.

    Detects:
    - `duplicate_invoice`: same entity, currency, identical line items booked twice.
    - `period_cutoff`: invoice dated outside the period booked inside the period.
    - `fx_error`: foreign amount converted with wrong-date rate (invoice or payment).
    - `payment_allocation`: payment remittance advice not fully credited to AR.
    """
    tz = parse_offset(manifest["timezone"])
    base = manifest["base_currency"]
    p_start = date.fromisoformat(manifest["period_start"])
    p_end = date.fromisoformat(manifest["period_end"])

    fx_map: dict[tuple[str, str, str], Decimal] = {}
    for r in tables.get("fx", []):
        fx_map[(r["date"], r["source_currency"], r["target_currency"])] = Decimal(r["rate"])

    def get_rate(d: date, cur: str) -> Decimal:
        if cur == base:
            return Decimal("1")
        return fx_map.get((d.isoformat(), cur, base), Decimal("1"))

    def to_base(amt: int, cur: str, d: date) -> int:
        return convert(amt, cur, base, get_rate(d, cur))

    invoices = tables.get("invoices", [])
    payments = tables.get("payments", [])
    ledger = tables.get("ledger", [])

    inv_by_id = {i["invoice_id"]: i for i in invoices}

    ledger_by_inv: dict[str, list[dict]] = collections.defaultdict(list)
    ledger_by_pay: dict[str, list[dict]] = collections.defaultdict(list)
    for r in ledger:
        if r.get("invoice_id"):
            ledger_by_inv[r["invoice_id"]].append(r)
        if r.get("payment_id"):
            ledger_by_pay[r["payment_id"]].append(r)

    findings: list[dict] = []
    voided = set()
    if hard:  # full credit note: Cr 1200 on the invoice without a payment
        for iid, rows in ledger_by_inv.items():
            if any(r["account"] == "1200" and r["credit_minor"] > 0 and not r.get("payment_id") for r in rows):
                voided.add(iid)

    # ------------------------------------------------------------------
    # 1. duplicate_invoice
    # ------------------------------------------------------------------
    groups: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for inv in invoices:
        groups[(inv["entity_id"], inv["currency"])].append(inv)

    handled_dups: set[str] = set()
    for (ent, cur), inv_list in groups.items():
        if len(inv_list) < 2:
            continue
        for i in range(len(inv_list)):
            for j in range(i + 1, len(inv_list)):
                inv1, inv2 = inv_list[i], inv_list[j]
                id1, id2 = inv1["invoice_id"], inv2["invoice_id"]
                if id1 in handled_dups or id2 in handled_dups or id1 in voided or id2 in voided:
                    continue
                d1 = local_date(inv1["issued_at"], tz)
                d2 = local_date(inv2["issued_at"], tz)
                if abs((d1 - d2).days) > 3:
                    continue

                items1 = inv1.get("line_items")
                items2 = inv2.get("line_items")
                identical = False
                if items1 is not None and items2 is not None:
                    if items1 == items2 or (hard and _line_key(items1) == _line_key(items2)):
                        identical = True
                elif inv1.get("total_minor") == inv2.get("total_minor"):
                    identical = True

                if identical:
                    rows1 = [r for r in ledger_by_inv[id1]
                             if r["account"] == "1200" and r["debit_minor"] > 0 and not r.get("payment_id")]
                    rows2 = [r for r in ledger_by_inv[id2]
                             if r["account"] == "1200" and r["debit_minor"] > 0 and not r.get("payment_id")]
                    if rows1 and rows2:
                        ordered = sorted([inv1, inv2], key=lambda x: (x["issued_at"], x["doc_id"]))
                        orig, dup = ordered[0], ordered[1]
                        dup_row = [r for r in ledger_by_inv[dup["invoice_id"]]
                                   if r["account"] == "1200" and r["debit_minor"] > 0 and not r.get("payment_id")][0]
                        orig_row = [r for r in ledger_by_inv[orig["invoice_id"]]
                                    if r["account"] == "1200" and r["debit_minor"] > 0 and not r.get("payment_id")][0]
                        findings.append({
                            "type": "duplicate_invoice",
                            "affected_ids": sorted([orig["invoice_id"], dup["invoice_id"]]),
                            "claimed_amount_minor": dup_row["debit_minor"],
                            "currency": base,
                            "evidence_ids": [orig["doc_id"], dup["doc_id"], orig_row["row_id"], dup_row["row_id"]],
                            "explanation": "duplicate invoice booked in ledger",
                        })
                        handled_dups.add(id1)
                        handled_dups.add(id2)

    # ------------------------------------------------------------------
    # 2. period_cutoff and fx_error on invoices
    # ------------------------------------------------------------------
    for inv in invoices:
        inv_id = inv["invoice_id"]
        d_inv = local_date(inv["issued_at"], tz)
        in_period = (p_start <= d_inv <= p_end)
        ar_rows = [r for r in ledger_by_inv[inv_id]
                   if r["account"] == "1200" and r["debit_minor"] > 0 and not r.get("payment_id")]
        rev_rows = [r for r in ledger_by_inv[inv_id]
                    if r["account"] == "4000" and r["credit_minor"] > 0 and not r.get("payment_id")]
        if not ar_rows:
            continue
        ar_row = ar_rows[0]
        rev_row = rev_rows[0] if rev_rows else None

        if not in_period:
            d_ar = local_date(ar_row["timestamp"], tz)
            if p_start <= d_ar <= p_end:
                ev = [inv["doc_id"], ar_row["row_id"]]
                if rev_row:
                    ev.append(rev_row["row_id"])
                findings.append({
                    "type": "period_cutoff",
                    "affected_ids": [inv_id],
                    "claimed_amount_minor": ar_row["debit_minor"],
                    "currency": base,
                    "evidence_ids": ev,
                    "explanation": "invoice issued outside period booked in period",
                })

        if inv["currency"] != base:
            correct_ar = to_base(inv["total_minor"], inv["currency"], d_inv)
            diff = abs(ar_row["debit_minor"] - correct_ar)
            if diff > 0:
                ev = [inv["doc_id"], ar_row["row_id"], f"{d_inv.isoformat()}:{inv['currency']}:{base}"]
                if rev_row:
                    ev.append(rev_row["row_id"])
                findings.append({
                    "type": "fx_error",
                    "affected_ids": [inv_id],
                    "claimed_amount_minor": diff,
                    "currency": base,
                    "evidence_ids": ev,
                    "explanation": "invoice converted with wrong FX rate date",
                })

    # ------------------------------------------------------------------
    # 3. fx_error on payments
    # ------------------------------------------------------------------
    for pay in payments:
        pay_id = pay["payment_id"]
        if pay["currency"] != base:
            d_pay = local_date(pay["timestamp"], tz)
            correct_cash = to_base(abs(pay["amount_minor"]), pay["currency"], d_pay)
            cash_rows = [r for r in ledger_by_pay[pay_id] if r["account"] == "1000"]
            if cash_rows:
                cash_row = cash_rows[0]
                posted_cash = cash_row["debit_minor"] if pay["amount_minor"] >= 0 else cash_row["credit_minor"]
                diff = abs(posted_cash - correct_cash)
                if diff > 0:
                    findings.append({
                        "type": "fx_error",
                        "affected_ids": [pay_id],
                        "claimed_amount_minor": diff,
                        "currency": base,
                        "evidence_ids": [pay["doc_id"], cash_row["row_id"],
                                         f"{d_pay.isoformat()}:{pay['currency']}:{base}"],
                        "explanation": "payment cash converted with wrong FX rate date",
                    })

    # ------------------------------------------------------------------
    # 4. payment_allocation
    # ------------------------------------------------------------------
    for pay in payments:
        pay_id = pay["payment_id"]
        refs = pay.get("invoice_refs")
        if not refs:
            continue
        for ref in refs:
            ref_inv_id = ref["invoice_id"]
            ref_amount = ref["amount_minor"]
            if ref_inv_id not in inv_by_id:
                continue
            ref_inv = inv_by_id[ref_inv_id]
            d_inv = local_date(ref_inv["issued_at"], tz)
            expected_credit = to_base(ref_amount, pay["currency"], d_inv)
            # the last part of a split credits the rest of the booked amount (policy.json ledger.payment)
            t_pay = datetime.fromisoformat(pay["timestamp"])
            earlier = [r["amount_minor"] for p in payments if datetime.fromisoformat(p["timestamp"]) < t_pay
                       for r in p.get("invoice_refs") or [] if r["invoice_id"] == ref_inv_id]
            if earlier and sum(earlier) + ref_amount == ref_inv["total_minor"]:
                expected_credit = to_base(ref_inv["total_minor"], pay["currency"], d_inv) - sum(
                    to_base(a, pay["currency"], d_inv) for a in earlier)

            ar_credits = [r for r in ledger_by_pay[pay_id]
                          if r["account"] == "1200" and r.get("invoice_id") == ref_inv_id and r["credit_minor"] > 0]
            posted_credit = sum(r["credit_minor"] for r in ar_credits)
            diff = expected_credit - posted_credit
            if diff > 0:
                unapp_rows = [r for r in ledger_by_pay[pay_id] if r["account"] == "2900"]
                ev = [pay["doc_id"], ref_inv["doc_id"]]
                if pay["currency"] != base:
                    ev.append(f"{d_inv.isoformat()}:{pay['currency']}:{base}")
                if unapp_rows:
                    ev.append(unapp_rows[0]["row_id"])
                for r in ar_credits:
                    ev.append(r["row_id"])
                findings.append({
                    "type": "payment_allocation",
                    "affected_ids": sorted([ref_inv_id, pay_id]),
                    "claimed_amount_minor": diff,
                    "currency": base,
                    "evidence_ids": ev,
                    "explanation": "payment remittance not fully allocated to AR",
                })

    return findings


class Reconcile:
    """Agent baseline policy: systematically reads all records, reconciles, and submits."""

    name = "reconcile"
    hard = False

    def __init__(self, seed: int = 0):
        self.seed = seed

    def reset(self, first_observation: dict) -> None:
        self.manifest = first_observation["manifest"]
        self.episode_id = self.manifest["episode_id"]
        self.tables: dict[str, list[dict]] = {
            "ledger": [],
            "invoices": [],
            "payments": [],
            "fx": [],
        }
        self.tables_to_page = ["ledger", "invoices", "payments", "fx"]
        self.table_idx = 0
        self.cursor: str | None = None
        self.doc_queue: list[str] = []
        self.state = "paging"
        self.step_count = 0

    def act(self, observation: dict) -> dict:
        self.step_count += 1
        if self.step_count == 1:
            return {"type": "list_records", "table": self.tables_to_page[0], "limit": 50}

        # Safety: submit before step limit runs out
        remaining = observation.get("steps_remaining", 100)
        if remaining <= 1 and self.state != "done":
            self.state = "done"
            f = reconcile_findings(self.manifest, self.tables, hard=self.hard)
            return {"type": "submit", "findings": {"episode_id": self.episode_id, "findings": f}}

        if self.state == "paging":
            res = observation.get("result")
            if res and "rows" in res:
                cur_tbl = self.tables_to_page[self.table_idx]
                self.tables[cur_tbl].extend(res["rows"])
                self.cursor = res.get("next_cursor")
                if self.cursor is not None:
                    return {"type": "list_records", "table": cur_tbl, "cursor": self.cursor, "limit": 50}
                else:
                    self.table_idx += 1
                    if self.table_idx < len(self.tables_to_page):
                        next_tbl = self.tables_to_page[self.table_idx]
                        self.cursor = None
                        return {"type": "list_records", "table": next_tbl, "limit": 50}
                    else:
                        # Find potential duplicate invoices that need line items verification
                        groups: dict[tuple, list[dict]] = collections.defaultdict(list)
                        for inv in self.tables["invoices"]:
                            groups[(inv["entity_id"], inv["currency"], inv["total_minor"])].append(inv)
                        for g_invs in groups.values():
                            if len(g_invs) >= 2:
                                for inv in g_invs:
                                    if inv["doc_id"] not in self.doc_queue:
                                        self.doc_queue.append(inv["doc_id"])

                        if self.doc_queue:
                            self.state = "fetching_docs"
                            return {"type": "get_document", "doc_id": self.doc_queue.pop(0)}
                        else:
                            self.state = "done"
                            f = reconcile_findings(self.manifest, self.tables, hard=self.hard)
                            return {"type": "submit", "findings": {"episode_id": self.episode_id, "findings": f}}

        if self.state == "fetching_docs":
            res = observation.get("result")
            if res and "document" in res:
                doc = res["document"]
                for inv in self.tables["invoices"]:
                    if inv.get("doc_id") == doc.get("doc_id"):
                        inv["line_items"] = doc.get("line_items")
            if self.doc_queue:
                return {"type": "get_document", "doc_id": self.doc_queue.pop(0)}
            else:
                self.state = "done"
                f = reconcile_findings(self.manifest, self.tables, hard=self.hard)
                return {"type": "submit", "findings": {"episode_id": self.episode_id, "findings": f}}

        return {"type": "submit", "findings": {"episode_id": self.episode_id, "findings": []}}


class ReconcileHard(Reconcile):
    """Reconcile plus the hard-mode policy rules (re-typed duplicates, credit notes)."""

    name = "reconcile_hard"
    hard = True
