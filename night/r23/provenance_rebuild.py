"""Independent Block 2 replay of the documented export format."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from tempfile import TemporaryDirectory

from auditenv.jury import SCENARIOS
from judge_adapter import generate_episode


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def read_json(path):
    return json.loads(path.read_text())


def read_docs(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def read_csv(path):
    with path.open(newline="") as source:
        return list(csv.DictReader(source))


def ledger_row(row):
    return {key: int(value) if key in ("debit_minor", "credit_minor") else value or None
            for key, value in row.items()}


def instant(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, f"offset missing: {value}")
    return result


def net(rows, account):
    return sum(r["debit_minor"] - r["credit_minor"] for r in rows if r["account"] == account)


def key(row):
    if row["payment_id"]:
        return "pay:" + row["payment_id"]
    if row["invoice_id"]:
        return "inv:" + row["invoice_id"]
    return "expense:" + row["timestamp"]


def allocation(payment):
    result = Counter()
    for ref in payment["invoice_refs"] or []:
        result[ref["invoice_id"]] += ref["amount_minor"]
    return result


def line_items(invoice):
    return Counter(("".join(c for c in item["description"].lower() if c.isalnum()),
                    item["quantity"], item["unit_price_minor"], item["amount_minor"])
                   for item in invoice["line_items"])


class Episode:
    def __init__(self, root):
        public = root / "public"
        self.manifest = read_json(public / "manifest.json")
        self.policy = read_json(public / "policy.json")
        self.base = self.manifest["base_currency"]
        self.zone = instant("2000-01-01T00:00:00" + self.manifest["timezone"]).tzinfo
        self.invoices = {d["invoice_id"]: d for d in read_docs(public / "invoices.jsonl")}
        self.payments = {d["payment_id"]: d for d in read_docs(public / "payments.jsonl")}
        self.rates = {r["fx_id"]: r["rate"] for r in read_csv(public / "fx.csv")}
        self.after = defaultdict(list)
        self.rows = {}
        for raw in read_csv(public / "ledger.csv"):
            row = ledger_row(raw)
            self.rows[row["row_id"]] = row
            self.after[key(row)].append(row)
        self.injections = read_json(root / "grader/provenance.json")["injections"]
        self.truth = read_json(root / "grader/truth.json")["issues"]

    def date(self, timestamp):
        return instant(timestamp).astimezone(self.zone).date().isoformat()

    def inside(self, timestamp):
        return self.manifest["period_start"] <= self.date(timestamp) <= self.manifest["period_end"]

    def fx_id(self, doc):
        return f"{self.date(doc.get('issued_at', doc.get('timestamp')))}:{doc['currency']}:{self.base}"

    def convert(self, amount, doc):
        currency = doc["currency"]
        if currency == self.base:
            return amount
        exponents = self.manifest["amount_exponents"]
        rate = Decimal(self.rates[self.fx_id(doc)])
        return int((Decimal(amount).scaleb(exponents[self.base] - exponents[currency])
                    * rate).to_integral_value(rounding=ROUND_HALF_UP))

    def rewind(self):
        books = dict(self.after)
        removed = set()
        for injection in reversed(self.injections):
            for change in reversed(injection["changes"]):
                journal = change["journal"]
                current = books.get(journal, [])
                require(sorted(current, key=lambda r: r["row_id"]) ==
                        sorted(change["after"] or [], key=lambda r: r["row_id"]),
                        f"{injection['issue_id']} {journal}: after rows differ")
                if change["before"] is None:
                    books.pop(journal, None)
                else:
                    books[journal] = change["before"]
            removed.update(injection["documents_added"])
        docs = list(self.invoices.values()) + list(self.payments.values())
        require(removed <= {d["doc_id"] for d in docs}, f"unknown added documents {removed}")
        return books, removed

    def clean(self, books, removed):
        balances = Counter()
        for journal, rows in books.items():
            require(sum(r["debit_minor"] - r["credit_minor"] for r in rows) == 0,
                    f"{journal}: unbalanced journal")
            for row in rows:
                require(key(row) == journal and row["currency"] == self.base and self.inside(row["timestamp"]),
                        f"{journal}: invalid rebuilt row {row['row_id']}")
                balances[row["entity_id"]] -= net([row], "2900")
        require(sum(r["debit_minor"] - r["credit_minor"] for rows in books.values() for r in rows) == 0,
                "unbalanced trial balance")
        require(all(amount >= 0 for amount in balances.values()),
                f"negative 2900 balances {dict((k, v) for k, v in balances.items() if v < 0)}")

        invoices = {i: d for i, d in self.invoices.items() if d["doc_id"] not in removed}
        payments = {p: d for p, d in self.payments.items() if d["doc_id"] not in removed}
        history = defaultdict(list)
        for pid, payment in payments.items():
            when = instant(payment["timestamp"])
            for iid, amount in allocation(payment).items():
                history[iid].append((when, pid, amount))
        expected_credits = Counter()
        for iid, refs in history.items():
            invoice = invoices[iid]
            booked = self.convert(invoice["total_minor"], invoice)
            for when, pid, amount in refs:
                earlier = [part for stamp, _, part in refs if stamp < when]
                expected = self.convert(amount, invoice)
                if sum(earlier) + amount == invoice["total_minor"]:
                    expected = booked - sum(self.convert(part, invoice) for part in earlier)
                rows = books.get("pay:" + pid, [])
                if self.inside(payments[pid]["timestamp"]):
                    credit = -net([r for r in rows if r["invoice_id"] == iid], "1200")
                    require(credit == expected, f"{pid} {iid}: AR credit {credit} != {expected}")
                    expected_credits[iid] += expected

        receipts = defaultdict(list)
        for pid, payment in payments.items():
            rows = books.get("pay:" + pid, [])
            require(bool(rows) == self.inside(payment["timestamp"]), f"{pid}: incorrect posting presence")
            if rows and payment["amount_minor"] > 0:
                remaining = payment["amount_minor"] - sum(allocation(payment).values())
                for entity in {r["entity_id"] for r in rows}:
                    receipts[entity, payment["currency"], remaining].append(payment)

        actual_credits = Counter()
        for journal, rows in books.items():
            if journal.startswith("pay:"):
                payment = payments[journal[4:]]
                require(net(rows, "1000") == self.convert(payment["amount_minor"], payment),
                        f"{journal}: wrong cash value")
                amount = payment["amount_minor"]
                if amount < 0:
                    entities = {r["entity_id"] for r in rows}
                    require(len(entities) == 1, f"{journal}: inconsistent refund entity")
                    candidates = receipts[next(iter(entities)), payment["currency"], -amount]
                    earlier = [p for p in candidates if instant(p["timestamp"]) < instant(payment["timestamp"])]
                    require(earlier, f"{journal}: no prior receipt for refund")
                    receipt = max(earlier, key=lambda p: instant(p["timestamp"]))
                    unapplied = self.convert(-amount, receipt)
                else:
                    unapplied = -self.convert(amount - sum(allocation(payment).values()), payment)
                require(net(rows, "2900") == unapplied, f"{journal}: wrong unapplied cash")
                require(all(r["account"] in {"1000", "1200", "2900", "7900"} for r in rows),
                        f"{journal}: wrong payment account")
                for row in rows:
                    if row["account"] == "1200":
                        actual_credits[row["invoice_id"]] += row["credit_minor"] - row["debit_minor"]
            if journal.startswith("inv:"):
                require(journal[4:] in invoices, f"{journal}: missing rebuilt invoice")
        require(actual_credits == expected_credits,
                f"AR movement differs: extra {actual_credits - expected_credits}, "
                f"missing {expected_credits - actual_credits}")

        for iid, invoice in invoices.items():
            rows = books.get("inv:" + iid, [])
            if not self.inside(invoice["issued_at"]):
                require(not rows, f"{iid}: out-of-period invoice booked")
                continue
            amount = self.convert(invoice["total_minor"], invoice)
            debit = [r for r in rows if r["account"] == "1200" and r["debit_minor"] == amount
                     and r["credit_minor"] == 0]
            revenue = [r for r in rows if r["account"] == "4000" and r["credit_minor"] == amount
                       and r["debit_minor"] == 0]
            require(len(debit) == len(revenue) == 1 and
                    instant(debit[0]["timestamp"]) == instant(revenue[0]["timestamp"]) and
                    all(r["entity_id"] == invoice["entity_id"] for r in rows),
                    f"{iid}: wrong invoice booking {[(r['row_id'], r['account']) for r in rows]}")
            if len(rows) == 4 and "credit_note" in self.policy["ledger"]:
                reversal = [r for r in rows if r not in debit + revenue]
                require(len({instant(r["timestamp"]) for r in reversal}) == 1 and
                        instant(reversal[0]["timestamp"]) > instant(debit[0]["timestamp"]) and
                        {(r["account"], r["debit_minor"], r["credit_minor"]) for r in reversal}
                        == {("1200", 0, amount), ("4000", amount, 0)},
                        f"{iid}: invalid reversal")
                require(any(other["entity_id"] == invoice["entity_id"]
                            and other["currency"] == invoice["currency"]
                            and line_items(other) == line_items(invoice)
                            and instant(other["issued_at"]) > instant(invoice["issued_at"])
                            and net(books.get("inv:" + other_id, []), "1200") > 0
                            for other_id, other in invoices.items() if other_id != iid),
                        f"{iid}: missing replacement")
                amount = 0
            else:
                require(len(rows) == 2, f"{iid}: expected a single booking")
            require(net(rows, "1200") - actual_credits[iid] == amount - expected_credits[iid],
                    f"{iid}: ending AR differs")

    def derive(self, injection, books):
        kind = injection["type"]
        changes = injection["changes"]
        if kind == "fx_error" and not changes and injection["scenario"] == "I2":
            # The inserted journal is recorded by the companion cutoff entry.
            companions = [i for i in self.injections if i["scenario"] == "I2" and
                          i["type"] == "period_cutoff"]
            require(len(companions) == 1,
                    "I2 FX has no journal link; the provenance format cannot pair multiple cutoff entries")
            changes = companions[0]["changes"]
        require(len(changes) == 1, f"cannot identify journal from changes {changes}")
        journal = changes[0]["journal"]
        namespace, record_id = journal.split(":", 1)
        rows = self.after[journal]
        if kind == "payment_allocation":
            payment = self.payments[record_id]
            short = []
            for iid, amount in allocation(payment).items():
                invoice = self.invoices[iid]
                posted = -net([r for r in rows if r["invoice_id"] == iid], "1200")
                original = -net([r for r in books[journal] if r["invoice_id"] == iid], "1200")
                if original != posted:
                    require(original == self.convert(amount, invoice), f"{journal} {iid}: baseline differs from ref")
                    short.append((iid, original - posted))
            require(len(short) == 1, f"{journal}: expected one changed allocation, got {short}")
            iid, amount = short[0]
            return {iid, record_id}, amount
        if kind == "fx_error":
            doc = (self.invoices if namespace == "inv" else self.payments)[record_id]
            account = "1200" if namespace == "inv" else "1000"
            amount = self.convert(doc.get("total_minor", doc.get("amount_minor")), doc)
            require(journal not in books or net(books[journal], account) == amount,
                    f"{journal}: pre-error value differs from policy")
            return {record_id}, abs(net(rows, account) - amount)
        invoice = self.invoices[record_id]
        require(journal not in books and all(self.inside(row["timestamp"]) for row in rows),
                f"{journal}: expected a new in-period booking")
        if kind == "period_cutoff":
            require(not self.inside(invoice["issued_at"]), f"{journal}: invoice issued in period")
            return {record_id}, net(rows, "1200")
        require(kind == "duplicate_invoice" and invoice["doc_id"] in injection["documents_added"],
                f"{journal}: unknown issue or missing inserted document")
        original = [iid for iid, doc in self.invoices.items()
                    if doc["entity_id"] == invoice["entity_id"] and doc["currency"] == invoice["currency"]
                    and doc["total_minor"] == invoice["total_minor"]
                    and line_items(doc) == line_items(invoice)
                    and instant(doc["issued_at"]) < instant(invoice["issued_at"])
                    and net(books.get("inv:" + iid, []), "1200") > 0]
        require(len(original) == 1, f"{journal}: possible originals {original}")
        return {original[0], record_id}, net(rows, "1200")

    def evidence_amount(self, kind, affected, ids):
        invoices = [self.invoices[i] for i in affected if i in self.invoices]
        payments = [self.payments[p] for p in affected if p in self.payments]
        docs = invoices + payments
        if any(d["doc_id"] not in ids for d in docs):
            return None
        rows = [self.rows[rid] for rid in ids if rid in self.rows]

        def booking(invoice):
            amounts = {r["debit_minor"] or r["credit_minor"] for r in rows
                       if r["invoice_id"] == invoice["invoice_id"] and r["payment_id"] is None
                       and self.inside(r["timestamp"]) and
                       ((r["account"] == "1200" and r["debit_minor"] > 0) or
                        (r["account"] == "4000" and r["credit_minor"] > 0))}
            return next(iter(amounts)) if len(amounts) == 1 else None

        if kind == "duplicate_invoice":
            earlier, later = sorted(invoices, key=lambda d: instant(d["issued_at"]))
            if earlier["entity_id"] == later["entity_id"] and earlier["currency"] == later["currency"] and \
                    line_items(earlier) == line_items(later) and booking(earlier) is not None:
                return booking(later)
            return None
        if kind == "period_cutoff":
            return booking(invoices[0]) if not self.inside(invoices[0]["issued_at"]) else None
        doc = invoices[0] if invoices else payments[0]
        if doc["currency"] != self.base and self.fx_id(doc) not in ids:
            return None
        if kind == "fx_error":
            posted = booking(doc) if invoices else next(
                (r["debit_minor"] - r["credit_minor"] for r in rows
                 if r["payment_id"] == doc["payment_id"] and r["account"] == "1000"), None)
            if posted is None:
                return None
            return abs(posted - self.convert(doc.get("total_minor", doc.get("amount_minor")), doc))
        payment = payments[0]
        relevant = [r for r in rows if r["payment_id"] == payment["payment_id"]]
        ar = [r for r in relevant if r["account"] == "1200" and r["invoice_id"] == doc["invoice_id"]]
        if ar:
            posted = -net(ar, "1200")
        elif "every ledger row of the payment" in self.policy["findings"]["evidence"]:
            # Completeness is checked against the public journal's row IDs.
            # The amount is computed exclusively from the cited records.
            journal = self.after["pay:" + payment["payment_id"]]
            if {r["row_id"] for r in relevant} != {r["row_id"] for r in journal}:
                return None
            if net(relevant, "1000") <= 0 or net(relevant, "2900") >= 0 or sum(
                    r["debit_minor"] - r["credit_minor"] for r in relevant) != 0:
                return None
            posted = 0
        else:
            return None
        return self.convert(allocation(payment)[doc["invoice_id"]], doc) - posted

    def compare(self, books):
        issues = {t["issue_id"]: t for t in self.truth}
        require(len(issues) == len(self.truth) == len(self.injections) and
                set(issues) == {i["issue_id"] for i in self.injections}, "truth/provenance issue IDs differ")
        for injection in self.injections:
            truth = issues[injection["issue_id"]]
            try:
                ids, amount = self.derive(injection, books)
                expected = (injection["type"], injection["scenario"], ids, amount, self.base)
                actual = (truth["type"], truth["scenario"], set(truth["affected_ids"]),
                          truth["expected_amount_minor"], truth["currency"])
                require(amount > 0 and expected == actual, f"derived {expected}; truth {actual}")
            except (ValueError, KeyError) as exc:
                raise ValueError(f"{truth['issue_id']} {truth['affected_ids']}: {exc}") from exc

    def evidence(self):
        docs = list(self.invoices.values()) + list(self.payments.values())
        public = self.rows.keys() | self.rates.keys() | {d["doc_id"] for d in docs}
        for truth in self.truth:
            affected = truth["affected_ids"]
            require(any(set(ids) <= public and
                        self.evidence_amount(truth["type"], affected, set(ids)) == truth["expected_amount_minor"]
                        for ids in truth["evidence_sets"]),
                    f"{truth['issue_id']} {affected}: no sufficient evidence set {truth['evidence_sets']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="72000-72099")
    parser.add_argument("--scenario", choices=("default", *SCENARIOS))
    parser.add_argument("--difficulty", choices=("default", "hard"))
    args = parser.parse_args()
    first, _, last = args.seeds.partition("-")
    cohorts = {"default": {}, **SCENARIOS}
    conditions = ("rebuilt", "discrepancy", "evidence")
    failed = False
    scratch = Path("/tmp/r23-codex2")
    scratch.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=scratch) as directory:
        root = Path(directory) / "episode"
        print("| Scenario | Difficulty | Rebuilt | Discrepancy | Evidence |", flush=True)
        print("|---|---|---:|---:|---:|", flush=True)
        for scenario, config in cohorts.items():
            if args.scenario and scenario != args.scenario:
                continue
            for difficulty in ("default", "hard"):
                if args.difficulty and difficulty != args.difficulty:
                    continue
                counts = Counter()
                for seed in range(int(first), int(last or first) + 1):
                    label = f"seed={seed} {scenario} {difficulty}"
                    try:
                        generate_episode(seed, {**config, "difficulty": difficulty}, str(root))
                        episode = Episode(root)
                        books, removed = episode.rewind()
                    except (ValueError, KeyError) as exc:
                        print(f"FAIL {label} setup: {exc}", flush=True)
                        failed = True
                        continue
                    checks = (lambda: episode.clean(books, removed), lambda: episode.compare(books), episode.evidence)
                    for condition, check in zip(conditions, checks):
                        try:
                            check()
                            counts[condition] += 1
                        except (ValueError, KeyError) as exc:
                            print(f"FAIL {label} {condition}: {exc}", flush=True)
                            failed = True
                total = int(last or first) - int(first) + 1
                cells = " | ".join(f"{counts[c]}/{total}" for c in conditions)
                print(f"| {scenario} | {difficulty} | {cells} |", flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
