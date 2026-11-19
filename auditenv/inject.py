"""Error injectors (CONTRACT §3). Each one changes the correct history, records the
before/after journals (provenance) and a truth issue with its evidence sets.
Evidence references are ("doc", doc_id), ("row", internal row key) or ("fx", fx_id)."""

from __future__ import annotations

import copy
from datetime import date, datetime, timedelta, timezone

from .money import iso, offset_str, parse_offset

MIN_DIFF = 10  # minor units: an injected FX difference must exceed rounding noise


def _foreign_entity(st):
    ents = [e for e in st.entities if e["currency"] != st.base]
    if not ents:
        e = st.new_entity()
        e["currency"] = st.rng.choice(st.foreign)
        st.entities.append(e)
        ents = [e]
    return st.rng.choice(ents)


def _entity(st, entity_id):
    return next(e for e in st.entities if e["id"] == entity_id)


def _row(st, jid, account):
    return next(r for r in st.journals[jid] if r["account"] == account)


def _booked(st, inv):
    return ("inv:" + inv["invoice_id"]) in st.journals


def _fx(st, d: date, cur: str):
    return ("fx", f"{d.isoformat()}:{cur}:{st.base}")


def _free(st, *ids):
    return not any(i in st.touched for i in ids)


def _wrong_date(st, correct: date, local_ts: str, amount: int, cur: str) -> date | None:
    """A plausible wrong rate date: the document's own local/UTC date first, else nearby days."""
    dt = datetime.fromisoformat(local_ts)
    tz_dates = [d for d in (dt.date(), dt.astimezone(timezone.utc).date()) if d != correct]
    near = [correct + timedelta(days=k) for k in (1, 2, 3, 5, 7, -1, -2, -3, -5)]
    st.rng.shuffle(near)
    good = lambda d: (d, cur) in st.fx and abs(st.conv(amount, cur, d) - st.conv(amount, cur, correct)) >= MIN_DIFF
    order = (tz_dates + near) if st.rng.random() < 0.6 else (near + tz_dates)
    return next((d for d in order if good(d)), None)


def _retype(st, items: list[dict]) -> list[dict]:
    return st.retype(items)


# ---------------------------------------------------------------- single errors
def duplicate_invoice(st, scenario="single") -> bool:
    cands = [i for i in st.invoices if st.in_period(i["_cdate"]) and _booked(st, i) and _free(st, i["invoice_id"])
             and i["_cdate"] + timedelta(days=4) <= st.pe]
    if not cands:
        return False
    orig = st.rng.choice(cands)
    d = orig["_cdate"] + timedelta(days=st.rng.randint(0, 3))
    hour = st.rng.randint(max(orig["_dt"].hour + 1, 8), 22) if d == orig["_cdate"] and orig["_dt"].hour < 22 else None
    if d == orig["_cdate"] and hour is None:
        d += timedelta(days=1)
    # the duplicate is always issued strictly after the original (truth amount = later copy)
    items = copy.deepcopy(orig["line_items"])
    if st.hard and st.rng.random() < 0.5:
        items = _retype(st, items)
    dup = st.new_invoice(_entity(st, orig["entity_id"]), d, hour=hour, items=items, currency=orig["currency"])
    jid = st.book_invoice(dup)
    st.touched.update({orig["invoice_id"], dup["invoice_id"]})
    ar = _row(st, jid, "1200")
    rev = _row(st, jid, "4000")
    orig_jid = "inv:" + orig["invoice_id"]
    ar_orig = _row(st, orig_jid, "1200")
    rev_orig = _row(st, orig_jid, "4000")
    evidence = [
        [("doc", orig["doc_id"]), ("doc", dup["doc_id"]), ("row", ar_orig["_k"]), ("row", ar["_k"])],
        [("doc", orig["doc_id"]), ("doc", dup["doc_id"]), ("row", ar_orig["_k"]), ("row", rev["_k"])],
        [("doc", orig["doc_id"]), ("doc", dup["doc_id"]), ("row", rev_orig["_k"]), ("row", ar["_k"])],
        [("doc", orig["doc_id"]), ("doc", dup["doc_id"]), ("row", rev_orig["_k"]), ("row", rev["_k"])],
    ]
    st.record({"type": "duplicate_invoice", "scenario": scenario,
               "affected_ids": [orig["invoice_id"], dup["invoice_id"]], "amount": ar["debit_minor"],
               "evidence": evidence},
              [{"journal": jid, "before": None, "after": st.snapshot(jid)}], [dup["doc_id"]],
              f"invoice {orig['invoice_id']} entered a second time as {dup['invoice_id']} and booked again")
    return True


def fx_invoice(st, inv=None, rate_date=None, scenario="single") -> bool:
    if inv is None:
        cands = [i for i in st.invoices if st.in_period(i["_cdate"]) and _booked(st, i)
                 and i["currency"] != st.base and _free(st, i["invoice_id"])]
        st.rng.shuffle(cands)
        for i in cands:
            d = _wrong_date(st, i["_cdate"], i["issued_at"], i["total_minor"], i["currency"])
            if d is not None:
                inv, rate_date = i, d
                break
        if inv is None:
            return False
    jid = "inv:" + inv["invoice_id"]
    before = st.snapshot(jid)
    correct = st.conv(inv["total_minor"], inv["currency"], inv["_cdate"])
    wrong = st.conv(inv["total_minor"], inv["currency"], rate_date)
    ar, rev = _row(st, jid, "1200"), _row(st, jid, "4000")
    ar["debit_minor"], rev["credit_minor"] = wrong, wrong
    st.touched.add(inv["invoice_id"])
    st.record({"type": "fx_error", "scenario": scenario, "affected_ids": [inv["invoice_id"]],
               "amount": abs(wrong - correct),
               "evidence": [[("doc", inv["doc_id"]), ("row", ar["_k"]), _fx(st, inv["_cdate"], inv["currency"])],
                            [("doc", inv["doc_id"]), ("row", rev["_k"]), _fx(st, inv["_cdate"], inv["currency"])]]},
              [{"journal": jid, "before": before, "after": st.snapshot(jid)}], (),
              f"invoice {inv['invoice_id']} converted with the {rate_date} rate instead of {inv['_cdate']}")
    return True


def fx_payment(st, pay, rate_date, scenario="single") -> bool:
    jid = "pay:" + pay["payment_id"]
    before = st.snapshot(jid)
    correct = st.conv(pay["amount_minor"], pay["currency"], pay["_cdate"])
    wrong = st.conv(pay["amount_minor"], pay["currency"], rate_date)
    cash = _row(st, jid, "1000")
    cash["debit_minor"] = wrong
    st.rebalance(jid)
    st.touched.add(pay["payment_id"])
    st.record({"type": "fx_error", "scenario": scenario, "affected_ids": [pay["payment_id"]],
               "amount": abs(wrong - correct),
               "evidence": [[("doc", pay["doc_id"]), ("row", cash["_k"]), _fx(st, pay["_cdate"], pay["currency"])]]},
              [{"journal": jid, "before": before, "after": st.snapshot(jid)}], (),
              f"payment {pay['payment_id']} cash converted with the {rate_date} rate instead of {pay['_cdate']}")
    return True


def payment_allocation(st, pay=None, partial=None, scenario="single") -> bool:
    rng = st.rng
    if pay is None:
        cands = []
        for p in st.payments:
            if ("pay:" + p["payment_id"]) not in st.journals or not p["invoice_refs"] or not _free(st, p["payment_id"]):
                continue
            for ref in p["invoice_refs"]:
                inv = st.invoice(ref["invoice_id"])
                if ref["amount_minor"] > 0 and _free(st, inv["invoice_id"]) and \
                        st.conv(ref["amount_minor"], p["currency"], inv["_cdate"]) >= 100:
                    cands.append((p, ref))
        if not cands:
            return False
        pay, ref = rng.choice(cands)
    else:
        ref = pay["invoice_refs"][0]
    if partial is None:
        partial = rng.random() < 0.6
    inv = st.invoice(ref["invoice_id"])
    jid = "pay:" + pay["payment_id"]
    before = st.snapshot(jid)
    cur = pay["currency"]
    ar = next(r for r in st.journals[jid] if r["account"] == "1200" and r["invoice_id"] == inv["invoice_id"])
    posted_before = ar["credit_minor"]
    new_alloc = max(1, round(ref["amount_minor"] * rng.uniform(0.3, 0.8))) if partial else 0
    moved = ref["amount_minor"] - new_alloc
    new_credit = st.conv(new_alloc, cur, inv["_cdate"])
    rows = st.journals[jid]
    if partial:
        ar["credit_minor"] = new_credit
    else:
        rows.remove(ar)
    unapplied = next((r for r in rows if r["account"] == "2900"), None)
    add = st.conv(moved, cur, pay["_cdate"])
    if unapplied is None:
        unapplied = st.row(pay["_dt"], "2900", -add, st.entity_of_payment[pay["payment_id"]], None,
                           pay["payment_id"])
        rows.append(unapplied)
    else:
        unapplied["credit_minor"] += add
    st.rebalance(jid)
    st.touched.update({pay["payment_id"], inv["invoice_id"]})
    extra = [_fx(st, inv["_cdate"], cur)] if cur != st.base else []
    # the set must reproduce the amount on its own: a partial allocation needs the AR credit actually
    # posted; with nothing allocated the 2900 row shows where the money went (posted AR credit = 0)
    if partial:
        evidence = [[("doc", pay["doc_id"]), ("doc", inv["doc_id"]), ("row", ar["_k"])] + extra]
    else:
        evidence = [[("doc", pay["doc_id"]), ("doc", inv["doc_id"]), ("row", unapplied["_k"])] + extra]
    st.record({"type": "payment_allocation", "scenario": scenario,
               "affected_ids": [inv["invoice_id"], pay["payment_id"]], "amount": posted_before - new_credit,
               "evidence": evidence},
              [{"journal": jid, "before": before, "after": st.snapshot(jid)}], (),
              f"payment {pay['payment_id']} allocated {'partially' if partial else 'nothing'} to "
              f"{inv['invoice_id']}; the rest went to unapplied cash")
    return True


def period_cutoff(st, inv=None, rate_date=None, booking_date=None, scenario="single") -> bool:
    rng = st.rng
    if inv is None:
        if rng.random() < 0.3:  # prior-period invoice booked late in this period
            cands = [i for i in st.invoices if st.ps - timedelta(days=10) <= i["_cdate"] < st.ps
                     and _free(st, i["invoice_id"])]
            booking_date = st.ps + timedelta(days=rng.randint(0, 3))
        else:  # next-period invoice backdated into this period
            cands = [i for i in st.invoices if st.pe < i["_cdate"] <= st.pe + timedelta(days=7)
                     and _free(st, i["invoice_id"])]
            booking_date = st.pe - timedelta(days=rng.randint(0, 2))
        if not cands:
            inv = st.new_invoice(rng.choice(st.entities), st.pe + timedelta(days=rng.randint(1, 5)))
            booking_date = st.pe - timedelta(days=rng.randint(0, 2))
        else:
            inv = rng.choice(cands)
    dt = st.at(booking_date, rng.randint(9, 22), rng.randrange(60))
    jid = st.book_invoice(inv, rate_date=rate_date or inv["_cdate"], dt=dt)
    st.touched.add(inv["invoice_id"])
    ar, rev = _row(st, jid, "1200"), _row(st, jid, "4000")
    st.record({"type": "period_cutoff", "scenario": scenario, "affected_ids": [inv["invoice_id"]],
               "amount": ar["debit_minor"],
               "evidence": [[("doc", inv["doc_id"]), ("row", ar["_k"])],
                            [("doc", inv["doc_id"]), ("row", rev["_k"])]]},
              [{"journal": jid, "before": None, "after": st.snapshot(jid)}], (),
              f"invoice {inv['invoice_id']} issued {inv['_cdate']} (outside the period) booked on {booking_date}")
    return True


# ---------------------------------------------------------------- interacting scenarios
def scenario_i1(st) -> None:
    """Foreign-currency payment at the period end: partially allocated and its cash converted
    with the rate of the date shown in the bank's timezone (next day)."""
    rng = st.rng
    ent = _foreign_entity(st)
    inv = st.new_invoice(ent, st.ps + timedelta(days=rng.randrange(st.ndays - 3)))
    st.book_invoice(inv)
    # ordinary bank offset and an ordinary evening hour: nothing about the document itself stands out;
    # the clerk used the date written in the bank's timezone, or the next-day value date
    pay = st.new_payment(st.pe, inv["currency"], inv["total_minor"], [(inv, inv["total_minor"])], ent["id"],
                         hour=rng.randint(18, 23))
    st.book_payment(pay)
    payment_allocation(st, pay=pay, partial=True, scenario="I1")
    cands = [datetime.fromisoformat(pay["timestamp"]).date(), st.pe + timedelta(days=1), st.pe + timedelta(days=2),
             st.pe + timedelta(days=3), st.pe - timedelta(days=1)]
    amt, cur = pay["amount_minor"], pay["currency"]
    d = next((d for d in cands if d != st.pe and
              abs(st.conv(amt, cur, d) - st.conv(amt, cur, st.pe)) >= MIN_DIFF), cands[1])
    fx_payment(st, pay, d, scenario="I1")


def scenario_i2(st) -> None:
    """Next-period foreign invoice backdated into the period and converted at the booking-date rate."""
    rng = st.rng
    ent = _foreign_entity(st)
    inv = st.new_invoice(ent, st.pe + timedelta(days=rng.randint(1, 3)))
    booking = st.pe - timedelta(days=rng.randint(0, 1))
    amt, cur = inv["total_minor"], inv["currency"]
    rate_date = next((d for d in (booking, booking - timedelta(days=1), booking - timedelta(days=2),
                                  booking - timedelta(days=4))
                      if abs(st.conv(amt, cur, d) - st.conv(amt, cur, inv["_cdate"])) >= MIN_DIFF), booking)
    period_cutoff(st, inv=inv, rate_date=rate_date, booking_date=booking, scenario="I2")
    jid = "inv:" + inv["invoice_id"]
    ar, rev = _row(st, jid, "1200"), _row(st, jid, "4000")
    correct = st.conv(amt, cur, inv["_cdate"])
    st.record({"type": "fx_error", "scenario": "I2", "affected_ids": [inv["invoice_id"]],
               "amount": abs(ar["debit_minor"] - correct),
               "evidence": [[("doc", inv["doc_id"]), ("row", ar["_k"]), _fx(st, inv["_cdate"], cur)],
                            [("doc", inv["doc_id"]), ("row", rev["_k"]), _fx(st, inv["_cdate"], cur)]]},
              [], (), f"invoice {inv['invoice_id']} converted with the {rate_date} rate instead of {inv['_cdate']}")


SINGLE = {
    "period_cutoff": period_cutoff,
    "duplicate_invoice": duplicate_invoice,
    "fx_error": fx_invoice,
    "payment_allocation": payment_allocation,
}


def apply(st, errors: dict, inter: dict) -> None:
    for _ in range(inter.get("I1", 0)):
        scenario_i1(st)
    for _ in range(inter.get("I2", 0)):
        scenario_i2(st)
    for typ in ("period_cutoff", "duplicate_invoice", "fx_error", "payment_allocation"):
        for _ in range(errors.get(typ, 0)):
            if not SINGLE[typ](st):
                _make_room(st, typ)
                if not SINGLE[typ](st):
                    raise RuntimeError(f"cannot inject {typ}")


def _make_room(st, typ) -> None:
    """Add a fresh, correctly booked event that the injector can use."""
    rng = st.rng
    if typ == "fx_error":
        inv = st.new_invoice(_foreign_entity(st), st.ps + timedelta(days=rng.randrange(st.ndays)))
        st.book_invoice(inv)
    elif typ == "duplicate_invoice":
        inv = st.new_invoice(rng.choice(st.entities), st.ps + timedelta(days=rng.randrange(st.ndays - 4)))
        st.book_invoice(inv)
    elif typ == "payment_allocation":
        ent = rng.choice(st.entities)
        inv = st.new_invoice(ent, st.ps + timedelta(days=rng.randrange(st.ndays - 5)))
        st.book_invoice(inv)
        pay = st.new_payment(inv["_cdate"] + timedelta(days=rng.randint(1, 4)), inv["currency"],
                             inv["total_minor"], [(inv, inv["total_minor"])], ent["id"])
        st.book_payment(pay)
