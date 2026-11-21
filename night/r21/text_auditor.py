"""Apply the published task and accounting policy to the public exports.

The audit never receives the grader-side records. On disagreement, individually
score the candidate findings to identify rejected candidates. The score reveals
the count of omissions, but cannot identify their records.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory

from auditenv.jury import SCENARIOS
from judge_adapter import generate_episode, score_episode


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(public, filename):
    with (public / filename).open(encoding="utf-8", newline="") as stream:
        if filename.endswith(".jsonl"):
            return [json.loads(line) for line in stream]
        return list(csv.DictReader(stream))


class PublicBooks:
    def __init__(self, public):
        self.task = (public / "task.txt").read_text(encoding="utf-8")
        self.policy = read_json(public / "policy.json")
        manifest = read_json(public / "manifest.json")
        self.episode_id = manifest["episode_id"]
        self.base = self.policy["base_currency"]
        self.exponents = manifest["amount_exponents"]
        self.timezone = datetime.fromisoformat("2000-01-01T00:00:00" + self.policy["timezone"]).tzinfo
        self.invoices = {row["invoice_id"]: row for row in read_rows(public, "invoices.jsonl")}
        self.payments = read_rows(public, "payments.jsonl")
        self.fx = {(row["date"], row["source_currency"], row["target_currency"]): row
                   for row in read_rows(public, "fx.csv")}
        self.ledger = read_rows(public, "ledger.csv")
        self.invoice_rows = defaultdict(list)
        self.payment_rows = defaultdict(list)
        for row in self.ledger:
            for field in ("debit_minor", "credit_minor"):
                row[field] = int(row[field])
            if row["payment_id"]:
                self.payment_rows[row["payment_id"]].append(row)
            elif row["invoice_id"]:
                self.invoice_rows[row["invoice_id"]].append(row)

    def date(self, timestamp):
        return datetime.fromisoformat(timestamp).astimezone(self.timezone).date().isoformat()

    def in_period(self, timestamp):
        period = self.policy["period"]
        return period["start"] <= self.date(timestamp) <= period["end"]

    def convert(self, amount, currency, timestamp):
        if currency == self.base:
            return amount, []
        row = self.fx[self.date(timestamp), currency, self.base]
        shift = self.exponents[self.base] - self.exponents[currency]
        converted = (Decimal(amount) * Decimal(row["rate"])).scaleb(shift)
        return int(converted.to_integral_value(rounding=ROUND_HALF_UP)), [row["fx_id"]]

    def audit(self):
        findings = []

        def report(kind, ids, amount, evidence):
            if kind in self.task and amount > 0:
                findings.append({"type": kind, "affected_ids": ids, "claimed_amount_minor": amount,
                                 "currency": self.base, "evidence_ids": evidence})

        identical = defaultdict(list)
        for invoice_id, invoice in sorted(self.invoices.items(),
                                          key=lambda item: datetime.fromisoformat(item[1]["issued_at"])):
            rows = self.invoice_rows[invoice_id]
            booking = next((r for r in rows if r["account"] == "1200" and r["debit_minor"]), None)
            if booking is None:
                continue
            doc = [invoice["doc_id"], booking["row_id"]]
            posted = booking["debit_minor"]
            if not self.in_period(invoice["issued_at"]):
                report("period_cutoff", [invoice_id], posted, doc)
            expected, fx = self.convert(invoice["total_minor"], invoice["currency"], invoice["issued_at"])
            if fx:
                report("fx_error", [invoice_id], abs(posted - expected), doc + fx)
            if "credit_note" in self.policy["ledger"] and any(
                row["account"] == "1200" and row["credit_minor"] == posted for row in rows
            ):
                continue
            # Hard-mode task text explicitly allows case, punctuation and
            # line order changes when an invoice is keyed in again.
            lines = []
            for line in invoice["line_items"]:
                if "may be re-typed" in self.task:
                    line = {**line, "description": re.sub(r"[^0-9a-z]", "", line["description"].lower())}
                lines.append(json.dumps(line, sort_keys=True))
            lines = tuple(sorted(lines))
            identity = invoice["entity_id"], invoice["currency"], lines
            for earlier_id, earlier_doc in identical[identity]:
                report("duplicate_invoice", [earlier_id, invoice_id], posted, earlier_doc + doc)
            identical[identity].append((invoice_id, doc))

        for payment in self.payments:
            payment_id = payment["payment_id"]
            rows = self.payment_rows[payment_id]
            if not rows:
                continue
            cash = next(row for row in rows if row["account"] == "1000")
            expected, fx = self.convert(abs(payment["amount_minor"]), payment["currency"], payment["timestamp"])
            if fx:
                report("fx_error", [payment_id], abs(cash["debit_minor"] + cash["credit_minor"] - expected),
                       [payment["doc_id"], cash["row_id"]] + fx)
            for ref in payment["invoice_refs"] or []:
                invoice_id = ref["invoice_id"]
                invoice = self.invoices[invoice_id]
                expected, fx = self.convert(ref["amount_minor"], invoice["currency"], invoice["issued_at"])
                credits = [row for row in rows if row["account"] == "1200" and
                           row["invoice_id"] == invoice_id and row["credit_minor"]]
                posted = sum(row["credit_minor"] for row in credits)
                evidence_rows = credits or [row for row in rows if row["account"] == "2900"]
                if evidence_rows:
                    report("payment_allocation", [invoice_id, payment_id], expected - posted,
                           [payment["doc_id"], invoice["doc_id"], evidence_rows[0]["row_id"]] + fx)
        return {"episode_id": self.episode_id, "findings": findings}


def classify(books, finding):
    if finding["type"] == "duplicate_invoice":
        original = finding["affected_ids"][0]
        if any(row["account"] == "1200" and row["credit_minor"] for row in books.invoice_rows[original]):
            return "(a) full reversal was not recognized by the duplicate rule"
    return "(c) the public rule produces this finding with the listed amount and evidence"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="40000-40099")
    args = parser.parse_args()
    lo, hi = map(int, args.seeds.split("-"))
    print("| Config | Difficulty | Scored | Mean F1 | Mean precision | Mean recall |")
    print("|---|---|---:|---:|---:|---:|")
    discrepancies = []
    for name, config in {"baseline": {}, **SCENARIOS}.items():
        for difficulty in ("default", "hard"):
            scores = []
            for seed in range(lo, hi + 1):
                label = f"{name}/{difficulty} seed {seed}"
                try:
                    with TemporaryDirectory(dir="/tmp/r21-codex1") as scratch:
                        episode = str(Path(scratch) / "episode")
                        generate_episode(seed, {**config, "difficulty": difficulty}, episode)
                        books = PublicBooks(Path(episode) / "public")
                        answer = books.audit()
                        score = score_episode(episode, answer, 0)
                        if score["f1"] is None:
                            raise ValueError("grader rejected the findings structure")
                        scores.append(score)
                        if score["f1"] == 1:
                            continue
                        for finding in answer["findings"]:
                            single = {**answer, "findings": [finding]}
                            if score_episode(episode, single, 0)["fp"]:
                                discrepancies.append(f"- {label} extra {json.dumps(finding)} {classify(books, finding)}")
                        if score["fn"]:
                            discrepancies.append(
                                f"- {label} missed {score['fn']} unresolved. Aggregate score gives no record IDs."
                            )
                except (OSError, ValueError, KeyError, StopIteration) as error:
                    discrepancies.append(f"- {label} (a) audit failed: {type(error).__name__}: {error}")
            averages = [mean(s[key] for s in scores) if scores else float("nan")
                        for key in ("f1", "precision", "recall")]
            print(f"| {name} | {difficulty} | {len(scores)} | "
                  + " | ".join(f"{value:.6f}" for value in averages) + " |", flush=True)
    print(f"\nDiscrepancy entries: {len(discrepancies)}")
    print("\n".join(discrepancies))


if __name__ == "__main__":
    main()
