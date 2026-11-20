"""Automated attack search for auditenv reward and matcher (HANDOFF R1).

Proves reward reliability by mutating the oracle answer, silence, and record-derived
findings across 20 fixed public seeds (clean, interacting, dirty) to search for:
  1. Any submission that beats the honest answer (R_attack > R_honest).
  2. Any submission that scores > 0 on clean books.
  3. Any corrupted finding (wrong IDs, amount strictly over tolerance, wrong currency,
     wrong type, missing/unrelated evidence, duplicate) falsely credited as a True Positive.
  4. Any malformed finding structure that bypasses schema validation.

Evaluation is deterministic and reproducible. Both honest and attack submissions
are evaluated with the same inspection_steps.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import random
import sys
import time
from typing import Any, Callable

from .generator import ISSUE_TYPES, generate
from .matcher import grade, tolerance
from .run import load_episodes, parse_seeds
from .schema import MAX_EVIDENCE, MAX_EXPLANATION, MAX_FINDINGS


MUTATION_FAMILIES = (
    "amount_tolerance",
    "ids",
    "evidence_padding",
    "types",
    "currency",
    "duplicates",
    "order",
    "silence_clean",
    "schema_limits",
    "combined",
)

DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "eval_example.json"
)
DEFAULT_FAILURE_REPORT_PATH = "attack_failures.json"


@dataclass(frozen=True)
class MutationCandidate:
    """A single mutated submission candidate for attack testing."""
    family: str
    name: str
    submission: dict[str, Any]
    corrupted_indices: tuple[int, ...] = ()
    is_malformed: bool = False
    is_honest_variation: bool = False
    inspection_steps: int = 0


@dataclass
class ViolationRecord:
    """A recorded violation where an attack broke the reward contract."""
    seed: int
    episode_id: str
    config: dict[str, Any]
    is_clean: bool
    family: str
    mutation_name: str
    reason: str
    honest_reward: float
    attack_reward: float
    inspection_steps: int
    submission: dict[str, Any]
    result: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Full reproducible record of this violation."""
        return {
            "seed": self.seed,
            "episode_id": self.episode_id,
            "config": self.config,
            "is_clean": self.is_clean,
            "family": self.family,
            "mutation_name": self.mutation_name,
            "reason": self.reason,
            "honest_reward": self.honest_reward,
            "attack_reward": self.attack_reward,
            "inspection_steps": self.inspection_steps,
            "submission": self.submission,
            "result": self.result,
        }


@dataclass
class AttackSearchResult:
    """Summary of the automated attack search run."""
    total_mutations: int
    total_violations: int
    violations: list[ViolationRecord]
    mutations_by_family: dict[str, int]
    seeds_evaluated: list[int]
    clean_seeds: list[int]
    dirty_seeds: list[int]
    elapsed_s: float
    min_mutations: int = 10000
    report_path: str | None = None

    @property
    def passed(self) -> bool:
        return (
            self.total_violations == 0
            and self.total_mutations >= self.min_mutations
            and len(self.seeds_evaluated) > 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Full structured payload of the search result."""
        return {
            "passed": self.passed,
            "total_mutations": self.total_mutations,
            "total_violations": self.total_violations,
            "min_mutations": self.min_mutations,
            "seeds_evaluated": self.seeds_evaluated,
            "clean_seeds": self.clean_seeds,
            "dirty_seeds": self.dirty_seeds,
            "mutations_by_family": self.mutations_by_family,
            "elapsed_s": round(self.elapsed_s, 4),
            "report_path": self.report_path,
            "violations": [v.to_dict() for v in self.violations],
        }

    def summary(self) -> str:
        status_str = "PASSED" if self.passed else "FAILED"
        lines = [
            f"=== HANDOFF R1 Automated Attack Search: {status_str} ===",
            f"Seeds evaluated: {len(self.seeds_evaluated)} (clean: {len(self.clean_seeds)}, dirty: {len(self.dirty_seeds)})",
            f"Total mutations tested: {self.total_mutations}",
            f"Total violations detected: {self.total_violations}",
            "Mutations by family:",
        ]
        for fam in sorted(self.mutations_by_family):
            lines.append(f"  - {fam:<20}: {self.mutations_by_family[fam]:>5d}")
        lines.append(f"Elapsed time: {self.elapsed_s:.3f} s")
        if self.report_path:
            lines.append(f"Failure report artifact: {self.report_path}")
        if self.violations:
            lines.append(f"\nRecorded violations ({len(self.violations)}):")
            for v in self.violations[:5]:
                lines.append(
                    f"  * Seed {v.seed} [{v.family}] {v.mutation_name}: {v.reason} "
                    f"(attack {v.attack_reward} vs honest {v.honest_reward}, step {v.inspection_steps})"
                )
            if len(self.violations) > 5:
                lines.append(f"  ... and {len(self.violations) - 5} more")
        return "\n".join(lines)


def load_target_episodes(config_path: str | None = None) -> list[tuple[int, dict]]:
    """Load target episodes using run.load_episodes; disallow invented fallbacks."""
    path = config_path or DEFAULT_CONFIG_PATH
    episodes = load_episodes(path)
    if not episodes:
        raise ValueError(f"No episodes found in config: {path}")
    return episodes


def write_failure_report(result: AttackSearchResult, path: str = DEFAULT_FAILURE_REPORT_PATH) -> None:
    """Persist a full reproducible record of all detected violations to disk."""
    payload = result.to_dict()
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2)


def _make_finding(
    type_: str,
    affected_ids: list[str],
    amount: int,
    currency: str,
    evidence_ids: list[str],
    explanation: str = "x",
) -> dict[str, Any]:
    return {
        "type": type_,
        "affected_ids": list(affected_ids),
        "claimed_amount_minor": int(amount),
        "currency": str(currency),
        "evidence_ids": list(evidence_ids),
        "explanation": str(explanation),
    }


def _from_issue(iss: dict, **override) -> dict[str, Any]:
    f = _make_finding(
        type_=iss["type"],
        affected_ids=list(iss["affected_ids"]),
        amount=int(iss["expected_amount_minor"]),
        currency=str(iss["currency"]),
        evidence_ids=list(iss["evidence_sets"][0]),
        explanation="honest",
    )
    f.update(override)
    return f


def generate_mutations_for_episode(
    ep: dict,
    rng: random.Random,
    per_seed_target: int = 550,
    steps: int = 0,
) -> list[MutationCandidate]:
    """Deterministically generate >= per_seed_target attack submissions for an episode."""
    ep_id = ep["episode_id"]
    truth = ep["truth"]
    tables = ep["tables"]
    manifest = ep["manifest"]
    base_curr = manifest["base_currency"]
    issues = truth["issues"]
    is_clean = len(issues) == 0

    mutations: list[MutationCandidate] = []

    # Table resources for crafting attacks
    all_invoices = tables.get("invoices", [])
    all_payments = tables.get("payments", [])
    all_ledger = tables.get("ledger", [])
    all_fx = tables.get("fx", [])

    invoice_ids = [i["invoice_id"] for i in all_invoices if i.get("invoice_id")]
    payment_ids = [p["payment_id"] for p in all_payments if p.get("payment_id")]
    doc_ids = [i["doc_id"] for i in all_invoices if i.get("doc_id")] + [
        p["doc_id"] for p in all_payments if p.get("doc_id")
    ]
    row_ids = [r["row_id"] for r in all_ledger if r.get("row_id")]
    currencies = list(dict.fromkeys([base_curr] + [r["source_currency"] for r in all_fx if r.get("source_currency")]))
    if len(currencies) == 1:
        currencies.append("EUR" if base_curr != "EUR" else "USD")

    # Honest findings baseline
    if is_clean:
        honest_findings: list[dict[str, Any]] = []
    else:
        honest_findings = [_from_issue(iss) for iss in issues]

    def add_mut(
        family: str,
        name: str,
        findings: list[Any],
        corrupted: tuple[int, ...] = (),
        is_malformed: bool = False,
        is_honest_variation: bool = False,
        inspection_steps: int = steps,
    ):
        sub = {"episode_id": ep_id, "findings": findings}
        mutations.append(
            MutationCandidate(
                family=family,
                name=name,
                submission=sub,
                corrupted_indices=corrupted,
                is_malformed=is_malformed,
                is_honest_variation=is_honest_variation,
                inspection_steps=inspection_steps,
            )
        )

    # -------------------------------------------------------------------------
    # 1. Silence and Clean Books Family
    # -------------------------------------------------------------------------
    add_mut(
        "silence_clean",
        "silence_submission",
        [],
        is_honest_variation=is_clean,
        inspection_steps=steps,
    )
    for s_val in (5, 20, 50):
        add_mut(
            "silence_clean",
            f"silence_step_{s_val}",
            [],
            is_honest_variation=is_clean,
            inspection_steps=s_val,
        )

    # Attacks on clean books / fabrications from tables
    if is_clean:
        for i_idx, inv in enumerate(all_invoices[:15]):
            iid = inv["invoice_id"]
            doc = inv["doc_id"]
            tot = inv["total_minor"]
            add_mut(
                "silence_clean",
                f"clean_fake_duplicate_{i_idx}",
                [_make_finding("duplicate_invoice", [iid, invoice_ids[(i_idx + 1) % len(invoice_ids)]], tot, base_curr, [doc])],
                corrupted=(0,),
            )
            add_mut(
                "silence_clean",
                f"clean_fake_fx_{i_idx}",
                [_make_finding("fx_error", [iid], max(1, tot // 100), base_curr, [doc])],
                corrupted=(0,),
            )
            add_mut(
                "silence_clean",
                f"clean_fake_cutoff_{i_idx}",
                [_make_finding("period_cutoff", [iid], tot, base_curr, [doc])],
                corrupted=(0,),
            )

        for p_idx, pay in enumerate(all_payments[:15]):
            pid = pay["payment_id"]
            pdoc = pay["doc_id"]
            tot = pay["amount_minor"]
            ref_id = pay["invoice_refs"][0]["invoice_id"] if pay.get("invoice_refs") else (invoice_ids[0] if invoice_ids else "inv_0")
            add_mut(
                "silence_clean",
                f"clean_fake_allocation_{p_idx}",
                [_make_finding("payment_allocation", [ref_id, pid], max(1, abs(tot) // 10), base_curr, [pdoc])],
                corrupted=(0,),
            )

        for k in (2, 5, 10, 20, 30):
            multi = []
            for j in range(k):
                inv = all_invoices[j % len(all_invoices)]
                multi.append(_make_finding("duplicate_invoice", [inv["invoice_id"]], inv["total_minor"], base_curr, [inv["doc_id"]]))
            add_mut("silence_clean", f"clean_multi_fabricated_{k}", multi, corrupted=tuple(range(len(multi))))

    # -------------------------------------------------------------------------
    # 2. Dirty books: Honest variations and mutations from issues
    # -------------------------------------------------------------------------
    if not is_clean:
        add_mut(
            "silence_clean",
            "oracle_honest_submission",
            list(honest_findings),
            is_honest_variation=True,
            inspection_steps=steps,
        )
        for s_val in (5, 20, 50):
            add_mut(
                "silence_clean",
                f"oracle_honest_step_{s_val}",
                list(honest_findings),
                is_honest_variation=True,
                inspection_steps=s_val,
            )

        if len(honest_findings) > 1:
            add_mut("silence_clean", "oracle_drop_first", honest_findings[1:])
            add_mut("silence_clean", "oracle_drop_last", honest_findings[:-1])
            add_mut("silence_clean", "oracle_single_only", honest_findings[:1])

        # --- AMOUNT & TOLERANCE / EQUALITY FAMILY ---
        for i_idx, iss in enumerate(issues):
            exp = iss["expected_amount_minor"]
            tol = tolerance(exp)
            # Exact equality
            exact_f = [dict(f) for f in honest_findings]
            exact_f[i_idx] = _from_issue(iss, claimed_amount_minor=exp)
            add_mut("amount_tolerance", f"exact_equality_iss_{i_idx}", exact_f, is_honest_variation=True)

            # Tolerance boundaries (should match)
            upper_f = [dict(f) for f in honest_findings]
            upper_f[i_idx] = _from_issue(iss, claimed_amount_minor=exp + tol)
            add_mut("amount_tolerance", f"upper_tolerance_edge_iss_{i_idx}", upper_f, is_honest_variation=True)

            lower_amt = max(0, exp - tol)
            lower_f = [dict(f) for f in honest_findings]
            lower_f[i_idx] = _from_issue(iss, claimed_amount_minor=lower_amt)
            add_mut("amount_tolerance", f"lower_tolerance_edge_iss_{i_idx}", lower_f, is_honest_variation=True)

            # Strictly over upper tolerance -> must NOT match
            for delta in (1, 2, 5, 10, tol + 1, 2 * tol + 5, 5 * tol + 20, 10 * tol + 50):
                over_f = [dict(f) for f in honest_findings]
                over_f[i_idx] = _from_issue(iss, claimed_amount_minor=exp + tol + delta)
                add_mut("amount_tolerance", f"over_tolerance_plus_{delta}_iss_{i_idx}", over_f, corrupted=(i_idx,))

            # Strictly below lower tolerance -> must NOT match
            for delta in (1, 2, 5, 10, tol + 1):
                if exp - tol - delta >= 0:
                    under_f = [dict(f) for f in honest_findings]
                    under_f[i_idx] = _from_issue(iss, claimed_amount_minor=exp - tol - delta)
                    add_mut("amount_tolerance", f"under_tolerance_minus_{delta}_iss_{i_idx}", under_f, corrupted=(i_idx,))

            add_mut("amount_tolerance", f"zero_amount_iss_{i_idx}", [dict(f) if j != i_idx else _from_issue(iss, claimed_amount_minor=0) for j, f in enumerate(honest_findings)], corrupted=(i_idx,) if exp > tol else ())
            add_mut("amount_tolerance", f"one_amount_iss_{i_idx}", [dict(f) if j != i_idx else _from_issue(iss, claimed_amount_minor=1) for j, f in enumerate(honest_findings)], corrupted=(i_idx,) if exp > tol + 1 else ())
            add_mut("amount_tolerance", f"half_amount_iss_{i_idx}", [dict(f) if j != i_idx else _from_issue(iss, claimed_amount_minor=exp // 2) for j, f in enumerate(honest_findings)], corrupted=(i_idx,) if abs(exp // 2 - exp) > tol else ())
            add_mut("amount_tolerance", f"double_amount_iss_{i_idx}", [dict(f) if j != i_idx else _from_issue(iss, claimed_amount_minor=exp * 2) for j, f in enumerate(honest_findings)], corrupted=(i_idx,))

            neg_f = [dict(f) for f in honest_findings]
            neg_f[i_idx] = _from_issue(iss, claimed_amount_minor=-50)
            add_mut("amount_tolerance", f"negative_amount_iss_{i_idx}", neg_f, is_malformed=True)

        # --- IDS FAMILY ---
        for i_idx, iss in enumerate(issues):
            aids = iss["affected_ids"]
            bad_suffix = [dict(f) for f in honest_findings]
            bad_suffix[i_idx] = _from_issue(iss, affected_ids=[a + "_fake9" for a in aids])
            add_mut("ids", f"corrupt_suffix_iss_{i_idx}", bad_suffix, corrupted=(i_idx,))

            spare_id = next((iid for iid in invoice_ids if iid not in aids), "INV_SPARE")
            swapped = [dict(f) for f in honest_findings]
            swapped[i_idx] = _from_issue(iss, affected_ids=[spare_id] + list(aids[1:]))
            add_mut("ids", f"swapped_id_iss_{i_idx}", swapped, corrupted=(i_idx,))

            if len(aids) > 1:
                dropped = [dict(f) for f in honest_findings]
                dropped[i_idx] = _from_issue(iss, affected_ids=aids[:1])
                add_mut("ids", f"dropped_id_iss_{i_idx}", dropped, corrupted=(i_idx,))

            extra_id = next((iid for iid in invoice_ids if iid not in aids), "INV_EXTRA")
            extra = [dict(f) for f in honest_findings]
            extra[i_idx] = _from_issue(iss, affected_ids=aids + [extra_id])
            add_mut("ids", f"extra_id_iss_{i_idx}", extra, corrupted=(i_idx,))

            if len(aids) > 1:
                rev = [dict(f) for f in honest_findings]
                rev[i_idx] = _from_issue(iss, affected_ids=list(reversed(aids)))
                add_mut("ids", f"reversed_ids_iss_{i_idx}", rev, is_honest_variation=True)

            dedup = [dict(f) for f in honest_findings]
            dedup[i_idx] = _from_issue(iss, affected_ids=aids + [aids[0]])
            add_mut("ids", f"dedup_ids_iss_{i_idx}", dedup, is_honest_variation=True)

        # --- EVIDENCE PADDING FAMILY ---
        for i_idx, iss in enumerate(issues):
            ev_sets = iss["evidence_sets"]
            primary_ev = ev_sets[0]

            for set_idx, alt_set in enumerate(ev_sets[1:], 1):
                alt_f = [dict(f) for f in honest_findings]
                alt_f[i_idx] = _from_issue(iss, evidence_ids=list(alt_set))
                add_mut("evidence_padding", f"alt_evidence_set_{set_idx}_iss_{i_idx}", alt_f, is_honest_variation=True)

            unused_docs_rows = [x for x in (doc_ids + row_ids) if x not in set(primary_ev)]
            for pad_count in (1, 2, 4, 8):
                avail = min(pad_count, MAX_EVIDENCE - len(primary_ev))
                if avail > 0:
                    padded_f = [dict(f) for f in honest_findings]
                    padded_ev = list(primary_ev) + unused_docs_rows[:avail]
                    padded_f[i_idx] = _from_issue(iss, evidence_ids=padded_ev)
                    add_mut("evidence_padding", f"padded_to_{len(padded_ev)}_iss_{i_idx}", padded_f, is_honest_variation=True)

            over_ev = list(primary_ev) + unused_docs_rows[: (MAX_EVIDENCE + 1 - len(primary_ev))]
            if len(over_ev) > MAX_EVIDENCE:
                over_f = [dict(f) for f in honest_findings]
                over_f[i_idx] = _from_issue(iss, evidence_ids=over_ev)
                add_mut("evidence_padding", f"over_padded_11_iss_{i_idx}", over_f, is_malformed=True)

            if len(primary_ev) > 1:
                incomp_f = [dict(f) for f in honest_findings]
                incomp_f[i_idx] = _from_issue(iss, evidence_ids=primary_ev[:1])
                if not any(set(s) <= set(primary_ev[:1]) for s in ev_sets):
                    add_mut("evidence_padding", f"incomplete_evidence_iss_{i_idx}", incomp_f, corrupted=(i_idx,))

            empty_ev = [dict(f) for f in honest_findings]
            empty_ev[i_idx] = _from_issue(iss, evidence_ids=[])
            add_mut("evidence_padding", f"empty_evidence_iss_{i_idx}", empty_ev, corrupted=(i_idx,))

            unrel_ev = [dict(f) for f in honest_findings]
            unrel_ev[i_idx] = _from_issue(iss, evidence_ids=unused_docs_rows[:4])
            add_mut("evidence_padding", f"unrelated_evidence_iss_{i_idx}", unrel_ev, corrupted=(i_idx,))

            if len(issues) > 1:
                donor = issues[(i_idx + 1) % len(issues)]["evidence_sets"][0]
                if not any(set(s) <= set(donor) for s in ev_sets):
                    borrowed = [dict(f) for f in honest_findings]
                    borrowed[i_idx] = _from_issue(iss, evidence_ids=list(donor))
                    add_mut("evidence_padding", f"borrowed_evidence_iss_{i_idx}", borrowed, corrupted=(i_idx,))

        # --- TYPES FAMILY ---
        for i_idx, iss in enumerate(issues):
            for ty in ISSUE_TYPES:
                if ty != iss["type"]:
                    ty_f = [dict(f) for f in honest_findings]
                    ty_f[i_idx] = _from_issue(iss, type=ty)
                    add_mut("types", f"wrong_type_{ty}_iss_{i_idx}", ty_f, corrupted=(i_idx,))
            for bad_ty in ("fraud", "unauthorized_draw", "tax_error"):
                bad_ty_f = [dict(f) for f in honest_findings]
                bad_ty_f[i_idx] = _from_issue(iss, type=bad_ty)
                add_mut("types", f"invalid_type_{bad_ty}_iss_{i_idx}", bad_ty_f, is_malformed=True)

        # --- CURRENCY FAMILY ---
        for i_idx, iss in enumerate(issues):
            for cur in currencies:
                if cur != iss["currency"]:
                    cur_f = [dict(f) for f in honest_findings]
                    cur_f[i_idx] = _from_issue(iss, currency=cur)
                    add_mut("currency", f"wrong_currency_{cur}_iss_{i_idx}", cur_f, corrupted=(i_idx,))
            low_cur_f = [dict(f) for f in honest_findings]
            low_cur_f[i_idx] = _from_issue(iss, currency=iss["currency"].lower())
            add_mut("currency", f"lowercase_currency_iss_{i_idx}", low_cur_f, is_malformed=True)

        # --- DUPLICATES FAMILY ---
        for i_idx in range(len(honest_findings)):
            for rep in (2, 3, 5):
                f_target = honest_findings[i_idx]
                dup_sub = honest_findings[: i_idx + 1] + [dict(f_target) for _ in range(rep - 1)] + honest_findings[i_idx + 1 :]
                corrupted_dups = tuple(range(i_idx + 1, i_idx + rep))
                add_mut("duplicates", f"dup_single_{rep}x_iss_{i_idx}", dup_sub, corrupted=corrupted_dups)

        dup_all = honest_findings + [dict(f) for f in honest_findings]
        add_mut("duplicates", "duplicate_all_oracle", dup_all, corrupted=tuple(range(len(honest_findings), len(dup_all))))

        # --- ORDER FAMILY ---
        if len(honest_findings) > 1:
            add_mut("order", "reversed_order", list(reversed(honest_findings)), is_honest_variation=True)

        shuffled = list(honest_findings)
        rng.shuffle(shuffled)
        add_mut("order", "shuffled_order", shuffled, is_honest_variation=True)

        fake_one = _make_finding("duplicate_invoice", ["inv_bad99"], 1000, base_curr, ["doc_bad99"])
        add_mut("order", "prepend_fake", [fake_one] + list(honest_findings), corrupted=(0,))
        add_mut("order", "append_fake", list(honest_findings) + [fake_one], corrupted=(len(honest_findings),))

    # -------------------------------------------------------------------------
    # 3. SCHEMA LIMITS FAMILY (Clean & Dirty)
    # -------------------------------------------------------------------------
    if honest_findings:
        template_f = dict(honest_findings[0])
    else:
        sample_inv = all_invoices[0] if all_invoices else {"invoice_id": "inv_0", "doc_id": "doc_0", "total_minor": 1000}
        template_f = _make_finding("duplicate_invoice", [sample_inv["invoice_id"]], sample_inv["total_minor"], base_curr, [sample_inv["doc_id"]])

    padded_30 = [dict(template_f) for _ in range(MAX_FINDINGS)]
    add_mut(
        "schema_limits",
        "max_30_findings",
        padded_30,
        corrupted=tuple(range(len(honest_findings), len(padded_30))),
    )

    padded_31 = [dict(template_f) for _ in range(MAX_FINDINGS + 1)]
    add_mut("schema_limits", "over_30_findings", padded_31, is_malformed=True)

    f_exp_1000 = [dict(template_f, explanation="x" * MAX_EXPLANATION)]
    add_mut("schema_limits", "explanation_1000_chars", f_exp_1000, is_honest_variation=(len(issues) == 1))
    f_exp_1001 = [dict(template_f, explanation="x" * (MAX_EXPLANATION + 1))]
    add_mut("schema_limits", "explanation_1001_chars", f_exp_1001, is_malformed=True)

    sub_bad_f = [dict(template_f, claimed_amount_minor=True)]
    add_mut("schema_limits", "bool_amount", sub_bad_f, is_malformed=True)
    sub_bad_ids = [dict(template_f, affected_ids=[""])]
    add_mut("schema_limits", "empty_string_id", sub_bad_ids, is_malformed=True)
    sub_bad_ev = [dict(template_f, evidence_ids=[""])]
    add_mut("schema_limits", "empty_string_evidence", sub_bad_ev, is_malformed=True)

    # -------------------------------------------------------------------------
    # 4. COMBINED / DETERMINISTIC RNG PAD TO TARGET
    # -------------------------------------------------------------------------
    comb_idx = 0
    while len(mutations) < per_seed_target:
        comb_idx += 1
        choice = rng.randint(0, 5)
        if is_clean or choice == 0:
            k_f = rng.randint(1, 5)
            f_list = []
            for j in range(k_f):
                ty = rng.choice(ISSUE_TYPES)
                inv = all_invoices[(comb_idx + j) % len(all_invoices)]
                f_list.append(_make_finding(ty, [inv["invoice_id"]], inv["total_minor"] + j * 10, base_curr, [inv["doc_id"]]))
            add_mut("combined", f"random_fabricated_{comb_idx}", f_list, corrupted=tuple(range(len(f_list))))
        elif choice == 1:
            f_list = [dict(f) for f in honest_findings]
            target_i = rng.randint(0, len(f_list) - 1)
            f_list[target_i]["claimed_amount_minor"] += tolerance(f_list[target_i]["claimed_amount_minor"]) + rng.randint(2, 500)
            add_mut("combined", f"amount_jitter_{comb_idx}", f_list, corrupted=(target_i,))
        elif choice == 2:
            f_list = [dict(f) for f in honest_findings]
            target_i = rng.randint(0, len(f_list) - 1)
            f_list[target_i]["affected_ids"] = [f_list[target_i]["affected_ids"][0] + f"_j{comb_idx}"]
            add_mut("combined", f"id_jitter_{comb_idx}", f_list, corrupted=(target_i,))
        elif choice == 3:
            f_list = [dict(f) for f in honest_findings]
            target_i = rng.randint(0, len(f_list) - 1)
            f_list[target_i]["evidence_ids"] = [f"doc_unrel_{comb_idx}"]
            add_mut("combined", f"evidence_jitter_{comb_idx}", f_list, corrupted=(target_i,))
        elif choice == 4:
            f_list = [dict(f) for f in honest_findings]
            target_i = rng.randint(0, len(f_list) - 1)
            cur_ty = f_list[target_i]["type"]
            other_types = [t for t in ISSUE_TYPES if t != cur_ty]
            f_list[target_i]["type"] = rng.choice(other_types)
            add_mut("combined", f"type_jitter_{comb_idx}", f_list, corrupted=(target_i,))
        else:
            f_list = [dict(f) for f in honest_findings]
            target_i = rng.randint(0, len(f_list) - 1)
            f_list.append(dict(f_list[target_i]))
            add_mut("combined", f"dup_jitter_{comb_idx}", f_list, corrupted=(len(f_list) - 1,))

    return mutations


def evaluate_mutation(
    mutation: MutationCandidate,
    truth: dict[str, Any],
    honest_submission: dict[str, Any],
    is_clean: bool,
    seed: int,
    episode_id: str,
    config: dict[str, Any] | None = None,
) -> ViolationRecord | None:
    """Evaluate a single mutation candidate against matcher.grade and check contract invariants."""
    cfg = dict(config or {})
    honest_res = grade(truth, honest_submission, episode_id, mutation.inspection_steps)
    honest_reward = honest_res["reward"]

    res = grade(truth, mutation.submission, episode_id, mutation.inspection_steps)
    reward = res["reward"]
    findings = mutation.submission.get("findings")
    n_findings = len(findings) if isinstance(findings, list) else 0
    issues = truth["issues"]

    # Invariant 1: Attack must never beat honest answer (with same inspection_steps)
    if reward > honest_reward + 1e-9:
        return ViolationRecord(
            seed=seed,
            episode_id=episode_id,
            config=cfg,
            is_clean=is_clean,
            family=mutation.family,
            mutation_name=mutation.name,
            reason="attack_beats_honest_answer",
            honest_reward=honest_reward,
            attack_reward=reward,
            inspection_steps=mutation.inspection_steps,
            submission=mutation.submission,
            result=res,
        )

    # Invariant 2: On clean books, any non-empty submission must not score > 0
    if is_clean and n_findings > 0:
        if reward > 0.0 or res["tp"] > 0:
            return ViolationRecord(
                seed=seed,
                episode_id=episode_id,
                config=cfg,
                is_clean=is_clean,
                family=mutation.family,
                mutation_name=mutation.name,
                reason="clean_books_scored_positive",
                honest_reward=honest_reward,
                attack_reward=reward,
                inspection_steps=mutation.inspection_steps,
                submission=mutation.submission,
                result=res,
            )

    # Invariant 3: TP count cannot exceed actual issues count
    if res["tp"] > len(issues):
        return ViolationRecord(
            seed=seed,
            episode_id=episode_id,
            config=cfg,
            is_clean=is_clean,
            family=mutation.family,
            mutation_name=mutation.name,
            reason="tp_exceeds_truth_issues",
            honest_reward=honest_reward,
            attack_reward=reward,
            inspection_steps=mutation.inspection_steps,
            submission=mutation.submission,
            result=res,
        )

    # Invariant 4: Intentionally corrupted findings must not receive TP
    if res["valid"] and mutation.corrupted_indices:
        labels = res.get("labels", [])
        for c_idx in mutation.corrupted_indices:
            if c_idx < len(labels) and labels[c_idx].get("tp"):
                return ViolationRecord(
                    seed=seed,
                    episode_id=episode_id,
                    config=cfg,
                    is_clean=is_clean,
                    family=mutation.family,
                    mutation_name=mutation.name,
                    reason=f"corrupted_finding_matched_tp_at_index_{c_idx}",
                    honest_reward=honest_reward,
                    attack_reward=reward,
                    inspection_steps=mutation.inspection_steps,
                    submission=mutation.submission,
                    result=res,
                )

    # Invariant 5: Malformed schema submissions must be rejected with valid=False and reward=-1.0
    if mutation.is_malformed:
        if res["valid"] or reward != -1.0:
            return ViolationRecord(
                seed=seed,
                episode_id=episode_id,
                config=cfg,
                is_clean=is_clean,
                family=mutation.family,
                mutation_name=mutation.name,
                reason="malformed_submission_accepted",
                honest_reward=honest_reward,
                attack_reward=reward,
                inspection_steps=mutation.inspection_steps,
                submission=mutation.submission,
                result=res,
            )

    # Invariant 6: Valid honest boundary variations must achieve full TP and honest reward
    if mutation.is_honest_variation and res["valid"]:
        if res["tp"] != len(issues) or res["fp"] != 0 or reward < honest_reward - 1e-9:
            return ViolationRecord(
                seed=seed,
                episode_id=episode_id,
                config=cfg,
                is_clean=is_clean,
                family=mutation.family,
                mutation_name=mutation.name,
                reason="honest_boundary_variation_rejected",
                honest_reward=honest_reward,
                attack_reward=reward,
                inspection_steps=mutation.inspection_steps,
                submission=mutation.submission,
                result=res,
            )

    return None


def run_attack_search(
    seeds: list[int] | None = None,
    config_path: str | None = None,
    min_mutations: int = 10000,
    per_seed_target: int = 550,
    inspection_steps: int = 0,
    verbose: bool = False,
    report_path: str | None = DEFAULT_FAILURE_REPORT_PATH,
    _extra_mutations_factory: Callable[[dict, random.Random], list[MutationCandidate]] | None = None,
) -> AttackSearchResult:
    """Run deterministic automated attack search across public seeds (>= 10,000 mutations)."""
    t0 = time.monotonic()
    episodes = load_target_episodes(config_path)
    if seeds is not None:
        seed_set = set(seeds)
        episodes = [e for e in episodes if e[0] in seed_set]

    # Empty seed selection must not pass
    if not episodes:
        raise ValueError("Seed selection is empty: no matching episodes found")

    if per_seed_target * len(episodes) < min_mutations:
        per_seed_target = (min_mutations + len(episodes) - 1) // len(episodes)

    total_mutations = 0
    violations: list[ViolationRecord] = []
    mutations_by_family: dict[str, int] = {f: 0 for f in MUTATION_FAMILIES}
    clean_seeds: list[int] = []
    dirty_seeds: list[int] = []
    seeds_evaluated: list[int] = []

    for seed, cfg in episodes:
        seeds_evaluated.append(seed)
        ep = generate(seed, cfg)
        ep_id = ep["episode_id"]
        truth = ep["truth"]
        is_clean = len(truth["issues"]) == 0
        if is_clean:
            clean_seeds.append(seed)
            honest_sub = {"episode_id": ep_id, "findings": []}
        else:
            dirty_seeds.append(seed)
            honest_sub = {
                "episode_id": ep_id,
                "findings": [_from_issue(iss) for iss in truth["issues"]],
            }

        rng = random.Random(seed * 10007 + 42)
        mutations = generate_mutations_for_episode(
            ep,
            rng=rng,
            per_seed_target=per_seed_target,
            steps=inspection_steps,
        )

        if _extra_mutations_factory is not None:
            mutations.extend(_extra_mutations_factory(ep, rng))

        for mut in mutations:
            total_mutations += 1
            mutations_by_family[mut.family] = mutations_by_family.get(mut.family, 0) + 1
            violation = evaluate_mutation(
                mutation=mut,
                truth=truth,
                honest_submission=honest_sub,
                is_clean=is_clean,
                seed=seed,
                episode_id=ep_id,
                config=cfg,
            )
            if violation is not None:
                violations.append(violation)

        if verbose:
            print(f"Seed {seed:4d} ({'clean' if is_clean else 'dirty'}): {len(mutations)} mutations tested, {len(violations)} violations")

    elapsed_s = time.monotonic() - t0
    result = AttackSearchResult(
        total_mutations=total_mutations,
        total_violations=len(violations),
        violations=violations,
        mutations_by_family=mutations_by_family,
        seeds_evaluated=seeds_evaluated,
        clean_seeds=clean_seeds,
        dirty_seeds=dirty_seeds,
        elapsed_s=elapsed_s,
        min_mutations=min_mutations,
        report_path=report_path if violations else None,
    )

    # Automatically persist failure report artifact if any violation occurred
    if violations and report_path:
        write_failure_report(result, path=report_path)

    return result


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for HANDOFF R1 acceptance command."""
    ap = argparse.ArgumentParser(
        description="Automated Attack Search (HANDOFF R1): deterministic >=10000 mutations across 20 seeds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--config", help="Path to episode config json (default configs/eval_example.json)")
    ap.add_argument("--seeds", type=parse_seeds, help="Comma-separated seeds or range (e.g. 9000-9019)")
    ap.add_argument("--min-mutations", type=int, default=10000, help="Minimum total mutations (default 10000)")
    ap.add_argument("--per-seed", type=int, default=550, help="Mutations per seed (default 550)")
    ap.add_argument("--steps", type=int, default=0, help="Inspection steps for evaluation (default 0)")
    ap.add_argument("-v", "--verbose", action="store_true", help="Verbose progress")
    ap.add_argument("--json", help="Path to write JSON summary results")
    ap.add_argument("--report-path", default=DEFAULT_FAILURE_REPORT_PATH, help="Path for automatic failure report artifact")
    args = ap.parse_args(argv)

    try:
        result = run_attack_search(
            seeds=args.seeds,
            config_path=args.config,
            min_mutations=args.min_mutations,
            per_seed_target=args.per_seed,
            inspection_steps=args.steps,
            verbose=args.verbose,
            report_path=args.report_path,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(result.summary())

    if args.json:
        dirname = os.path.dirname(args.json)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(args.json, "w") as fh:
            json.dump(result.to_dict(), fh, indent=2)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
