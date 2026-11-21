"""Independent chronology / causality checker for the public books (round 20).

Generates episodes in memory with `auditenv.generator.generate(seed, config)` and reads ONLY the public parts
(`tables`, `policy`, `manifest`, `task`); truth and provenance are never touched. No other auditenv module is used
except `auditenv.jury.SCENARIOS` (the config list).

Checks (ids in brackets are the keys printed in the report):
  a  [a_pay_before_inv]     a payment that references an invoice is not earlier (instant) than the invoice's issued_at
     [a_ref_unknown]        every invoice_ref names an existing invoice
     [a_due_before_issue]   due_at >= issued_at
  b  [b_cn_before_booking]  a credit note (Dr 4000 / Cr 1200, invoice_id, no payment_id) is strictly after the original
                            invoice booking (CONTRACT: "inside the period and after the booking")
     [b_cn_orphan]          a credit note has an original booking in the ledger
     [b_cn_not_full]        the credit note reverses the booking in full (same amount)
     [b_reissue_before_orig] a re-issued replacement (same entity, currency, line items, other id) of a credit-noted
                            invoice is not issued before the cancelled original
  c  [c_neg_credit]         per customer and payment currency, running unapplied credit from documents
                            (receipt: amount - sum(refs); refund: amount < 0) never goes negative in timestamp order
                            (receipts sort before refunds at an equal instant)
  d  [d_ledger_out_period]  every ledger row's company-tz date lies in [period_start, period_end]
     [d_cutoff_item]        (counted, not a violation unless unexplained) an invoice booked in the ledger although its
                            issue date is outside the period -- the policy's period_cutoff error kind
  e  [e_fx_missing]         every foreign-currency document the books need a rate for (booked invoices, payments,
                            invoices referenced by payments) has fx row "{company-tz date}:{doc cur}:{base}"
  f  [f_inv_booked_before_issue] an invoice's ledger booking instant is not before its issued_at
     [f_pay_posted_before_doc]  a payment journal's instant is not before the payment timestamp
     [f_ar_before_booking]  an AR credit for an invoice in a payment journal is not earlier than the invoice booking
                            (CONTRACT allows an in-period invoice to be posted after its issue instant, but cash
                            applied to a receivable before it is posted makes that invoice's AR negative in time order)
     [f_inv_not_booked]     every invoice issued inside the period is booked ("Invoice issued ... inside the period")
     [f_pay_not_posted]     every payment dated inside the period has a ledger journal
     [f_overallocated]      running sum of positive invoice_refs to an invoice never exceeds its total
     [f_pay_entity]         a payment journal's entity_id equals the entity of every invoice it references
     [f_fx_posted]          posted base amounts use the policy-date rate: invoice AR debit = convert(total,
                            rate(issue date)), payment cash row = convert(|amount|, rate(payment date))

A violation is "explained" when the config may contain an injected error type that produces it (see EXPLAINS) and
the number of distinct affected ids for that type does not exceed the injected count (when the count is known).
Exit 0 iff no unexplained violation in the clean configs D01-D05 (default and hard).

Run: PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/chronology.py [--seeds 30000-30299]
"""
import argparse
import collections
import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from auditenv.generator import generate
from auditenv.jury import SCENARIOS

ALL_TYPES = {"duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff"}
EXPLAINS = {  # violation key -> injected error type that can cause it
    "d_cutoff_item": "period_cutoff",
    "f_inv_booked_before_issue": "period_cutoff",
    "f_fx_posted": "fx_error",
}
INFO = {"c_tie"}  # counted, never a violation
CHECKS = ["a_pay_before_inv", "a_ref_unknown", "a_due_before_issue", "b_cn_before_booking", "b_cn_orphan",
          "b_cn_not_full", "b_reissue_before_orig", "c_neg_credit", "d_ledger_out_period", "d_cutoff_item",
          "e_fx_missing", "f_inv_booked_before_issue", "f_pay_posted_before_doc", "f_ar_before_booking",
          "f_inv_not_booked", "f_pay_not_posted", "f_overallocated", "f_pay_entity", "f_fx_posted", "c_tie"]


def tzinfo(s):
    sign = 1 if s[0] == "+" else -1
    h, m = s[1:].split(":")
    return timezone(sign * timedelta(hours=int(h), minutes=int(m)))


def ts(s):
    return datetime.fromisoformat(s)


def norm_items(items):
    return sorted((re.sub(r"[^0-9a-z]", "", i["description"].lower()), i["quantity"], i["unit_price_minor"],
                   i["amount_minor"]) for i in items)


def allowed_types(cfg):
    """Injected error types (with count, None = unknown) this config may contain."""
    if "errors" not in cfg:  # errors drawn at random: any type, count unknown
        return {t: None for t in ALL_TYPES}
    out = collections.Counter({t: n for t, n in cfg.get("errors", {}).items() if n})
    inter = cfg.get("interacting", {})
    for _ in range(inter.get("I1", 0)):
        out["payment_allocation"] += 1
        out["fx_error"] += 1
    for _ in range(inter.get("I2", 0)):
        out["period_cutoff"] += 1
        out["fx_error"] += 1
    return dict(out)


def check_episode(ep):
    """Return list of (check_key, ids_tuple, detail_str) from public data only."""
    T, pol, man = ep["tables"], ep["policy"], ep["manifest"]
    z = tzinfo(pol["timezone"])
    base = pol["base_currency"]
    ps, pe = pol["period"]["start"], pol["period"]["end"]
    exps = man["amount_exponents"]
    cdate = lambda s: ts(s).astimezone(z).date().isoformat()
    inper = lambda s: ps <= cdate(s) <= pe
    fx = {f["fx_id"]: f["rate"] for f in T["fx"]}
    inv = {i["invoice_id"]: i for i in T["invoices"]}
    out = []

    def rate(cur, day):
        return fx.get(f"{day}:{cur}:{base}")

    def convert(amount, cur, r):
        q = Decimal(amount) / (Decimal(10) ** exps[cur]) * Decimal(r) * (Decimal(10) ** exps[base])
        return int(q.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    # ledger indexes
    booking = collections.defaultdict(list)   # invoice_id -> AR debit rows without payment_id
    cnotes = collections.defaultdict(list)    # invoice_id -> AR credit rows without payment_id (credit notes)
    pay_rows = collections.defaultdict(list)  # payment_id -> rows
    for r in T["ledger"]:
        if not inper(r["timestamp"]):
            out.append(("d_ledger_out_period", (r["row_id"],), r["timestamp"]))
        if r["payment_id"]:
            pay_rows[r["payment_id"]].append(r)
        elif r["invoice_id"] and r["account"] == "1200":
            (booking if r["debit_minor"] else cnotes)[r["invoice_id"]].append(r)

    # invoices: due date, booking vs issue, cutoff, completeness, fx
    for i in T["invoices"]:
        iid = i["invoice_id"]
        if ts(i["due_at"]) < ts(i["issued_at"]):
            out.append(("a_due_before_issue", (iid,), f"issued {i['issued_at']} due {i['due_at']}"))
        for r in booking.get(iid, []):
            if ts(r["timestamp"]) < ts(i["issued_at"]):
                out.append(("f_inv_booked_before_issue", (iid, r["row_id"]), f"issued {i['issued_at']} booked {r['timestamp']}"))
        if booking.get(iid) and not inper(i["issued_at"]):
            out.append(("d_cutoff_item", (iid, booking[iid][0]["row_id"]), f"issued {i['issued_at']} ({cdate(i['issued_at'])}) period {ps}..{pe}"))
        if inper(i["issued_at"]) and not booking.get(iid):
            out.append(("f_inv_not_booked", (iid,), f"issued {i['issued_at']}"))
        if booking.get(iid) and i["currency"] != base:
            r_ = rate(i["currency"], cdate(i["issued_at"]))
            if r_ is None:
                out.append(("e_fx_missing", (iid, f"{cdate(i['issued_at'])}:{i['currency']}:{base}"), "invoice"))
            else:
                exp = convert(i["total_minor"], i["currency"], r_)
                for r in booking[iid]:
                    if r["debit_minor"] != exp:
                        out.append(("f_fx_posted", (iid, r["row_id"]), f"posted {r['debit_minor']} expected {exp}"))
        elif booking.get(iid):
            for r in booking[iid]:
                if r["debit_minor"] != i["total_minor"]:
                    out.append(("f_fx_posted", (iid, r["row_id"]), f"base-cur posted {r['debit_minor']} total {i['total_minor']}"))

    # credit notes (b)
    for iid, rows in cnotes.items():
        orig = booking.get(iid)
        if not orig:
            out.append(("b_cn_orphan", (iid,) + tuple(r["row_id"] for r in rows), "credit note without booking"))
            continue
        bts = max(ts(r["timestamp"]) for r in orig)
        for r in rows:
            if ts(r["timestamp"]) <= bts:
                out.append(("b_cn_before_booking", (iid, r["row_id"]), f"cn {r['timestamp']} booking {orig[0]['timestamp']}"))
        if sum(r["credit_minor"] for r in rows) != sum(r["debit_minor"] for r in orig):
            out.append(("b_cn_not_full", (iid,), f"cn {sum(r['credit_minor'] for r in rows)} booked {sum(r['debit_minor'] for r in orig)}"))
        o = inv.get(iid)
        if o:
            key = (o["entity_id"], o["currency"], norm_items(o["line_items"]))
            for j in T["invoices"]:
                if j["invoice_id"] != iid and (j["entity_id"], j["currency"], norm_items(j["line_items"])) == key:
                    if ts(j["issued_at"]) < ts(o["issued_at"]):
                        out.append(("b_reissue_before_orig", (iid, j["invoice_id"]), f"orig {o['issued_at']} reissue {j['issued_at']}"))

    # payments (a, c, e, f)
    events = collections.defaultdict(list)  # (entity, cur) -> [(instant, order, delta, payment_id)]
    alloc = collections.defaultdict(list)   # invoice_id -> [(instant, amount, payment_id)]
    for p in T["payments"]:
        pid, pts, cur = p["payment_id"], ts(p["timestamp"]), p["currency"]
        refs = p["invoice_refs"] or []
        rows = pay_rows.get(pid, [])
        if inper(p["timestamp"]) and not rows:
            out.append(("f_pay_not_posted", (pid,), p["timestamp"]))
        for r in rows:
            if ts(r["timestamp"]) < pts:
                out.append(("f_pay_posted_before_doc", (pid, r["row_id"]), f"doc {p['timestamp']} posted {r['timestamp']}"))
        ents = {r["entity_id"] for r in rows if r["entity_id"]}
        for ref in refs:
            i = inv.get(ref["invoice_id"])
            if i is None:
                out.append(("a_ref_unknown", (pid, ref["invoice_id"]), ""))
                continue
            if pts < ts(i["issued_at"]):
                out.append(("a_pay_before_inv", (pid, i["invoice_id"]), f"paid {p['timestamp']} issued {i['issued_at']}"))
            if ents and ents != {i["entity_id"]}:
                out.append(("f_pay_entity", (pid, i["invoice_id"]), f"journal {sorted(ents)} invoice {i['entity_id']}"))
            alloc[i["invoice_id"]].append((pts, ref["amount_minor"], pid))
            if i["currency"] != base and rows and rate(i["currency"], cdate(i["issued_at"])) is None:
                out.append(("e_fx_missing", (pid, i["invoice_id"], f"{cdate(i['issued_at'])}:{i['currency']}:{base}"), "ref invoice"))
            for r in rows:
                if r["account"] == "1200" and r["credit_minor"] and r["invoice_id"] == i["invoice_id"] and booking.get(i["invoice_id"]):
                    if ts(r["timestamp"]) < min(ts(b["timestamp"]) for b in booking[i["invoice_id"]]):
                        out.append(("f_ar_before_booking", (pid, i["invoice_id"], r["row_id"]), f"ar credit {r['timestamp']} booking {booking[i['invoice_id']][0]['timestamp']}"))
        if rows and cur != base:
            r_ = rate(cur, cdate(p["timestamp"]))
            if r_ is None:
                out.append(("e_fx_missing", (pid, f"{cdate(p['timestamp'])}:{cur}:{base}"), "payment"))
            else:
                exp = convert(abs(p["amount_minor"]), cur, r_)
                for r in rows:
                    if r["account"] == "1000" and (r["debit_minor"] or r["credit_minor"]) != exp:
                        out.append(("f_fx_posted", (pid, r["row_id"]), f"cash {r['debit_minor'] or r['credit_minor']} expected {exp}"))
        ent = next(iter(ents)) if len(ents) == 1 else ({inv[x["invoice_id"]]["entity_id"] for x in refs if x["invoice_id"] in inv} or {None}).pop()
        if ent is None:
            continue  # unidentified receipt: credit belongs to nobody known
        if p["amount_minor"] < 0:
            events[(ent, cur)].append((pts, 1, p["amount_minor"], pid))
        else:
            events[(ent, cur)].append((pts, 0, p["amount_minor"] - sum(x["amount_minor"] for x in refs), pid))

    for (ent, cur), evs in events.items():
        evs.sort()
        bal, seen = 0, []
        for k, (t, order, delta, pid) in enumerate(evs):
            bal += delta
            seen.append(pid)
            if order == 1 and any(e[0] == t and e[1] == 0 for e in evs):
                out.append(("c_tie", (ent, pid), "refund at same instant as a receipt"))
            if bal < 0:
                out.append(("c_neg_credit", (ent, cur, pid), f"balance {bal} {cur} at {t.isoformat()} after {seen}"))
                bal = 0  # report each shortfall once

    for iid, al in alloc.items():
        al.sort()
        run = 0
        for t, amt, pid in al:
            run += amt
            if run > inv[iid]["total_minor"]:
                out.append(("f_overallocated", (iid, pid), f"refs {run} > total {inv[iid]['total_minor']} at {t.isoformat()}"))
    return out


def configs():
    yield "default", "default", {}
    yield "hard", "hard", {"difficulty": "hard"}
    for name, cfg in SCENARIOS.items():
        yield name, "default", dict(cfg)
        yield name, "hard", dict(cfg, difficulty="hard")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", default="30000-30299", help="inclusive range a-b")
    args = ap.parse_args(argv)
    lo, hi = (int(x) for x in args.seeds.split("-"))
    counts = collections.defaultdict(collections.Counter)  # (name, diff) -> check -> n
    unexplained, n_eps = [], 0
    for name, diff, cfg in configs():
        allowed = allowed_types(cfg)
        clean = name in {f"D{n:02d}" for n in range(1, 6)}
        for seed in range(lo, hi + 1):
            ep = generate(seed, cfg)
            n_eps += 1
            viol = check_episode(ep)
            per_type_ids = collections.defaultdict(set)
            for key, ids, _ in viol:
                if key in EXPLAINS and EXPLAINS[key] in allowed:
                    per_type_ids[EXPLAINS[key]].add(ids[0])
            for key, ids, detail in viol:
                counts[(name, diff)][key] += 1
                if key in INFO:
                    continue
                t = EXPLAINS.get(key)
                ok = t in allowed and (allowed[t] is None or len(per_type_ids[t]) <= allowed[t])
                if not ok:
                    unexplained.append((clean, name, diff, seed, key, ids, detail))
    print(f"episodes checked: {n_eps} (seeds {lo}-{hi}, {n_eps // (hi - lo + 1)} configs)\n")
    used = [c for c in CHECKS if any(counts[k][c] for k in counts)]
    print("config/diff".ljust(14) + " ".join(c[:14].rjust(14) for c in used))
    for k in counts:
        print(f"{k[0]}/{k[1]}".ljust(14) + " ".join(str(counts[k][c]).rjust(14) for c in used))
    print(f"\ntotals: " + ", ".join(f"{c}={sum(counts[k][c] for k in counts)}" for c in CHECKS))
    print(f"\nunexplained violations: {len(unexplained)} ({sum(u[0] for u in unexplained)} in clean configs)")
    for clean, name, diff, seed, key, ids, detail in unexplained:
        print(f"  {'CLEAN ' if clean else ''}{name}/{diff} seed={seed} {key} ids={list(ids)} {detail}")
    return 1 if any(u[0] for u in unexplained) else 0


if __name__ == "__main__":
    sys.exit(main())
