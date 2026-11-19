"""Naive baseline that submits the same issue types for every document."""

from auditenv.schema import ISSUE_TYPES, MAX_FINDINGS

_TABLES = ("invoices", "payments")
_FIELDS = {
    "invoices": ("invoice_id", "total_minor"),
    "payments": ("payment_id", "amount_minor"),
}


class FlagAll:
    name = "flag_all"

    def __init__(self, seed: int = 0):
        pass

    def reset(self, first_observation: dict) -> None:
        manifest = first_observation["manifest"]
        self._episode_id = manifest["episode_id"]
        self._currency = manifest["base_currency"]
        self._table_index = 0
        self._findings = []

    def act(self, observation: dict) -> dict:
        result = observation.get("result") or {}
        cursor = None
        if "rows" in result:
            self._add_findings(_TABLES[self._table_index], result["rows"])
            cursor = result["next_cursor"]
            if cursor is None:
                self._table_index += 1
        elif observation.get("error"):
            self._table_index += 1

        if self._table_index == len(_TABLES) or observation["steps_remaining"] <= 1:
            return {
                "type": "submit",
                "findings": {
                    "episode_id": self._episode_id, "findings": self._findings,
                },
            }
        return {
            "type": "list_records", "table": _TABLES[self._table_index],
            "cursor": cursor, "limit": 50,
        }

    def _add_findings(self, table: str, rows: list[dict]) -> None:
        id_field, amount_field = _FIELDS[table]
        for row in rows:
            for issue_type in ISSUE_TYPES:
                if len(self._findings) == MAX_FINDINGS:
                    return
                self._findings.append({
                    "type": issue_type,
                    "affected_ids": [row[id_field]],
                    "claimed_amount_minor": abs(row[amount_field]),
                    "currency": self._currency,
                    "evidence_ids": [row["doc_id"]],
                })
