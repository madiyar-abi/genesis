"""Independent verifier of generated episodes (jury criterion "data and truth").

Works only from the public tables plus the closed files (truth, provenance); it does not
reuse generator internals. For each episode it checks:
1. structure: ids unique, counts, base-currency ledger, one-sided integer amounts;
2. pre-injection books (provenance changes reverted): every journal balances and the books
   follow the bookkeeping policy exactly -> zero discrepancies;
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
from collections import defaultdict
from datetime import date
from pathlib import Path

from .money import convert, local_date, parse_offset


class Books:
    def __init__(self, manifest: dict, tables: dict):
        self.m = manifest
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
        js = self.journals()
        for jid, rows in js.items():
            if sum(r["debit_minor"] for r in rows) != sum(r["credit_minor"] for r in rows):
                problems.append(f"unbalanced journal {jid}")
        # invoices: booking, period, FX
        booked, self.voided = {}, set()
        for jid, rows in js.items():
            if jid.startswith("inv:"):
                ar = [r for r in rows if r["account"] == "1200"]
                rev = [r for r in rows if r["account"] == "4000"]
                if len(ar) == 2 and len(rev) == 2:  # booking + full credit note (cancelled invoice)
                    ar_dr = [r for r in ar if r["debit_minor"]]
                    amounts = {r["debit_minor"] + r["credit_minor"] for r in ar + rev}
                    reversal = [r for r in ar + rev if (r["account"] == "1200") == bool(r["credit_minor"])]
                    if len(ar_dr) != 1 or len(amounts) != 1 or len(reversal) != 2 \
                            or reversal[0]["timestamp"] != reversal[1]["timestamp"] \
                            or datetime_key(reversal[0]["timestamp"]) < datetime_key(ar_dr[0]["timestamp"]):
                        problems.append(f"malformed credit note in {jid}")
                        continue
                    if not self.in_period(reversal[0]["timestamp"]):
                        problems.append(f"credit note {reversal[0]['row_id']} outside the period")
                    self.voided.add(jid[4:])
                    ar = ar_dr
                    rev = [r for r in rev if r["credit_minor"]]
                if len(ar) != 1 or len(rev) != 1 or ar[0]["debit_minor"] != rev[0]["credit_minor"]:
                    problems.append(f"malformed invoice journal {jid}")
                    continue
                booked[jid[4:]] = ar[0]
        for iid, ar in booked.items():
            inv = self.invoices.get(iid)
            if inv is None:
                problems.append(f"ledger references unknown invoice {iid}")
                continue
            if not self.in_period(ar["timestamp"]):
                problems.append(f"ledger row {ar['row_id']} outside the period")
            if not self.in_period(inv["issued_at"]):
                issues.append(("period_cutoff", (iid,), ar["debit_minor"]))
            correct = self.conv(inv["total_minor"], inv["currency"], inv["issued_at"])
            if ar["debit_minor"] != correct:
                issues.append(("fx_error", (iid,), abs(ar["debit_minor"] - correct)))
        for iid, inv in self.invoices.items():
            for n, line in enumerate(inv["line_items"], start=1):
                if line["amount_minor"] != line["quantity"] * line["unit_price_minor"]:
                    problems.append(f"invoice {iid} line {n} amount != quantity times unit price")
            if sum(li["amount_minor"] for li in inv["line_items"]) != inv["total_minor"]:
                problems.append(f"invoice {iid} total != line items")
            if self.in_period(inv["issued_at"]) and iid not in booked:
                problems.append(f"in-period invoice {iid} not booked")
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
            rows = js.get("pay:" + pid)
            if not self.in_period(pay["timestamp"]):
                if rows:
                    problems.append(f"out-of-period payment {pid} booked")
                continue
            if not rows:
                problems.append(f"in-period payment {pid} not booked")
                continue
            cash = [r for r in rows if r["account"] == "1000"]
            if len(cash) != 1:
                problems.append(f"payment {pid}: expected one cash row")
                continue
            posted = cash[0]["debit_minor"] - cash[0]["credit_minor"]
            correct = self.conv(pay["amount_minor"], pay["currency"], pay["timestamp"])
            if posted != correct:
                issues.append(("fx_error", (pid,), abs(posted - correct)))
            refs = pay["invoice_refs"] or []
            if sum(r["amount_minor"] for r in refs) > max(pay["amount_minor"], 0):
                problems.append(f"payment {pid}: refs exceed amount")
            for ref in refs:
                inv = self.invoices.get(ref["invoice_id"])
                if inv is None:
                    problems.append(f"payment {pid} references unknown invoice")
                    continue
                expected = self.conv(ref["amount_minor"], pay["currency"], inv["issued_at"])
                credit = sum(r["credit_minor"] - r["debit_minor"] for r in rows
                             if r["account"] == "1200" and r["invoice_id"] == inv["invoice_id"])
                if credit < expected:
                    issues.append(("payment_allocation", tuple(sorted((inv["invoice_id"], pid))), expected - credit))
                elif credit > expected:
                    problems.append(f"payment {pid} over-allocated to {inv['invoice_id']}")
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


def _structure(ep: dict) -> list[str]:
    problems = []
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
    for key, rows in (("invoice_id", t["invoices"]), ("payment_id", t["payments"]), ("fx_id", t["fx"])):
        if len({r[key] for r in rows}) != len(rows):
            problems.append(f"duplicate {key}")
    for r in t["ledger"]:
        d, c = r["debit_minor"], r["credit_minor"]
        if r["currency"] != m["base_currency"] or type(d) is not int or type(c) is not int or (d > 0) == (c > 0) \
                or d < 0 or c < 0:
            problems.append(f"bad ledger row {r['row_id']}")
    if not 200 <= len(t["ledger"]) <= 2000 or not 20 <= actual_docs <= 200:
        problems.append("episode size outside 200-2000 rows / 20-200 documents")
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
            row = ev_rows[0]
            ok = (not books.in_period(inv["issued_at"]) and books.in_period(row["timestamp"])
                  and row["debit_minor"] + row["credit_minor"] == exp)
        elif typ == "fx_error":
            doc, row = ev_docs[0], ev_rows[0]
            if "invoice_id" in doc:
                correct = conv(doc["total_minor"], doc["currency"], doc["issued_at"])
            else:
                correct = conv(doc["amount_minor"], doc["currency"], doc["timestamp"])
            ok = abs(row["debit_minor"] + row["credit_minor"] - correct) == exp
        else:  # payment_allocation
            pay = next(d for d in ev_docs if "payment_id" in d)
            inv = next(d for d in ev_docs if "invoice_id" in d and "payment_id" not in d)
            ref = next(r for r in pay["invoice_refs"] if r["invoice_id"] == inv["invoice_id"])
            expected = conv(ref["amount_minor"], pay["currency"], inv["issued_at"])
            row = ev_rows[0]
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


def verify_episode(ep: dict) -> list[str]:
    problems = _structure(ep)
    m, t = ep["manifest"], ep["tables"]
    if ep["truth"].get("episode_id") != m["episode_id"]:
        problems.append("truth episode_id differs from manifest")
    # pre-injection: correct books
    pre_issues, pre_problems = Books(m, revert(ep)).discrepancies()
    problems += [f"pre-injection: {p}" for p in pre_problems]
    problems += [f"pre-injection discrepancy {i}" for i in pre_issues]
    # post-injection: declared discrepancies == recomputed discrepancies
    issues, post_problems = Books(m, t).discrepancies()
    problems += [f"post-injection: {p}" for p in post_problems]
    found = sorted(issues)
    declared = sorted((i["type"], tuple(i["affected_ids"]), i["expected_amount_minor"])
                      for i in ep["truth"]["issues"])
    if found != declared:
        problems.append(f"truth mismatch: recomputed {found} declared {declared}")
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
            problems += [f"{iss['issue_id']}: {p}" for p in _sufficient(Books(m, t), iss, s, rows, docs)]
    return problems


def _verify_directory(root: Path) -> int:
    from .load import load_episode

    index = root / "index.json"
    indexed = index.exists()
    try:
        entries = {p.name for p in root.iterdir() if p.is_dir() and (p / "public").is_dir()}
        if indexed:
            records = json.loads(index.read_text(encoding="utf-8"))
            if not isinstance(records, list) or not records:
                raise ValueError("expected a nonempty episode list")
            expected = set()
            for record in records:
                name = record.get("episode_id") if isinstance(record, dict) else None
                if not isinstance(name, str) or not name or name in expected:
                    raise ValueError(f"invalid or duplicate episode_id {name!r}")
                expected.add(name)
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
            if indexed and ep["episode_id"] != name:
                problems.append(f"manifest episode_id differs from directory {name}")
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
    ap.add_argument("--seeds", default="0-199")
    ap.add_argument("--dir", default=None,
                    help="verify every episode under this directory (e.g. episodes/dev)")
    args = ap.parse_args(argv)
    bad = total = 0

    if args.dir is not None:
        return _verify_directory(Path(args.dir))

    for seed in parse_seeds(args.seeds):
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
