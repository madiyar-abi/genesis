"""Reward attack tests (SPEC section 05): real episodes through AuditEnv in train mode.

Each property is checked over >= 10 seeds. Findings are built grader-side from env._ep
(truth and tables) — fine in tests, never in a policy.
"""

from __future__ import annotations

import copy
import json
import os
import random
import tempfile
import unittest
from decimal import ROUND_HALF_UP, Decimal

from auditenv.attack import (
    MUTATION_FAMILIES,
    MutationCandidate,
    evaluate_mutation,
    generate_mutations_for_episode,
    run_attack_search,
)
from auditenv.env import AuditEnv
from auditenv.matcher import tolerance
from auditenv.policies.oracle import Oracle

TYPES = ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")
DIRTY = {"errors": {t: 1 for t in TYPES}, "interacting": {"I1": 1, "I2": 1}, "mode": "train"}
CLEAN = {"errors": {}, "mode": "train"}
SEEDS = range(300, 312)  # 12 seeds


# ---------------------------------------------------------------- helpers
def new_env(seed: int, config: dict) -> tuple[AuditEnv, dict]:
    env = AuditEnv()
    obs, _ = env.reset(seed, config)
    return env, obs


def oracle_findings(env: AuditEnv, obs: dict) -> list[dict]:
    o = Oracle(env._ep["truth"])
    o.reset(obs)
    return o.act(obs)["findings"]["findings"]


def submit(env: AuditEnv, findings: list[dict]):
    return env.step({"type": "submit", "findings": {"episode_id": env.episode_id, "findings": findings}})


def inspect(env: AuditEnv, n: int) -> None:
    for _ in range(n):
        obs, reward, term, trunc, _ = env.step({"type": "list_records", "table": "ledger", "cursor": None,
                                                "limit": 50})
        assert obs["error"] is None and reward == 0.0 and not term and not trunc


def play(seed: int, config: dict, build, n_inspect: int = 0):
    """Reset, take n_inspect list_records steps, submit build(env, obs). Returns (reward, obs, info, env)."""
    env, first = new_env(seed, config)
    findings = build(env, first)
    inspect(env, n_inspect)
    obs, reward, term, trunc, info = submit(env, findings)
    assert term and not trunc
    return reward, obs, info, env


def issues(env: AuditEnv) -> list[dict]:
    return env._ep["truth"]["issues"]


def tables(env: AuditEnv) -> dict:
    return env._ep["tables"]


def base(env: AuditEnv) -> str:
    return env._ep["manifest"]["base_currency"]


def ar_debit_rows(env: AuditEnv) -> dict:
    """invoice_id -> its AR debit row (invoice journal: account 1200, payment_id null)."""
    out = {}
    for r in tables(env)["ledger"]:
        if r["account"] == "1200" and r["debit_minor"] > 0 and r["invoice_id"] and r["payment_id"] is None:
            out.setdefault(r["invoice_id"], r)
    return out


def finding(type_, ids, amount, currency, evidence, why="x") -> dict:
    return {"type": type_, "affected_ids": list(ids), "claimed_amount_minor": int(amount),
            "currency": currency, "evidence_ids": list(evidence), "explanation": why}


def from_issue(iss: dict, **override) -> dict:
    f = finding(iss["type"], iss["affected_ids"], iss["expected_amount_minor"], iss["currency"],
                iss["evidence_sets"][0])
    f.update(override)
    return f


def expected_reward(f1: float, steps: int) -> float:
    return round(max(-1.0, min(1.0, 2 * f1 - 1 - 0.002 * steps)), 6)


def all_affected(env: AuditEnv) -> set:
    return {a for iss in issues(env) for a in iss["affected_ids"]}


# ---------------------------------------------------------------- tests
class TestRewardAttacks(unittest.TestCase):

    def assert_all_fp(self, env: AuditEnv, n: int):
        res = env.result
        self.assertTrue(res["valid"], res["error"])
        self.assertEqual(res["tp"], 0, [l for l in res["labels"] if l["tp"]])
        self.assertEqual(res["fp"], n)
        self.assertTrue(all(not l["tp"] for l in res["labels"]))

    # 1
    def test_oracle_beats_silence_on_dirty_books(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                r_oracle, _, info, env = play(seed, DIRTY, oracle_findings)
                self.assertEqual(info["tp"], len(issues(env)))
                self.assertEqual(r_oracle, 1.0)
                r_silent, _, _, _ = play(seed, DIRTY, lambda e, o: [])
                self.assertEqual(r_silent, -1.0)
                self.assertGreater(r_oracle, r_silent)

    # 2
    def test_silence_beats_false_accusations_on_clean_books(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                r_silent, _, _, env = play(seed, CLEAN, lambda e, o: [])
                self.assertEqual(issues(env), [])
                self.assertEqual(r_silent, 1.0)

                def fabricate(e, o):
                    t, b, ar = tables(e), base(e), ar_debit_rows(e)
                    invs = [i for i in t["invoices"] if i["invoice_id"] in ar]
                    out = []
                    for a, c in zip(invs[0:6:2], invs[1:6:2]):
                        out.append(finding("duplicate_invoice", [a["invoice_id"], c["invoice_id"]],
                                           ar[c["invoice_id"]]["debit_minor"], b, [a["doc_id"], c["doc_id"]]))
                    for i in invs[6:9]:
                        r = ar[i["invoice_id"]]
                        out.append(finding("fx_error", [i["invoice_id"]], max(1, r["debit_minor"] // 100), b,
                                           [i["doc_id"], r["row_id"]]))
                        out.append(finding("period_cutoff", [i["invoice_id"]], r["debit_minor"], b,
                                           [i["doc_id"], r["row_id"]]))
                    pays = [p for p in t["payments"] if p["invoice_refs"]]
                    for p in pays[:3]:
                        rows = [r["row_id"] for r in t["ledger"] if r["payment_id"] == p["payment_id"]]
                        ref = p["invoice_refs"][0]
                        out.append(finding("payment_allocation", [ref["invoice_id"], p["payment_id"]],
                                           max(1, abs(ref["amount_minor"]) // 10), b, [p["doc_id"], *rows[:2]]))
                    return out

                r_fake, _, info, env = play(seed, CLEAN, fabricate)
                self.assertGreaterEqual(info["fp"], 6)
                self.assert_all_fp(env, info["fp"])
                self.assertEqual(r_fake, -1.0)
                self.assertLess(r_fake, r_silent)

    # 3
    def test_duplicates_give_no_gain(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                r_once, _, _, _ = play(seed, DIRTY, oracle_findings)
                r_twice, _, info, env = play(seed, DIRTY, lambda e, o: [f for f in oracle_findings(e, o)
                                                                        for _ in range(2)])
                n = len(issues(env))
                self.assertEqual((info["tp"], info["fp"]), (n, n))
                self.assertLess(r_twice, r_once)
                labels = env.result["labels"]
                self.assertTrue(all(l["reason"] == "duplicate" for l in labels if not l["tp"]))

                r_one, _, _, _ = play(seed, DIRTY, lambda e, o: oracle_findings(e, o)[:1])
                r_five, _, info5, env5 = play(seed, DIRTY, lambda e, o: oracle_findings(e, o)[:1] * 5)
                self.assertEqual((info5["tp"], info5["fp"]), (1, 4))
                self.assertLess(r_five, r_one)

    # 4
    def test_flag_everything_is_bad(self):
        def flag_all(round_robin):
            def build(e, o):
                t, b, ar = tables(e), base(e), ar_debit_rows(e)
                invs, pays = t["invoices"], t["payments"]
                out = []
                pairs = ([(k, TYPES[k % 4]) for k in range(len(invs))] if round_robin
                         else [(k, ty) for k in range(len(invs)) for ty in TYPES])
                for k, ty in pairs[:30]:
                    inv = invs[k]
                    iid = inv["invoice_id"]
                    row = ar.get(iid)
                    amount = row["debit_minor"] if row else inv["total_minor"]
                    ev = [inv["doc_id"]] + ([row["row_id"]] if row else [])
                    if ty == "duplicate_invoice":
                        other = invs[(k + 1) % len(invs)]
                        ids, ev = [iid, other["invoice_id"]], ev + [other["doc_id"]]
                    elif ty == "payment_allocation":
                        p = pays[k % len(pays)]
                        ids, ev = [iid, p["payment_id"]], ev + [p["doc_id"]]
                    else:
                        ids = [iid]
                    out.append(finding(ty, ids, amount, b, ev))
                return out
            return build

        def all_types_wrong_amount(e, o):
            out = [from_issue(iss, type=ty, claimed_amount_minor=iss["expected_amount_minor"]
                              + tolerance(iss["expected_amount_minor"]) + 1000)
                   for iss in issues(e) for ty in TYPES]
            return out[:30]

        for seed in SEEDS:
            with self.subTest(seed=seed):
                r_oracle, _, _, _ = play(seed, DIRTY, oracle_findings)
                for rr in (False, True):
                    r_flag, _, info, _ = play(seed, DIRTY, flag_all(rr))
                    self.assertEqual(info["tp"] + info["fp"], 30)
                    self.assertLess(r_flag, 0.0)
                    self.assertLessEqual(r_flag, r_oracle - 1.0)
                r_wrong, _, info, env = play(seed, DIRTY, all_types_wrong_amount)
                self.assert_all_fp(env, 30)
                self.assertEqual(r_wrong, -1.0)

    # 5
    def test_step_economy_only_slightly_separates_equal_answers(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                rewards = {}
                for n in (0, 20, 60):
                    r, _, info, env = play(seed, DIRTY, oracle_findings, n_inspect=n)
                    self.assertEqual(info["inspection_steps"], n)
                    self.assertEqual(info["tp"], len(issues(env)))
                    rewards[n] = r
                self.assertGreaterEqual(len(issues(env)), 4)
                self.assertAlmostEqual(rewards[0] - rewards[20], 20 * 0.002, places=9)
                self.assertAlmostEqual(rewards[20] - rewards[60], 40 * 0.002, places=9)
                r_less, _, info, _ = play(seed, DIRTY, lambda e, o: oracle_findings(e, o)[:-1])
                self.assertEqual(info["fn"], 1)
                self.assertGreater(rewards[60], r_less)

    # 6
    def test_guessed_affected_ids_are_fp(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                def fake_suffix(e, o):
                    return [from_issue(iss, affected_ids=[a + "9" for a in iss["affected_ids"]])
                            for iss in issues(e)]

                def other_real(e, o):
                    t, used = tables(e), all_affected(e)
                    spare_inv = [i["invoice_id"] for i in t["invoices"] if i["invoice_id"] not in used]
                    spare_pay = [p["payment_id"] for p in t["payments"] if p["payment_id"] not in used]
                    out = []
                    for k, iss in enumerate(issues(e)):
                        ids = [(spare_pay if a in {p["payment_id"] for p in t["payments"]} else spare_inv)[k]
                               for a in iss["affected_ids"]]
                        out.append(from_issue(iss, affected_ids=ids))
                    return out

                def subset_superset(e, o):
                    t, used = tables(e), all_affected(e)
                    extra = next(i["invoice_id"] for i in t["invoices"] if i["invoice_id"] not in used)
                    out = [from_issue(iss, affected_ids=iss["affected_ids"] + [extra]) for iss in issues(e)]
                    out += [from_issue(iss, affected_ids=iss["affected_ids"][:1]) for iss in issues(e)
                            if len(iss["affected_ids"]) > 1]
                    return out

                for build in (fake_suffix, other_real, subset_superset):
                    r, _, info, env = play(seed, DIRTY, build)
                    self.assert_all_fp(env, info["fp"])
                    self.assertGreater(info["fp"], 0)
                    self.assertEqual(r, -1.0)

    # 7
    def test_unsupported_evidence_is_fp(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                def bad_evidence(e, o):
                    rng = random.Random(seed)
                    t = tables(e)
                    real = [r["row_id"] for r in t["ledger"]] + [d["doc_id"] for d in t["invoices"] + t["payments"]]
                    out = []
                    for iss in issues(e):
                        union = {x for s in iss["evidence_sets"] for x in s}
                        others = rng.sample([x for x in real if x not in union], 10)
                        out.append(from_issue(iss, evidence_ids=others))       # real but unrelated records
                        out.append(from_issue(iss, evidence_ids=[]))           # no evidence
                        partial = iss["evidence_sets"][0][:1]                  # incomplete set
                        if not any(set(s) <= set(partial) for s in iss["evidence_sets"]):
                            out.append(from_issue(iss, evidence_ids=partial))
                    return out

                def borrowed_evidence(e, o):
                    iss_ = issues(e)
                    out = []
                    for k, iss in enumerate(iss_):
                        donor = iss_[(k + 1) % len(iss_)]["evidence_sets"][0]
                        if not any(set(s) <= set(donor) for s in iss["evidence_sets"]):
                            out.append(from_issue(iss, evidence_ids=donor))
                    return out

                for build in (bad_evidence, borrowed_evidence):
                    r, _, info, env = play(seed, DIRTY, build)
                    self.assertGreater(info["fp"], 0)
                    self.assert_all_fp(env, info["fp"])
                    self.assertEqual(r, -1.0)

    # 8
    def test_foreign_currency_is_fp(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                def foreign(e, o):
                    t, b = tables(e), base(e)
                    exps = e._ep["manifest"]["amount_exponents"]
                    docs = {i["invoice_id"]: i["currency"] for i in t["invoices"]}
                    docs.update({p["payment_id"]: p["currency"] for p in t["payments"]})
                    any_foreign = next(i["currency"] for i in t["invoices"] if i["currency"] != b)
                    out = []
                    for iss in issues(e):
                        cur = next((docs[a] for a in iss["affected_ids"] if docs.get(a, b) != b), any_foreign)
                        out.append(from_issue(iss, currency=cur))  # same number, foreign label
                        fx = next(r for r in t["fx"] if r["source_currency"] == cur and r["target_currency"] == b)
                        amt = (Decimal(iss["expected_amount_minor"]) / Decimal(10) ** exps[b] / Decimal(fx["rate"])
                               * Decimal(10) ** exps[cur]).quantize(Decimal(1), rounding=ROUND_HALF_UP)
                        out.append(from_issue(iss, currency=cur, claimed_amount_minor=int(amt)))
                    return out

                r, _, info, env = play(seed, DIRTY, foreign)
                self.assert_all_fp(env, 2 * len(issues(env)))
                self.assertEqual(r, -1.0)

    # 9
    def test_resubmission_after_end(self):
        for seed in SEEDS:
            for config, first in ((DIRTY, oracle_findings), (CLEAN, lambda e, o: [])):
                with self.subTest(seed=seed, clean=config is CLEAN):
                    r1, _, _, env = play(seed, config, first)
                    self.assertEqual(r1, 1.0)
                    saved, saved_obj, n_log = copy.deepcopy(env.result), env.result, len(env.grader_log)
                    # second submit: a different answer (flag the truth twice, or a fake finding)
                    again = oracle_findings(env, {"manifest": env._ep["manifest"]}) * 2 or [
                        finding("period_cutoff", [tables(env)["invoices"][0]["invoice_id"]], 1, base(env),
                                [tables(env)["invoices"][0]["doc_id"]])]
                    for action in ({"type": "submit", "findings": {"episode_id": env.episode_id,
                                                                   "findings": again}},
                                   {"type": "list_records", "table": "ledger"}):
                        obs, reward, term, trunc, info = env.step(action)
                        self.assertEqual(obs["error"]["code"], "episode_over")
                        self.assertEqual(reward, 0.0)
                        self.assertIsNone(obs["result"])
                        self.assertEqual(info, {})
                        self.assertIs(env.result, saved_obj)
                        self.assertEqual(env.result, saved)
                        self.assertEqual(len(env.grader_log), n_log)

    # 10
    def test_bad_input_terminates_with_minus_one(self):
        def cases(env, obs):
            ep = env.episode_id
            good = oracle_findings(env, obs)
            out = [
                ("findings missing", {"type": "submit"}),
                ("findings is list", {"type": "submit", "findings": good}),
                ("findings is str", {"type": "submit", "findings": "all of them"}),
                ("findings.findings is dict", {"type": "submit", "findings": {"episode_id": ep,
                                                                              "findings": good[0]}}),
                ("finding not dict", {"type": "submit", "findings": {"episode_id": ep,
                                                                     "findings": good[:-1] + ["x"]}}),
                ("31 findings", {"type": "submit", "findings": {"episode_id": ep,
                                                                "findings": (good * 31)[:31]}}),
                ("wrong episode_id", {"type": "submit", "findings": {"episode_id": "ep_000000000000",
                                                                     "findings": good}}),
                ("no episode_id", {"type": "submit", "findings": {"findings": good}}),
                ("bool amount", {"type": "submit", "findings": {"episode_id": ep, "findings": [
                    dict(good[0], claimed_amount_minor=True)]}}),
                ("negative amount", {"type": "submit", "findings": {"episode_id": ep, "findings": [
                    dict(good[0], claimed_amount_minor=-5)]}}),
                ("11 evidence ids", {"type": "submit", "findings": {"episode_id": ep, "findings": [
                    dict(good[0], evidence_ids=[r["row_id"] for r in tables(env)["ledger"][:11]])]}}),
            ]
            for key in ("type", "affected_ids", "claimed_amount_minor", "currency", "evidence_ids"):
                bad = [dict(f) for f in good]
                del bad[0][key]
                out.append((f"missing {key}", {"type": "submit", "findings": {"episode_id": ep,
                                                                              "findings": bad}}))
            return out

        env0, obs0 = new_env(SEEDS[0], DIRTY)
        names = [name for name, _ in cases(env0, obs0)]
        for seed in SEEDS:
            for idx, name in enumerate(names):
                with self.subTest(seed=seed, case=name):
                    env, obs = new_env(seed, DIRTY)
                    action = cases(env, obs)[idx][1]
                    obs, reward, term, trunc, info = env.step(action)
                    self.assertTrue(term)
                    self.assertFalse(trunc)
                    self.assertEqual(reward, -1.0)
                    self.assertEqual(obs["error"]["code"], "invalid_findings")
                    self.assertFalse(env.result["valid"])
                    self.assertFalse(info["valid"])

    # 11
    def test_timeout(self):
        for seed in SEEDS:
            for config in (DIRTY, CLEAN):
                with self.subTest(seed=seed, clean=config is CLEAN, limit="steps"):
                    env, _ = new_env(seed, config)
                    for k in range(1, 101):
                        obs, reward, term, trunc, info = env.step(
                            {"type": "list_records", "table": "payments", "cursor": None, "limit": 1})
                        self.assertFalse(term)
                        if k < 100:
                            self.assertFalse(trunc)
                            self.assertEqual(reward, 0.0)
                    self.assertTrue(trunc)
                    res = env.result
                    self.assertTrue(res["valid"])
                    self.assertEqual((res["tp"], res["fp"]), (0, 0))
                    self.assertEqual(res["inspection_steps"], 100)
                    f1 = 1.0 if not issues(env) else 0.0
                    self.assertEqual(res["f1"], f1)
                    self.assertEqual(reward, expected_reward(f1, 100))
                    self.assertEqual(reward, 0.8 if not issues(env) else -1.0)
                    self.assertEqual(env.grader_log[-1]["end"], "step_limit")

                with self.subTest(seed=seed, clean=config is CLEAN, limit="time"):
                    cfg = dict(config, time_limit_s=0)
                    for late_submit in (False, True):
                        env, obs0 = new_env(seed, cfg)
                        action = ({"type": "submit", "findings": {"episode_id": env.episode_id,
                                                                  "findings": oracle_findings(env, obs0)}}
                                  if late_submit else {"type": "list_records", "table": "ledger"})
                        obs, reward, term, trunc, info = env.step(action)
                        self.assertTrue(trunc)
                        self.assertFalse(term)
                        self.assertEqual(obs["error"]["code"], "time_limit")
                        f1 = 1.0 if not issues(env) else 0.0
                        self.assertEqual(env.result["tp"], 0)  # a late answer is not graded
                        self.assertEqual(reward, expected_reward(f1, 1))
                        self.assertEqual(env.grader_log[-1]["end"], "time_limit")

    # 12
    def test_amount_tolerance_cannot_be_gamed(self):
        for seed in SEEDS:
            with self.subTest(seed=seed):
                def outside(e, o):
                    out = []
                    for iss in issues(e):
                        exp, tol = iss["expected_amount_minor"], tolerance(iss["expected_amount_minor"])
                        out.append(from_issue(iss, claimed_amount_minor=exp + tol + 1))
                        if exp - tol - 1 >= 0:
                            out.append(from_issue(iss, claimed_amount_minor=exp - tol - 1))
                    return out

                r, _, info, env = play(seed, DIRTY, outside)
                self.assert_all_fp(env, info["fp"])
                self.assertGreaterEqual(info["fp"], len(issues(env)))
                self.assertEqual(r, -1.0)

                for sign in (1, -1):
                    def edge(e, o, sign=sign):
                        return [from_issue(iss, claimed_amount_minor=iss["expected_amount_minor"]
                                           + sign * tolerance(iss["expected_amount_minor"]))
                                for iss in issues(e)]
                    r, _, info, env = play(seed, DIRTY, edge)
                    self.assertEqual((info["tp"], info["fp"]), (len(issues(env)), 0))
                    self.assertEqual(r, 1.0)

    # 13: HANDOFF R1 Automated Attack Search
    def test_handoff_r1_automatic_attack_search(self):
        result = run_attack_search()
        self.assertTrue(result.passed, result.summary())
        self.assertGreaterEqual(result.total_mutations, 10000)
        self.assertEqual(result.total_violations, 0, [v.__dict__ for v in result.violations])
        self.assertEqual(len(result.seeds_evaluated), 20)
        self.assertGreaterEqual(len(result.clean_seeds), 4)
        self.assertGreaterEqual(len(result.dirty_seeds), 10)
        for fam in MUTATION_FAMILIES:
            self.assertIn(fam, result.mutations_by_family)
            self.assertGreater(result.mutations_by_family[fam], 0, f"family {fam} had no mutations")

    # 14: HANDOFF R1 Attack Search Reproducibility
    def test_handoff_r1_attack_search_reproducible(self):
        r1 = run_attack_search()
        r2 = run_attack_search()
        self.assertEqual(r1.total_mutations, r2.total_mutations)
        self.assertEqual(r1.total_violations, r2.total_violations)
        self.assertEqual(r1.mutations_by_family, r2.mutations_by_family)
        self.assertEqual(r1.seeds_evaluated, r2.seeds_evaluated)

    # 15: HANDOFF R1 Invariant and Defect Checks
    def test_handoff_r1_mutation_invariants_and_defect_checks(self):
        env_dirty, obs_dirty = new_env(9014, DIRTY)
        truth_dirty = env_dirty._ep["truth"]
        ep_id_dirty = env_dirty.episode_id
        rng = random.Random(42)
        muts_dirty = generate_mutations_for_episode(env_dirty._ep, rng=rng, per_seed_target=100)
        self.assertGreaterEqual(len(muts_dirty), 100)

        honest_dirty = {"episode_id": ep_id_dirty, "findings": [from_issue(i) for i in truth_dirty["issues"]]}
        for m in muts_dirty:
            v = evaluate_mutation(m, truth_dirty, honest_dirty, False, 9014, ep_id_dirty)
            self.assertIsNone(v, f"Violation on dirty seed: {v}")

        env_clean, _ = new_env(9000, CLEAN)
        truth_clean = env_clean._ep["truth"]
        ep_id_clean = env_clean.episode_id
        muts_clean = generate_mutations_for_episode(env_clean._ep, rng=rng, per_seed_target=100)
        self.assertGreaterEqual(len(muts_clean), 100)

        honest_clean = {"episode_id": ep_id_clean, "findings": []}
        for m in muts_clean:
            v = evaluate_mutation(m, truth_clean, honest_clean, True, 9000, ep_id_clean)
            self.assertIsNone(v, f"Violation on clean seed: {v}")

    # 16: HANDOFF R1 Empty Seed Selection Prevention
    def test_handoff_r1_empty_seed_selection_prevented(self):
        with self.assertRaises(ValueError):
            run_attack_search(seeds=[99999])
        with self.assertRaises(ValueError):
            run_attack_search(seeds=[])

    # 17: HANDOFF R1 Failure Report Artifact Regression Test with Simulated Violation
    def test_handoff_r1_failure_report_artifact_on_simulated_violation(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_report_path = tmp.name

        try:
            # Simulate a violation: an honest variation that was maliciously corrupted to fail matching
            def inject_bad_mutation(ep, rng):
                truth = ep["truth"]
                ep_id = ep["episode_id"]
                iss = truth["issues"][0]
                exp = iss["expected_amount_minor"]
                tol = tolerance(exp)
                # Over-tolerance amount falsely claimed as honest variation -> triggers honest_boundary_variation_rejected
                bad_f = from_issue(iss, claimed_amount_minor=exp + tol + 9999)
                return [
                    MutationCandidate(
                        family="amount_tolerance",
                        name="simulated_flawed_honest_variation",
                        submission={"episode_id": ep_id, "findings": [bad_f]},
                        is_honest_variation=True,
                        inspection_steps=0,
                    )
                ]

            res = run_attack_search(
                seeds=[9014],
                min_mutations=1,
                per_seed_target=5,
                report_path=tmp_report_path,
                _extra_mutations_factory=inject_bad_mutation,
            )

            self.assertFalse(res.passed)
            self.assertGreaterEqual(res.total_violations, 1)
            self.assertTrue(os.path.isfile(tmp_report_path))

            with open(tmp_report_path) as fh:
                data = json.load(fh)

            self.assertFalse(data["passed"])
            self.assertGreaterEqual(data["total_violations"], 1)
            self.assertTrue(len(data["violations"]) >= 1)

            # Verify complete reproducible record format of each violation
            v = data["violations"][0]
            required_keys = {
                "seed",
                "episode_id",
                "config",
                "is_clean",
                "family",
                "mutation_name",
                "reason",
                "honest_reward",
                "attack_reward",
                "inspection_steps",
                "submission",
                "result",
            }
            self.assertTrue(required_keys <= set(v.keys()), f"Missing keys in violation record: {required_keys - set(v.keys())}")
            self.assertIsInstance(v["config"], dict)
            self.assertIsInstance(v["submission"], dict)
            self.assertIn("episode_id", v["submission"])
            self.assertIn("findings", v["submission"])
            self.assertIsInstance(v["result"], dict)
            self.assertIn("tp", v["result"])
            self.assertIn("fp", v["result"])
            self.assertIn("reward", v["result"])
            self.assertEqual(v["inspection_steps"], 0)

        finally:
            if os.path.exists(tmp_report_path):
                os.remove(tmp_report_path)


if __name__ == "__main__":
    unittest.main()
