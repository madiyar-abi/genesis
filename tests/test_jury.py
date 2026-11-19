"""The jury's checklist as explicit tests: contract, leaks, matcher/reward, reproducibility, data.

Each test names the jury item it covers. Many items are also tested in more depth elsewhere
(test_env, test_matcher, test_reward_attacks, test_transform, test_verify); this file keeps the
whole list in one place so a reviewer can map criteria to tests.
"""

import copy
import json
import os
import unittest

from auditenv.env import AuditEnv
from auditenv.generator import ISSUE_TYPES, SCENARIOS, generate
from auditenv.load import load_episode
from auditenv.matcher import grade
from auditenv.metrics import terminal_reward
from auditenv.run import make_policy, run_episode
from auditenv.verify import Books, revert
from tests.test_schemas import _SCHEMA_ROOT, _matches

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRTY = {"errors": {t: 1 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}
CLEAN = {"errors": {}}
FORBIDDEN = ("truth", "provenance", "evidence_sets", "expected_amount_minor", "issue_id", "injections",
             "grader", "transform_seed")


def _exported():
    for split in ("train", "dev"):
        base = os.path.join(ROOT, "episodes", split)
        with open(os.path.join(base, "index.json")) as fh:
            for entry in json.load(fh):
                yield split, entry, load_episode(os.path.join(base, entry["episode_id"]))


def _oracle_findings(truth):
    return [{"type": i["type"], "affected_ids": list(i["affected_ids"]), "claimed_amount_minor":
             i["expected_amount_minor"], "currency": i["currency"], "evidence_ids": list(i["evidence_sets"][0])}
            for i in truth["issues"]]


class ContractTests(unittest.TestCase):
    """Jury 1: reset/step contract, bounded errors, termination."""

    def setUp(self):
        self.env = AuditEnv()
        self.obs, _ = self.env.reset(31, DIRTY)
        self.eid = self.obs["manifest"]["episode_id"]

    def step(self, action):
        return self.env.step(action)

    def assertBoundedError(self, action, code, step=1):
        obs, reward, term, trunc, info = self.step(action)
        self.assertEqual(obs["error"]["code"], code, action)
        self.assertLessEqual(len(obs["error"]["message"]), 200)
        self.assertEqual(obs["step"], step)  # the step is consumed
        self.assertEqual((reward, term, trunc, info), (0.0, False, False, {}))
        self.assertEqual(set(obs), {"step", "steps_remaining", "result", "error"})

    def test_invalid_action_name(self):
        self.assertBoundedError({"type": "run_sql", "query": "select *"}, "unknown_action")

    def test_invalid_table(self):
        self.assertBoundedError({"type": "list_records", "table": "truth"}, "unknown_table")

    def test_cursor_beyond_data(self):
        self.assertBoundedError({"type": "list_records", "table": "ledger", "cursor": "ledger:100000"}, "bad_params")

    def test_cursor_exactly_at_end_gives_empty_page(self):
        n = self.obs["manifest"]["counts"]["fx"]
        obs, *_ = self.step({"type": "list_records", "table": "fx", "cursor": f"fx:{n}"})
        self.assertIsNone(obs["error"])
        self.assertEqual((obs["result"]["rows"], obs["result"]["next_cursor"]), ([], None))

    def test_get_record_unknown_id(self):
        self.assertBoundedError({"type": "get_record", "table": "ledger", "id": "NO-SUCH-ROW"}, "not_found")

    def test_get_document_unknown_doc(self):
        self.assertBoundedError({"type": "get_document", "doc_id": "NO-SUCH-DOC"}, "not_found")

    def test_calculator_rejects_code_and_division_by_zero(self):
        for k, expr in enumerate(("__import__('os').system('id')", "open('/etc/passwd').read()", "2**64",
                                  "(lambda: 1)()", "1/0"), start=1):
            self.assertBoundedError({"type": "calculator", "expression": expr}, "calc_error", step=k)

    def test_calculator_decimal_arithmetic(self):
        obs, *_ = self.step({"type": "calculator", "expression": "(1250.00 * 1.0842) / 2"})
        self.assertEqual(obs["result"], {"value": "677.625"})

    def test_submit_invalid_structure_ends_with_minus_one(self):
        for bad in ("not json", None, {"episode_id": self.eid}, {"episode_id": "other", "findings": []},
                    {"episode_id": self.eid, "findings": [{"type": "fraud"}]}):
            self.env.reset(31, DIRTY)
            obs, reward, term, trunc, _ = self.step({"type": "submit", "findings": bad})
            self.assertEqual((reward, term, trunc), (-1.0, True, False), bad)
            self.assertEqual(obs["error"]["code"], "invalid_findings")

    def test_submit_empty_findings_on_dirty_books(self):
        obs, reward, term, trunc, info = self.step({"type": "submit", "findings": {"episode_id": self.eid,
                                                                                    "findings": []}})
        self.assertTrue(term and not trunc)
        self.assertEqual(reward, -1.0)  # F1 = 0 on dirty books, no inspection steps
        self.assertEqual(info["fn"], len(self.env._ep["truth"]["issues"]))

    def test_resubmission_and_actions_after_terminated(self):
        self.step({"type": "submit", "findings": {"episode_id": self.eid, "findings": []}})
        result = copy.deepcopy(self.env.result)
        for action in ({"type": "submit", "findings": {"episode_id": self.eid,
                                                       "findings": _oracle_findings(self.env._ep["truth"])}},
                       {"type": "list_records", "table": "ledger"}):
            obs, reward, term, trunc, info = self.step(action)
            self.assertEqual(obs["error"]["code"], "episode_over")
            self.assertEqual((reward, info, obs["step"]), (0.0, {}, 1))
            self.assertTrue(term)
        self.assertEqual(self.env.result, result)  # the grade cannot be replaced

    def test_step_101_and_actions_after_truncated(self):
        for k in range(1, 101):
            obs, reward, term, trunc, _ = self.step({"type": "calculator", "expression": "1+1"})
            self.assertEqual(trunc, k == 100)
            self.assertFalse(term)
        self.assertEqual(obs["steps_remaining"], 0)
        self.assertEqual(reward, -1.0)  # empty answer on dirty books, train mode
        for action in ({"type": "calculator", "expression": "1"},
                       {"type": "submit", "findings": {"episode_id": self.eid, "findings": []}}):
            obs, reward, term, trunc, info = self.step(action)
            self.assertEqual(obs["error"]["code"], "episode_over")
            self.assertEqual((obs["step"], reward, trunc, info), (100, 0.0, True, {}))

    def test_tools_list_is_exactly_five_actions(self):
        self.assertEqual([t["type"] for t in self.obs["tools"]],
                         ["list_records", "get_record", "get_document", "calculator", "submit"])


class LeakTests(unittest.TestCase):
    """Jury 1: truth, provenance and seed never reach the policy."""

    def _all_text(self, mode):
        env, texts = AuditEnv(), []
        for policy in ("reconcile", "random", "flag_all"):
            traj = run_episode(env, None, 4242, {**DIRTY, "mode": mode},
                               policy_factory=lambda e: make_policy(policy, e, 1))
            texts += [json.dumps(t["observation"]) for t in traj]
            obs, _ = env.reset(4242, {**DIRTY, "mode": mode})
            for action in ({"type": "get_record", "table": "ledger", "id": "../grader/truth.json"},
                           {"type": "get_document", "doc_id": "/etc/passwd"},
                           {"type": "calculator", "expression": "__import__('os')"},
                           {"type": "list_records", "table": "provenance"}):
                texts.append(json.dumps(env.step(action)))
        return texts, env

    def test_no_truth_keys_or_paths_in_any_observation(self):
        for mode in ("train", "eval"):
            texts, env = self._all_text(mode)
            for text in texts:
                for word in FORBIDDEN + ("Traceback", "/Users/", ".py\"", "seed"):
                    self.assertNotIn(word, text, (mode, word))

    def test_intermediate_reward_is_zero_and_eval_hides_the_result(self):
        env = AuditEnv()
        for mode in ("train", "eval"):
            traj = run_episode(env, None, 77, {**DIRTY, "mode": mode},
                               policy_factory=lambda e: make_policy("reconcile", e))
            self.assertTrue(all(t["reward"] == 0.0 for t in traj[:-1]))
            if mode == "eval":
                self.assertEqual(traj[-1]["reward"], 0.0)
                obs, reward, term, trunc, info = env.step({"type": "calculator", "expression": "1"})
                self.assertEqual(info, {})
            else:
                self.assertGreater(traj[-1]["reward"], 0.9)

    def test_eval_info_is_empty_on_every_step(self):
        env = AuditEnv()
        obs, info = env.reset(78, {**DIRTY, "mode": "eval"})
        self.assertEqual(set(info), {"episode_id", "mode", "max_steps"})
        eid = obs["manifest"]["episode_id"]
        for action in ({"type": "list_records", "table": "ledger"},
                       {"type": "submit", "findings": {"episode_id": eid, "findings": _oracle_findings(
                           env._ep["truth"])}}):
            obs, reward, term, trunc, info = env.step(action)
            self.assertEqual((reward, info), (0.0, {}))
        self.assertEqual(obs["result"], {"submitted": True})


class RewardTests(unittest.TestCase):
    """Jury 3: matcher and reward on a real episode."""

    @classmethod
    def setUpClass(cls):
        cls.ep = generate(55, DIRTY)
        cls.eid, cls.truth = cls.ep["episode_id"], cls.ep["truth"]
        cls.correct = _oracle_findings(cls.truth)

    def grade(self, findings, steps=0, truth=None):
        return grade(truth or self.truth, {"episode_id": self.eid, "findings": findings}, self.eid, steps)

    def one(self, **change):
        f = copy.deepcopy(self.correct[0])
        f.update(change)
        return f

    def test_exact_match_is_tp(self):
        r = self.grade(self.correct)
        self.assertEqual((r["tp"], r["fp"], r["fn"], r["f1"], r["reward"]), (len(self.correct), 0, 0, 1.0, 1.0))

    def test_each_wrong_field_is_a_false_positive(self):
        other = next(t for t in ISSUE_TYPES if t != self.correct[0]["type"])
        exp = self.correct[0]["claimed_amount_minor"]
        for bad in (self.one(type=other), self.one(claimed_amount_minor=exp + max(1, exp // 1000) + 1),
                    self.one(currency="ZZZ" if self.correct[0]["currency"] != "ZZZ" else "YYY"),
                    self.one(evidence_ids=self.correct[0]["evidence_ids"][:1]),
                    self.one(affected_ids=["GUESSED-ID"])):
            r = self.grade([bad] + self.correct[1:])
            self.assertEqual((r["tp"], r["fp"], r["fn"]), (len(self.correct) - 1, 1, 1), bad)

    def test_extra_finding_fp_missing_finding_fn(self):
        r = self.grade(self.correct + [self.one(affected_ids=["NOT-AN-ISSUE"])])
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (len(self.correct), 1, 0))
        r = self.grade(self.correct[1:])
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (len(self.correct) - 1, 0, 1))

    def test_duplicate_finding_is_one_tp_and_one_fp(self):
        r = self.grade(self.correct + [self.correct[0]])
        self.assertEqual((r["tp"], r["fp"]), (len(self.correct), 1))
        self.assertLess(r["reward"], self.grade(self.correct)["reward"])

    def test_clean_company_silence_vs_accusation(self):
        ep = generate(56, CLEAN)
        silent = grade(ep["truth"], {"episode_id": ep["episode_id"], "findings": []}, ep["episode_id"], 10)
        self.assertEqual((silent["f1"], silent["reward"]), (1.0, 0.98))
        accuse = grade(ep["truth"], {"episode_id": ep["episode_id"], "findings": [self.one()]}, ep["episode_id"], 10)
        self.assertEqual(accuse["f1"], 0.0)
        self.assertLess(accuse["reward"], 0)

    def test_flag_all_is_strongly_negative(self):
        env = AuditEnv()
        rewards = [run_episode(env, None, s, cfg, policy_factory=lambda e: make_policy("flag_all", e))[-1]["reward"]
                   for s in range(10) for cfg in (DIRTY, CLEAN)]
        self.assertLessEqual(max(rewards), -0.9)

    def test_reward_formula_edge_cases(self):
        self.assertEqual(terminal_reward(1.0, 0), 1.0)
        self.assertEqual(terminal_reward(1.0, 100), 0.8)
        self.assertEqual(terminal_reward(0.0, 0), -1.0)
        self.assertEqual(terminal_reward(0.0, 100), -1.0)  # clipped
        self.assertEqual(terminal_reward(0.5, 50), -0.1)
        self.assertEqual(self.grade(self.correct, steps=99)["reward"], 0.802)


class ReproducibilityTests(unittest.TestCase):
    """Jury 4: determinism, seed sensitivity, transform invariance."""

    def test_same_seed_byte_identical_different_seed_different(self):
        a, b = generate(91, DIRTY), generate(91, DIRTY)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        c = generate(92, DIRTY)
        self.assertNotEqual(a["episode_id"], c["episode_id"])
        self.assertNotEqual(a["tables"], c["tables"])

    def test_transform_keeps_oracle_reward_with_new_ids(self):
        env = AuditEnv()
        for seed in (93, 94, 95):
            base = run_episode(env, None, seed, DIRTY, policy_factory=lambda e: make_policy("oracle", e))
            old_ids = {i for iss in env._ep["truth"]["issues"] for i in iss["affected_ids"]}
            moved = run_episode(env, None, seed, {**DIRTY, "transform_seed": 5},
                                policy_factory=lambda e: make_policy("oracle", e))
            new_ids = {i for iss in env._ep["truth"]["issues"] for i in iss["affected_ids"]}
            self.assertEqual(base[-1]["reward"], moved[-1]["reward"])
            self.assertFalse(old_ids & new_ids)


class DataTests(unittest.TestCase):
    """Jury 2: the exported train/dev episodes."""

    @classmethod
    def setUpClass(cls):
        cls.episodes = list(_exported())
        cls.schemas = {p.name: json.loads(p.read_text()) for p in _SCHEMA_ROOT.glob("*.schema.json")}

    def test_twenty_episodes_exported(self):
        self.assertEqual(len(self.episodes), 20)

    def test_balanced_before_and_after_errors(self):
        for split, entry, ep in self.episodes:
            for tables in (revert(ep), ep["tables"]):
                books = Books(ep["manifest"], tables)
                for jid, rows in books.journals().items():
                    self.assertEqual(sum(r["debit_minor"] for r in rows), sum(r["credit_minor"] for r in rows),
                                     (entry["episode_id"], jid))
            pre_issues, pre_problems = Books(ep["manifest"], revert(ep)).discrepancies()
            self.assertEqual((pre_issues, pre_problems), ([], []), entry["episode_id"])

    def test_every_evidence_id_reachable_through_the_tools(self):
        env = AuditEnv()
        for split, entry, ep in self.episodes:
            env.reset(entry["seed"], entry["config"])
            self.assertEqual(env.episode_id, entry["episode_id"])
            for iss in ep["truth"]["issues"]:
                for ev in {i for s in iss["evidence_sets"] for i in s}:
                    hit = False
                    for action in ({"type": "get_document", "doc_id": ev},
                                   {"type": "get_record", "table": "ledger", "id": ev},
                                   {"type": "get_record", "table": "fx", "id": ev}):
                        env.reset(entry["seed"], entry["config"])
                        hit |= env.step(action)[0]["error"] is None
                    self.assertTrue(hit, (entry["episode_id"], ev))

    def test_manifests_match_the_schema(self):
        for split, entry, ep in self.episodes:
            self.assertTrue(_matches(ep["manifest"], self.schemas["manifest.schema.json"], "manifest.schema.json",
                                     self.schemas), entry["episode_id"])
            self.assertTrue(_matches(ep["truth"], self.schemas["truth.schema.json"], "truth.schema.json",
                                     self.schemas), entry["episode_id"])

    def test_coverage_types_scenarios_clean(self):
        types, scenarios, clean = set(), set(), 0
        for split, entry, ep in self.episodes:
            issues = ep["truth"]["issues"]
            clean += not issues
            types |= {i["type"] for i in issues}
            scenarios |= {i["scenario"] for i in issues}
        self.assertEqual(types, set(ISSUE_TYPES))
        self.assertTrue(set(SCENARIOS) <= scenarios)
        self.assertGreaterEqual(clean, 4)


class EdgeCaseDataTests(unittest.TestCase):
    """Jury 2: the hard bookkeeping cases occur and are booked correctly (verifier: 0 discrepancies)."""

    @classmethod
    def setUpClass(cls):
        cls.eps = [generate(s, CLEAN) for s in range(60)]

    def _with(self, pred):
        hits = [ep for ep in self.eps if pred(ep)]
        self.assertTrue(hits)
        for ep in hits:
            self.assertEqual(ep["truth"]["issues"], [])
            pre, problems = Books(ep["manifest"], ep["tables"]).discrepancies()
            self.assertEqual((pre, problems), ([], []), ep["episode_id"])
        return hits

    def test_zero_exponent_currency(self):
        hits = self._with(lambda ep: "JPY" in {i["currency"] for i in ep["tables"]["invoices"]})
        for ep in hits:
            self.assertEqual(ep["manifest"]["amount_exponents"]["JPY"], 0)

    def test_refunds_split_multi_invoice_and_unidentified_payments(self):
        self._with(lambda ep: any(p["amount_minor"] < 0 for p in ep["tables"]["payments"]))
        self._with(lambda ep: any(p["invoice_refs"] is None for p in ep["tables"]["payments"]))
        self._with(lambda ep: any(len(p["invoice_refs"] or []) > 1 for p in ep["tables"]["payments"]))
        refs = lambda ep: [r["invoice_id"] for p in ep["tables"]["payments"] for r in p["invoice_refs"] or []]
        self._with(lambda ep: len(refs(ep)) > len(set(refs(ep))))  # an invoice paid in several payments

    def test_midnight_documents_use_the_company_timezone(self):
        from datetime import date as _date

        def crossing(ep):
            books = Books(ep["manifest"], ep["tables"])
            for inv in ep["tables"]["invoices"]:
                written = _date.fromisoformat(inv["issued_at"][:10])
                if written != books.cdate(inv["issued_at"]) and (books.in_period(inv["issued_at"])
                                                                  != (books.ps <= written <= books.pe)):
                    return True
            return False

        self._with(crossing)


if __name__ == "__main__":
    unittest.main()
