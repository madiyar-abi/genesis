"""Shared matcher and terminal reward (CONTRACT §6). Published on purpose: normalisation,
tolerance and the tie rule for ambiguous matches are all in this file.

- normalisation: `schema.normalize_finding` (strip ids, dedupe+sort, uppercase currency)
- tolerance: abs(claimed - expected) <= max(1, expected // 1000)
- one-to-one, greedy in submission order: a finding takes the first still-unmatched truth issue
  (truth order) it fully satisfies; repeats and non-matching findings are false positives.
"""

from __future__ import annotations

from .metrics import prf1, terminal_reward
from .schema import normalize_finding, validate_findings


def tolerance(expected_minor: int) -> int:
    return max(1, expected_minor // 1000)


def _checks(f: dict, issue: dict) -> dict:
    return {
        "type": f["type"] == issue["type"],
        "ids": f["affected_ids"] == sorted(issue["affected_ids"]),
        "currency": f["currency"] == issue["currency"],
        "amount": abs(f["claimed_amount_minor"] - issue["expected_amount_minor"])
                  <= tolerance(issue["expected_amount_minor"]),
        "evidence": any(set(s) <= set(f["evidence_ids"]) for s in issue["evidence_sets"]),
    }


def _why(f: dict, issues: list[dict], matched: set[int]) -> str:
    """Grader-side reason a finding is a false positive (for failure analysis only)."""
    best, best_score = "no_matching_issue", -1
    for i, issue in enumerate(issues):
        c = _checks(f, issue)
        if all(c.values()):
            return "duplicate" if i in matched else "unknown"
        if not c["ids"]:
            continue
        failed = [k for k in ("type", "currency", "amount", "evidence") if not c[k]]
        score = 4 - len(failed)
        if score > best_score:
            best, best_score = "wrong_" + failed[0], score
    return best


def match(issues: list[dict], findings: list[dict]) -> dict:
    """Match validated findings against truth issues. Returns counts, metrics and per-finding labels."""
    norm = [normalize_finding(f) for f in findings]
    matched: dict[int, int] = {}
    labels = []
    for fi, f in enumerate(norm):
        hit = next((ii for ii, iss in enumerate(issues)
                    if ii not in matched and all(_checks(f, iss).values())), None)
        if hit is None:
            labels.append({"finding": fi, "tp": False, "reason": _why(f, issues, set(matched))})
        else:
            matched[hit] = fi
            labels.append({"finding": fi, "tp": True, "issue_id": issues[hit]["issue_id"]})
    tp = len(matched)
    fp, fn = len(norm) - tp, len(issues) - tp
    p, r, f1 = prf1(tp, fp, fn)
    missed = [{"issue_id": iss["issue_id"], "type": iss["type"]} for i, iss in enumerate(issues) if i not in matched]
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1,
            "labels": labels, "missed": missed}


def grade(truth: dict, submission, episode_id: str, inspection_steps: int) -> dict:
    """Full grading of one submission. Invalid structure -> reward -1 (CONTRACT §5)."""
    err = validate_findings(submission, episode_id)
    if err is not None:
        n = len(truth["issues"])
        return {"valid": False, "error": err[:200], "tp": 0, "fp": 0, "fn": n, "precision": 0.0,
                "recall": 0.0, "f1": 0.0, "reward": -1.0, "inspection_steps": inspection_steps,
                "labels": [], "missed": [{"issue_id": i["issue_id"], "type": i["type"]} for i in truth["issues"]]}
    m = match(truth["issues"], submission["findings"])
    return {"valid": True, "error": None, **m, "reward": terminal_reward(m["f1"], inspection_steps),
            "inspection_steps": inspection_steps}


def public_summary(result: dict) -> dict:
    """What a policy may see after the episode in train mode: counts and metrics, no truth content."""
    return {k: result[k] for k in ("valid", "tp", "fp", "fn", "precision", "recall", "f1", "reward",
                                   "inspection_steps")}
