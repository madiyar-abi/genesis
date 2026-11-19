"""Reconciliation baseline that treats common accounting shortcuts as rules."""

from collections import defaultdict
from collections.abc import Iterator
from itertools import islice

from ..money import convert
from ..schema import MAX_FINDINGS

_TABLES = ("ledger", "invoices", "payments", "fx")


def _findings(manifest: dict, tables: dict[str, list[dict]]) -> Iterator[dict]:
    base = manifest["base_currency"]
    start = manifest["period_start"]
    end = manifest["period_end"]
    receivables = {}
    unapplied_credits = defaultdict(list)
    for row in tables["ledger"]:
        if row["account"] == "1200" and row["payment_id"] is None and row["debit_minor"] > 0:
            receivables[row["invoice_id"]] = row
        elif row["account"] == "2900" and row["credit_minor"] > 0:
            unapplied_credits[row["payment_id"]].append(row)

    rates = {
        (row["date"], row["source_currency"]): row["rate"]
        for row in tables["fx"] if row["target_currency"] == base
    }

    def finding(kind, ids, amount, evidence):
        return {
            "type": kind,
            "affected_ids": sorted(ids),
            "claimed_amount_minor": amount,
            "currency": base,
            "evidence_ids": evidence,
        }

    first_by_amount = {}
    invoices = sorted(
        tables["invoices"], key=lambda invoice: (invoice["issued_at"], invoice["invoice_id"]),
    )
    for invoice in invoices:
        invoice_id = invoice["invoice_id"]
        row = receivables.get(invoice_id)
        if row is None:
            continue

        currency = invoice["currency"]
        total = invoice["total_minor"]
        debit = row["debit_minor"]
        group = (invoice["entity_id"], currency, total)
        first = first_by_amount.setdefault(group, invoice)
        if first is not invoice:
            first_row = receivables.get(first["invoice_id"])
            evidence = [first["doc_id"], invoice["doc_id"]]
            if first_row:
                evidence.append(first_row["row_id"])
            evidence.append(row["row_id"])
            yield finding(
                "duplicate_invoice", [first["invoice_id"], invoice_id], debit,
                evidence,
            )

        written_date = invoice["issued_at"][:10]
        evidence = [invoice["doc_id"], row["row_id"]]
        if not start <= written_date <= end and start <= row["timestamp"][:10] <= end:
            yield finding("period_cutoff", [invoice_id], debit, evidence)

        rate = rates.get((written_date, currency))
        if currency != base and rate is not None:
            discrepancy = abs(debit - convert(total, currency, base, rate))
            if discrepancy:
                yield finding("fx_error", [invoice_id], discrepancy, evidence + [f"{written_date}:{currency}:{base}"])

    docs = {invoice["invoice_id"]: invoice["doc_id"] for invoice in tables["invoices"]}
    for payment in tables["payments"]:
        refs = payment["invoice_refs"]
        if refs:
            payment_id = payment["payment_id"]
            for row in unapplied_credits.get(payment_id, ()):
                yield finding(
                    "payment_allocation", [refs[0]["invoice_id"], payment_id],
                    row["credit_minor"],
                    [payment["doc_id"], docs.get(refs[0]["invoice_id"], payment["doc_id"]), row["row_id"]],
                )


class NaiveReconcile:
    name = "naive_reconcile"

    def __init__(self, seed: int = 0):
        pass

    def reset(self, first_observation: dict) -> None:
        self._manifest = first_observation["manifest"]
        self._tables = {name: [] for name in _TABLES}
        self._table_index = 0

    def act(self, observation: dict) -> dict:
        result = observation.get("result") or {}
        cursor = None
        if "rows" in result:
            self._tables[_TABLES[self._table_index]].extend(result["rows"])
            cursor = result["next_cursor"]
            if cursor is None:
                self._table_index += 1
        elif observation.get("error"):
            self._table_index += 1

        if self._table_index == len(_TABLES) or observation["steps_remaining"] <= 1:
            findings = _findings(self._manifest, self._tables)
            return {
                "type": "submit",
                "findings": {
                    "episode_id": self._manifest["episode_id"],
                    "findings": list(islice(findings, MAX_FINDINGS)),
                },
            }

        return {
            "type": "list_records", "table": _TABLES[self._table_index],
            "cursor": cursor, "limit": 50,
        }
