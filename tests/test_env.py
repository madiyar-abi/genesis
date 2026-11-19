"""Tests for auditenv.env.AuditEnv (CONTRACT §4) on real generated episodes."""

import json
import unittest

from auditenv.env import AuditEnv

DIRTY = {"errors": {"duplicate_invoice": 1, "payment_allocation": 1, "fx_error": 1, "period_cutoff": 1},
         "interacting": {"I1": 1, "I2": 1}}
CLEAN = {"errors": {}}
SEED = 11
ID_KEYS = {"ledger": "row_id", "invoices": "invoice_id", "payments": "payment_id", "fx": "fx_id"}
CALC = {"type": "calculator", "expression": "1+1"}
FORBIDDEN_KEYS = {"truth", "evidence_sets", "expected_amount_minor", "issue_id", "provenance", "seed"}


def oracle_findings(env):
    """Grader-side: the perfect submission built from truth (test-only)."""
    return {"episode_id": env.episode_id, "findings": [
        {"type": i["type"], "affected_ids": list(i["affected_ids"]),
         "claimed_amount_minor": i["expected_amount_minor"], "currency": i["currency"],
         "evidence_ids": list(i["evidence_sets"][0]), "explanation": "t"}
        for i in env._ep["truth"]["issues"]]}


def all_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from all_keys(v)


class EnvTestBase(unittest.TestCase):
    def make(self, config=DIRTY, seed=SEED, **over):
        env = AuditEnv()
        obs, info = env.reset(seed, {**config, **over})
        return env, obs, info

    def assertBoundedError(self, env, action, code):
        before = env._steps
        obs, reward, term, trunc, info = env.step(action)
        self.assertIsNotNone(obs["error"], action)
        self.assertEqual(obs["error"]["code"], code, action)
        self.assertLessEqual(len(obs["error"]["message"]), 200)
        self.assertIsNone(obs["result"])
        self.assertEqual(obs["step"], before + 1, "error must consume a step")
        self.assertEqual(reward, 0.0)
        self.assertFalse(term or trunc)
        return obs


class ResetTests(EnvTestBase):
    def test_reset_observation_and_info(self):
        env, obs, info = self.make()
        self.assertEqual(set(obs), {"task", "manifest", "policy", "tools", "steps_remaining"})
        self.assertEqual(obs["steps_remaining"], 100)
        self.assertEqual(info["episode_id"], obs["manifest"]["episode_id"])
        self.assertEqual(info["episode_id"], env.episode_id)
        self.assertEqual({t["type"] for t in obs["tools"]},
                         {"list_records", "get_record", "get_document", "calculator", "submit"})
        json.dumps(obs), json.dumps(info)

    def test_unknown_config_key(self):
        with self.assertRaises(ValueError):
            AuditEnv().reset(1, {"errors": {}, "bogus": 1})

    def test_reproducible(self):
        def play(seed, config):
            env = AuditEnv()
            obs, info = env.reset(seed, config)
            out = [(obs, info)]
            obs, *rest = env.step({"type": "list_records", "table": "ledger", "cursor": None, "limit": 5})
            out.append((obs, *rest))
            rid = obs["result"]["rows"][2]["row_id"]
            for a in ({"type": "get_record", "table": "ledger", "id": rid},
                      {"type": "list_records", "table": "invoices", "cursor": obs["result"]["next_cursor"]
                       .replace("ledger", "invoices"), "limit": 3},
                      {"type": "get_record", "table": "fx", "id": "nope"},
                      {"type": "calculator", "expression": "10/4"},
                      {"type": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}}):
                out.append(env.step(a))
            return out

        a, b = play(SEED, DIRTY), play(SEED, DIRTY)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        c = play(SEED + 1, DIRTY)
        self.assertNotEqual(a[0][1]["episode_id"], c[0][1]["episode_id"])

    def test_reset_isolates_state(self):
        env, obs, info = self.make()
        env.step(CALC)
        env.step({"type": "submit", "findings": {"episode_id": env.episode_id, "findings": []}})
        self.assertIsNotNone(env.result)
        obs, info = env.reset(SEED, DIRTY)
        self.assertIsNone(env.result)
        self.assertEqual(obs["steps_remaining"], 100)
        obs, reward, term, trunc, info = env.step(CALC)
        self.assertEqual(obs["step"], 1)
        self.assertEqual(obs["steps_remaining"], 99)
        self.assertIsNone(obs["error"])
        self.assertEqual(obs["result"], {"value": "2"})
        self.assertFalse(term or trunc)

    def test_step_before_reset(self):
        with self.assertRaises(RuntimeError):
            AuditEnv().step(CALC)


class ToolTests(EnvTestBase):
    def test_list_records_limit_clamped(self):
        env, obs, _ = self.make()
        o, *_ = env.step({"type": "list_records", "table": "ledger", "cursor": None, "limit": 1000})
        self.assertIsNone(o["error"])
        self.assertEqual(len(o["result"]["rows"]), 50)
        self.assertEqual(o["result"]["total"], obs["manifest"]["counts"]["ledger"])
        self.assertEqual(set(o["result"]), {"rows", "next_cursor", "total"})

    def test_paging_visits_every_row_once(self):
        env, obs, _ = self.make()
        counts = obs["manifest"]["counts"]
        for table, key in ID_KEYS.items():
            with self.subTest(table=table):
                seen, cursor = [], None
                while True:
                    o, *_ = env.step({"type": "list_records", "table": table, "cursor": cursor, "limit": 1000})
                    self.assertIsNone(o["error"])
                    self.assertLessEqual(len(o["result"]["rows"]), 50)
                    self.assertEqual(o["result"]["total"], counts[table])
                    seen += [r[key] for r in o["result"]["rows"]]
                    cursor = o["result"]["next_cursor"]
                    if cursor is None:
                        break
                self.assertEqual(len(seen), counts[table])
                self.assertEqual(len(set(seen)), counts[table])

    def test_paging_small_limit(self):
        env, obs, _ = self.make()
        seen, cursor = [], None
        while True:
            o, *_ = env.step({"type": "list_records", "table": "payments", "cursor": cursor, "limit": 7})
            self.assertLessEqual(len(o["result"]["rows"]), 7)
            seen += [r["payment_id"] for r in o["result"]["rows"]]
            cursor = o["result"]["next_cursor"]
            if cursor is None:
                break
        self.assertEqual(sorted(seen), sorted(set(seen)))
        self.assertEqual(len(seen), obs["manifest"]["counts"]["payments"])

    def test_cursor_stable(self):
        env, _, _ = self.make()
        o1, *_ = env.step({"type": "list_records", "table": "ledger", "cursor": None, "limit": 10})
        cur = o1["result"]["next_cursor"]
        self.assertIsInstance(cur, str)
        o2, *_ = env.step({"type": "list_records", "table": "ledger", "cursor": cur, "limit": 10})
        env.step({"type": "list_records", "table": "fx", "cursor": None, "limit": 30})
        o3, *_ = env.step({"type": "list_records", "table": "ledger", "cursor": cur, "limit": 10})
        self.assertEqual(o2["result"], o3["result"])
        self.assertNotEqual(o1["result"]["rows"], o2["result"]["rows"])
        # Same cursor in a fresh env with same seed/config -> same page.
        env2, _, _ = self.make()
        o4, *_ = env2.step({"type": "list_records", "table": "ledger", "cursor": cur, "limit": 10})
        self.assertEqual(o2["result"], o4["result"])

    def test_invoices_listing_omits_line_items_but_record_and_document_have_them(self):
        env, _, _ = self.make()
        o, *_ = env.step({"type": "list_records", "table": "invoices", "cursor": None, "limit": 50})
        rows = o["result"]["rows"]
        self.assertTrue(rows)
        for r in rows:
            self.assertNotIn("line_items", r)
        inv = rows[0]
        o, *_ = env.step({"type": "get_record", "table": "invoices", "id": inv["invoice_id"]})
        self.assertIsNone(o["error"])
        rec = o["result"]["record"]
        self.assertIn("line_items", rec)
        self.assertEqual(rec["total_minor"], sum(li["amount_minor"] for li in rec["line_items"]))
        o, *_ = env.step({"type": "get_document", "doc_id": inv["doc_id"]})
        self.assertIsNone(o["error"])
        self.assertEqual(o["result"]["document"], rec)
        # listing again still omits line_items (no mutation of the underlying table)
        o, *_ = env.step({"type": "get_record", "table": "invoices", "id": inv["invoice_id"]})
        self.assertIn("line_items", o["result"]["record"])

    def test_get_document_payment(self):
        env, _, _ = self.make()
        o, *_ = env.step({"type": "list_records", "table": "payments", "cursor": None, "limit": 1})
        pay = o["result"]["rows"][0]
        o, *_ = env.step({"type": "get_document", "doc_id": pay["doc_id"]})
        self.assertEqual(o["result"]["document"], pay)

    def test_returned_records_are_copies(self):
        env, _, _ = self.make()
        o, *_ = env.step({"type": "list_records", "table": "ledger", "cursor": None, "limit": 1})
        row = o["result"]["rows"][0]
        row["debit_minor"] = -999
        o, *_ = env.step({"type": "get_record", "table": "ledger", "id": row["row_id"]})
        self.assertNotEqual(o["result"]["record"]["debit_minor"], -999)

    def test_get_record_not_found_consumes_step(self):
        env, _, _ = self.make()
        o = self.assertBoundedError(env, {"type": "get_record", "table": "ledger", "id": "NOPE-1"}, "not_found")
        self.assertEqual(o["steps_remaining"], 99)
        self.assertBoundedError(env, {"type": "get_document", "doc_id": "NOPE-2"}, "not_found")

    def test_unknown_action(self):
        env, _, _ = self.make()
        self.assertBoundedError(env, {"type": "rm -rf"}, "unknown_action")
        self.assertBoundedError(env, {}, "unknown_action")
        self.assertBoundedError(env, "list_records", "unknown_action")
        self.assertBoundedError(env, None, "unknown_action")

    def test_unknown_table(self):
        env, _, _ = self.make()
        self.assertBoundedError(env, {"type": "list_records", "table": "truth", "cursor": None, "limit": 5},
                                "unknown_table")
        self.assertBoundedError(env, {"type": "get_record", "table": "secrets", "id": "x"}, "unknown_table")
        self.assertBoundedError(env, {"type": "list_records", "cursor": None, "limit": 5}, "unknown_table")

    def test_bad_limit(self):
        env, _, _ = self.make()
        for limit in (0, -1, "5", True, 2.5, None):
            with self.subTest(limit=limit):
                self.assertBoundedError(env, {"type": "list_records", "table": "ledger", "cursor": None,
                                              "limit": limit}, "bad_params")

    def test_bad_cursor(self):
        env, _, _ = self.make()
        for cursor in ("garbage", "ledger:-1", "invoices:5", "ledger:99999", "ledger:", 5, ["ledger:0"]):
            with self.subTest(cursor=cursor):
                self.assertBoundedError(env, {"type": "list_records", "table": "ledger", "cursor": cursor,
                                              "limit": 5}, "bad_params")

    def test_bad_id_types(self):
        env, _, _ = self.make()
        self.assertBoundedError(env, {"type": "get_record", "table": "ledger", "id": 5}, "bad_params")
        self.assertBoundedError(env, {"type": "get_document", "doc_id": None}, "bad_params")

    def test_calculator(self):
        env, _, _ = self.make()
        o, *_ = env.step({"type": "calculator", "expression": "(1.10 + 2.20) * 3"})
        self.assertIsNone(o["error"])
        self.assertEqual(o["result"], {"value": "9.9"})
        for expr in ("__import__('os')", "open('/etc/passwd')", "2**10", 5, "1/0"):
            with self.subTest(expr=expr):
                self.assertBoundedError(env, {"type": "calculator", "expression": expr}, "calc_error")


class TerminationTests(EnvTestBase):
    def test_submit_train_mode(self):
        env, _, _ = self.make()
        env.step(CALC)
        env.step(CALC)
        n = len(env._ep["truth"]["issues"])
        self.assertGreater(n, 0)
        obs, reward, term, trunc, info = env.step({"type": "submit", "findings": oracle_findings(env)})
        self.assertTrue(term)
        self.assertFalse(trunc)
        self.assertIsNone(obs["error"])
        self.assertAlmostEqual(reward, 1.0 - 0.002 * 2, places=6)
        self.assertEqual((info["tp"], info["fp"], info["fn"]), (n, 0, 0))
        self.assertEqual(info["inspection_steps"], 2)
        self.assertEqual(info["reward"], reward)
        self.assertTrue(info["valid"])

    def test_submit_eval_mode(self):
        env, _, _ = self.make(mode="eval")
        obs, reward, term, trunc, info = env.step({"type": "submit", "findings": oracle_findings(env)})
        self.assertTrue(term)
        self.assertEqual(reward, 0.0)
        self.assertEqual(info, {})
        self.assertNotIn("accepted", json.dumps(obs))
        self.assertEqual(env.result["reward"], 1.0)
        self.assertEqual(env.result["fn"], 0)

    def test_eval_mode_truncation_hides_reward(self):
        env, _, _ = self.make(mode="eval", max_steps=2)
        env.step(CALC)
        obs, reward, term, trunc, info = env.step(CALC)
        self.assertTrue(trunc)
        self.assertEqual(reward, 0.0)
        self.assertEqual(info, {})
        self.assertEqual(env.result["reward"], -1.0)

    def test_step_after_end(self):
        env, _, _ = self.make()
        env.step(CALC)
        last, *_ = env.step({"type": "submit", "findings": {"episode_id": env.episode_id, "findings": []}})
        for _ in range(2):
            obs, reward, term, trunc, info = env.step(CALC)
            self.assertEqual(obs["error"]["code"], "episode_over")
            self.assertEqual(reward, 0.0)
            self.assertEqual(obs["step"], last["step"])
            self.assertEqual(obs["steps_remaining"], last["steps_remaining"])
            self.assertIsNone(obs["result"])
            self.assertEqual(info, {})
        self.assertEqual(len(env.grader_log), 1)

    def _run_out(self, config, expected_reward):
        env, _, _ = self.make(config)
        for i in range(1, 100):
            obs, reward, term, trunc, info = env.step(CALC)
            self.assertEqual((reward, term, trunc), (0.0, False, False), i)
            self.assertEqual(obs["steps_remaining"], 100 - i)
        obs, reward, term, trunc, info = env.step(CALC)
        self.assertEqual(obs["step"], 100)
        self.assertEqual(obs["steps_remaining"], 0)
        self.assertFalse(term)
        self.assertTrue(trunc)
        self.assertEqual(obs["result"], {"value": "2"})
        self.assertAlmostEqual(reward, expected_reward, places=6)
        self.assertEqual(info["reward"], reward)
        self.assertEqual(info["inspection_steps"], 100)
        self.assertEqual(info["fp"], 0)
        return env, info

    def test_truncation_clean_graded_as_empty(self):
        env, info = self._run_out(CLEAN, 2 * 1.0 - 1 - 0.2)
        self.assertEqual(info["f1"], 1.0)

    def test_truncation_dirty_graded_as_empty(self):
        env, info = self._run_out(DIRTY, -1.0)
        self.assertEqual(info["f1"], 0.0)
        self.assertEqual(info["fn"], len(env._ep["truth"]["issues"]))

    def test_max_steps_config(self):
        env, obs, info = self.make(CLEAN, max_steps=5)
        self.assertEqual(obs["steps_remaining"], 5)
        for _ in range(4):
            self.assertFalse(env.step(CALC)[3])
        obs, reward, term, trunc, info = env.step(CALC)
        self.assertTrue(trunc)
        self.assertEqual(obs["steps_remaining"], 0)
        self.assertAlmostEqual(reward, 1.0 - 0.002 * 5, places=6)

    def test_submit_on_last_step_is_submit(self):
        env, _, _ = self.make(CLEAN)
        for _ in range(99):
            env.step(CALC)
        obs, reward, term, trunc, info = env.step(
            {"type": "submit", "findings": {"episode_id": env.episode_id, "findings": []}})
        self.assertEqual(obs["step"], 100)
        self.assertTrue(term)
        self.assertFalse(trunc)
        self.assertAlmostEqual(reward, 1.0 - 0.002 * 99, places=6)
        self.assertEqual(env.grader_log[-1]["end"], "submit")

    def test_invalid_findings_train(self):
        for bad in ({"episode_id": "ep_wrong", "findings": []}, None,
                    {"episode_id": "SELF", "findings": [{"type": "fx_error"}]}):
            with self.subTest(bad=bad):
                env, _, _ = self.make()
                if isinstance(bad, dict) and bad["episode_id"] == "SELF":
                    bad = dict(bad, episode_id=env.episode_id)
                obs, reward, term, trunc, info = env.step({"type": "submit", "findings": bad})
                self.assertTrue(term)
                self.assertFalse(trunc)
                self.assertEqual(reward, -1.0)
                self.assertFalse(info["valid"])
                self.assertEqual(obs["error"]["code"], "invalid_findings")
                self.assertLessEqual(len(obs["error"]["message"]), 200)
                self.assertFalse(env.grader_log[-1]["valid"])

    def test_invalid_findings_eval(self):
        env, _, _ = self.make(mode="eval")
        obs, reward, term, trunc, info = env.step({"type": "submit", "findings": None})
        self.assertTrue(term)
        self.assertEqual(reward, 0.0)
        self.assertEqual(info, {})
        self.assertEqual(env.result["reward"], -1.0)

    def test_time_limit_zero_truncates_first_step(self):
        env, _, _ = self.make(CLEAN, time_limit_s=0)
        obs, reward, term, trunc, info = env.step(CALC)
        self.assertTrue(trunc)
        self.assertFalse(term)
        self.assertEqual(obs["step"], 1)
        self.assertEqual(info["tp"] + info["fp"], 0)
        self.assertEqual(env.grader_log[-1]["end"], "time_limit")

    def test_time_limit_beats_submit(self):
        env, _, _ = self.make(CLEAN, time_limit_s=0)
        obs, reward, term, trunc, info = env.step(
            {"type": "submit", "findings": {"episode_id": env.episode_id, "findings": []}})
        self.assertTrue(trunc)
        self.assertFalse(term)


class LeakageTests(EnvTestBase):
    def test_no_truth_leakage(self):
        probe = "PROBE-" + "q" * 50  # > 40 chars
        for mode in ("train", "eval"):
            with self.subTest(mode=mode):
                env, obs, info = self.make(mode=mode)
                records = [obs, info]
                actions = [
                    {"type": "list_records", "table": "ledger", "cursor": None, "limit": 50},
                    {"type": "list_records", "table": "invoices", "cursor": None, "limit": 50},
                    {"type": "list_records", "table": "payments", "cursor": None, "limit": 50},
                    {"type": "list_records", "table": "fx", "cursor": None, "limit": 50},
                    {"type": "get_record", "table": "ledger", "id": probe},
                    {"type": "get_record", "table": probe, "id": probe},
                    {"type": "get_document", "doc_id": probe},
                    {"type": "list_records", "table": probe, "cursor": None, "limit": 5},
                    {"type": "list_records", "table": "ledger", "cursor": probe, "limit": 5},
                    {"type": "list_records", "table": "ledger", "cursor": None, "limit": probe},
                    {"type": probe},
                    {"type": "calculator", "expression": probe},
                    {"type": "calculator", "expression": "__import__('os')"},
                    {"type": "submit", "findings": oracle_findings(env)},
                    CALC,  # after end
                ]
                for a in actions:
                    obs, reward, term, trunc, info = env.step(a)
                    records += [obs, info]
                    if obs["error"] is not None:
                        self.assertLessEqual(len(obs["error"]["message"]), 200)
                        self.assertNotIn(probe, obs["error"]["message"])
                text = json.dumps(records)
                keys = set()
                for r in records:
                    keys |= set(all_keys(r))
                self.assertFalse(keys & FORBIDDEN_KEYS, keys & FORBIDDEN_KEYS)
                for issue in env._ep["truth"]["issues"]:
                    self.assertNotIn(issue["issue_id"], text)


if __name__ == "__main__":
    unittest.main()
