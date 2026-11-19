"""Load exported episodes back from disk (inverse of export.py).

Usage:
    from auditenv.load import load_episode
    ep = load_episode("episodes/dev/ep_34a13a83cba2")

Returns: {episode_id, manifest, policy, tables, truth, provenance}
(same keys as generate() minus "task").

Conversion rules:
- CSV empty cell → None
- debit_minor, credit_minor (ledger) → int
- rate (fx) stays a string
- JSONL records: parsed with json.loads, types preserved from JSON
"""

from __future__ import annotations

import csv
import json
import os

from .generator import FX_FIELDS, LEDGER_FIELDS


# Ledger fields that are integers in the generated episode
_LEDGER_INT_FIELDS = {"debit_minor", "credit_minor"}

# Ledger fields that can be null (empty string in CSV → None)
_LEDGER_NULLABLE = {"entity_id", "invoice_id", "payment_id"}


def _read_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _read_csv(path: str, fields: tuple[str, ...], int_fields: set[str],
              nullable: set[str]) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            parsed: dict = {}
            for f in fields:
                val = row[f]
                if f in int_fields:
                    parsed[f] = int(val)
                elif f in nullable and val == "":
                    parsed[f] = None
                else:
                    parsed[f] = val
            rows.append(parsed)
    return rows


def load_episode(path: str) -> dict:
    """Load an exported episode directory back into the generate() format (minus 'task').

    Args:
        path: Path to the episode directory (e.g. "episodes/dev/ep_34a13a83cba2")
              containing public/ and grader/ subdirectories.

    Returns:
        dict with keys: episode_id, manifest, policy, tables, truth, provenance
    """
    pub_dir = os.path.join(path, "public")
    grd_dir = os.path.join(path, "grader")

    manifest = _read_json(os.path.join(pub_dir, "manifest.json"))
    policy = _read_json(os.path.join(pub_dir, "policy.json"))

    ledger = _read_csv(
        os.path.join(pub_dir, "ledger.csv"),
        LEDGER_FIELDS,
        _LEDGER_INT_FIELDS,
        _LEDGER_NULLABLE,
    )

    invoices = _read_jsonl(os.path.join(pub_dir, "invoices.jsonl"))
    payments = _read_jsonl(os.path.join(pub_dir, "payments.jsonl"))

    fx = _read_csv(
        os.path.join(pub_dir, "fx.csv"),
        FX_FIELDS,
        set(),  # no int fields in fx
        set(),  # no nullable fields in fx
    )

    truth = _read_json(os.path.join(grd_dir, "truth.json"))
    provenance = _read_json(os.path.join(grd_dir, "provenance.json"))

    tables = {
        "ledger": ledger,
        "invoices": invoices,
        "payments": payments,
        "fx": fx,
    }

    return {
        "episode_id": manifest["episode_id"],
        "manifest": manifest,
        "policy": policy,
        "tables": tables,
        "truth": truth,
        "provenance": provenance,
    }
