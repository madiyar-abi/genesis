"""Benign transformation for paired checks: relabel every id and permute row order.
The underlying company, the errors and the oracle answer (under the new ids) are unchanged."""

from __future__ import annotations

import copy
import random
import re

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]*")

ID_FIELDS = {
    "ledger": ("row_id",),
    "invoices": ("doc_id", "invoice_id", "entity_id"),
    "payments": ("doc_id", "payment_id"),
}
PREFIX = {"row_id": "T", "doc_id": "DX", "invoice_id": "IV", "payment_id": "PM", "entity_id": "EN"}


def _remap(obj, mapping):
    if isinstance(obj, dict):
        return {k: _remap(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_remap(v, mapping) for v in obj]
    if isinstance(obj, str):
        if obj in mapping:
            return mapping[obj]
        if obj[:4] in ("inv:", "pay:") and obj[4:] in mapping:  # provenance journal keys
            return obj[:4] + mapping[obj[4:]]
        if " " in obj:  # free text (provenance descriptions): remap whole id-like tokens
            return _TOKEN.sub(lambda m: mapping.get(m.group(0), m.group(0)), obj)
    return obj


def transform(episode: dict, transform_seed: int) -> dict:
    rng = random.Random(f"transform|{transform_seed}|{episode['episode_id']}")
    t = episode["tables"]
    originals = []
    for table, fields in ID_FIELDS.items():
        for rec in t[table]:
            originals += [(f, rec[f]) for f in fields if rec[f] is not None]
    for rec in t["ledger"]:
        originals += [(f, rec[f]) for f in ("entity_id",) if rec[f] is not None]
    mapping, used = {}, set()
    for field, old in originals:
        if old in mapping:
            continue
        while True:
            new = f"{PREFIX[field]}{rng.randrange(16**7):07x}".upper()
            if new not in used:
                used.add(new)
                mapping[old] = new
                break
    out = copy.deepcopy(episode)
    out["tables"] = _remap(t, mapping)
    for table in ("ledger", "invoices", "payments"):
        rng.shuffle(out["tables"][table])
    truth = _remap(episode["truth"], mapping)
    for iss in truth["issues"]:
        iss["affected_ids"] = sorted(iss["affected_ids"])
        iss["evidence_sets"] = [sorted(s) for s in iss["evidence_sets"]]
    out["truth"] = truth
    out["provenance"] = _remap(episode["provenance"], mapping)
    out["provenance"]["transform_seed"] = transform_seed
    return out
