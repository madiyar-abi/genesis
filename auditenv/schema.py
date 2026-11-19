"""Findings schema: validation and normalisation (CONTRACT §5, §6)."""

from __future__ import annotations

import re

# The four issue / finding types.
ISSUE_TYPES: tuple[str, ...] = (
    "duplicate_invoice",
    "payment_allocation",
    "fx_error",
    "period_cutoff",
)

MAX_FINDINGS = 30
MAX_EVIDENCE = 10
MAX_EXPLANATION = 1000
MAX_AFFECTED = 10

# ---------------------------------------------------------------------------
# Keys allowed inside a single finding dict.
# ---------------------------------------------------------------------------
_FINDING_KEYS = frozenset(
    {
        "type",
        "affected_ids",
        "claimed_amount_minor",
        "currency",
        "evidence_ids",
        "explanation",
    }
)


def normalize_finding(f: dict) -> dict:
    """Return a normalised copy of a single finding dict.

    * Strip leading/trailing whitespace from string id fields.
    * Dedupe + sort ``affected_ids`` and ``evidence_ids``.
    * Uppercase ``currency``.
    """
    result: dict = {}

    # type — keep as-is (string).
    result["type"] = f.get("type")

    # affected_ids — strip, dedupe, sort.
    raw_affected = f.get("affected_ids")
    if isinstance(raw_affected, list):
        seen: set[str] = set()
        deduped: list[str] = []
        for item in raw_affected:
            s = str(item).strip() if not isinstance(item, str) else item.strip()
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        result["affected_ids"] = sorted(deduped)
    else:
        result["affected_ids"] = raw_affected

    # claimed_amount_minor — keep as-is.
    result["claimed_amount_minor"] = f.get("claimed_amount_minor")

    # currency — uppercase.
    cur = f.get("currency")
    if isinstance(cur, str):
        result["currency"] = cur.upper()
    else:
        result["currency"] = cur

    # evidence_ids — strip, sort, dedupe.
    raw_evidence = f.get("evidence_ids")
    if isinstance(raw_evidence, list):
        seen_e: set[str] = set()
        deduped_e: list[str] = []
        for item in raw_evidence:
            s = str(item).strip() if not isinstance(item, str) else item.strip()
            if s not in seen_e:
                seen_e.add(s)
                deduped_e.append(s)
        result["evidence_ids"] = sorted(deduped_e)
    else:
        result["evidence_ids"] = raw_evidence

    # explanation — keep as-is (optional, default "").
    result["explanation"] = f.get("explanation", "")

    return result


def validate_findings(obj: object, episode_id: str) -> str | None:
    """Validate a findings submission object.

    Returns ``None`` if valid, otherwise a short error message string.
    """

    if not isinstance(obj, dict):
        return "findings object must be a dict"
    extra_top = set(obj) - {"episode_id", "findings"}
    if extra_top:
        return f"unknown top-level keys: {sorted(map(str, extra_top))[:5]}"

    # --- episode_id ---
    if obj.get("episode_id") != episode_id:
        return (
            f"episode_id mismatch: expected {episode_id!r}, "
            f"got {obj.get('episode_id')!r}"
        )

    # --- findings list ---
    findings = obj.get("findings")
    if not isinstance(findings, list):
        return "findings must be a list"

    if len(findings) > MAX_FINDINGS:
        return f"too many findings: {len(findings)} > {MAX_FINDINGS}"

    for i, f in enumerate(findings):
        err = _validate_one(f, i)
        if err is not None:
            return err

    return None


def _validate_one(f: object, index: int) -> str | None:
    """Validate a single finding dict.  Returns error message or None."""

    if not isinstance(f, dict):
        return f"finding[{index}] is not a dict"

    # Extra unknown keys → invalid.
    extra = set(f.keys()) - _FINDING_KEYS
    if extra:
        return f"finding[{index}] has unknown keys: {sorted(extra)}"

    # --- type ---
    ftype = f.get("type")
    if ftype not in ISSUE_TYPES:
        return f"finding[{index}].type: unknown type {ftype!r}"

    # --- affected_ids ---
    affected = f.get("affected_ids")
    if not isinstance(affected, list) or len(affected) == 0:
        return f"finding[{index}].affected_ids must be a non-empty list"
    if len(affected) > MAX_AFFECTED:
        return (
            f"finding[{index}].affected_ids: too many ({len(affected)} > {MAX_AFFECTED})"
        )
    for j, aid in enumerate(affected):
        if not isinstance(aid, str) or len(aid.strip()) == 0:
            return f"finding[{index}].affected_ids[{j}]: must be a non-empty string"

    # --- claimed_amount_minor ---
    amount = f.get("claimed_amount_minor")
    # Must be int (not bool) and >= 0.
    if isinstance(amount, bool) or not isinstance(amount, int):
        return f"finding[{index}].claimed_amount_minor: must be int, got {type(amount).__name__}"
    if amount < 0:
        return f"finding[{index}].claimed_amount_minor: must be >= 0"

    # --- currency ---
    currency = f.get("currency")
    if not isinstance(currency, str):
        return f"finding[{index}].currency: must be a string"
    if not re.fullmatch(r"[A-Z]{3}", currency):
        return f"finding[{index}].currency: must be 3 uppercase letters, got {currency!r}"

    # --- evidence_ids ---
    evidence = f.get("evidence_ids")
    if not isinstance(evidence, list):
        return f"finding[{index}].evidence_ids: must be a list"
    if len(evidence) > MAX_EVIDENCE:
        return (
            f"finding[{index}].evidence_ids: too many ({len(evidence)} > {MAX_EVIDENCE})"
        )
    for j, eid in enumerate(evidence):
        if not isinstance(eid, str) or len(eid.strip()) == 0:
            return f"finding[{index}].evidence_ids[{j}]: must be a non-empty string"

    # --- explanation (optional, default "") ---
    explanation = f.get("explanation", "")
    if not isinstance(explanation, str):
        return f"finding[{index}].explanation: must be a string"
    if len(explanation) > MAX_EXPLANATION:
        return (
            f"finding[{index}].explanation: too long ({len(explanation)} > {MAX_EXPLANATION})"
        )

    return None
