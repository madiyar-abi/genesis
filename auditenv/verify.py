"""Independent verifier of generated episodes (jury criterion "data and truth").

Works only from the public tables plus the closed files (truth, provenance); it does not
reuse generator internals. For each episode it checks:
1. structure: ids unique, counts, base-currency ledger, one-sided integer amounts;
2. pre-injection books (provenance changes reverted): every journal balances and the books
   follow the bookkeeping policy exactly -> zero discrepancies; in both books every account is in the
   published chart and allowed for its journal type, entities match the invoices, and unreferenced
   payment remainders sit in 2900 at the payment-date rate;
3. post-injection books: every journal still balances, and the set of discrepancies recomputed
   from the records equals the truth (type, affected_ids, amount) — nothing undeclared, nothing
   unsupported;
4. evidence: every evidence id exists in the public tables and each evidence set contains the
   affected document and a ledger row of the affected ids.
`verify_episode(ep)` returns a list of problems (empty = valid).
"""

from __future__ import annotations

import copy
import csv
import json
import re
from functools import lru_cache
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from .money import EXPONENT, convert, local_date, parse_offset

CHART = {"1000", "1200", "2900", "4000", "6100", "6200", "6300", "6400", "7900"}  # docs/CONTRACT.md §2


class Books:
    def __init__(self, manifest: dict, tables: dict, credit_notes: bool = True):
        self.m = manifest
        self.credit_notes = credit_notes  # only the hard-mode policy publishes the credit-note rule
        self.base = manifest["base_currency"]
        self.tz = parse_offset(manifest["timezone"])
        self.ps = date.fromisoformat(manifest["period_start"])
        self.pe = date.fromisoformat(manifest["period_end"])
        self.ledger = tables["ledger"]
        self.invoices = {i["invoice_id"]: i for i in tables["invoices"]}
        self.payments = {p["payment_id"]: p for p in tables["payments"]}
        self.fx = {(r["date"], r["source_currency"], r["target_currency"]): r["rate"] for r in tables["fx"]}

    def cdate(self, ts: str) -> date:
        return local_date(ts, self.tz)

    def in_period(self, ts: str) -> bool:
        return self.ps <= self.cdate(ts) <= self.pe

    def conv(self, amount: int, cur: str, ts: str) -> int:
        if cur == self.base:
            return amount
        return convert(amount, cur, self.base, self.fx[(self.cdate(ts).isoformat(), cur, self.base)])

    def allocated(self, credit: int, ref: int, cur: str, ts: str) -> set[int]:
        """Reference amounts a (0 <= a < ref, document currency) whose conversion at `ts` is the AR credit."""
        if cur == self.base:
            return {credit} if 0 <= credit < ref else set()
        rate = Decimal(self.fx[(self.cdate(ts).isoformat(), cur, self.base)])
        per_unit = rate.scaleb(EXPONENT[self.base] - EXPONENT[cur])  # base minor units per document minor unit
        guess = int(Decimal(credit) / per_unit)
        width = min(int(1 / per_unit) + 3, 1000)  # a rate this small is no real currency pair; bound the search
        return {a for a in range(max(0, guess - width), min(ref, guess + width + 1))
                if self.conv(a, cur, ts) == credit}

    def not_fx(self, posted: int, amount: int, cur: str) -> str | None:
        """Why a wrong base amount cannot be an fx_error (a rate of the wrong date), or None if it can be."""
        if cur == self.base:
            return "with no FX involved (base currency)"
        if all(posted != convert(amount, cur, self.base, rate) for (_, src, tgt), rate in self.fx.items()
               if (src, tgt) == (cur, self.base)):
            return "that no published rate produces"
        return None

    def ref_problems(self, pid: str, pay: dict) -> list[str]:
        """Remittance consistency of one payment document, whatever its posting period. The generator never pays
        an invoice before its issue or one it later cancels (checked on all payments), so both hold outside the
        period too. Needs self.voided (set by discrepancies)."""
        problems = []
        refs = pay["invoice_refs"] or []
        if sum(r["amount_minor"] for r in refs) > max(pay["amount_minor"], 0):
            problems.append(f"payment {pid}: refs exceed amount")
        if len({r["invoice_id"] for r in refs}) != len(refs):
            problems.append(f"payment {pid} references an invoice twice")
        if any(r["amount_minor"] <= 0 for r in refs):
            problems.append(f"payment {pid}: non-positive invoice ref")
        for ref in refs:
            inv = self.invoices.get(ref["invoice_id"])
            if inv is None:
                problems.append(f"payment {pid} references unknown invoice {ref['invoice_id']}")
                continue
            if datetime_key(inv["issued_at"]) > datetime_key(pay["timestamp"]):
                problems.append(f"payment {pid} settles invoice {inv['invoice_id']} issued after the payment")
            if inv["invoice_id"] in self.voided:
                problems.append(f"payment {pid} settles a cancelled invoice {inv['invoice_id']}")
            if inv["currency"] != pay["currency"]:
                problems.append(f"payment {pid} settles an other-currency invoice {inv['invoice_id']}")
        return problems

    def journals(self) -> dict[str, list[dict]]:
        groups = defaultdict(list)
        for r in self.ledger:
            if r["payment_id"]:
                groups["pay:" + r["payment_id"]].append(r)
            elif r["invoice_id"]:
                groups["inv:" + r["invoice_id"]].append(r)
            else:
                groups["exp:" + r["timestamp"]].append(r)
        return groups

    def discrepancies(self) -> tuple[list[tuple], list[str]]:
        """Return (issues, problems): issues = (type, tuple(sorted ids), amount)."""
        issues, problems = [], []
        for r in self.ledger:
            if not self.in_period(r["timestamp"]):
                problems.append(f"ledger row {r['row_id']} outside the period")
        js = self.journals()
        for jid, rows in js.items():
            if sum(r["debit_minor"] for r in rows) != sum(r["credit_minor"] for r in rows):
                problems.append(f"unbalanced journal {jid}")
        # invoices: booking, period, FX
        booked, self.voided = {}, {}  # voided: cancelled invoice -> instant of its credit note
        for jid, rows in js.items():
            if jid.startswith("inv:"):
                ar = [r for r in rows if r["account"] == "1200"]
                rev = [r for r in rows if r["account"] == "4000"]
                # booking + full credit note (cancelled invoice)
                if self.credit_notes and len(ar) == 2 and len(rev) == 2:
                    ar_dr = [r for r in ar if r["debit_minor"]]
                    amounts = {r["debit_minor"] + r["credit_minor"] for r in ar + rev}
                    reversal = [r for r in ar + rev if (r["account"] == "1200") == bool(r["credit_minor"])]
                    if len(ar_dr) != 1 or len(amounts) != 1 or len(reversal) != 2 \
                            or datetime_key(reversal[0]["timestamp"]) != datetime_key(reversal[1]["timestamp"]) \
                            or datetime_key(reversal[0]["timestamp"]) < datetime_key(ar_dr[0]["timestamp"]):
                        problems.append(f"malformed credit note in {jid}")
                        continue
                    self.voided[jid[4:]] = datetime_key(reversal[0]["timestamp"])
                    ar = ar_dr
                    rev = [r for r in rev if r["credit_minor"]]
                if len(ar) != 1 or len(rev) != 1 or not ar[0]["debit_minor"] \
                        or ar[0]["debit_minor"] != rev[0]["credit_minor"]:
                    problems.append(f"malformed invoice journal {jid}")
                    continue
                if datetime_key(ar[0]["timestamp"]) != datetime_key(rev[0]["timestamp"]):
                    problems.append(f"invoice booking rows have different timestamps in {jid}")
                booked[jid[4:]] = ar[0]
        for iid, ar in booked.items():
            inv = self.invoices.get(iid)
            if inv is None:
                problems.append(f"ledger references unknown invoice {iid}")
                continue
            if not self.in_period(inv["issued_at"]):
                issues.append(("period_cutoff", (iid,), ar["debit_minor"]))
            elif datetime_key(ar["timestamp"]) < datetime_key(inv["issued_at"]):
                problems.append(f"invoice {iid} booked before it was issued")
            correct = self.conv(inv["total_minor"], inv["currency"], inv["issued_at"])
            if ar["debit_minor"] != correct:
                why = self.not_fx(ar["debit_minor"], inv["total_minor"], inv["currency"])
                if why:  # not an error type of the contract: never matches a declared issue
                    problems.append(f"invoice {iid} booked at a wrong amount {why}")
                    issues.append(("booking_error", (iid,), abs(ar["debit_minor"] - correct)))
                else:
                    issues.append(("fx_error", (iid,), abs(ar["debit_minor"] - correct)))
        for iid, inv in self.invoices.items():
            for n, line in enumerate(inv["line_items"], start=1):
                if line["amount_minor"] != line["quantity"] * line["unit_price_minor"]:
                    problems.append(f"invoice {iid} line {n} amount != quantity times unit price")
            if sum(li["amount_minor"] for li in inv["line_items"]) != inv["total_minor"]:
                problems.append(f"invoice {iid} total != line items")
            if self.in_period(inv["issued_at"]) and iid not in booked:
                problems.append(f"in-period invoice {iid} not booked")
        # hard mode: a cancelled invoice is re-issued as a new invoice with identical line items, booked in the
        # period after the credit note; each replacement serves one cancelled invoice (CONTRACT §2)
        used = set()
        for iid, cancelled_at in sorted(self.voided.items(), key=lambda kv: kv[1]):
            inv = self.invoices.get(iid)
            if inv is None:
                continue
            key = (inv["entity_id"], inv["currency"], line_key(inv["line_items"]))
            new = next((o for o in sorted(self.invoices.values(), key=lambda o: datetime_key(o["issued_at"]))
                        if o["invoice_id"] != iid and o["invoice_id"] not in self.voided and o["invoice_id"] in booked
                        and o["invoice_id"] not in used and self.in_period(o["issued_at"])
                        and datetime_key(o["issued_at"]) >= cancelled_at
                        and (o["entity_id"], o["currency"], line_key(o["line_items"])) == key), None)
            if new is None:
                problems.append(f"credit-noted invoice {iid} has no replacement invoice with the same line items, "
                                f"issued at or after the credit note and booked in the period")
            else:
                used.add(new["invoice_id"])
        # duplicates: same entity, currency, same line items (re-typed text allowed) -> later copy;
        # an invoice cancelled by a full credit note is not a duplicate of its replacement
        seen = defaultdict(list)
        for inv in self.invoices.values():
            if inv["invoice_id"] in self.voided:
                continue
            key = (inv["entity_id"], inv["currency"], line_key(inv["line_items"]))
            seen[key].append(inv)
        for group in seen.values():
            if len(group) < 2:
                continue
            group.sort(key=lambda i: datetime_key(i["issued_at"]))
            for dup in group[1:]:
                ids = tuple(sorted((group[0]["invoice_id"], dup["invoice_id"])))
                ar = booked.get(dup["invoice_id"])
                issues.append(("duplicate_invoice", ids, ar["debit_minor"] if ar else 0))
        # payments: cash FX, allocations, unapplied remainder
        for pid, pay in self.payments.items():
            problems += self.ref_problems(pid, pay)
            rows = js.get("pay:" + pid)
            if not self.in_period(pay["timestamp"]):
                if rows:
                    problems.append(f"out-of-period payment {pid} booked")
                continue
            if not rows:
                problems.append(f"in-period payment {pid} not booked")
                continue
            if any(datetime_key(r["timestamp"]) != datetime_key(pay["timestamp"]) for r in rows):
                problems.append(f"payment {pid}: journal row not dated at the payment")
            cash = [r for r in rows if r["account"] == "1000"]
            if len(cash) != 1:
                problems.append(f"payment {pid}: expected one cash row")
                continue
            posted = cash[0]["debit_minor"] - cash[0]["credit_minor"]
            correct = self.conv(pay["amount_minor"], pay["currency"], pay["timestamp"])
            if posted != correct:
                why = self.not_fx(posted, pay["amount_minor"], pay["currency"])
                if why:  # not an error type of the contract: never matches a declared issue
                    problems.append(f"payment {pid}: cash booked at a wrong amount {why}")
                    issues.append(("booking_error", (pid,), abs(posted - correct)))
                else:
                    issues.append(("fx_error", (pid,), abs(posted - correct)))
            refs = pay["invoice_refs"] or []
            if pay["currency"] == self.base and any(r["account"] == "7900" for r in rows):
                problems.append(f"payment {pid}: FX gain/loss on a base-currency payment")
            extras = {0}  # what the allocation shortfalls may add to 2900 (each moved part at the payment-date rate)
            for ref in refs:
                inv = self.invoices.get(ref["invoice_id"])
                if inv is None:  # reported by ref_problems
                    continue
                expected = self.conv(ref["amount_minor"], pay["currency"], inv["issued_at"])
                credit = sum(r["credit_minor"] - r["debit_minor"] for r in rows
                             if r["account"] == "1200" and r["invoice_id"] == inv["invoice_id"])
                if credit < expected:
                    moved = {self.conv(ref["amount_minor"] - a, pay["currency"], pay["timestamp"])
                             for a in self.allocated(credit, ref["amount_minor"], pay["currency"], inv["issued_at"])}
                    if not moved:
                        problems.append(f"payment {pid}: AR credit to {inv['invoice_id']} is no conversion of a "
                                        f"part of the reference")
                    extras = {e + m for e in extras for m in moved}
                    issues.append(("payment_allocation", tuple(sorted((inv["invoice_id"], pid))), expected - credit))
                elif credit > expected:
                    problems.append(f"payment {pid} over-allocated to {inv['invoice_id']}")
            # the unreferenced remainder is Cr 2900 at the payment-date rate; an allocation shortfall adds the
            # unallocated part of that reference, also at the payment-date rate (CONTRACT §2)
            rest = pay["amount_minor"] - sum(r["amount_minor"] for r in refs)
            rest = self.conv(rest, pay["currency"], pay["timestamp"])
            unapplied = sum(r["credit_minor"] - r["debit_minor"] for r in rows if r["account"] == "2900")
            if unapplied - rest not in extras:
                problems.append(f"payment {pid}: incorrect unapplied cash for {'' if refs else 'un'}referenced payment")
            ar_ids = {r["invoice_id"] for r in rows if r["account"] == "1200"}
            if not ar_ids <= {r["invoice_id"] for r in refs}:
                problems.append(f"payment {pid} credits an invoice it does not reference")
        return issues, problems


def line_key(items: list[dict]) -> tuple:
    """Order-, case- and punctuation-insensitive identity of an invoice's lines."""
    return tuple(sorted(("".join(ch for ch in li["description"].lower() if ch.isalnum()), li["quantity"],
                         li["unit_price_minor"], li["amount_minor"]) for li in items))


def datetime_key(ts: str):
    from .money import parse_ts
    return parse_ts(ts)


RATE = re.compile(r"[0-9]+(\.[0-9]+)?")  # plain ASCII decimal, as the generator writes it (no sign, exponent, _)


def _structure(ep: dict) -> list[str]:
    error = _schema_error(ep.get("manifest"), _schema("manifest.schema.json"), "manifest")
    if error:
        return [error]  # the checks below index the manifest's fields
    problems = []
    if not isinstance(ep.get("task"), str) or not ep["task"].strip():
        problems.append("public task text must contain instructions")
    m, t = ep["manifest"], ep["tables"]
    for name in ("ledger", "invoices", "payments", "fx"):
        if m["counts"][name] != len(t[name]):
            problems.append(f"manifest count mismatch for {name}")
    actual_docs = len(t["invoices"]) + len(t["payments"])
    if m["counts"].get("documents") != actual_docs:
        problems.append("manifest count mismatch for documents")
    ids = [r["row_id"] for r in t["ledger"]] + [d["doc_id"] for d in t["invoices"] + t["payments"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate row_id/doc_id")
    if not all(isinstance(i, str) and i.strip() for i in ids):
        problems.append("row_id/doc_id must be a non-empty string")
    for key, rows in (("invoice_id", t["invoices"]), ("payment_id", t["payments"]), ("fx_id", t["fx"])):
        if len({r[key] for r in rows}) != len(rows):
            problems.append(f"duplicate {key}")
    rate_keys = set()
    for rate in t["fx"]:
        key = (rate["date"], rate["source_currency"], rate["target_currency"])
        if key in rate_keys:
            problems.append(f"duplicate FX rate for {key}")
        rate_keys.add(key)
        if rate["fx_id"] != ":".join(key):
            problems.append(f"fx_id differs from date and currency pair: {rate['fx_id']}")
        # every published rate, used or not: a reader must be able to convert with any of them; above 10^9 is no
        # real currency pair and would exceed the conversion's decimal precision
        value = rate.get("rate")
        if not isinstance(value, str) or not RATE.fullmatch(value) or not 0 < Decimal(value) < 10 ** 9:
            problems.append(f"fx rate {rate['fx_id']}: rate must be a positive decimal below 10^9")
    pol = ep["policy"]
    if (pol["base_currency"], pol["timezone"], pol["period"]["start"], pol["period"]["end"]) != \
            (m["base_currency"], m["timezone"], m["period_start"], m["period_end"]):
        problems.append("policy contradicts the manifest (base currency, timezone or period)")
    if set(pol["ledger"]["accounts"]) != CHART:
        problems.append("policy chart of accounts contradicts the contract")
    currencies = {m["base_currency"]}
    currencies.update(row["currency"] for table in ("ledger", "invoices", "payments") for row in t[table])
    currencies.update(row[key] for row in t["fx"] for key in ("source_currency", "target_currency"))
    exponents = m["amount_exponents"]
    if (m["rounding"] != "ROUND_HALF_UP" or not isinstance(exponents, dict)
            or not currencies.issubset(exponents)
            or any(type(e) is not int or EXPONENT.get(c) != e for c, e in exponents.items())):
        problems.append("manifest rounding or amount exponents contradict the contract")
    inv_ids = {i["invoice_id"] for i in t["invoices"]}
    pay_ids = {p["payment_id"] for p in t["payments"]}
    for r in t["ledger"]:
        d, c = r["debit_minor"], r["credit_minor"]
        if r["currency"] != m["base_currency"] or type(d) is not int or type(c) is not int or (d > 0) == (c > 0) \
                or d < 0 or c < 0:
            problems.append(f"bad ledger row {r['row_id']}")
        if r.get("invoice_id") is not None and r["invoice_id"] not in inv_ids:
            problems.append(f"ledger row {r['row_id']} references unknown invoice {r['invoice_id']}")
        if r.get("payment_id") is not None and r["payment_id"] not in pay_ids:
            problems.append(f"ledger row {r['row_id']} references unknown payment {r['payment_id']}")
    for p in t["payments"]:  # CONTRACT §1/§2: int minor units, ISO-8601 timestamps with an offset
        refs = p.get("invoice_refs")
        if type(p.get("amount_minor")) is not int or (refs is not None and (
                not isinstance(refs, list)
                or any(not isinstance(r, dict) or type(r.get("amount_minor")) is not int for r in refs))):
            problems.append(f"payment {p.get('payment_id')}: amount_minor must be an integer")
        elif refs and any(not isinstance(r.get("invoice_id"), str) for r in refs):
            problems.append(f"payment {p.get('payment_id')}: invoice_refs invoice_id must be a string")
    stamps = [(f"ledger row {r['row_id']}", r["timestamp"]) for r in t["ledger"]]
    stamps += [(f"payment {p['payment_id']}", p["timestamp"]) for p in t["payments"]]
    stamps += [(f"invoice {i['invoice_id']}", i[k]) for i in t["invoices"] for k in ("issued_at", "due_at")]
    for label, ts in stamps:
        try:
            aware = datetime_key(ts).tzinfo is not None
        except (TypeError, ValueError):
            aware = False
        if not aware:
            problems.append(f"{label}: timestamp must be ISO-8601 with a timezone offset")
    if not 200 <= len(t["ledger"]) <= 2000 or not 20 <= actual_docs <= 200:
        problems.append("episode size outside 200-2000 rows / 20-200 documents")
    return problems


PAYMENT_ACCOUNTS = ("1000", "1200", "2900", "7900")


def _ledger_policy(tables: dict, accounts: dict) -> list[str]:
    """Account usage of the published policy.ledger: chart of accounts, accounts per journal type, entities."""
    problems = []
    invoices = {i["invoice_id"]: i for i in tables["invoices"]}
    pay_entities = defaultdict(set)
    for r in tables["ledger"]:
        rid, acc, iid, pid = r["row_id"], r["account"], r["invoice_id"], r["payment_id"]
        if acc not in accounts:
            problems.append(f"ledger row {rid}: unknown account {acc}")
            continue
        if pid:
            if acc not in PAYMENT_ACCOUNTS:
                problems.append(f"ledger row {rid}: account {acc} not allowed in payment journal")
            elif acc != "1200":
                pay_entities[pid].add(r["entity_id"])
        elif iid:
            if acc not in ("1200", "4000"):
                problems.append(f"ledger row {rid}: account {acc} not allowed in invoice journal")
        elif r["entity_id"] is not None or not ((acc.startswith("6") and r["debit_minor"])
                                                 or (acc == "1000" and r["credit_minor"])):
            problems.append(f"ledger row {rid}: not an expense journal posting (Dr 6xxx / Cr 1000, no ids)")
        if (acc == "1200" or not pid) and iid in invoices and r["entity_id"] != invoices[iid]["entity_id"]:
            problems.append(f"ledger row {rid}: entity differs from invoice {iid}")
    for pid, entities in pay_entities.items():
        if len(entities) > 1:
            problems.append(f"payment {pid}: cash, unapplied and FX rows name different entities")
    return problems


def revert(ep: dict) -> dict:
    """Undo the recorded injections (newest first) -> pre-injection public tables."""
    tables = copy.deepcopy(ep["tables"])
    for inj in reversed(ep["provenance"]["injections"]):
        for ch in reversed(inj["changes"]):
            kind, key = ch["journal"].split(":", 1)
            if kind == "inv":
                keep = [r for r in tables["ledger"] if not (r["invoice_id"] == key and not r["payment_id"])]
            else:
                keep = [r for r in tables["ledger"] if r["payment_id"] != key]
            tables["ledger"] = keep + copy.deepcopy(ch["before"] or [])
        added = set(inj["documents_added"])
        tables["invoices"] = [i for i in tables["invoices"] if i["doc_id"] not in added]
        tables["payments"] = [p for p in tables["payments"] if p["doc_id"] not in added]
    return tables


def _booking_row(r: dict, iid: str) -> bool:
    """The invoice's own booking: Dr 1200 or Cr 4000 with its invoice_id and no payment."""
    return r["invoice_id"] == iid and r["payment_id"] is None and \
        ((r["account"] == "1200" and r["debit_minor"] > 0) or (r["account"] == "4000" and r["credit_minor"] > 0))


def _sufficient(books: Books, iss: dict, s: list, rows: dict, docs: dict) -> list[str]:
    """Recompute the declared amount from the evidence records alone (plus the manifest)."""
    ev_rows = [rows[i] for i in s if i in rows]
    ev_docs = [docs[i] for i in s if i in docs]
    rates = {i: books.fx[tuple(i.split(":"))] for i in s if i.count(":") == 2 and tuple(i.split(":")) in books.fx}

    def conv(amount, cur, ts):
        if cur == books.base:
            return amount
        key = f"{books.cdate(ts).isoformat()}:{cur}:{books.base}"
        if key not in rates:
            raise KeyError(key)
        return convert(amount, cur, books.base, rates[key])

    typ, exp = iss["type"], iss["expected_amount_minor"]
    try:
        if typ == "duplicate_invoice":
            a, b = sorted(ev_docs, key=lambda d: datetime_key(d["issued_at"]))
            same = (a["entity_id"], a["currency"], line_key(a["line_items"])) == \
                (b["entity_id"], b["currency"], line_key(b["line_items"]))
            bookings = {}
            for doc in (a, b):
                bookings[doc["invoice_id"]] = [
                    row["debit_minor"] + row["credit_minor"] for row in ev_rows
                    if row["invoice_id"] == doc["invoice_id"] and row["entity_id"] == doc["entity_id"]
                    and row["payment_id"] is None and row["currency"] == books.base
                    and books.in_period(row["timestamp"])
                    and ((row["account"] == "1200" and row["debit_minor"] > 0 and row["credit_minor"] == 0)
                         or (row["account"] == "4000" and row["credit_minor"] > 0 and row["debit_minor"] == 0))
                ]
            ok = (same and len(bookings) == 2 and set(bookings) == set(iss["affected_ids"])
                  and datetime_key(a["issued_at"]) < datetime_key(b["issued_at"])
                  and bool(bookings[a["invoice_id"]]) and exp in bookings[b["invoice_id"]])
        elif typ == "period_cutoff":
            inv = next(d for d in ev_docs if "invoice_id" in d)
            row = next(r for r in ev_rows if _booking_row(r, inv["invoice_id"]))
            ok = (not books.in_period(inv["issued_at"]) and books.in_period(row["timestamp"])
                  and row["debit_minor"] + row["credit_minor"] == exp)
        elif typ == "fx_error":
            doc = ev_docs[0]
            if "invoice_id" in doc:
                row = next(r for r in ev_rows if _booking_row(r, doc["invoice_id"]))
                correct = conv(doc["total_minor"], doc["currency"], doc["issued_at"])
            else:
                row = next(r for r in ev_rows if r["payment_id"] == doc["payment_id"] and r["account"] == "1000")
                correct = conv(doc["amount_minor"], doc["currency"], doc["timestamp"])
            ok = abs(row["debit_minor"] + row["credit_minor"] - correct) == exp
        else:  # payment_allocation
            pay = next(d for d in ev_docs if "payment_id" in d)
            inv = next(d for d in ev_docs if "invoice_id" in d and "payment_id" not in d)
            ref = next(r for r in pay["invoice_refs"] if r["invoice_id"] == inv["invoice_id"])
            expected = conv(ref["amount_minor"], pay["currency"], inv["issued_at"])
            row = next(r for r in ev_rows if r["payment_id"] == pay["payment_id"] and (
                r["account"] == "2900" or (r["account"] == "1200" and r["invoice_id"] == inv["invoice_id"])))
            if row["account"] == "1200":
                ok = ({pay["payment_id"], inv["invoice_id"]} == set(iss["affected_ids"])
                      and row["payment_id"] == pay["payment_id"] and row["invoice_id"] == inv["invoice_id"]
                      and row["debit_minor"] == 0 and row["credit_minor"] > 0
                      and expected - row["credit_minor"] == exp)
            else:  # 2900 row: nothing was allocated, the whole ref went to unapplied cash -> amount = expected
                # (the missing AR credit is an absence no id can show; step 3 proves it from the whole ledger).
                # A base-currency payment needs no rate: the unapplied credit must cover the whole ref.
                covers = pay["currency"] != books.base or row["credit_minor"] >= ref["amount_minor"]
                ok = row["account"] == "2900" and row["payment_id"] == pay["payment_id"] and exp == expected and covers
        return [] if ok else [f"evidence set {s} does not reproduce the amount"]
    except (KeyError, StopIteration, ValueError, IndexError):
        return [f"evidence set {s} is missing a record needed to reproduce the amount"]


def _invoice_error(invoice: dict) -> str | None:
    if not isinstance(invoice, dict):
        return "invoice must be an object"
    label = f"invoice {invoice.get('invoice_id', '<missing ID>')}"
    for field in ("invoice_id", "doc_id", "entity_id", "currency"):
        if not isinstance(invoice.get(field), str) or not invoice[field].strip():
            return f"{label}: {field} must be a nonblank string"
    for field in ("issued_at", "due_at"):
        try:
            instant = datetime_key(invoice.get(field))
        except (TypeError, ValueError):
            return f"{label}: invalid {field}"
        if instant.tzinfo is None:
            return f"{label}: {field} must include a timezone offset"
    if type(invoice.get("total_minor")) is not int:
        return f"{label}: total_minor must be an integer"
    if not isinstance(invoice.get("line_items"), list):
        return f"{label}: line_items must be an array"
    for i, line in enumerate(invoice["line_items"]):
        if not isinstance(line, dict) or not isinstance(line.get("description"), str):
            return f"{label}: line_items[{i}].description must be a string"
        for field in ("quantity", "unit_price_minor", "amount_minor"):
            if type(line.get(field)) is not int:
                return f"{label}: line_items[{i}].{field} must be an integer"
    return None


@lru_cache(maxsize=None)
def _schema(name: str) -> dict:
    path = Path(__file__).resolve().parents[1] / "schemas" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_error(value, schema, path):
    """Check the keywords used in truth.schema.json and manifest.schema.json, reporting the first invalid field.
    An object field not in `properties` must match `additionalProperties`; without it, it is unexpected."""
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int}
    if kind and type(value) is not types[kind]:
        return f"{path}: expected {kind}"
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        return f"{path}: must be {schema['const']!r}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path}: invalid choice"
    if kind == "object":
        for name in schema.get("required", ()):
            if name not in value:
                return f"{path}.{name}: required"
        for name, item in value.items():
            if "propertyNames" in schema:
                error = _schema_error(name, schema["propertyNames"], f"{path} key {name!r}")
                if error:
                    return error
            sub = schema.get("properties", {}).get(name, schema.get("additionalProperties", False))
            if sub is False:
                return f"{path}.{name}: unexpected field"
            error = _schema_error(item, sub, f"{path}.{name}") if isinstance(sub, dict) else None
            if error:
                return error
    if kind == "array":
        if len(value) < schema.get("minItems", 0):
            return f"{path}: empty list"
        for index, item in enumerate(value):
            error = _schema_error(item, schema["items"], f"{path}[{index}]")
            if error:
                return error
        if schema.get("uniqueItems") and len(set(value)) != len(value):
            return f"{path}: duplicate ID"
    if "pattern" in schema and not re.search(schema["pattern"], value):
        return f"{path}: invalid string"
    if schema.get("format") == "date":
        try:  # fromisoformat alone also takes the basic form 20250301
            valid = re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) and date.fromisoformat(value)
        except ValueError:
            valid = False
        if not valid:
            return f"{path}: invalid date"
    if "minimum" in schema and value < schema["minimum"]:
        return f"{path}: below minimum"
    return None


def _scenario_problems(issues: list[dict], payment_ids: set) -> list[str]:
    """CONTRACT §3 scenario labels: I1 = payment_allocation + fx_error on that payment, I2 = period_cutoff +
    fx_error on the same invoice; every other issue is "single"."""
    problems, paired = [], set()
    for a in range(len(issues)):
        for b in range(a + 1, len(issues)):
            x, y = issues[a], issues[b]
            kinds = {x["type"]: x, y["type"]: y}
            scenario = None
            if set(kinds) == {"payment_allocation", "fx_error"}:
                fx_ids = kinds["fx_error"]["affected_ids"]
                if len(fx_ids) == 1 and fx_ids[0] in payment_ids and fx_ids[0] in kinds["payment_allocation"]["affected_ids"]:
                    scenario = "I1"
            elif set(kinds) == {"period_cutoff", "fx_error"} and x["affected_ids"] == y["affected_ids"]:
                scenario = "I2"
            if scenario:
                paired.update((a, b))
                if x.get("scenario") != scenario or y.get("scenario") != scenario:
                    problems.append(f"{x['issue_id']}, {y['issue_id']}: interacting errors must have scenario {scenario}")
    for i, iss in enumerate(issues):
        if i not in paired and iss.get("scenario") != "single":
            problems.append(f"{iss['issue_id']}: scenario {iss.get('scenario')} without its interacting partner")
    return problems


def verify_episode(ep: dict) -> list[str]:
    for invoice in ep["tables"]["invoices"]:
        error = _invoice_error(invoice)
        if error:
            return [error]
    error = _schema_error(ep.get("truth"), _schema("truth.schema.json"), "truth")
    if error:
        return [error]
    problems = _structure(ep)
    # the bookkeeping checks below assume a valid manifest, int amounts, string refs, offset-aware timestamps
    # and convertible rates
    if any(p.startswith(("manifest.", "manifest:", "manifest key")) or "must be an integer" in p
           or "timestamp must be" in p or "fx rate " in p or "invoice_id must be" in p for p in problems):
        return problems
    m, t = ep["manifest"], ep["tables"]
    if ep["truth"].get("episode_id") != m["episode_id"]:
        problems.append("truth episode_id differs from manifest")
    accounts = ep["policy"]["ledger"]["accounts"]
    # pre-injection: correct books
    pre_tables = revert(ep)
    credit_notes = "credit_note" in ep["policy"]["ledger"]
    pre_issues, pre_problems = Books(m, pre_tables, credit_notes).discrepancies()
    problems += [f"pre-injection: {p}" for p in pre_problems + _ledger_policy(pre_tables, accounts)]
    problems += [f"pre-injection discrepancy {i}" for i in pre_issues]
    # post-injection: declared discrepancies == recomputed discrepancies
    books = Books(m, t, credit_notes)
    issues, post_problems = books.discrepancies()
    problems += [f"post-injection: {p}" for p in post_problems + _ledger_policy(t, accounts)]
    found = sorted(issues)
    declared = sorted((i["type"], tuple(i["affected_ids"]), i["expected_amount_minor"])
                      for i in ep["truth"]["issues"])
    if found != declared:
        problems.append(f"truth mismatch: recomputed {found} declared {declared}")
    problems += _scenario_problems(ep["truth"]["issues"], {p["payment_id"] for p in t["payments"]})
    # evidence
    rows = {r["row_id"]: r for r in t["ledger"]}
    docs = {d["doc_id"]: d for d in t["invoices"] + t["payments"]}
    fx_ids = {r["fx_id"] for r in t["fx"]}
    issue_ids = set()
    for iss in ep["truth"]["issues"]:
        if iss["issue_id"] in issue_ids:
            problems.append(f"duplicate truth issue_id {iss['issue_id']}")
        issue_ids.add(iss["issue_id"])
        if iss.get("currency") != m["base_currency"]:
            problems.append(f"{iss['issue_id']}: truth currency differs from ledger base currency")
        aff = set(iss["affected_ids"])
        if not iss["evidence_sets"]:
            problems.append(f"{iss['issue_id']}: no evidence set")
        for s in iss["evidence_sets"]:
            if not set(s) <= rows.keys() | docs.keys() | fx_ids:
                problems.append(f"{iss['issue_id']}: evidence id not in public tables")
                continue
            if len(s) > 10:
                problems.append(f"{iss['issue_id']}: evidence set larger than 10")
            doc_ok = any(i in docs and (docs[i].get("invoice_id") in aff or docs[i].get("payment_id") in aff)
                         for i in s)
            row_ok = any(i in rows and (rows[i]["invoice_id"] in aff or rows[i]["payment_id"] in aff) for i in s)
            if not (doc_ok or iss["type"] == "duplicate_invoice") or not (row_ok or iss["type"] == "duplicate_invoice"):
                problems.append(f"{iss['issue_id']}: evidence set does not cover the affected records")
            if iss["type"] == "duplicate_invoice":
                if sum(i in docs for i in s) != 2:
                    problems.append(f"{iss['issue_id']}: duplicate evidence must show both documents")
                row_invs = {rows[i]["invoice_id"] for i in s if i in rows
                            and rows[i].get("payment_id") is None
                            and rows[i].get("account") in ("1200", "4000")}
                if row_invs != aff:
                    problems.append(f"{iss['issue_id']}: duplicate evidence must show booking rows for both invoices")
            problems += [f"{iss['issue_id']}: {p}" for p in _sufficient(books, iss, s, rows, docs)]
    return problems


def _verify_directory(root: Path) -> int:
    from .generator import gen_config
    from .load import load_episode

    index = root / "index.json"
    indexed = index.exists()
    try:
        entries = {p.name for p in root.iterdir() if p.is_dir() and (p / "public").is_dir()}
        if indexed:
            records = json.loads(index.read_text(encoding="utf-8"))
            if not isinstance(records, list) or not records:
                raise ValueError("expected a nonempty episode list")
            by_id = {}
            for record in records:
                name = record.get("episode_id") if isinstance(record, dict) else None
                if not isinstance(name, str) or not name or name in by_id:
                    raise ValueError(f"invalid or duplicate episode_id {name!r}")
                by_id[name] = record
            expected = set(by_id)
            if entries != expected:
                raise ValueError(f"missing episodes {sorted(expected - entries)}, "
                                 f"unlisted episodes {sorted(entries - expected)}")
    except (OSError, ValueError) as exc:
        print(f"{index}: {exc}")
        return 1

    if not entries:
        print(f"{root}: no episodes found")
        return 1
    bad = 0
    for name in sorted(entries):
        try:
            ep = load_episode(root / name)
            problems = verify_episode(ep)
            if indexed:
                record = by_id[name]
                provenance = ep["provenance"]
                if ep["episode_id"] != name:
                    problems.append(f"manifest episode_id differs from directory {name}")
                seed = record.get("seed")
                if type(seed) is not int or seed != provenance.get("seed"):
                    problems.append("index.json seed differs from provenance")
                config = record.get("config")
                if (not isinstance(config, dict) or gen_config(config) != provenance["config"]
                        or config.get("transform_seed") != provenance.get("transform_seed")):
                    problems.append("index.json config differs from provenance")
        except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, ArithmeticError, csv.Error) as exc:
            problems = [str(exc)]
        if problems:
            bad += 1
            print(f"{name}: {problems[:3]}")
    print(f"{len(entries) - bad}/{len(entries)} episodes valid; episodes with problems: {bad}")
    return 1 if bad else 0


def main(argv=None) -> int:
    import argparse

    from .generator import generate
    from .run import parse_seeds

    ap = argparse.ArgumentParser(description="verify generated episodes")
    ap.add_argument("--seeds", type=parse_seeds, default="0-199")
    ap.add_argument("--dir", default=None,
                    help="verify every episode under this directory (e.g. episodes/dev)")
    args = ap.parse_args(argv)
    bad = total = 0

    if args.dir is not None:
        return _verify_directory(Path(args.dir))

    for seed in args.seeds:
        for cfg in (None, {"errors": {}}, {"errors": {"duplicate_invoice": 2, "payment_allocation": 2, "fx_error": 2,
                                                       "period_cutoff": 2}, "interacting": {"I1": 1, "I2": 1}}):
            total += 1
            probs = verify_episode(generate(seed, cfg))
            if probs:
                bad += 1
                print(seed, cfg, probs[:3])
    print(f"{total - bad}/{total} episodes valid; episodes with problems: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
