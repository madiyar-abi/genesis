"""Compare the published audit rules with public episode records.

Scope: the 20 jury configurations in both difficulties plus unconfigured
default and hard. The only bookkeeping and evidence used are public. Scenario
counts are experimental controls, not facts available to an auditor.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import re

from auditenv.generator import generate
from auditenv.jury import SCENARIOS

ACCOUNT_NAMES = {
    "1000": "Cash", "1200": "Accounts receivable", "2900": "Unapplied cash", "4000": "Revenue",
    "6100": "Rent", "6200": "Payroll", "6300": "Software", "6400": "Bank fees", "7900": "FX gain/loss",
}


def items_key(invoice, relaxed):
    items = [(item["description"], item["quantity"], item["unit_price_minor"], item["amount_minor"])
             for item in invoice["line_items"]]
    if relaxed:
        return tuple(sorted((re.sub(r"[^a-z0-9]", "", text.lower()), qty, price, amount)
                            for text, qty, price, amount in items))
    return tuple(sorted(items))


def audit(ep, config, check, observe):
    tables, policy, manifest = ep["tables"], ep["policy"], ep["manifest"]
    base = policy["base_currency"]
    zone = datetime.fromisoformat("2000-01-01T00:00:00" + policy["timezone"]).tzinfo
    start, end = (policy["period"][key] for key in ("start", "end"))
    hard = config.get("difficulty") == "hard"
    exponents = manifest["amount_exponents"]
    issues = defaultdict(list)
    rates = {}
    invoices = {i["invoice_id"]: i for i in tables["invoices"]}
    invoice_rows, payment_rows, expenses = defaultdict(list), defaultdict(list), defaultdict(list)

    def day(timestamp):
        return datetime.fromisoformat(timestamp).astimezone(zone).date().isoformat()

    def scaled(amount, currency, rate):
        value = Decimal(amount).scaleb(-exponents[currency]) * rate
        return int(value.scaleb(exponents[base]).quantize(Decimal(1), rounding=ROUND_HALF_UP))

    def convert(amount, currency, date):
        if currency == base:
            return amount, None
        fx_id = f"{date}:{currency}:{base}"
        rate = rates.get((date, currency, base))
        check("rate_date", rate is not None, fx_id)
        if rate is None:
            return None, fx_id
        return scaled(amount, currency, rate), fx_id

    def posting(rows):
        return Counter({key: amount for key, amount in signed_totals(rows).items() if amount})

    def signed_totals(rows):
        totals = Counter()
        for row in rows:
            totals[row["account"], row["invoice_id"]] += row["debit_minor"] - row["credit_minor"]
        return totals

    def evidence(kind, amount, ids, records):
        check("positive_base_minor", type(amount) is int and amount > 0, *ids, amount)
        check("evidence_" + kind, all(records) and len(records) == len(set(records)), *ids, *records)
        issues[kind].append((ids, amount, records))

    check("company_period", (base, policy["timezone"], start, end) ==
          tuple(manifest[key] for key in ("base_currency", "timezone", "period_start", "period_end"))
          and start <= end, manifest["episode_id"])
    check("rounding", policy["rounding"] == "ROUND_HALF_UP to integer minor units"
          and manifest["rounding"] == "ROUND_HALF_UP", manifest["episode_id"])
    check("tolerance", policy["findings"]["tolerance_minor"] == 0, manifest["episode_id"])
    kinds = {"duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff"}
    check("issue_types", set(policy["findings"]["affected_ids"]) == kinds
          and all(kind in ep["task"] for kind in kinds), manifest["episode_id"])
    check("hard_text", ("credit_note" in policy["ledger"]) == hard
          and ("Hard mode:" in ep["task"]) == hard, manifest["episode_id"])
    check("account_legend", policy["ledger"]["accounts"] == ACCOUNT_NAMES, manifest["episode_id"])
    for row in tables["fx"]:
        pair = (row["date"], row["source_currency"], row["target_currency"])
        rate = Decimal(row["rate"])
        check("rate_direction", row["fx_id"] == ":".join(pair) and pair[1] != base
              and pair[1] in exponents and pair[2] == base and rate > 0 and pair not in rates, row["fx_id"])
        rates[pair] = rate

    for row in tables["ledger"]:
        rid = row["row_id"]
        check("ledger_base_currency", row["currency"] == base, rid)
        check("accounts", row["account"] in policy["ledger"]["accounts"], rid, row["account"])
        check("minor_units", all(type(row[key]) is int and row[key] >= 0
                                 for key in ("debit_minor", "credit_minor")), rid)
        check("period_rule", start <= day(row["timestamp"]) <= end, rid, row["timestamp"])
        if row["payment_id"]:
            payment_rows[row["payment_id"]].append(row)
        elif row["invoice_id"]:
            invoice_rows[row["invoice_id"]].append(row)
        else:
            expenses[row["timestamp"]].append(row)

    for rows in expenses.values():
        total = sum(row["debit_minor"] - row["credit_minor"] for row in rows)
        check("expense", total == 0 and all(
            (r["account"] == "1000" and r["credit_minor"] > 0 and not r["debit_minor"])
            or (r["account"].startswith("6") and r["debit_minor"] > 0 and not r["credit_minor"])
            for r in rows), *(r["row_id"] for r in rows))

    booked, reversed_ids = {}, set()
    for iid, invoice in invoices.items():
        rows = invoice_rows[iid]
        date = day(invoice["issued_at"])
        debits = [r for r in rows if r["account"] == "1200" and r["debit_minor"]]
        revenue = [r for r in rows if r["account"] == "4000" and r["credit_minor"]]
        reversal = [r for r in rows if (r["account"] == "1200" and r["credit_minor"])
                    or (r["account"] == "4000" and r["debit_minor"])]
        check("invoice_shape", len(debits) == len(revenue) == bool(rows)
              and len(rows) == len(debits) + len(revenue) + len(reversal)
              and all(r["entity_id"] == invoice["entity_id"] for r in rows), iid, *(r["row_id"] for r in rows))
        if not debits or not revenue:
            check("invoice_required", not start <= date <= end, iid, date)
            continue
        ar, sales = debits[0], revenue[0]
        booked[iid] = ar
        posted = ar["debit_minor"]
        check("invoice_balance", posted == sales["credit_minor"], iid, ar["row_id"], sales["row_id"])
        expected, fx_id = convert(invoice["total_minor"], invoice["currency"], date)
        check("conversion", expected is not None and (posted == expected or fx_id is not None),
              iid, ar["row_id"], posted, expected)
        if expected is not None and posted != expected:
            if fx_id:
                evidence("fx_error", abs(posted - expected), (iid,), (invoice["doc_id"], ar["row_id"], fx_id))
                check("wrong_date_explains", any(
                    other_day != date and src == invoice["currency"] and dst == base
                    and scaled(invoice["total_minor"], src, rate) == posted
                    for (other_day, src, dst), rate in rates.items()), iid, ar["row_id"], posted, fx_id)
        if not start <= date <= end:
            evidence("period_cutoff", posted, (iid,), (invoice["doc_id"], ar["row_id"]))
        if reversal:
            reversed_ids.add(iid)
            check("credit_note", hard and len(reversal) == 2
                  and posting(reversal) == {("4000", iid): posted, ("1200", iid): -posted}
                  and all(datetime.fromisoformat(r["timestamp"]) > datetime.fromisoformat(ar["timestamp"])
                          for r in reversal), iid, ar["row_id"], *(r["row_id"] for r in reversal))

    duplicates, equal_totals = defaultdict(list), Counter()
    for iid in booked:
        i = invoices[iid]
        duplicates[i["entity_id"], i["currency"], items_key(i, hard)].append(iid)
        equal_totals[i["entity_id"], i["currency"], i["total_minor"]] += 1
    observe("recurring_equal_amounts", sum(n > 1 for n in equal_totals.values()))
    for ids in duplicates.values():
        active = sorted((iid for iid in ids if iid not in reversed_ids),
                        key=lambda iid: datetime.fromisoformat(invoices[iid]["issued_at"]))
        for iid in set(ids) & reversed_ids:
            replacements = [other for other in active
                            if datetime.fromisoformat(invoices[other]["issued_at"])
                            > datetime.fromisoformat(invoices[iid]["issued_at"])]
            check("reissue", bool(replacements), iid, *ids)
            for other in replacements:
                observe("retyped_reissues", invoices[iid]["line_items"] != invoices[other]["line_items"])
        for original, duplicate in zip(active, active[1:]):
            check("later_copy", datetime.fromisoformat(invoices[original]["issued_at"])
                  < datetime.fromisoformat(invoices[duplicate]["issued_at"]), original, duplicate)
            observe("retyped_duplicates", invoices[original]["line_items"] != invoices[duplicate]["line_items"])
            evidence("duplicate_invoice", booked[duplicate]["debit_minor"], (original, duplicate),
                     tuple(invoices[iid]["doc_id"] for iid in (original, duplicate))
                     + tuple(booked[iid]["row_id"] for iid in (original, duplicate)))

    paid = Counter()
    for pay in tables["payments"]:
        pid, amount = pay["payment_id"], pay["amount_minor"]
        refs = pay["invoice_refs"] or []
        rows = payment_rows[pid]
        cur, date = pay["currency"], day(pay["timestamp"])
        check("payment_period", bool(rows) == (start <= date <= end), pid, date)
        if not rows:
            continue
        cash = [r for r in rows if r["account"] == "1000"]
        unapplied = [r for r in rows if r["account"] == "2900"]
        totals = signed_totals(rows)
        check("payment_shape", len(cash) == 1 and len(unapplied) <= 1 and all(
            r["account"] in {"1000", "1200", "2900", "7900"}
            and bool(r["invoice_id"]) == (r["account"] == "1200") for r in rows),
            pid, *(r["row_id"] for r in rows))
        check("payment_balance", sum(totals.values()) == 0, pid, *(r["row_id"] for r in rows))
        if not cash:
            continue
        expected, fx_id = convert(amount, cur, date)
        actual = totals["1000", None]
        check("conversion", expected is not None and (actual == expected or fx_id is not None),
              pid, cash[0]["row_id"], actual, expected)
        if expected is not None and actual != expected:
            if fx_id:
                evidence("fx_error", abs(actual - expected), (pid,), (pay["doc_id"], cash[0]["row_id"], fx_id))
                check("wrong_date_explains", any(
                    other_day != date and src == cur and dst == base
                    and scaled(amount, src, rate) == actual
                    for (other_day, src, dst), rate in rates.items()), pid, cash[0]["row_id"], actual, fx_id)
        ref_ids = {ref["invoice_id"] for ref in refs}
        check("refs", len(ref_ids) == len(refs)
              and {iid for account, iid in totals if account == "1200"} <= ref_ids
              and all(ref["amount_minor"] > 0 for ref in refs)
              and sum(ref["amount_minor"] for ref in refs) <= max(amount, 0)
              and (amount >= 0 or pay["invoice_refs"] is None), pid, *sorted(ref_ids))
        shortfalls = 0
        missing_source_minor = 0
        for ref in refs:
            iid = ref["invoice_id"]
            i = invoices.get(iid)
            check("ref_currency", i is not None and i["currency"] == cur, pid, iid)
            if i is None:
                continue
            paid[iid] += 1
            observe("partial_remittances", ref["amount_minor"] < i["total_minor"])
            expected_ar, inv_fx = convert(ref["amount_minor"], i["currency"], day(i["issued_at"]))
            actual_ar = -totals["1200", iid]
            if expected_ar is None:
                continue
            check("ar_credit", 0 <= actual_ar <= expected_ar, pid, iid, actual_ar, expected_ar)
            if actual_ar < expected_ar:
                shortfalls += 1
                if actual_ar == 0:
                    missing_source_minor += ref["amount_minor"]
                ar_rows = [r for r in rows if r["account"] == "1200" and r["invoice_id"] == iid]
                candidates = ar_rows if actual_ar else unapplied
                evidence("payment_allocation", expected_ar - actual_ar, (iid, pid),
                         (pay["doc_id"], i["doc_id"], candidates[0]["row_id"] if candidates else None)
                         + ((inv_fx,) if inv_fx else ()))
        rest = amount - sum(r["amount_minor"] for r in refs)
        expected_rest, _ = convert(rest, cur, date)
        actual_rest = -totals["2900", None]
        if shortfalls == 0:
            check("unapplied_payment_date", actual_rest == expected_rest, pid,
                  *(r["row_id"] for r in unapplied), actual_rest, expected_rest)
        elif missing_source_minor or actual_rest != expected_rest:
            observe("allocation_remainder_departures")
        if amount < 0:
            observe("refunds")
            check("refund", set(totals) == {("1000", None), ("2900", None)} and actual < 0
                  and actual_rest == expected_rest, pid, *(r["row_id"] for r in rows))
        elif not refs:
            observe("receipts_without_remittance")
        if totals["7900", None]:
            observe("fx_balance_adjustments")
    observe("split_payments", sum(count > 1 for count in paid.values()))

    if "errors" in config:
        expected_counts = Counter(config["errors"])
        for scenario, kinds in {"I1": ("payment_allocation", "fx_error"),
                                "I2": ("period_cutoff", "fx_error")}.items():
            for kind in kinds:
                expected_counts[kind] += config["interacting"].get(scenario, 0)
        for kind in sorted(set(policy["findings"]["affected_ids"])):
            check("scenario_findings", len(issues[kind]) == expected_counts[kind], kind,
                  f"expected={expected_counts[kind]}", f"actual={len(issues[kind])}", *issues[kind])
    for kind, cases in issues.items():
        observe(kind, len(cases))
    if not any(issues.values()):
        observe("clean_episodes")


def configs():
    yield "default", {}
    yield "hard", {"difficulty": "hard"}
    for name, config in SCENARIOS.items():
        yield name + "/default", config
        yield name + "/hard", dict(config, difficulty="hard")


def flatten(value, prefix=""):
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            yield from flatten(item, name)
        else:
            yield name, item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="31000-31199", help="inclusive seed range")
    args = parser.parse_args()
    low, high = map(int, args.seeds.split("-"))
    if low > high:
        parser.error("seed range starts after it ends")
    counts, observed, problems = Counter(), Counter(), Counter()
    text_samples = set()
    sample_count = 0
    default_sizes = {}
    for name, config in configs():
        for seed in range(low, high + 1):
            ep = generate(seed, config)

            def check(rule, ok, *details):
                counts[rule] += 1
                if not ok:
                    problems[rule] += 1
                    print(f"FAIL {name} seed={seed} {rule}: {details!r}")

            def observe(rule, n=1):
                observed[rule] += n

            sample = (name in {"default", "hard"} and seed < low + 5) or (
                seed == low and name.endswith("/default") and int(name[1:3]) % 2 == 0)
            if sample:
                sample_count += 1
                text_samples.add(ep["task"])
                text_samples.update(f"{key}: {value}" for key, value in flatten(ep["policy"])
                                    if key not in {"base_currency", "timezone", "period.start", "period.end"})
            audit(ep, config, check, observe)
            group = "unconfigured" if name in {"default", "hard"} else name.split("/")[0]
            ledger_size = len(ep["tables"]["ledger"])
            if name == "hard" or name.endswith("/hard"):
                check("hard_ledger_larger", ledger_size > default_sizes[group, seed],
                      ep["manifest"]["episode_id"], ledger_size, default_sizes[group, seed])
            else:
                default_sizes[group, seed] = ledger_size
    print(f"Read task and policy from {sample_count} discovery samples.")
    for claim in sorted(text_samples):
        print(f"CLAIM {claim}")
    for kind, stats in (("CHECK", counts), ("OBSERVED", observed), ("FAILURES", problems)):
        for key, total in sorted(stats.items()):
            print(f"{kind} {key}: {total}")
    print(f"Audited {42 * (high - low + 1)} episodes across 42 configurations; "
          f"{sum(counts.values())} checks, {sum(problems.values())} unexpected failures.")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
