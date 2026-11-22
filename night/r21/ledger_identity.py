"""Re-derive journal, receivable, unapplied cash and FX identities from public books."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

from auditenv.generator import generate
from auditenv.jury import SCENARIOS

CHECKS = ("journal", "ar_running", "ar_close", "unapplied_running", "refund_2900", "fx", "trial")


def amount(row):
    return row["debit_minor"] - row["credit_minor"]


def row_ids(rows):
    return ",".join(row["row_id"] for row in rows) or "(no ledger rows)"


def unallocated(payment):
    return payment["amount_minor"] - sum(ref["amount_minor"] for ref in payment["invoice_refs"] or [])


def audit(tables, manifest, policy):
    counts = Counter()
    violations = []
    zone = datetime.fromisoformat("2000-01-01T00:00:00" + policy["timezone"]).tzinfo
    base = policy["base_currency"]
    exponents = manifest["amount_exponents"]
    rates = {(r["date"], r["source_currency"]): Decimal(r["rate"]) for r in tables["fx"]
             if r["target_currency"] == base}

    def local_date(timestamp):
        return datetime.fromisoformat(timestamp).astimezone(zone).date().isoformat()

    def convert(value, currency, timestamp):
        rate = rates[local_date(timestamp), currency] if currency != base else Decimal(1)
        result = (Decimal(value) * rate).scaleb(exponents[base] - exponents[currency])
        return int(result.to_integral_value(rounding=ROUND_HALF_UP))

    def check(name, actual, expected, ids, detail="", *, minimum=False, causes=()):
        counts[name] += 1
        if (actual < expected if minimum else actual != expected):
            violations.append((name, ids, actual, expected, detail, causes))

    journals = defaultdict(list)
    invoice_ar = defaultdict(list)
    unapplied = defaultdict(list)
    for row in tables["ledger"]:
        timestamp = datetime.fromisoformat(row["timestamp"])
        key = (timestamp, row["payment_id"], None if row["payment_id"] else row["invoice_id"], row["entity_id"])
        journals[key].append(row)
        if row["account"] == "1200":
            invoice_ar[row["invoice_id"]].append(row)
        elif row["account"] == "2900":
            unapplied[row["entity_id"]].append(row)
    for key, rows in journals.items():
        check("journal", sum(map(amount, rows)), 0, row_ids(rows), str(key))
    check("trial", sum(map(amount, tables["ledger"])), 0, row_ids(tables["ledger"]))

    invoices = {doc["invoice_id"]: doc for doc in tables["invoices"]}
    applied = defaultdict(int)
    payment_journals = defaultdict(list)
    for key, rows in journals.items():
        if key[1]:
            payment_journals[key[1]].extend(rows)
    receipts = defaultdict(list)
    for payment in tables["payments"]:
        if payment["amount_minor"] > 0 and unallocated(payment) > 0:
            for entity in {row["entity_id"] for row in payment_journals[payment["payment_id"]]}:
                key = (entity, payment["currency"], unallocated(payment))
                receipts[key].append(datetime.fromisoformat(payment["timestamp"]))
    period = policy["period"]
    checked_fx_ids = set()
    for pay in tables["payments"]:
        payment_id = pay["payment_id"]
        if not period["start"] <= local_date(pay["timestamp"]) <= period["end"]:
            continue
        refs = pay["invoice_refs"] or []
        expected_ar = 0
        for ref in refs:
            invoice_id = ref["invoice_id"]
            invoice = invoices[invoice_id]
            cash_applied = convert(ref["amount_minor"], invoice["currency"], invoice["issued_at"])
            applied[invoice_id] += cash_applied
            expected_ar += cash_applied
        cash = convert(pay["amount_minor"], pay["currency"], pay["timestamp"])
        rows = payment_journals[payment_id]
        remainder_date = datetime.fromisoformat(pay["timestamp"])
        if pay["amount_minor"] < 0:
            entity = next((row["entity_id"] for row in rows if row["account"] == "1000"), None)
            key = (entity, pay["currency"], -pay["amount_minor"])
            remainder_date = max((date for date in receipts[key] if date < remainder_date), default=remainder_date)
        remainder = convert(unallocated(pay), pay["currency"], remainder_date.isoformat())
        if pay["amount_minor"] < 0:
            check("refund_2900", sum(amount(row) for row in rows if row["account"] == "2900"),
                  -remainder, row_ids(rows), f"{payment_id} 2900 rate date={local_date(remainder_date.isoformat())}")
        expected_fx = expected_ar + remainder - cash
        fx_rows = [row for row in rows if row["account"] == "7900"]
        bank = sum(amount(row) for row in rows if row["account"] == "1000")
        credits = -sum(amount(row) for row in rows if row["account"] == "1200")
        causes = []
        if bank != cash:
            causes.append("fx_error")
        if credits < expected_ar:
            causes.append("payment_allocation")
        checked_fx_ids.update(row["row_id"] for row in fx_rows)
        for row in fx_rows or [None]:
            check("fx", amount(row) if row else 0, expected_fx, row_ids([row] if row else rows),
                  f"{payment_id} correct cash={cash} AR credit={expected_ar} remainder={remainder}",
                  causes=causes)

    for row in tables["ledger"]:
        if row["account"] == "7900" and row["row_id"] not in checked_fx_ids:
            check("fx", amount(row), 0, row["row_id"], "no in-period payment documents this FX posting")

    for invoice_id, invoice in invoices.items():
        day = local_date(invoice["issued_at"])
        total = convert(invoice["total_minor"], invoice["currency"], invoice["issued_at"])
        rows = invoice_ar[invoice_id]
        opening = total if day < period["start"] else 0
        expected_booking = total if period["start"] <= day <= period["end"] else 0
        running = opening
        booking_delta = 0
        ordered = sorted(rows, key=lambda row: (datetime.fromisoformat(row["timestamp"]), -amount(row)))
        for row in ordered:
            running += amount(row)
            if not row["payment_id"] and row["debit_minor"]:
                booking_delta += expected_booking - row["debit_minor"]
            causes = ("fx_error",) if booking_delta > 0 and running + booking_delta >= 0 else ()
            check("ar_running", running, 0, row["row_id"], invoice_id, minimum=True, causes=causes)
        booking = sum(row["debit_minor"] for row in rows if not row["payment_id"])
        credit_note = sum(row["credit_minor"] for row in rows if not row["payment_id"])
        credits = sum(row["credit_minor"] for row in rows if row["payment_id"])
        causes = []
        if booking and not expected_booking:
            causes.append("period_cutoff")
        elif booking and booking != expected_booking:
            causes.append("fx_error")
        if credits < applied[invoice_id]:
            causes.append("payment_allocation")
        expected = opening + expected_booking - applied[invoice_id] - (total if credit_note else 0)
        check("ar_close", running, expected, row_ids(rows), invoice_id, causes=causes)

    for entity, rows in unapplied.items():
        balance = 0
        ordered = sorted(rows, key=lambda row: (datetime.fromisoformat(row["timestamp"]), amount(row)))
        for row in ordered:
            balance -= amount(row)
            check("unapplied_running", balance, 0, row["row_id"], str(entity), minimum=True)
    return counts, violations


def classify(tables, manifest, policy, violations):
    """Yield class, absolute base residue, refund debit and the original violation."""
    payments = {doc["payment_id"]: doc for doc in tables["payments"]}
    invoices = {doc["invoice_id"]: doc for doc in tables["invoices"]}
    rows = {row["row_id"]: row for row in tables["ledger"]}
    account_rows = defaultdict(list)
    for row in rows.values():
        key = row["entity_id"] if row["account"] == "2900" else row["invoice_id"]
        account_rows[row["account"], key].append(row)
    zone = datetime.fromisoformat("2000-01-01T00:00:00" + policy["timezone"]).tzinfo
    base = policy["base_currency"]
    rates = {(row["date"], row["source_currency"]): Decimal(row["rate"]) for row in tables["fx"]
             if row["target_currency"] == base}

    def convert(value, currency, timestamp):
        day = datetime.fromisoformat(timestamp).astimezone(zone).date().isoformat()
        if currency == base:
            return value
        shift = manifest["amount_exponents"][base] - manifest["amount_exponents"][currency]
        result = (Decimal(value) * rates[day, currency]).scaleb(shift)
        return int(result.to_integral_value(rounding=ROUND_HALF_UP))

    for violation in violations:
        check, ids, actual, expected, key, _ = violation
        residue = abs(actual - expected)
        category, refund = "c", 0
        if check == "unapplied_running":
            ordered = sorted(account_rows["2900", rows[ids]["entity_id"]],
                             key=lambda row: (datetime.fromisoformat(row["timestamp"]), amount(row)))
            currency_credit = Counter()
            last_refund = 0
            for row in ordered:
                doc = payments[row["payment_id"]]
                currency = doc["currency"]
                remainder = unallocated(doc)
                currency_credit[currency] += remainder
                if -amount(row) != convert(remainder, currency, doc["timestamp"]) or currency_credit[currency] < 0:
                    break
                if remainder < 0:
                    last_refund = amount(row)
                if row["row_id"] == ids:
                    if last_refund:
                        category, refund = "a", last_refund
                    break
        elif check in {"ar_running", "ar_close"}:
            invoice = invoices[key]
            ordered = sorted(account_rows["1200", key],
                             key=lambda row: (datetime.fromisoformat(row["timestamp"]), -amount(row)))
            applied = []
            matches = True
            for row in ordered:
                if row["payment_id"]:
                    doc = payments[row["payment_id"]]
                    values = [ref["amount_minor"] for ref in doc["invoice_refs"] or [] if ref["invoice_id"] == key]
                    if row["credit_minor"] != sum(convert(value, invoice["currency"], invoice["issued_at"])
                                                  for value in values):
                        matches = False
                        break
                    applied.extend(values)
                if check == "ar_running" and row["row_id"] == ids:
                    break
            if matches and applied and residue <= len(applied) and sum(applied) <= invoice["total_minor"]:
                separate = sum(convert(value, invoice["currency"], invoice["issued_at"]) for value in applied)
                combined = convert(sum(applied), invoice["currency"], invoice["issued_at"])
                if residue == abs(separate - combined):
                    category = "b"
        yield category, residue, refund, violation


def classify_clean(lo, hi):
    print("| Config | Difficulty | FX refund (a) | AR rounding (b) | Other (c) | Max (a) base minor | Max (a) % |")
    print("|---|---|---:|---:|---:|---:|---:|")
    total = Counter()
    details = []
    by_check = []
    for name in ("D01", "D02", "D03", "D04", "D05"):
        for difficulty in ("default", "hard"):
            counts = Counter()
            checked, mismatched = Counter(), Counter()
            max_minor, max_percent = 0, Fraction(0)
            for seed in range(lo, hi + 1):
                episode = generate(seed, {**SCENARIOS[name], "difficulty": difficulty})
                tables, manifest, policy = (episode[key] for key in ("tables", "manifest", "policy"))
                checks, violations = audit(tables, manifest, policy)
                checked.update(checks)
                for category, residue, refund, violation in classify(tables, manifest, policy, violations):
                    counts[category] += 1
                    if category == "a":
                        max_minor = max(max_minor, residue)
                        max_percent = max(max_percent, Fraction(100 * residue, refund))
                    check, ids, actual, expected, detail, _ = violation
                    mismatched[check] += 1
                    details.append(f"- {name}/{difficulty} seed {seed} class {category} {check} ({ids}): "
                                   f"observed {actual}, expected {expected}; {detail}")
            total.update(counts)
            print(f"| {name} | {difficulty} | {counts['a']} | {counts['b']} | {counts['c']} | "
                  f"{max_minor} | {float(max_percent):.6f}% |", flush=True)
            cells = [f"{checked[k]:,} / {mismatched[k]:,}" for k in CHECKS]
            by_check.append(f"| {name} | {difficulty} | " + " | ".join(cells) + " |")
    print("\nChecks executed / mismatches\n")
    print("| Config | Difficulty | " + " | ".join(CHECKS) + " |")
    print("|---|---|" + "---:|" * len(CHECKS))
    print("\n".join(by_check))
    print(f"\nClassified {sum(total.values())} clean violations: (a) {total['a']}, (b) {total['b']}, (c) {total['c']}.")
    if details:
        print("\nViolations:")
        print("\n".join(details))
    return bool(total["a"] or total["c"])



def allowed(config):
    if "errors" not in config:
        return {"duplicate_invoice", "period_cutoff", "fx_error", "payment_allocation"}
    kinds = {kind for kind, count in config["errors"].items() if count}
    inter = config.get("interacting", {})
    if inter.get("I1"):
        kinds.update(("payment_allocation", "fx_error"))
    if inter.get("I2"):
        kinds.update(("period_cutoff", "fx_error"))
    return kinds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="41000-41299")
    parser.add_argument("--classify", action="store_true", help="classify violations in clean D01–D05 scenarios")
    args = parser.parse_args()
    lo, hi = map(int, args.seeds.split("-"))
    if args.classify:
        return classify_clean(lo, hi)
    failures = 0
    clean = []
    examples = {}
    print("| Config | Difficulty | " + " | ".join(CHECKS) + " |")
    print("|---|---|" + "---:|" * len(CHECKS))
    for name, config in {"baseline": {}, **SCENARIOS}.items():
        for difficulty in ("default", "hard"):
            checked, explained, unexplained = Counter(), Counter(), Counter()
            for seed in range(lo, hi + 1):
                episode = generate(seed, {**config, "difficulty": difficulty})
                counts, violations = audit(episode["tables"], episode["manifest"], episode["policy"])
                checked.update(counts)
                for check, ids, actual, expected, detail, causes in violations:
                    if allowed(config).intersection(causes):
                        explained[check] += 1
                        continue
                    failures += 1
                    unexplained[check] += 1
                    line = f"- {name}/{difficulty} seed {seed} {check} ({ids}): observed {actual}, expected {expected}; {detail}"
                    examples.setdefault((name, difficulty, check), line)
                    if name in {"D01", "D02", "D03", "D04", "D05"}:
                        clean.append(line)
            cells = [f"{checked[k]:,} / {explained[k]:,} / {unexplained[k]:,}" for k in CHECKS]
            print(f"| {name} | {difficulty} | " + " | ".join(cells) + " |", flush=True)
    print(f"\nUnexplained violations: {failures}. Clean scenario violations: {len(clean)}.")
    if clean:
        print("\nClean scenario violations:")
        print("\n".join(clean))
    selected = [line for (name, _, _), line in examples.items() if name not in {"D01", "D02", "D03", "D04", "D05"}]
    if selected:
        print("\nFirst unexplained violation of each check outside clean scenarios:")
        print("\n".join(selected))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
