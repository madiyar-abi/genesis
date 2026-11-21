"""Synthetic company generator (CONTRACT §2-3).

Order: hidden company history (entities, invoices, payments, expenses, FX) ->
correct double-entry ledger -> injected errors with recorded causal change
(provenance) -> rendering with randomised ids/order -> truth with evidence sets.
Deterministic: same (seed, config, GENERATOR_VERSION) -> identical episode.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from .money import EXPONENT, convert, iso, offset_str, parse_offset, rate_str

GENERATOR_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"
ISSUE_TYPES = ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")
ALLOCATIONS = ("partial", "missing")  # payment_allocation: part of the ref allocated, or nothing
SCENARIOS = ("I1", "I2")
MAX_ISSUES = 12
DIFFICULTIES = ("default", "hard")

USD_VALUE = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "CHF": 1.12, "JPY": 0.0067, "KZT": 0.0021}
BASES = ("USD", "EUR", "GBP", "KZT")
OFFSETS_MIN = (-300, -180, 0, 60, 180, 300, 330, 540)
PRODUCTS = (
    ("Consulting hours", 80, 250, 1, 40),
    ("Software license", 300, 3000, 1, 10),
    ("Implementation services", 1000, 8000, 1, 3),
    ("Training session", 400, 1500, 1, 5),
    ("Cloud hosting", 200, 2000, 1, 3),
    ("Hardware lease", 150, 900, 1, 12),
    ("Data migration", 1500, 6000, 1, 2),
    ("Security review", 2000, 9000, 1, 1),
)
ACCOUNTS = {
    "1000": "Cash", "1200": "Accounts receivable", "2900": "Unapplied cash",
    "4000": "Revenue", "6100": "Rent", "6200": "Payroll", "6300": "Software",
    "6400": "Bank fees", "7900": "FX gain/loss",
}
LEDGER_FIELDS = ("row_id", "timestamp", "account", "debit_minor", "credit_minor", "currency",
                 "entity_id", "invoice_id", "payment_id")
INVOICE_FIELDS = ("doc_id", "invoice_id", "entity_id", "issued_at", "due_at", "currency",
                  "total_minor", "line_items")
PAYMENT_FIELDS = ("doc_id", "payment_id", "timestamp", "currency", "amount_minor", "invoice_refs")
FX_FIELDS = ("fx_id", "date", "source_currency", "target_currency", "rate")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def secret() -> str:
    """Grader-only key. Unset (public train/dev) -> episodes are reproducible by anyone. For hidden
    runs set AUDITENV_SECRET in the grader process only: without it the seed cannot be recovered
    from episode_id and episodes cannot be regenerated, even with this open-source generator."""
    return os.environ.get("AUDITENV_SECRET", "")


def gen_config(config: dict) -> dict:
    """Normalise the generation-relevant config (equal meaning -> equal company)."""
    explicit = "errors" in config or "interacting" in config
    given_e, given_i = config.get("errors", {}), config.get("interacting", {})
    for name, counts, allowed in (("errors", given_e, ISSUE_TYPES), ("interacting", given_i, SCENARIOS)):
        if not isinstance(counts, dict):
            raise ValueError(f"{name} must be an object of counts")
        for key, val in counts.items():
            if key not in allowed or isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise ValueError(f"invalid count or unknown key in {name}")
    n = config.get("n_invoices")
    if n is not None and (isinstance(n, bool) or not isinstance(n, int) or not 10 <= n <= 100):
        raise ValueError("n_invoices must be an int in [10, 100] (keeps documents <= 200)")
    if not isinstance(config.get("distractors", True), bool):
        raise ValueError("distractors must be true or false")
    ts = config.get("transform_seed")
    if ts is not None and (isinstance(ts, bool) or not isinstance(ts, int)):
        raise ValueError("transform_seed must be an int or null")
    difficulty = config.get("difficulty", "default")
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {DIFFICULTIES}")
    allocation = config.get("allocation")
    if allocation is not None and allocation not in ALLOCATIONS:
        raise ValueError(f"allocation must be one of {ALLOCATIONS} or null")
    if not isinstance(config.get("ensure_distractors", False), bool):
        raise ValueError("ensure_distractors must be true or false")
    gen = {
        "errors": {t: given_e.get(t, 0) for t in ISSUE_TYPES} if explicit else None,
        "interacting": {k: given_i.get(k, 0) for k in SCENARIOS} if explicit else None,
        "n_invoices": n,
        "distractors": bool(config.get("distractors", True)),
    }
    if difficulty != "default":  # absent for default: default episodes stay byte-identical
        gen["difficulty"] = difficulty
    if allocation is not None:  # likewise: absent unless a payment_allocation variant is requested
        gen["allocation"] = allocation
    if config.get("ensure_distractors"):  # likewise: absent unless requested
        gen["ensure_distractors"] = True
    return gen


def episode_id_for(seed: int, config: dict, key: str | None = None) -> str:
    """`key` overrides AUDITENV_SECRET (judge_adapter passes its grader key); empty -> the public key."""
    msg = f"{GENERATOR_VERSION}|{seed}|{canonical(gen_config(config))}|{config.get('transform_seed')}"
    key = ((secret() if key is None else key) or "auditenv-public").encode()
    return "ep_" + hmac.new(key, msg.encode(), hashlib.sha256).hexdigest()[:12]


def _month_end(d: date) -> date:
    nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return nxt - timedelta(days=1)


class State:
    """Mutable hidden history of one company. Internal fields start with '_'."""

    def __init__(self, seed: int, config: dict, key: str | None = None):
        self.seed = seed
        self.config = config
        self.gen = gen_config(config)
        self.hard = self.gen.get("difficulty") == "hard"
        key = secret() if key is None else key
        self.rng = random.Random(f"auditenv|{key}|{GENERATOR_VERSION}|{seed}|{canonical(self.gen)}")
        rng = self.rng
        self.base = rng.choice(BASES)
        pool = [c for c in USD_VALUE if c != self.base]
        rng.shuffle(pool)
        self.foreign = sorted(pool[: rng.randint(2, 3)])
        self.tz_min = rng.choice(OFFSETS_MIN)
        self.tz_str = offset_str(self.tz_min)
        self.tz = parse_offset(self.tz_str)
        self.ps = date(rng.choice((2025, 2026)), rng.randint(1, 12), 1)
        self.pe = _month_end(self.ps)
        self.ndays = (self.pe - self.ps).days + 1
        self.bank_offset = rng.choice(OFFSETS_MIN)
        self.invoices: list[dict] = []
        self.payments: list[dict] = []
        self.journals: dict[str, list[dict]] = {}
        self.entity_of_payment: dict[str, str | None] = {}
        self.touched: set[str] = set()
        self.issues: list[dict] = []
        self.injections: list[dict] = []
        self._k = 0
        self._used: set[str] = set()
        self._styles = {
            "invoice": rng.randrange(4), "payment": rng.randrange(3), "doc": rng.randrange(3),
            "entity": rng.randrange(3), "row": rng.randrange(3),
        }
        self._build_fx()

    # ---------- ids ----------
    def new_id(self, kind: str) -> str:
        rng, s = self.rng, self._styles[kind]
        while True:
            n = rng.randrange(1, 10**6)
            if kind == "invoice":
                i = (f"INV-{n:06d}", f"SI-{self.ps.year}-{n:06d}", f"F{n:07d}",
                     f"{self.ps.year % 100}{self.ps.month:02d}-{n:06d}")[s]
            elif kind == "payment":
                i = (f"PAY-{n:06d}", f"RCPT{n:07d}", f"BNK-{n:06d}")[s]
            elif kind == "doc":
                i = (f"D-{n:06x}", f"DOC{n:07d}", f"{rng.randrange(16**8):08x}")[s]
            else:
                i = (f"C-{n % 10**4:04d}", f"CUST{n % 10**5:05d}", f"E{n % 10**4:04d}")[s]
            if i not in self._used:
                self._used.add(i)
                return i

    # ---------- fx / time ----------
    def _build_fx(self):
        self.fx: dict[tuple[date, str], Decimal] = {}
        self.fx_rows: list[dict] = []
        start, end = self.ps - timedelta(days=60), self.pe + timedelta(days=15)
        for cur in self.foreign:
            level = USD_VALUE[cur] / USD_VALUE[self.base] * self.rng.uniform(0.9, 1.1)
            d = start
            while d <= end:
                level *= 1 + self.rng.uniform(-0.006, 0.006)
                r = rate_str(level)
                self.fx[(d, cur)] = Decimal(r)
                self.fx_rows.append({"fx_id": f"{d.isoformat()}:{cur}:{self.base}", "date": d.isoformat(),
                                     "source_currency": cur, "target_currency": self.base, "rate": r})
                d += timedelta(days=1)

    def rate(self, d: date, cur: str) -> Decimal:
        return Decimal(1) if cur == self.base else self.fx[(d, cur)]

    def conv(self, amount: int, cur: str, d: date) -> int:
        return convert(amount, cur, self.base, self.rate(d, cur))

    def in_period(self, d: date) -> bool:
        return self.ps <= d <= self.pe

    def at(self, d: date, hour: int, minute: int) -> datetime:
        return datetime.combine(d, time(hour, minute), self.tz)

    def cdate(self, dt: datetime) -> date:
        return dt.astimezone(self.tz).date()

    # ---------- documents ----------
    def line_items(self, cur: str, n: int | None = None) -> list[dict]:
        rng = self.rng
        items = []
        for prod in rng.sample(PRODUCTS, n or rng.choice((1, 1, 2, 2, 3, 4))):
            name, lo, hi, qlo, qhi = prod
            unit = max(1, round(rng.uniform(lo, hi) / USD_VALUE[cur])) * 10 ** EXPONENT[cur]
            qty = rng.randint(qlo, qhi)
            ref = f"{rng.choice(('PO', 'PRJ', 'SOW', 'REF'))}-{rng.randrange(1000, 9999)}"
            items.append({"description": f"{name} ({ref})", "quantity": qty,
                          "unit_price_minor": unit, "amount_minor": unit * qty})
        return items

    def new_entity(self) -> dict:
        cur = self.base if self.rng.random() < 0.6 else self.rng.choice(self.foreign)
        return {"id": self.new_id("entity"), "currency": cur, "offset": self.rng.choice(OFFSETS_MIN)}

    def retype(self, items: list[dict]) -> list[dict]:
        """Hard mode: the same lines keyed in again by hand: other order, case and ref punctuation."""
        items = [dict(i) for i in items]
        self.rng.shuffle(items)
        for i in items:
            name, sep, ref = i["description"].rpartition(" (")
            upper = self.rng.random() < 0.5
            if not sep:  # no reference to re-type (e.g. retainer text): change the case only
                i["description"] = i["description"].upper() if upper else i["description"].lower()
                continue
            ref = ref.rstrip(")").replace("-", self.rng.choice((" ", "", "/")))
            i["description"] = f"{name.upper() if upper else name.lower()} - {ref}"
        return items

    def new_invoice(self, ent: dict, d: date, hour: int | None = None, items=None,
                    offset_min: int | None = None, currency: str | None = None) -> dict:
        rng = self.rng
        if hour is None:
            hour = rng.choice((0, 23)) if rng.random() < 0.08 else rng.randint(8, 22)
        instant = self.at(d, hour, rng.randrange(60))
        off = ent["offset"] if offset_min is None else offset_min
        local = instant.astimezone(parse_offset(offset_str(off)))
        cur = currency or ent["currency"]
        items = items if items is not None else self.line_items(cur)
        inv = {
            "doc_id": self.new_id("doc"), "invoice_id": self.new_id("invoice"), "entity_id": ent["id"],
            "issued_at": iso(local), "due_at": iso(local + timedelta(days=rng.choice((14, 30, 45)))),
            "currency": cur, "total_minor": sum(i["amount_minor"] for i in items), "line_items": items,
            "_dt": instant, "_cdate": d, "_tie": rng.random(),
        }
        self.invoices.append(inv)
        return inv

    def new_payment(self, d: date, cur: str, amount: int, refs: list | None, entity_id: str | None,
                    hour: int | None = None, offset_min: int | None = None) -> dict:
        rng = self.rng
        if hour is None:
            hour = rng.choice((0, 23)) if rng.random() < 0.08 else rng.randint(8, 22)
        instant = self.at(d, hour, rng.randrange(60))
        off = self.bank_offset if offset_min is None else offset_min
        pay = {
            "doc_id": self.new_id("doc"), "payment_id": self.new_id("payment"),
            "timestamp": iso(instant.astimezone(parse_offset(offset_str(off)))), "currency": cur,
            "amount_minor": amount,
            "invoice_refs": None if refs is None else [{"invoice_id": i["invoice_id"], "amount_minor": a}
                                                       for i, a in refs],
            "_dt": instant, "_cdate": d, "_tie": rng.random(),
        }
        self.payments.append(pay)
        self.entity_of_payment[pay["payment_id"]] = entity_id
        return pay

    # ---------- ledger ----------
    def row(self, dt: datetime, account: str, signed: int, entity=None, invoice=None, payment=None) -> dict:
        """signed > 0 -> debit, < 0 -> credit."""
        self._k += 1
        return {"_k": self._k, "_dt": dt, "_tie": self.rng.random(), "timestamp": iso(dt.astimezone(self.tz)),
                "account": account, "debit_minor": max(signed, 0), "credit_minor": max(-signed, 0),
                "currency": self.base, "entity_id": entity, "invoice_id": invoice, "payment_id": payment}

    def book_invoice(self, inv: dict, rate_date: date | None = None, dt: datetime | None = None) -> str:
        amt = self.conv(inv["total_minor"], inv["currency"], rate_date or inv["_cdate"])
        dt = dt or inv["_dt"]
        jid = "inv:" + inv["invoice_id"]
        e, i = inv["entity_id"], inv["invoice_id"]
        self.journals[jid] = [self.row(dt, "1200", amt, e, i), self.row(dt, "4000", -amt, e, i)]
        return jid

    def invoice(self, invoice_id: str) -> dict:
        return next(i for i in self.invoices if i["invoice_id"] == invoice_id)

    def book_payment(self, pay: dict, cash_rate_date: date | None = None) -> str:
        pid, dt, cur = pay["payment_id"], pay["_dt"], pay["currency"]
        ent = self.entity_of_payment[pid]
        rows = [self.row(dt, "1000", self.conv(pay["amount_minor"], cur, cash_rate_date or pay["_cdate"]),
                         ent, None, pid)]
        allocated = 0
        for ref in pay["invoice_refs"] or []:
            inv = self.invoice(ref["invoice_id"])
            rows.append(self.row(dt, "1200", -self.conv(ref["amount_minor"], cur, inv["_cdate"]),
                                 inv["entity_id"], inv["invoice_id"], pid))
            allocated += ref["amount_minor"]
        rest = pay["amount_minor"] - allocated
        if rest:
            rows.append(self.row(dt, "2900", -self.conv(rest, cur, pay["_cdate"]), ent, None, pid))
        jid = "pay:" + pid
        self.journals[jid] = rows
        self.rebalance(jid)
        return jid

    def rebalance(self, jid: str) -> None:
        """Set the 7900 FX gain/loss row so the journal balances (removed if zero)."""
        rows = [r for r in self.journals[jid] if r["account"] != "7900"]
        old = next((r for r in self.journals[jid] if r["account"] == "7900"), None)
        diff = sum(r["debit_minor"] - r["credit_minor"] for r in rows)
        if diff:
            r0 = rows[0]
            fx = self.row(r0["_dt"], "7900", -diff, r0["entity_id"], None, r0["payment_id"])
            if old is not None:
                fx["_k"], fx["_tie"] = old["_k"], old["_tie"]
            rows.append(fx)
        self.journals[jid] = rows

    def book_expense(self, n: int, d: date, account: str, amount: int) -> None:
        dt = self.at(d, self.rng.randint(8, 18), self.rng.randrange(60))
        self.journals[f"exp:{n}"] = [self.row(dt, account, amount), self.row(dt, "1000", -amount)]

    def ledger_rows(self) -> list[dict]:
        return [r for rows in self.journals.values() for r in rows]

    # ---------- injection bookkeeping ----------
    def snapshot(self, jid: str):
        return copy.deepcopy(self.journals.get(jid))

    def record(self, issue: dict, changes: list[dict], docs_added=(), description: str = "") -> None:
        issue["issue_id"] = f"ISS-{len(self.issues) + 1}"
        self.issues.append(issue)
        self.injections.append({"issue_id": issue["issue_id"], "type": issue["type"],
                                "scenario": issue.get("scenario", "single"), "description": description,
                                "changes": changes, "documents_added": list(docs_added)})


# ---------------------------------------------------------------- history
def build_history(st: State) -> None:
    rng = st.rng
    distractors = st.gen["distractors"]
    st.entities = [st.new_entity() for _ in range(rng.randint(8, 18))]
    n_inv = st.gen["n_invoices"] or rng.randint(30, 60)
    for _ in range(n_inv):
        u = rng.random()
        if u < 0.2:
            d = st.ps - timedelta(days=rng.randint(1, 35))
        elif u < 0.92:
            d = st.ps + timedelta(days=rng.randrange(st.ndays))
        else:
            d = st.pe + timedelta(days=rng.randint(1, 7))
        st.new_invoice(rng.choice(st.entities), d)

    if distractors:
        # legitimate recurring amounts: weekly retainer, same price, different week in the text
        ent = rng.choice(st.entities)
        unit = max(1, round(rng.uniform(400, 1500) / USD_VALUE[ent["currency"]])) * 10 ** EXPONENT[ent["currency"]]
        for week in range(4):
            start = st.ps + timedelta(days=week * 7)
            d = start + timedelta(days=rng.randint(0, 2))
            label = f"Support retainer, service week {start.isoformat()} to {(start + timedelta(days=6)).isoformat()}"
            st.new_invoice(ent, d, items=[{"description": label, "quantity": 1,
                                           "unit_price_minor": unit, "amount_minor": unit}])
        # timezone boundary: in-period in company tz although the local date says next period
        east = [e for e in st.entities if e["offset"] > st.tz_min]
        if east:
            st.new_invoice(rng.choice(east), st.pe, hour=23)
        west = [e for e in st.entities if e["offset"] < st.tz_min]
        if west:
            st.new_invoice(rng.choice(west), st.pe + timedelta(days=1), hour=0)
            st.new_invoice(rng.choice(west), st.ps, hour=0)

    if st.hard:  # some invoices are keyed in by hand, so a re-typed description is no sign of a duplicate
        for inv in st.invoices:
            if rng.random() < 0.12:
                inv["line_items"] = st.retype(inv["line_items"])
    for inv in list(st.invoices):
        if st.in_period(inv["_cdate"]):
            lag = rng.randint(1, 3) if rng.random() < 0.3 else 0  # legitimate posting lag inside the period
            if lag and inv["_cdate"] + timedelta(days=lag) <= st.pe:
                st.book_invoice(inv, dt=st.at(inv["_cdate"] + timedelta(days=lag), rng.randint(8, 22),
                                              rng.randrange(60)))
            else:
                st.book_invoice(inv)

    _build_payments(st, distractors)
    if st.hard:
        _build_reissues(st)
    while len(st.invoices) + len(st.payments) < 22:  # keep >= 20 documents after any injection
        st.book_invoice(st.new_invoice(rng.choice(st.entities), st.ps + timedelta(days=rng.randrange(st.ndays))))
    _build_expenses(st)


def _pay_date(st: State, inv: dict, lo: int = 2, hi: int = 30) -> date:
    if inv["_cdate"] < st.ps:
        return st.ps + timedelta(days=st.rng.randrange(st.ndays))
    return inv["_cdate"] + timedelta(days=st.rng.randint(lo, hi))


def _build_payments(st: State, distractors: bool) -> None:
    rng = st.rng
    plans = []  # (date, currency, amount, [(inv, amt)], entity_id)
    for inv in list(st.invoices):
        if inv["_cdate"] > st.pe:
            continue
        total, cur, ent = inv["total_minor"], inv["currency"], inv["entity_id"]
        u = rng.random()
        if u < 0.5:
            plans.append((_pay_date(st, inv), cur, total, [(inv, total)], ent))
        elif u < 0.62:  # split payment (legitimate)
            a = max(1, round(total * rng.uniform(0.3, 0.7)))
            d1 = _pay_date(st, inv, 2, 15)
            plans.append((d1, cur, a, [(inv, a)], ent))
            plans.append((d1 + timedelta(days=rng.randint(1, 15)), cur, total - a, [(inv, total - a)], ent))
        elif u < 0.72:  # partial payment, correctly allocated, invoice stays open
            a = max(1, round(total * rng.uniform(0.4, 0.9)))
            plans.append((_pay_date(st, inv), cur, a, [(inv, a)], ent))
        elif u < 0.77 and distractors:  # overpayment -> unapplied cash, later refunded
            extra = max(1, round(total * rng.uniform(0.01, 0.05)))
            d = _pay_date(st, inv, 2, 12)
            plans.append((d, cur, total + extra, [(inv, total)], ent))
            plans.append((d + timedelta(days=rng.randint(2, 10)), cur, -extra, None, ent))
    plans = [p for p in plans if st.in_period(p[0])]
    if st.gen.get("ensure_distractors"):
        _ensure_split_and_refund(st, plans)
    # multi-invoice payments: merge some full payments of the same entity+currency
    merged, used = [], set()
    plans.sort(key=lambda p: (p[0], p[1], p[2]))
    for i, p in enumerate(plans):
        if i in used:
            continue
        if p[3] and len(p[3]) == 1 and rng.random() < 0.25:
            for j in range(i + 1, len(plans)):
                q = plans[j]
                if (j not in used and q[3] and len(q[3]) == 1 and q[4] == p[4] and q[1] == p[1]
                        and q[3][0][0] is not p[3][0][0] and (q[0] - p[0]).days <= 10):
                    used.add(j)
                    p = (q[0], p[1], p[2] + q[2], p[3] + q[3], p[4])
                    break
        merged.append(p)
    if distractors:  # unidentified receipts: no remittance info -> unapplied cash
        for _ in range(rng.randint(1, 2)):
            ent = rng.choice(st.entities)
            amt = max(1, round(rng.uniform(100, 3000) / USD_VALUE[ent["currency"]])) * 10 ** EXPONENT[ent["currency"]]
            merged.append((st.ps + timedelta(days=rng.randrange(st.ndays)), ent["currency"], amt, None, None))
    for d, cur, amt, refs, ent in merged:
        st.book_payment(st.new_payment(d, cur, amt, refs, ent))


def _ensure_split_and_refund(st: State, plans: list) -> None:
    """Config "ensure_distractors": at least one invoice paid in two legitimate parts and one overpayment that is
    refunded later in the period (the jury's clean scenarios D02, D03). Turns full single payments into them."""
    rng = st.rng
    paid = {}
    for p in plans:
        for inv, _ in p[3] or ():
            paid[inv["invoice_id"]] = paid.get(inv["invoice_id"], 0) + 1
    full = [i for i, p in enumerate(plans) if p[3] and len(p[3]) == 1 and p[2] == p[3][0][0]["total_minor"] >= 2
            and st.in_period(p[0] + timedelta(days=2))]
    if not any(n >= 2 for n in paid.values()) and full:
        d, cur, total, refs, ent = plans[i := full.pop(rng.randrange(len(full)))]
        a = max(1, round(total * rng.uniform(0.3, 0.7)))
        plans[i] = (d, cur, a, [(refs[0][0], a)], ent)
        plans.append((d + timedelta(days=1), cur, total - a, [(refs[0][0], total - a)], ent))
    if not any(p[2] < 0 for p in plans) and full:
        d, cur, total, refs, ent = plans[i := full.pop(rng.randrange(len(full)))]
        extra = max(1, round(total * rng.uniform(0.01, 0.05)))
        plans[i] = (d, cur, total + extra, refs, ent)
        plans.append((d + timedelta(days=1), cur, -extra, None, ent))


def _build_reissues(st: State) -> None:
    """Hard mode: legitimate cancel-and-reissue. An unpaid invoice is reversed by a credit note
    (Dr 4000 / Cr 1200, same invoice_id) and re-issued with identical line items under a new
    number. It looks exactly like a duplicate unless the reversal in the ledger is checked."""
    rng = st.rng
    paid = {ref["invoice_id"] for p in st.payments for ref in p["invoice_refs"] or []}
    def booked_at(inv):  # the AR row can lag the issue date (posting lag)
        return next(r["_dt"] for r in st.journals["inv:" + inv["invoice_id"]] if r["account"] == "1200")

    cands = [i for i in st.invoices if st.in_period(i["_cdate"]) and ("inv:" + i["invoice_id"]) in st.journals
             and i["invoice_id"] not in paid and st.cdate(booked_at(i)) + timedelta(days=4) <= st.pe]
    rng.shuffle(cands)
    for orig in cands[: rng.randint(2, 3)]:
        at = booked_at(orig).astimezone(st.tz)
        d = at.date() + timedelta(days=rng.randint(0, 3))
        if d == at.date() and at.hour >= 21:
            d += timedelta(days=1)
        hour = rng.randint(max(at.hour + 2, 9), 22) if d == at.date() else rng.randint(9, 22)
        items = copy.deepcopy(orig["line_items"])
        if rng.random() < 0.5:  # the replacement is keyed in by hand as often as a duplicate copy
            items = st.retype(items)
        new = st.new_invoice(next(e for e in st.entities if e["id"] == orig["entity_id"]), d, hour=hour,
                             items=items, currency=orig["currency"])
        jid = "inv:" + orig["invoice_id"]
        amt = next(r["debit_minor"] for r in st.journals[jid] if r["account"] == "1200")
        dt = new["_dt"] - timedelta(minutes=rng.randint(1, 50))
        e, i = orig["entity_id"], orig["invoice_id"]
        st.journals[jid] += [st.row(dt, "4000", amt, e, i), st.row(dt, "1200", -amt, e, i)]
        st.book_invoice(new)
        st.touched.update({orig["invoice_id"], new["invoice_id"]})


def _build_expenses(st: State) -> None:
    rng = st.rng
    scale = 10 ** EXPONENT[st.base] / USD_VALUE[st.base]
    n = 0

    def add(d, account, usd):
        nonlocal n
        n += 1
        st.book_expense(n, d, account, max(1, round(usd * scale)))

    add(st.ps, "6100", rng.uniform(3000, 12000))
    add(st.ps + timedelta(days=14), "6200", rng.uniform(20000, 80000))
    add(st.pe, "6200", rng.uniform(20000, 80000))
    target = rng.randint(900, 1400) if st.hard else rng.randint(230, 420)
    while len(st.ledger_rows()) < target:
        account = rng.choice(("6300", "6300", "6400", "6400", "6400"))
        usd = rng.uniform(20, 900) if account == "6300" else rng.uniform(1, 60)
        add(st.ps + timedelta(days=rng.randrange(st.ndays)), account, usd)


# ---------------------------------------------------------------- render
def _plan(st: State) -> tuple[dict, dict]:
    rng = st.rng
    if st.gen["errors"] is not None:
        errors, inter = dict(st.gen["errors"]), dict(st.gen["interacting"])
    else:
        errors = {t: rng.choice((0, 0, 1, 1, 2)) for t in ISSUE_TYPES}
        inter = {s: int(rng.random() < 0.3) for s in SCENARIOS}
    if sum(errors.values()) + 2 * sum(inter.values()) > MAX_ISSUES:
        raise ValueError(f"at most {MAX_ISSUES} issues per episode")
    return errors, inter


def _public(rec: dict, fields) -> dict:
    return {f: copy.deepcopy(rec[f]) for f in fields}


def render(st: State, episode_id: str) -> dict:
    rows = sorted(st.ledger_rows(), key=lambda r: (r["_dt"], r["_tie"]))
    start = st.rng.randrange(1, 5000)
    style = st._styles["row"]
    key_to_id = {}
    for n, r in enumerate(rows):
        num = start + n
        key_to_id[r["_k"]] = (f"L{num:05d}", f"GL-{num:06d}", f"R{num}")[style]
    ledger = []
    for r in rows:
        pub = _public(r, LEDGER_FIELDS[1:])
        ledger.append({"row_id": key_to_id[r["_k"]], **pub})
    invoices = [_public(i, INVOICE_FIELDS) for i in sorted(st.invoices, key=lambda i: (i["_dt"], i["_tie"]))]
    payments = [_public(p, PAYMENT_FIELDS) for p in sorted(st.payments, key=lambda p: (p["_dt"], p["_tie"]))]
    fx = [dict(r) for r in st.fx_rows]

    def ev_id(e):
        kind, val = e
        return key_to_id[val] if kind == "row" else val  # "doc" -> doc_id, "fx" -> fx_id

    issues = []
    for iss in st.issues:
        issues.append({
            "issue_id": iss["issue_id"], "type": iss["type"], "scenario": iss.get("scenario", "single"),
            "affected_ids": sorted(iss["affected_ids"]), "expected_amount_minor": iss["amount"],
            "currency": st.base, "evidence_sets": [sorted(ev_id(e) for e in s) for s in iss["evidence"]],
        })

    def snap(rows_):
        if rows_ is None:
            return None
        return [{"row_id": key_to_id.get(r["_k"], f"pre-{r['_k']}"), **_public(r, LEDGER_FIELDS[1:])}
                for r in rows_]

    injections = []
    for inj in st.injections:
        injections.append({**{k: inj[k] for k in ("issue_id", "type", "scenario", "description",
                                                    "documents_added")},
                           "changes": [{"journal": c["journal"], "before": snap(c["before"]),
                                        "after": snap(c["after"])} for c in inj["changes"]]})
    manifest = {
        "schema_version": SCHEMA_VERSION, "generator_version": GENERATOR_VERSION, "episode_id": episode_id,
        "base_currency": st.base, "period_start": st.ps.isoformat(), "period_end": st.pe.isoformat(),
        "timezone": st.tz_str,
        "counts": {"ledger": len(ledger), "invoices": len(invoices), "payments": len(payments),
                   "fx": len(fx), "documents": len(invoices) + len(payments)},
        "rounding": "ROUND_HALF_UP",
        "amount_exponents": {c: EXPONENT[c] for c in sorted({st.base, *st.foreign})},
    }
    return {
        "episode_id": episode_id,
        "manifest": manifest,
        "policy": policy_for(st),
        "tables": {"ledger": ledger, "invoices": invoices, "payments": payments, "fx": fx},
        "truth": {"episode_id": episode_id, "issues": issues},
        "provenance": {
            "generator_version": GENERATOR_VERSION, "seed": st.seed,
            "config": st.gen,
            "company": {"base_currency": st.base, "foreign_currencies": st.foreign, "timezone": st.tz_str,
                        "bank_offset": offset_str(st.bank_offset), "entities": len(st.entities)},
            "injections": injections,
        },
    }


def policy_for(st: State) -> dict:
    return {
        "base_currency": st.base,
        "timezone": st.tz_str,
        "period": {"start": st.ps.isoformat(), "end": st.pe.isoformat(),
                   "rule": "a record belongs to the period iff its timestamp converted to the company "
                           "timezone has a date in [start, end] (inclusive)"},
        "fx": {"rate_date": "transaction date in the company timezone (invoice: issued_at; payment: timestamp)",
               "direction": "rate = units of target_currency per 1 unit of source_currency (major units)",
               "conversion": "base_minor = round_half_up(amount_minor / 10^exp_src * rate * 10^exp_base)"},
        "rounding": "ROUND_HALF_UP to integer minor units",
        "ledger": {
            "currency": "every ledger row is in base_currency",
            "accounts": ACCOUNTS,
            "invoice": "Dr 1200 / Cr 4000 at the invoice issue-date rate, only for invoices issued in the period",
            "payment": "Dr 1000 at the payment-date rate; Cr 1200 per invoice_ref at that invoice's issue-date "
                       "rate; remainder (or all, if invoice_refs is null) Cr 2900 at the payment-date rate; "
                       "difference to 7900; negative amount = refund (Dr 2900 / Cr 1000)",
            "expense": "Dr 6xxx / Cr 1000",
            **({"credit_note": "a cancelled invoice is reversed in full: Dr 4000 / Cr 1200 with the same "
                               "invoice_id and no payment_id; a re-issued replacement is booked as a new invoice"}
               if st.hard else {}),
        },
        "findings": {
            "amount": "misstatement in the ledger, base currency minor units, positive; duplicate_invoice: the "
                      "AR debit of the later-issued copy; fx_error: abs(posted - correct); period_cutoff: the AR "
                      "debit posted; payment_allocation: expected AR credit for the ref - AR credit posted",
            "tolerance": "abs(claimed - expected) <= tolerance_minor; tolerance_minor is 0, so the amount must be exact",
            "tolerance_minor": 0,
            "affected_ids": {"duplicate_invoice": "[original_invoice_id, duplicate_invoice_id]",
                             "payment_allocation": "[invoice_id, payment_id]",
                             "fx_error": "[invoice_id] or [payment_id]",
                             "period_cutoff": "[invoice_id]"},
            "evidence": "doc_id / row_id / fx_id values; must include at least one full acceptable evidence set: "
                        "duplicate_invoice: both invoice docs + one AR (or revenue) row of each invoice, the original and the "
                        "later copy; "
                        "payment_allocation: payment doc + invoice doc + the AR credit row of that invoice in the "
                        "payment (or, if nothing was allocated to it, the 2900 row) + the invoice-date fx_id if foreign; fx_error: doc + AR/revenue (invoice) or cash (payment) row "
                        "+ the fx_id of the correct date; period_cutoff: invoice doc + AR (or revenue) row",
        },
    }


TASK_TEXT = (
    "You are auditing one company for one reporting period. Find misstatements in the ledger caused by: "
    "duplicate_invoice (the same invoice entered twice: same entity, currency and identical line items), "
    "payment_allocation (a payment's remittance says it pays an invoice but the ledger credits less to that "
    "invoice's receivable), fx_error (a foreign-currency amount converted with a rate of the wrong date), "
    "period_cutoff (an invoice issued outside the period booked in this period). The books may be clean. "
    "Split payments, partial payments, refunds, unidentified receipts and recurring equal amounts can be "
    "legitimate. Use the tools to read records (max 50 rows per page) and submit findings once; every "
    "action costs a step (max 100 including submit)."
)


TASK_HARD = (
    " Hard mode: the ledger is larger; line items keyed in by hand (some invoices, re-issues and duplicate "
    "copies) may be re-typed (other order, case and punctuation of the descriptions) with the same products, "
    "quantities and prices; an invoice cancelled by a full credit note and re-issued with the same line items "
    "is legitimate."
)


def generate(seed: int, config: dict | None = None, key: str | None = None) -> dict:
    """Generate one episode: public tables + grader-only truth and provenance. `key` overrides AUDITENV_SECRET."""
    from . import inject  # local import: inject uses State

    config = dict(config or {})
    st = State(int(seed), config, key)
    build_history(st)
    errors, inter = _plan(st)
    inject.apply(st, errors, inter)
    episode = render(st, episode_id_for(int(seed), config, key))
    episode["task"] = TASK_TEXT + (TASK_HARD if st.hard else "")
    if config.get("transform_seed") is not None:
        from .transform import transform
        episode = transform(episode, int(config["transform_seed"]))
    return episode
