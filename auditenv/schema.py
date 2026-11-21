"""Findings schema: structural validation and normalisation (CONTRACT §5, §6).

Structural (the whole submission is invalid, reward -1): a value of the wrong JSON type, a missing required field,
an unknown key, or a limit exceeded (31+ findings, 11+ evidence ids before dedupe, explanation over 1000 code points).
Anything else -- an unknown type string, a wrong id, currency, amount or evidence -- is a structurally valid finding
that simply does not match (a false positive, `matcher.py`).
"""

from __future__ import annotations

# The four documented issue / finding types. A finding with any other string type is valid but never matches.
ISSUE_TYPES: tuple[str, ...] = (
    "duplicate_invoice",
    "payment_allocation",
    "fx_error",
    "period_cutoff",
)

MAX_FINDINGS = 30
MAX_EVIDENCE = 10
MAX_EXPLANATION = 1000

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
_REQUIRED = ("type", "affected_ids", "claimed_amount_minor", "currency", "evidence_ids")


def normalize_finding(f: dict) -> dict:
    """Return a normalised copy of a validated finding.

    Strings are kept exactly (no strip, no case change). ``affected_ids`` and ``evidence_ids`` are sets: duplicates
    are dropped and they are returned sorted, so the representation is deterministic; compare them as sets.
    """
    return {
        "type": f["type"],
        "affected_ids": sorted(set(f["affected_ids"])),
        "claimed_amount_minor": f["claimed_amount_minor"],
        "currency": f["currency"],
        "evidence_ids": sorted(set(f["evidence_ids"])),
        "explanation": f.get("explanation", ""),
    }


def validate_findings(obj: object, episode_id: str) -> str | None:
    """Validate a findings submission object.

    Returns ``None`` if valid, otherwise a short error message string. Never raises: anything the checks
    below do not anticipate (exotic in-process objects) is an invalid submission, not a crash.
    """
    try:
        return _validate(obj, episode_id)
    except Exception:
        return "malformed findings"


def _validate(obj: object, episode_id: str) -> str | None:

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
    """Validate the structure of a single finding dict.  Returns error message or None."""

    if not isinstance(f, dict):
        return f"finding[{index}] is not a dict"

    # Extra unknown keys → invalid.
    extra = set(f.keys()) - _FINDING_KEYS
    if extra:
        return f"finding[{index}] has unknown keys: {sorted(map(str, extra))[:5]}"
    missing = [k for k in _REQUIRED if k not in f]
    if missing:
        return f"finding[{index}] is missing required keys: {missing}"

    for key in ("type", "currency"):
        if not isinstance(f[key], str):
            return f"finding[{index}].{key}: must be a string"

    # --- claimed_amount_minor: a JSON integer (1234.0 parses as a float), never a bool ---
    amount = f["claimed_amount_minor"]
    if isinstance(amount, bool) or not isinstance(amount, int):
        return f"finding[{index}].claimed_amount_minor: must be int, got {type(amount).__name__}"

    # --- id lists: the evidence limit applies to the raw list, before duplicates are dropped ---
    for key in ("affected_ids", "evidence_ids"):
        ids = f[key]
        if not isinstance(ids, list):
            return f"finding[{index}].{key}: must be a list"
        for j, item in enumerate(ids):
            if not isinstance(item, str):
                return f"finding[{index}].{key}[{j}]: must be a string"
    if len(f["evidence_ids"]) > MAX_EVIDENCE:
        return (
            f"finding[{index}].evidence_ids: too many ({len(f['evidence_ids'])} > {MAX_EVIDENCE})"
        )

    # --- explanation (optional): length in code points ---
    explanation = f.get("explanation", "")
    if not isinstance(explanation, str):
        return f"finding[{index}].explanation: must be a string"
    if len(explanation) > MAX_EXPLANATION:
        return (
            f"finding[{index}].explanation: too long ({len(explanation)} > {MAX_EXPLANATION})"
        )

    return None
