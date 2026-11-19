"""Seeded exploratory policy using identifiers seen in public records."""

import random

from auditenv.schema import ISSUE_TYPES

_ID_FIELDS = {
    "ledger": "row_id",
    "invoices": "invoice_id",
    "payments": "payment_id",
    "fx": "fx_id",
}


class RandomExplorer:
    name = "random_explorer"

    def __init__(self, seed: int = 0):
        self.seed = seed

    def reset(self, first_observation: dict) -> None:
        self._rng = random.Random(self.seed)
        manifest = first_observation["manifest"]
        self._episode_id = manifest["episode_id"]
        self._currency = manifest["base_currency"]
        self._target_steps = self._rng.randint(20, 40)
        self._inspections = 0
        self._records = {}
        self._documents = {}
        self._table = None
        self._cursors = {}

    def act(self, observation: dict) -> dict:
        result = observation.get("result") or {}
        if self._table is not None:
            if "rows" in result:
                self._cursors[self._table] = result["next_cursor"]
                for row in result["rows"]:
                    self._remember(self._table, row)
            elif "record" in result:
                self._remember(self._table, result["record"])

        if self._inspections >= self._target_steps or observation["steps_remaining"] <= 1:
            return self._submit()

        actions = ["list_records"]
        if self._records:
            actions.append("get_record")
        if self._documents:
            actions.append("get_document")
        action = self._rng.choice(actions)
        self._inspections += 1
        if action == "list_records":
            self._table = self._rng.choice(tuple(_ID_FIELDS))
            return {
                "type": action, "table": self._table,
                "cursor": self._cursors.get(self._table), "limit": 50,
            }
        if action == "get_record":
            self._table, record_id = self._rng.choice(tuple(self._records))
            return {"type": action, "table": self._table, "id": record_id}
        self._table = None
        return {"type": action, "doc_id": self._rng.choice(tuple(self._documents))}

    def _remember(self, table: str, row: dict) -> None:
        self._records[table, row[_ID_FIELDS[table]]] = row
        if "doc_id" in row:
            self._documents[row["doc_id"]] = None

    def _submit(self) -> dict:
        records = tuple(self._records.items())
        count = min(len(records), self._rng.randint(0, 3))
        findings = []
        for (_, record_id), row in self._rng.sample(records, count):
            evidence_id = row.get("doc_id") or row.get("row_id")
            findings.append({
                "type": self._rng.choice(ISSUE_TYPES),
                "affected_ids": [record_id],
                "claimed_amount_minor": self._rng.randint(0, 100_000),
                "currency": self._currency,
                "evidence_ids": [evidence_id] if evidence_id else [],
            })
        return {
            "type": "submit",
            "findings": {"episode_id": self._episode_id, "findings": findings},
        }
