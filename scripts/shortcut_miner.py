#!/usr/bin/env python3
"""Shortcut miner: does one observable surface feature of a record predict that it is part of a truth issue?

    uv run python scripts/shortcut_miner.py                       # seeds 0-999, configs {} + HEAVY
    uv run python scripts/shortcut_miner.py --hard --seeds 0-499  # same configs with difficulty: hard
    uv run python scripts/shortcut_miner.py --json /tmp/miner.json --report-only

Records: ledger rows, invoices, payments. Features use only what list_records / get_record /
get_document return (plus the manifest/policy period and timezone) -- never truth or provenance.
Labels per issue type T:
  affected (primary) -- invoice/payment: its id is in a T issue's affected_ids;
                        ledger row: its invoice_id or payment_id is in a T issue's affected_ids
  evidence           -- invoice/payment: its doc_id, ledger row: its row_id, is in a T evidence set
For each (table, feature, value) with support >= --min-support records: precision = P(label | value),
lift = precision / base rate of that table. Values with precision > 0.5 are flagged; exit 1 if any
(unless --report-only).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auditenv.generator import ISSUE_TYPES, generate  # noqa: E402
from auditenv.money import parse_offset  # noqa: E402
from auditenv.run import parse_seeds  # noqa: E402

HEAVY = {"errors": {t: 2 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}  # as auditenv.check
CONFIGS = {"random_mix": {}, "heavy": HEAVY}
LABELINGS = ("affected", "evidence")
TABLES = ("ledger", "invoices", "payments")
FLAG = 0.5


def shape(s) -> str:
    """Id format: digits -> 9, letters -> A (e.g. 'INV-000123' -> 'AAA-999999')."""
    return "null" if s is None else re.sub(r"[A-Za-z]", "A", re.sub(r"\d", "9", s))


def amount_feats(prefix: str, a: int) -> list:
    a = abs(a)
    return [(prefix + "round100", a % 100 == 0), (prefix + "round1000", a % 1000 == 0),
            (prefix + "last2", a % 100), (prefix + "parity", a % 2), (prefix + "digits", len(str(a)))]


def time_feats(ts: str, tz, ps: date, pe: date) -> list:
    dt = datetime.fromisoformat(ts)
    cd = dt.astimezone(tz).date()
    if cd < ps or cd > pe:
        rel = f"out{(cd - ps).days if cd < ps else (cd - pe).days:+d}"
    elif (cd - ps).days < 3:
        rel = f"start+{(cd - ps).days}"
    elif (pe - cd).days < 3:
        rel = f"end-{(pe - cd).days}"
    else:
        rel = "mid"
    return [("hour", dt.hour), ("minute", dt.minute), ("minute0", dt.minute == 0), ("weekday", dt.weekday()),
            ("offset", ts[-6:]), ("day_rel_period", rel), ("local_date_ne_company_date", dt.date() != cd)]


def bucket(n: int) -> str:
    return str(n) if n < 4 else "4+"


def case_pattern(s: str) -> str:
    letters = [c for c in s if c.isalpha()]
    if all(c.isupper() for c in letters):
        return "upper"
    if all(c.islower() for c in letters):
        return "lower"
    return "mixed"


def ledger_features(rows: list, tz, ps, pe) -> list:
    amt_count = Counter(r["debit_minor"] or r["credit_minor"] for r in rows)
    inv_size = Counter(r["invoice_id"] for r in rows if r["invoice_id"])
    pay_size = Counter(r["payment_id"] for r in rows if r["payment_id"])
    out = []
    for n, r in enumerate(rows):
        side = "D" if r["debit_minor"] else "C"
        amt = r["debit_minor"] or r["credit_minor"]
        base = time_feats(r["timestamp"], tz, ps, pe) + amount_feats("amount_", amt) + [
            ("side", side), ("currency", r["currency"]),
            ("row_id_shape", shape(r["row_id"])), ("row_id_last_digit", r["row_id"][-1]),
            ("position_decile", n * 10 // len(rows)),
            ("has_entity", r["entity_id"] is not None), ("has_invoice", r["invoice_id"] is not None),
            ("has_payment", r["payment_id"] is not None), ("entity_shape", shape(r["entity_id"])),
            ("amount_count_in_table", bucket(amt_count[amt])),
            ("invoice_journal_size", bucket(inv_size[r["invoice_id"]]) if r["invoice_id"] else "-"),
            ("payment_journal_size", bucket(pay_size[r["payment_id"]]) if r["payment_id"] else "-"),
        ]
        feats = [("account", r["account"]), ("account_side", r["account"] + side),
                 ("entity_id", r["entity_id"])] + base
        feats += [(f"{k}@acct{r['account']}", v) for k, v in base]  # same feature within one account
        out.append(feats)
    return out


def invoice_features(invs: list, tz, tzs: str, ps, pe, base_cur: str) -> list:
    tot_count = Counter(i["total_minor"] for i in invs)
    ent_tot = Counter((i["entity_id"], i["currency"], i["total_minor"]) for i in invs)
    ent_count = Counter(i["entity_id"] for i in invs)
    out = []
    for n, i in enumerate(invs):
        due = (datetime.fromisoformat(i["due_at"]) - datetime.fromisoformat(i["issued_at"])).days
        items = i["line_items"]
        feats = time_feats(i["issued_at"], tz, ps, pe) + amount_feats("total_", i["total_minor"]) + [
            ("offset_eq_company", i["issued_at"][-6:] == tzs),
            ("invoice_id_shape", shape(i["invoice_id"])), ("doc_id_shape", shape(i["doc_id"])),
            ("entity_shape", shape(i["entity_id"])), ("entity_id", i["entity_id"]),
            ("invoice_id_last_digit", i["invoice_id"][-1]), ("due_days", due),
            ("currency", i["currency"]), ("is_base_currency", i["currency"] == base_cur),
            ("n_line_items", len(items)), ("position_decile", n * 10 // len(invs)),
            ("total_count_in_table", bucket(tot_count[i["total_minor"]])),
            ("same_entity_currency_total_count", bucket(ent_tot[(i["entity_id"], i["currency"], i["total_minor"])])),
            ("entity_invoice_count", bucket(ent_count[i["entity_id"]])),
            ("desc_case_patterns", "/".join(sorted({case_pattern(li["description"]) for li in items}))),
            ("desc_ref_style", "/".join(sorted({"paren" if "(" in li["description"] else
                                                 ("dash" if " - " in li["description"] else "none")
                                                 for li in items}))),
        ]
        for li in items:
            feats += [("item_quantity", li["quantity"])] + amount_feats("item_unit_", li["unit_price_minor"])
            feats += [("desc_token", t) for t in re.findall(r"[a-z]+|\d+", li["description"].lower())]
            feats += [("desc_raw_word", w) for w in re.findall(r"[A-Za-z]+", li["description"])]
        out.append(sorted(set(feats), key=repr))  # an invoice counts once per value
    return out


def payment_features(pays: list, invs: list, tz, tzs: str, ps, pe, base_cur: str) -> list:
    totals = {i["invoice_id"]: i["total_minor"] for i in invs}
    amt_count = Counter(p["amount_minor"] for p in pays)
    off_mode = Counter(p["timestamp"][-6:] for p in pays).most_common(1)[0][0]
    out = []
    for n, p in enumerate(pays):
        refs = p["invoice_refs"]
        rsum = sum(r["amount_minor"] for r in refs or [])
        feats = time_feats(p["timestamp"], tz, ps, pe) + amount_feats("amount_", p["amount_minor"]) + [
            ("offset_eq_company", p["timestamp"][-6:] == tzs),
            ("offset_eq_most_common_payment_offset", p["timestamp"][-6:] == off_mode),
            ("payment_id_shape", shape(p["payment_id"])), ("doc_id_shape", shape(p["doc_id"])),
            ("payment_id_last_digit", p["payment_id"][-1]),
            ("currency", p["currency"]), ("is_base_currency", p["currency"] == base_cur),
            ("amount_sign", "neg" if p["amount_minor"] < 0 else "pos"),
            ("n_refs", "null" if refs is None else len(refs)),
            ("refs_vs_amount", "-" if refs is None else ("eq" if rsum == p["amount_minor"] else
                                                         ("lt" if rsum < p["amount_minor"] else "gt"))),
            ("refs_full_invoice_total", "-" if not refs else
             all(totals.get(r["invoice_id"]) == r["amount_minor"] for r in refs)),
            ("amount_count_in_table", bucket(amt_count[p["amount_minor"]])),
            ("position_decile", n * 10 // len(pays)),
        ]
        out.append(feats)
    return out


def labels(ep: dict) -> dict:
    aff = {t: set() for t in ISSUE_TYPES}
    ev = {t: set() for t in ISSUE_TYPES}
    for iss in ep["truth"]["issues"]:
        aff[iss["type"]].update(iss["affected_ids"])
        for s in iss["evidence_sets"]:
            ev[iss["type"]].update(s)
    return {"affected": aff, "evidence": ev}


def mine(seeds: list[int], hard: bool = False, configs: dict | None = None, min_support: int = 30,
         top: int = 10) -> dict:
    total: Counter = Counter()  # (table, feature, value) -> records
    pos: Counter = Counter()    # (labeling, type, table, feature, value) -> positive records
    base_n: Counter = Counter()  # table -> records
    base_pos: Counter = Counter()  # (labeling, type, table) -> positive records
    episodes = 0
    for seed in seeds:
        for base_cfg in (configs or CONFIGS).values():
            cfg = {**base_cfg, "difficulty": "hard"} if hard else dict(base_cfg)
            ep = generate(seed, cfg)
            episodes += 1
            m, tb, lab = ep["manifest"], ep["tables"], labels(ep)
            tz, ps, pe = parse_offset(m["timezone"]), date.fromisoformat(m["period_start"]), \
                date.fromisoformat(m["period_end"])
            per_table = {
                "ledger": (tb["ledger"], ledger_features(tb["ledger"], tz, ps, pe),
                           lambda r, ids: r["invoice_id"] in ids or r["payment_id"] in ids, lambda r: r["row_id"]),
                "invoices": (tb["invoices"],
                             invoice_features(tb["invoices"], tz, m["timezone"], ps, pe, m["base_currency"]),
                             lambda r, ids: r["invoice_id"] in ids, lambda r: r["doc_id"]),
                "payments": (tb["payments"], payment_features(tb["payments"], tb["invoices"], tz, m["timezone"], ps, pe,
                                                              m["base_currency"]),
                             lambda r, ids: r["payment_id"] in ids, lambda r: r["doc_id"]),
            }
            for table, (recs, feats, is_aff, ev_id) in per_table.items():
                base_n[table] += len(recs)
                for rec, fs in zip(recs, feats):
                    keys = [(table, k, v) for k, v in fs]
                    total.update(keys)
                    for t in ISSUE_TYPES:
                        for labeling, hit in (("affected", is_aff(rec, lab["affected"][t])),
                                              ("evidence", ev_id(rec) in lab["evidence"][t])):
                            if hit:
                                base_pos[(labeling, t, table)] += 1
                                pos.update((labeling, t) + k for k in keys)

    result = {"episodes": episodes, "seeds": len(seeds), "hard": hard, "configs": list((configs or CONFIGS)),
              "min_support": min_support, "records": dict(base_n), "labelings": {}, "flagged": []}
    for labeling in LABELINGS:
        per_type = {}
        for t in ISSUE_TYPES:
            base = {tb_: base_pos[(labeling, t, tb_)] / base_n[tb_] if base_n[tb_] else 0.0 for tb_ in TABLES}
            cands = []
            for (table, feat, val), n in total.items():
                if n < min_support:
                    continue
                p = pos[(labeling, t, table, feat, val)] / n
                if p == 0:
                    continue
                cands.append({"table": table, "feature": feat, "value": repr(val) if not isinstance(val, str) else val,
                              "support": n, "positives": pos[(labeling, t, table, feat, val)], "precision": p,
                              "lift": p / base[table] if base[table] else 0.0})
            cands.sort(key=lambda c: (-c["precision"], -c["support"], c["table"], c["feature"], c["value"]))
            flagged = [c for c in cands if c["precision"] > FLAG]
            per_type[t] = {"base_rate": base, "top": cands[:top], "flagged_count": len(flagged),
                           "max_precision": cands[0]["precision"] if cands else 0.0}
            result["flagged"] += [{"labeling": labeling, "type": t, **c} for c in flagged]
        result["labelings"][labeling] = per_type
    return result


def markdown(r: dict, seconds: float) -> str:
    out = [f"# Shortcut miner: {'hard' if r['hard'] else 'default'} mode, {r['seeds']} seeds x "
           f"{'/'.join(r['configs'])} = {r['episodes']} episodes ({seconds:.1f} s)", "",
           "Records: " + ", ".join(f"{t} {r['records'].get(t, 0)}" for t in TABLES) +
           f". Support >= {r['min_support']}. Flag: precision > {FLAG}.", "",
           "## Max precision per issue type", "", "| type | affected max P | evidence max P | flagged (aff/ev) |",
           "|---|---|---|---|"]
    for t in ISSUE_TYPES:
        a, e = r["labelings"]["affected"][t], r["labelings"]["evidence"][t]
        out.append(f"| {t} | {a['max_precision']:.3f} | {e['max_precision']:.3f} | "
                   f"{a['flagged_count']}/{e['flagged_count']} |")
    for labeling in LABELINGS:
        for t in ISSUE_TYPES:
            d = r["labelings"][labeling][t]
            out += ["", f"## {labeling}: {t}", "", "Base rate: " +
                    ", ".join(f"{tb} {d['base_rate'][tb]:.4f}" for tb in TABLES), "",
                    "| table | feature | value | support | pos | precision | lift |", "|---|---|---|---|---|---|---|"]
            for c in d["top"]:
                mark = " **FLAG**" if c["precision"] > FLAG else ""
                out.append(f"| {c['table']} | {c['feature']} | {c['value']} | {c['support']} | {c['positives']} | "
                           f"{c['precision']:.3f}{mark} | {c['lift']:.1f} |")
    out += ["", f"Flagged values: {len(r['flagged'])}"]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="0-999")
    ap.add_argument("--hard", action="store_true", help="difficulty: hard")
    ap.add_argument("--min-support", type=int, default=30)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", metavar="PATH", help="also write the full result as JSON")
    ap.add_argument("--report-only", action="store_true", help="exit 0 even if values are flagged")
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    r = mine(parse_seeds(args.seeds), args.hard, min_support=args.min_support, top=args.top)
    print(markdown(r, time.monotonic() - t0))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(r, fh, indent=1)
    return 0 if args.report_only or not r["flagged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
