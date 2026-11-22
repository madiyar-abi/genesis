"""Independently check the Block 2 scenario matrix from episode exports."""

import argparse
import csv
import json
import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import judge_adapter
from auditenv.jury import SCENARIOS


def read_json(path):
    return json.loads(path.read_text())


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def invoice_signature(invoice):
    return (
        invoice["entity_id"], invoice["currency"], invoice["total_minor"],
        tuple(sorted((line["quantity"], line["unit_price_minor"], line["amount_minor"],
                      "".join(char for char in line["description"].casefold() if char.isalnum()))
                     for line in invoice["line_items"])),
    )


class PublicBooks:
    def __init__(self, path):
        manifest = read_json(path / "manifest.json")
        policy = read_json(path / "policy.json")
        self.base = manifest["base_currency"]
        self.exponents = manifest["amount_exponents"]
        self.start = manifest["period_start"]
        self.end = manifest["period_end"]
        assert (self.start, self.end) == (policy["period"]["start"], policy["period"]["end"])
        offset = manifest["timezone"]
        assert offset == policy["timezone"]
        hours, minutes = map(int, offset[1:].split(":"))
        sign = {"-": -1, "+": 1}[offset[0]]
        self.zone = timezone(sign * timedelta(hours=hours, minutes=minutes))
        self.ledger = read_csv(path / "ledger.csv")
        self.invoices = self.documents(path / "invoices.jsonl", "invoice_id")
        self.payments = self.documents(path / "payments.jsonl", "payment_id")
        self.rates = defaultdict(dict)
        for row in read_csv(path / "fx.csv"):
            self.rates[row["source_currency"], row["target_currency"]][row["date"]] = Decimal(row["rate"])
        self.invoice_rows = defaultdict(list)
        self.payment_rows = defaultdict(list)
        for row in self.ledger:
            if row["payment_id"]:
                self.payment_rows[row["payment_id"]].append(row)
            elif row["invoice_id"]:
                self.invoice_rows[row["invoice_id"]].append(row)
        self.payment_times = {
            payment_id: datetime.fromisoformat(payment["timestamp"])
            for payment_id, payment in self.payments.items()
        }
        self.allocations = defaultdict(list)
        for payment_id, payment in self.payments.items():
            for ref in payment["invoice_refs"] or []:
                self.allocations[ref["invoice_id"]].append((payment_id, ref["amount_minor"]))

    @staticmethod
    def documents(path, identifier):
        return {record[identifier]: record for record in map(json.loads, path.read_text().splitlines())}

    def day(self, timestamp):
        return datetime.fromisoformat(timestamp).astimezone(self.zone).date().isoformat()

    def convert(self, amount, currency, day, rate=None):
        if currency == self.base:
            return amount
        if rate is None:
            rate = self.rates[currency, self.base][day]
        scale = self.exponents[self.base] - self.exponents[currency]
        return int((Decimal(amount).scaleb(scale) * rate).to_integral_value(rounding=ROUND_HALF_UP))

    @staticmethod
    def posting(rows, account, side):
        return sum(int(row[side + "_minor"]) for row in rows if row["account"] == account)

    def invoice_amount(self, invoice, amount):
        return self.convert(amount, invoice["currency"], self.day(invoice["issued_at"]))

    def expected_credit(self, invoice_id, payment_id, amount):
        invoice = self.invoices[invoice_id]
        paid_at = self.payment_times[payment_id]
        earlier = [value for earlier_id, value in self.allocations[invoice_id]
                   if self.payment_times[earlier_id] < paid_at]
        total = invoice["total_minor"]
        if earlier and sum(earlier) + amount == total:
            return self.invoice_amount(invoice, total) - sum(self.invoice_amount(invoice, value) for value in earlier)
        return self.invoice_amount(invoice, amount)

    @staticmethod
    def unallocated(payment):
        return payment["amount_minor"] - sum(ref["amount_minor"] for ref in payment["invoice_refs"] or [])

    def matches_postings(self, rows, expected):
        actual = Counter()
        for row in rows:
            actual[row["account"]] += int(row["debit_minor"]) - int(row["credit_minor"])
        return actual == Counter(expected)

    def allocation_differences(self):
        for invoice_id, refs in self.allocations.items():
            for payment_id, amount in refs:
                rows = [row for row in self.payment_rows[payment_id] if row["invoice_id"] == invoice_id]
                expected = self.expected_credit(invoice_id, payment_id, amount)
                actual = self.posting(rows, "1200", "credit")
                if 0 <= actual < expected:
                    yield payment_id, invoice_id, actual, expected

    def correct_receipt(self, payment_id):
        payment = self.payments[payment_id]
        rows = self.payment_rows[payment_id]
        currency = payment["currency"]
        day = self.day(payment["timestamp"])
        cash = self.convert(payment["amount_minor"], currency, day)
        remainder = self.convert(self.unallocated(payment), currency, day)
        ar = 0
        for ref in payment["invoice_refs"] or []:
            invoice_id = ref["invoice_id"]
            expected = self.expected_credit(invoice_id, payment_id, ref["amount_minor"])
            invoice_rows = [row for row in rows if row["invoice_id"] == invoice_id]
            if self.posting(invoice_rows, "1200", "credit") != expected:
                return False
            ar += expected
        return self.matches_postings(rows, {"1000": cash, "1200": -ar, "2900": -remainder,
                                            "7900": ar + remainder - cash})

    def split_payments(self):
        for invoice_id, refs in self.allocations.items():
            invoice = self.invoices[invoice_id]
            payment_ids = {payment_id for payment_id, _ in refs}
            if len(payment_ids) < 2 or sum(amount for _, amount in refs) != invoice["total_minor"]:
                continue
            if all(amount > 0 and self.payments[payment_id]["currency"] == invoice["currency"]
                   and self.correct_receipt(payment_id) for payment_id, amount in refs):
                yield invoice_id, tuple(sorted(payment_ids))

    def refunds(self):
        receipts = defaultdict(list)
        for payment_id, payment in self.payments.items():
            remainder = self.unallocated(payment)
            if remainder > 0:
                for entity in {row["entity_id"] for row in self.payment_rows[payment_id]}:
                    receipts[entity, payment["currency"], remainder].append(payment_id)
        for payment_id, payment in self.payments.items():
            amount = -payment["amount_minor"]
            if amount <= 0 or payment["invoice_refs"] is not None:
                continue
            rows = self.payment_rows[payment_id]
            currency = payment["currency"]
            cash = self.convert(amount, currency, self.day(payment["timestamp"]))
            for entity in {row["entity_id"] for row in rows if row["account"] == "2900"}:
                earlier = (receipt_id for receipt_id in receipts[entity, currency, amount]
                           if self.payment_times[receipt_id] < self.payment_times[payment_id])
                receipt_id = max(earlier, key=self.payment_times.__getitem__, default=None)
                if receipt_id is None:
                    continue
                receipt_day = self.day(self.payments[receipt_id]["timestamp"])
                debit = self.convert(amount, currency, receipt_day)
                if self.correct_receipt(receipt_id) and self.matches_postings(
                    rows, {"1000": -cash, "2900": debit, "7900": cash - debit}
                ):
                    yield payment_id, receipt_id

    def invoice_pairs(self):
        groups = defaultdict(list)
        for invoice_id in self.invoice_rows:
            if self.posting(self.invoice_rows[invoice_id], "1200", "debit") > 0:
                invoice = self.invoices[invoice_id]
                groups[invoice["currency"], invoice["total_minor"]].append(invoice_id)
        for group in groups.values():
            yield from combinations(group, 2)

    def fx_differences(self):
        documents = (
            ("invoice", self.invoices, self.invoice_rows, "issued_at", "total_minor", "1200"),
            ("payment", self.payments, self.payment_rows, "timestamp", "amount_minor", "1000"),
        )
        for kind, records, journal, timestamp, amount_key, account in documents:
            for identifier, record in records.items():
                amount = record[amount_key]
                currency = record["currency"]
                if amount <= 0 or currency == self.base or not journal[identifier]:
                    continue
                day = self.day(record[timestamp])
                observed = self.posting(journal[identifier], account, "debit")
                if observed == self.convert(amount, currency, day):
                    continue
                alternatives = tuple(
                    other_day for other_day, rate in self.rates[currency, self.base].items()
                    if other_day != day and observed == self.convert(amount, currency, day, rate)
                )
                yield kind, identifier, day, alternatives

    def cutoff_differences(self):
        for invoice_id, rows in self.invoice_rows.items():
            day = self.day(self.invoices[invoice_id]["issued_at"])
            if self.start <= day <= self.end:
                continue
            for row in rows:
                posted = self.day(row["timestamp"])
                if (row["account"] == "1200" and int(row["debit_minor"]) > 0
                        and self.start <= posted <= self.end):
                    yield invoice_id, row["row_id"], day, posted


def check(number, books, truth_types):
    expected = ()
    if 6 <= number <= 8:
        expected = ("duplicate_invoice",)
    elif 9 <= number <= 11:
        expected = ("payment_allocation",)
    elif 12 <= number <= 13:
        expected = ("fx_error",)
    elif 14 <= number <= 15:
        expected = ("period_cutoff",)
    elif 16 <= number <= 18:
        expected = ("payment_allocation", "fx_error")
    elif number >= 19:
        expected = ("period_cutoff", "fx_error")
    checks = {"truth count/types": (truth_types == Counter(expected), dict(truth_types))}
    variants = defaultdict(set)

    if number <= 8:
        duplicates, distinct = [], []
        for first, second in books.invoice_pairs():
            left, right = books.invoices[first], books.invoices[second]
            if invoice_signature(left) == invoice_signature(right):
                duplicates.append((first, second, left["doc_id"], right["doc_id"]))
            else:
                distinct.append((first, second))
        checks["legitimate equal totals"] = (bool(distinct), list(books.invoice_rows))
        if number <= 5:
            split = list(books.split_payments())
            refunds = list(books.refunds())
            days = {books.day(row["timestamp"]) for row in books.ledger}
            checks["correct split"] = (bool(split), list(books.payments))
            checks["correct refund"] = (
                bool(refunds), [pid for pid, payment in books.payments.items() if payment["amount_minor"] < 0]
            )
            for label, boundary in (("first day", books.start), ("last day", books.end)):
                checks[label] = (boundary in days, min(books.ledger, key=lambda row: abs(
                    (datetime.fromisoformat(books.day(row["timestamp"])) - datetime.fromisoformat(boundary)).days
                ))["row_id"])
        else:
            variants["candidate pair count"].add(len(duplicates))
            checks["duplicate candidates have distinct invoice/document IDs"] = (
                bool(duplicates) and all(a != b and c != d for a, b, c, d in duplicates),
                duplicates or list(books.invoice_rows),
            )

    if 9 <= number <= 11 or 16 <= number <= 18:
        differences = list(books.allocation_differences())
        missing = [difference for difference in differences if difference[2] == 0]
        partial = [difference for difference in differences if difference[2] > 0]
        if number <= 11:
            evidence = differences or list(books.payments)
            checks["one allocation shortfall"] = (len(differences) == 1, evidence)
            if number == 9:
                checks["missing allocation"] = (len(missing) == 1, evidence)
            elif number == 10:
                checks["partial allocation"] = (len(partial) == 1, evidence)
            if missing:
                variants["allocation mode"].add("missing")
            if partial:
                variants["allocation mode"].add("partial")

    if 12 <= number <= 13 or number >= 16:
        fx = list(books.fx_differences())
        checks["one different-date published FX rate"] = (len(fx) == 1 and bool(fx[0][3]), fx)

    if 14 <= number <= 15 or number >= 19:
        cutoff = list(books.cutoff_differences())
        checks["one outside invoice booked inside company period"] = (len(cutoff) == 1, cutoff)

    if 16 <= number <= 18:
        joint = [
            (payment_id, invoice_id, actual, expected_amount, day, alternatives)
            for payment_id, invoice_id, actual, expected_amount in partial
            for kind, identifier, day, alternatives in fx
            if kind == "payment" and identifier == payment_id and day == books.end and alternatives
        ]
        checks["partial allocation and wrong FX on same period-end payment"] = (
            len(joint) == 1, {"allocation": differences, "fx": fx, "period_end": books.end}
        )
        for payment_id, invoice_id, actual, expected_amount, day, alternatives in joint:
            variants["currency pair"].add((books.payments[payment_id]["currency"], books.base))
            variants["company timezone"].add(books.zone.utcoffset(None))
            variants["posted fraction of expected AR"].add(Fraction(actual, expected_amount))
            variants["invoice age in days"].add(
                (datetime.fromisoformat(day) - datetime.fromisoformat(
                    books.day(books.invoices[invoice_id]["issued_at"])
                )).days
            )
            variants["possible FX day offsets"].add(day_offsets(day, alternatives))

    if number >= 19:
        joint = [
            (invoice_id, issued, posted, alternatives)
            for invoice_id, _, issued, posted in cutoff
            for kind, identifier, day, alternatives in fx
            if kind == "invoice" and identifier == invoice_id and day == issued
            and issued > books.end and alternatives
        ]
        checks["same next-period invoice booked inside at wrong FX"] = (
            len(joint) == 1, {"cutoff": cutoff, "fx": fx}
        )
        for invoice_id, issued, posted, alternatives in joint:
            variants["currency pair"].add((books.invoices[invoice_id]["currency"], books.base))
            variants["company timezone"].add(books.zone.utcoffset(None))
            variants["issue lead over close in days"].add(day_offsets(books.end, (issued,))[0])
            variants["booking lag relative to close in days"].add(day_offsets(books.end, (posted,))[0])
            variants["possible FX day offsets"].add(day_offsets(issued, alternatives))

    return checks, variants


def day_offsets(day, others):
    return tuple((datetime.fromisoformat(other) - datetime.fromisoformat(day)).days for other in others)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="50000-50199", help="inclusive START-END")
    parser.add_argument("--scratch", type=Path, default=Path("/tmp/r22-codex1"))
    args = parser.parse_args()
    start, end = map(int, args.seeds.split("-"))
    if start > end:
        parser.error("seed range must be increasing")
    args.scratch.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("AUDITENV_KEY_FILE", str(args.scratch / "key"))
    counts = defaultdict(Counter)
    variants = defaultdict(lambda: defaultdict(set))
    failures = 0
    with tempfile.TemporaryDirectory(dir=args.scratch) as scratch:
        path = Path(scratch) / "episode"
        for scenario, config in SCENARIOS.items():
            number = int(scenario[1:])
            for seed in range(start, end + 1):
                for difficulty in ("default", "hard"):
                    judge_adapter.generate_episode(seed, {**config, "difficulty": difficulty}, path)
                    truth_types = Counter(issue["type"] for issue in read_json(path / "grader/truth.json")["issues"])
                    books = PublicBooks(path / "public")
                    checks, observed = check(number, books, truth_types)
                    for name, (holds, evidence) in checks.items():
                        counts[scenario][name] += holds
                        if not holds:
                            failures += 1
                            print(f"FAIL {scenario} seed={seed} difficulty={difficulty} {name}: {evidence!r}")
                    for name, values in observed.items():
                        variants[scenario][name].update(values)

    total = 2 * (end - start + 1)
    print("| Scenario | " + f"Requirement (episodes out of {total}) |")
    print("|---|---|")
    for scenario, requirements in counts.items():
        summary = "; ".join(f"{name}: {count}/{total}" for name, count in requirements.items())
        print(f"| {scenario} | {summary} |")
    for scenario, parameters in variants.items():
        for name, values in parameters.items():
            sample = ", ".join(sorted(map(str, values))) if len(values) <= 8 else ""
            detail = f" ({sample})" if sample else ""
            print(f"{scenario} {name}: {len(values)} distinct{detail}")
    allocation_modes = set().union(*(variants[d]["allocation mode"] for d in ("D09", "D10", "D11")))
    print(f"D09–D11 observed allocation modes: {', '.join(sorted(allocation_modes))}")
    print(f"{len(counts) * total} episodes; {failures} failed per-episode checks")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
