"""Shared matcher and terminal reward (CONTRACT §6). Published on purpose: normalisation,
tolerance and the tie rule for ambiguous matches are all in this file.

- normalisation: `schema.normalize_finding` -- strings exact (case and whitespace count, no conversion);
  affected_ids and evidence_ids are sets (order and repeats do not matter)
- edge finding -> issue only if: type equal, set(affected_ids) == set(issue.affected_ids), currency equal,
  abs(claimed - expected) <= tolerance, every evidence id exists in the episode's public data, and the evidence
  set contains at least one of the issue's evidence sets
- tolerance: the episode policy's `findings.tolerance_minor` (a fixed non-negative int, 0 = exact; `tolerance_of`)
- one-to-one: a maximum-cardinality bipartite matching (findings, repeats included, against truth issues).
  Ties between maximum matchings: issue ids sorted by code point, and the lexicographically smallest sorted
  sequence of (issue_id, finding index) pairs wins. Unmatched findings, repeats included, are false positives.
"""

from __future__ import annotations

from .metrics import prf1, terminal_reward
from .schema import normalize_finding, validate_findings

# Primary keys per public table: the ids `get_record` / `get_document` can fetch (ledger invoice/payment references
# are not ids of their own).
ID_FIELDS = {"ledger": ("row_id",), "invoices": ("invoice_id", "doc_id"), "payments": ("payment_id", "doc_id"),
             "fx": ("fx_id",)}


def public_ids(tables: dict) -> set[str]:
    """Every id a policy can see in the episode's public tables: row, document, invoice, payment and fx ids."""
    return {row[key] for name, keys in ID_FIELDS.items() for row in tables[name] for key in keys}


def tolerance_of(policy: dict) -> int:
    """The published amount tolerance in minor units (policy `findings.tolerance_minor`, default 0)."""
    tol = (policy.get("findings") or {}).get("tolerance_minor", 0)  # absent = exact
    if isinstance(tol, bool) or not isinstance(tol, int) or tol < 0:
        raise ValueError("policy findings.tolerance_minor must be a non-negative int")
    return tol


def _checks(f: dict, issue: dict, known_ids: set[str], tolerance: int) -> dict:
    evidence = set(f["evidence_ids"])
    return {
        "type": f["type"] == issue["type"],
        "ids": set(f["affected_ids"]) == set(issue["affected_ids"]),
        "currency": f["currency"] == issue["currency"],
        "amount": abs(f["claimed_amount_minor"] - issue["expected_amount_minor"]) <= tolerance,
        "evidence": evidence <= known_ids and any(set(s) <= evidence for s in issue["evidence_sets"]),
    }


def _why(f: dict, issues: list[dict], matched: set[int], known_ids: set[str], tolerance: int) -> str:
    """Grader-side reason a finding is a false positive (for failure analysis only)."""
    if not set(f["evidence_ids"]) <= known_ids:
        return "unknown_evidence"
    best, best_score = "no_matching_issue", -1
    for i, issue in enumerate(issues):
        c = _checks(f, issue, known_ids, tolerance)
        if all(c.values()):
            return "duplicate" if i in matched else "unknown"
        if not c["ids"]:
            continue
        failed = [k for k in ("type", "currency", "amount", "evidence") if not c[k]]
        score = 4 - len(failed)
        if score > best_score:
            best, best_score = "wrong_" + failed[0], score
    return best


def _max_matching(adj: dict[int, list[int]], issues: list[int], banned_f: set[int]) -> int:
    """Size of a maximum matching between `issues` and findings not in `banned_f` (Kuhn's augmenting paths)."""
    owner: dict[int, int] = {}

    def augment(i: int, seen: set[int]) -> bool:
        for f in adj[i]:
            if f in banned_f or f in seen:
                continue
            seen.add(f)
            if f not in owner or augment(owner[f], seen):
                owner[f] = i
                return True
        return False

    return sum(augment(i, set()) for i in issues)


def _assign(adj: dict[int, list[int]], order: list[int]) -> dict[int, int]:
    """Maximum matching issue -> finding with the published tie rule. `order` lists issues by issue_id; fixing
    pairs in that order (findings by index) and keeping a pair only while a maximum matching still exists yields
    the lexicographically smallest sorted (issue_id, finding index) sequence among all maximum matchings."""
    best = _max_matching(adj, order, set())
    fixed: dict[int, int] = {}
    for pos, i in enumerate(order):
        rest = order[pos + 1:]
        for f in adj[i]:
            if f in fixed.values():
                continue
            if len(fixed) + 1 + _max_matching(adj, rest, set(fixed.values()) | {f}) == best:
                fixed[i] = f
                break
    return fixed


def match(issues: list[dict], findings: list[dict], known_ids: set[str], tolerance: int = 0) -> dict:
    """Match validated findings against truth issues. Returns counts, metrics and per-finding labels."""
    norm = [normalize_finding(f) for f in findings]
    adj = {ii: [fi for fi, f in enumerate(norm) if all(_checks(f, iss, known_ids, tolerance).values())]
           for ii, iss in enumerate(issues)}
    order = sorted(range(len(issues)), key=lambda ii: issues[ii]["issue_id"])
    matched = _assign(adj, order)
    by_finding = {fi: ii for ii, fi in matched.items()}
    labels = []
    for fi, f in enumerate(norm):
        if fi in by_finding:
            labels.append({"finding": fi, "tp": True, "issue_id": issues[by_finding[fi]]["issue_id"]})
        else:
            labels.append({"finding": fi, "tp": False,
                           "reason": _why(f, issues, set(matched), known_ids, tolerance)})
    tp = len(matched)
    fp, fn = len(norm) - tp, len(issues) - tp
    p, r, f1 = prf1(tp, fp, fn)
    missed = [{"issue_id": iss["issue_id"], "type": iss["type"]} for i, iss in enumerate(issues) if i not in matched]
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1,
            "labels": labels, "missed": missed}


def grade(truth: dict, submission, episode_id: str, inspection_steps: int, known_ids: set[str],
          tolerance: int = 0) -> dict:
    """Full grading of one submission. Invalid structure -> reward -1 (CONTRACT §5). `known_ids` = `public_ids` of
    the episode's tables; `tolerance` = `tolerance_of` its policy."""
    err = validate_findings(submission, episode_id)
    if err is not None:
        n = len(truth["issues"])
        return {"valid": False, "error": err[:200], "tp": 0, "fp": 0, "fn": n, "precision": 0.0,
                "recall": 0.0, "f1": 0.0, "reward": -1.0, "inspection_steps": inspection_steps,
                "labels": [], "missed": [{"issue_id": i["issue_id"], "type": i["type"]} for i in truth["issues"]]}
    m = match(truth["issues"], submission["findings"], known_ids, tolerance)
    return {"valid": True, "error": None, **m, "reward": terminal_reward(m["f1"], inspection_steps),
            "inspection_steps": inspection_steps}


def grade_episode(ep: dict, submission, inspection_steps: int) -> dict:
    """`grade` against a generated or loaded episode, with its own public ids and published tolerance."""
    return grade(ep["truth"], submission, ep["episode_id"], inspection_steps, public_ids(ep["tables"]),
                 tolerance_of(ep["policy"]))


def public_summary(result: dict) -> dict:
    """What a policy may see after the episode in train mode: counts and metrics, no truth content."""
    return {k: result[k] for k in ("valid", "tp", "fp", "fn", "precision", "recall", "f1", "reward",
                                   "inspection_steps")}
