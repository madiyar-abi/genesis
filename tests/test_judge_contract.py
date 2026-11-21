"""Block 1 of the jury's check definitions (C01-C20), run through `judge_adapter` exactly as the jury calls it:
generate_episode -> reset({"mode": "closed", "episode_dir": ...}) -> step({"name", "args"}) -> score_episode.
Fixtures as in the definitions: C clean (record R1, document D1), E one declared error, L a table of 101+ rows,
U an id absent from the public data (chosen after reading it)."""

import json
import os
import shutil
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import patch

import judge_adapter as ja
from auditenv.generator import generate
from auditenv.load import load_episode
from auditenv.matcher import public_ids

ja._WARNED = True  # public test seeds: the grader-key warning is tested on its own
os.environ.setdefault("AUDITENV_KEY_FILE", os.path.join(tempfile.mkdtemp(), "grader.key"))  # not ~/.auditenv

ONLY = {"I1": 0, "I2": 0}
FORBIDDEN_KEYS = {"truth", "provenance", "seed", "evidence_sets", "expected_amount_minor", "issue_id", "scenario",
                  "issues", "transform_seed", "labels", "missed"}


def oracle_findings(ep: dict) -> dict:
    """Grader-side oracle answer: the truth with its first evidence set."""
    return {"episode_id": ep["manifest"]["episode_id"],
            "findings": [{"type": i["type"], "affected_ids": list(i["affected_ids"]),
                          "claimed_amount_minor": i["expected_amount_minor"], "currency": i["currency"],
                          "evidence_ids": list(i["evidence_sets"][0]), "explanation": "oracle"}
                         for i in ep["truth"]["issues"]]}


def keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from keys(v)


def act(name, **args):
    return {"name": name, "args": args}


class JudgeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.c_dir, cls.e_dir = os.path.join(cls.tmp, "C"), os.path.join(cls.tmp, "E")
        ja.generate_episode(11, {"errors": {}, "interacting": ONLY}, cls.c_dir)
        ja.generate_episode(12, {"errors": {"fx_error": 1}, "interacting": ONLY}, cls.e_dir)
        cls.c, cls.e = load_episode(cls.c_dir), load_episode(cls.e_dir)
        cls.r1 = cls.c["tables"]["ledger"][0]["row_id"]
        cls.d1 = cls.c["tables"]["invoices"][0]["doc_id"]
        known = public_ids(cls.c["tables"])
        cls.u = next(f"U-{i}" for i in range(10 ** 6) if f"U-{i}" not in known)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def open(self, episode_dir=None, team=None):
        env = ja.make_env()
        obs, info = env.reset(0, {"mode": "closed", "episode_dir": episode_dir or self.c_dir,
                                  "team_config": team or {}})
        return env, obs, info

    def assertBoundedError(self, obs, code=None):
        self.assertIsNone(obs["result"])
        self.assertEqual(set(obs["error"]), {"code", "message"})
        if code:
            self.assertEqual(obs["error"]["code"], code)
        self.assertNotIn(self.tmp, json.dumps(obs))

    def test_c01_reset_returns_json_pair(self):
        out = ja.make_env().reset(0, {"mode": "closed", "episode_dir": self.c_dir, "team_config": {}})
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 2)
        json.dumps(out, allow_nan=False)

    def test_c02_first_observation(self):
        _, obs, info = self.open()
        self.assertEqual(set(obs), {"task", "manifest", "policy", "remaining_steps"})
        self.assertEqual(obs["remaining_steps"], 100)
        self.assertTrue(obs["task"].strip())
        self.assertFalse(FORBIDDEN_KEYS & set(keys([obs, info])))

    def test_c03_manifest_matches_the_data(self):
        _, obs, _ = self.open()
        m, t = obs["manifest"], self.c["tables"]
        for k in ("schema_version", "episode_id", "base_currency", "period_start", "period_end", "timezone",
                  "counts", "rounding"):
            self.assertIn(k, m)
        self.assertEqual({k: m["counts"][k] for k in t}, {k: len(v) for k, v in t.items()})
        self.assertEqual(m["counts"]["documents"], len(t["invoices"]) + len(t["payments"]))
        self.assertEqual(m["rounding"], "ROUND_HALF_UP")

    def test_c04_step_tuple(self):
        env, _, _ = self.open()
        out = env.step(act("list_records", table="ledger", cursor=None, limit=50))
        self.assertEqual(len(out), 5)
        obs, reward, terminated, truncated, info = out
        self.assertIs(type(terminated), bool)
        self.assertIs(type(truncated), bool)
        self.assertEqual(set(obs), {"result", "error", "remaining_steps"})
        self.assertEqual(set(obs["result"]), {"records", "next_cursor"})
        json.dumps(out, allow_nan=False)

    def test_c05_c06_pages_cover_the_table_and_repeat(self):
        rows = self.c["tables"]["ledger"]
        self.assertGreaterEqual(len(rows), 101)  # fixture L: at least three pages
        env, _, _ = self.open()
        seen, cursor, cursors = [], None, []
        while True:
            obs = env.step(act("list_records", table="ledger", cursor=cursor, limit=50))[0]
            self.assertLessEqual(len(obs["result"]["records"]), 50)
            seen += [r["row_id"] for r in obs["result"]["records"]]
            cursors.append(cursor)
            cursor = obs["result"]["next_cursor"]
            if cursor is None:
                break
        self.assertEqual(seen, [r["row_id"] for r in rows])  # no gaps, no repeats, every row reachable
        again = [env.step(act("list_records", table="ledger", cursor=cursors[1], limit=50))[0] for _ in range(2)]
        self.assertEqual(again[0]["result"], again[1]["result"])
        self.assertEqual(again[0]["remaining_steps"] - 1, again[1]["remaining_steps"])

    def test_c07_get_record(self):
        env, _, _ = self.open()
        obs = env.step(act("get_record", table="ledger", id=self.r1))[0]
        self.assertEqual(obs["result"], self.c["tables"]["ledger"][0])

    def test_c08_get_document(self):
        env, _, _ = self.open()
        obs = env.step(act("get_document", doc_id=self.d1))[0]
        self.assertEqual(obs["result"], self.c["tables"]["invoices"][0])

    def test_c09_calculator_decimal(self):
        env, _, _ = self.open()
        obs = env.step(act("calculator", expression="0.1+0.2"))[0]
        self.assertEqual(Decimal(obs["result"]), Decimal("0.3"))
        self.assertEqual(obs["result"], "0.3")

    def test_c10_calculator_refuses_code(self):
        env, _, _ = self.open()
        for expr in ("open('/etc/passwd').read()", "__import__('os').system('id')", "1+1; import os"):
            with self.subTest(expr):
                obs = env.step(act("calculator", expression=expr))[0]
                self.assertBoundedError(obs, "calc_error")
                self.assertNotIn("root:", json.dumps(obs))

    def test_c11_c12_unknown_ids(self):
        env, _, _ = self.open()
        obs = env.step(act("get_record", table="ledger", id=self.u))[0]
        self.assertBoundedError(obs, "not_found")
        self.assertEqual(obs["remaining_steps"], 99)
        obs = env.step(act("get_document", doc_id=self.u))[0]
        self.assertBoundedError(obs, "not_found")
        self.assertEqual(obs["remaining_steps"], 98)

    def test_c13_unknown_action(self):
        env, _, _ = self.open()
        for bad in (act("delete_records", table="ledger"), {"name": "get_record"}, {"args": {}}, "submit",
                    {"name": "get_record", "args": {"type": "submit"}}):
            with self.subTest(bad):
                remaining = env.step(act("calculator", expression="1"))[0]["remaining_steps"]
                obs, reward, terminated, truncated, _ = env.step(bad)
                self.assertIsNotNone(obs["error"])
                self.assertEqual(obs["remaining_steps"], remaining - 1)
                self.assertFalse(terminated or truncated)

    def test_c14_errors_cost_one_step_and_do_not_break_access(self):
        env, _, _ = self.open()
        a = env.step(act("get_record", table="ledger", id=self.r1))[0]
        b = env.step(act("get_record", table="ledger", id=self.u))[0]
        c = env.step(act("get_record", table="ledger", id=self.r1))[0]
        self.assertEqual([a["remaining_steps"], b["remaining_steps"], c["remaining_steps"]], [99, 98, 97])
        self.assertEqual(a["result"], c["result"])

    def test_c15_submit_is_final(self):
        env, _, _ = self.open(self.e_dir)
        obs, _, terminated, truncated, _ = env.step(act("submit", findings=oracle_findings(self.e)))
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(obs["result"], {"accepted": True})
        final = dict(env.grader_log[-1])
        for later in (act("submit", findings={"episode_id": self.e["episode_id"], "findings": []}),
                      act("get_record", table="ledger", id=self.r1)):
            obs, _, terminated, _, _ = env.step(later)
            self.assertTrue(terminated)
            self.assertEqual(obs["error"]["code"], "episode_over")
        self.assertEqual(len(env.grader_log), 1)
        self.assertEqual(env.grader_log[-1], final)

    def test_c16_submit_as_action_100(self):
        env, _, _ = self.open(self.e_dir)
        for _ in range(99):
            self.assertFalse(env.step(act("calculator", expression="1+1"))[3])
        obs, _, terminated, truncated, _ = env.step(act("submit", findings=oracle_findings(self.e)))
        self.assertEqual((terminated, truncated, obs["result"]), (True, False, {"accepted": True}))
        self.assertEqual(env.grader_log[-1]["inspection_steps"], 99)
        self.assertEqual(env.grader_log[-1]["tp"], 1)

    def test_c17_hundred_inspections_truncate(self):
        env, _, _ = self.open(self.e_dir)
        for i in range(100):
            obs, _, terminated, truncated, _ = env.step(act("calculator", expression="1+1"))
            self.assertEqual(truncated, i == 99)
        self.assertFalse(terminated)
        log = env.grader_log[-1]
        self.assertEqual((log["end"], log["tp"], log["fp"]), ("step_limit", 0, 0))
        obs, _, _, truncated, _ = env.step(act("submit", findings=oracle_findings(self.e)))
        self.assertTrue(truncated)
        self.assertEqual(obs["error"]["code"], "episode_over")
        self.assertEqual(len(env.grader_log), 1)

    def test_c18_time_limit_truncates_with_empty_findings(self):
        env = ja.make_env()
        now = [0.0]
        env._env._clock = lambda: now[0]  # deterministic wall clock, policy time included
        env.reset(0, {"mode": "closed", "episode_dir": self.e_dir, "team_config": {}})
        env.step(act("calculator", expression="1"))
        now[0] = 60.5  # the policy "thinks" past the 60 s limit
        obs, _, terminated, truncated, _ = env.step(act("submit", findings=oracle_findings(self.e)))
        self.assertEqual((terminated, truncated, obs["error"]["code"]), (False, True, "time_limit"))
        self.assertEqual((env.grader_log[-1]["end"], env.grader_log[-1]["tp"]), ("time_limit", 0))

    def test_c18_reset_work_counts_toward_deadline(self):
        from auditenv.generator import generate

        for mode, target, original, extra in (
            ("closed", "judge_adapter.load_episode", load_episode, {"episode_dir": self.e_dir}),
            ("train", "auditenv.env.generate", generate, {}),
        ):
            with self.subTest(mode=mode):
                env = ja.make_env()
                now = [0.0]
                env._env._clock = lambda: now[0]

                def slow(*args):
                    now[0] += 11
                    return original(*args)

                with patch(target, side_effect=slow):
                    env.reset(2, {"mode": mode, **extra})
                now[0] = 61
                obs, _, terminated, truncated, _ = env.step(act("calculator", expression="1"))
                self.assertEqual((terminated, truncated, obs["error"]["code"]), (False, True, "time_limit"))

    def test_c19_closed_rewards_are_zero(self):
        env, _, info = self.open(self.e_dir)
        rewards, infos = [], [info]
        for a in (act("list_records", table="payments", cursor=None, limit=5), act("get_record", table="fx", id=self.u),
                  act("submit", findings=oracle_findings(self.e))):
            obs, reward, terminated, truncated, info = env.step(a)
            rewards.append(reward)
            infos.append(info)
        self.assertTrue(all(type(r) in (int, float) and r == 0 for r in rewards))
        self.assertEqual(infos[1:], [{}, {}, {}])
        self.assertGreater(env.grader_log[-1]["reward"], 0.9)  # the true reward stays grader-side

    def test_c20_no_closed_data_in_any_policy_channel(self):
        for ep_dir, ep in ((self.c_dir, self.c), (self.e_dir, self.e)):
            env, obs, info = self.open(ep_dir)
            seen = [obs, info]
            for table in ("ledger", "invoices", "payments", "fx"):
                cursor = None
                while True:
                    out = env.step(act("list_records", table=table, cursor=cursor, limit=50))
                    seen.append(out)
                    cursor = out[0]["result"]["next_cursor"]
                    if cursor is None or out[0]["remaining_steps"] < 25:
                        break
            for d in (ep["tables"]["invoices"] + ep["tables"]["payments"])[:10]:
                seen.append(env.step(act("get_document", doc_id=d["doc_id"])))
            seen += [env.step(act("get_record", table="nope", id="x")), env.step(act("calculator", expression="x")),
                     env.step(act("submit", findings={"episode_id": ep["episode_id"], "findings": [{"bad": 1}]}))]
            text = json.dumps(seen)
            self.assertFalse(FORBIDDEN_KEYS & set(keys(seen)))
            self.assertNotIn(self.tmp, text)
            for issue in ep["truth"]["issues"]:
                self.assertNotIn(issue["issue_id"], text)

    def test_rejected_episode_leaves_the_open_one(self):
        env, _, _ = self.open(self.e_dir)
        env.step(act("calculator", expression="1"))
        bad = os.path.join(self.tmp, "bad-policy")
        shutil.copytree(self.c_dir, bad)
        with open(os.path.join(bad, "public", "policy.json"), encoding="utf-8") as fh:
            policy = json.load(fh)
        policy["findings"]["tolerance_minor"] = -1
        with open(os.path.join(bad, "public", "policy.json"), "w", encoding="utf-8") as fh:
            json.dump(policy, fh)
        with self.assertRaises(ValueError):
            env.reset(0, {"mode": "closed", "episode_dir": bad, "team_config": {}})
        obs = env.step(act("get_record", table="ledger", id=self.e["tables"]["ledger"][0]["row_id"]))[0]
        self.assertEqual((obs["remaining_steps"], obs["result"]), (98, self.e["tables"]["ledger"][0]))

    def test_reset_restarts_the_same_episode(self):
        env, first, _ = self.open(self.e_dir)
        env.step(act("calculator", expression="1"))
        again, _ = env.reset(0, {"mode": "closed", "episode_dir": self.e_dir, "team_config": {}})
        self.assertEqual(again, first)
        self.assertEqual(again["manifest"]["episode_id"], self.e["episode_id"])

    def test_train_mode_generates_and_returns_the_terminal_reward(self):
        env = ja.make_env()
        cfg = {"errors": {"fx_error": 1}, "interacting": ONLY}
        obs, info = env.reset(12, {"mode": "train", "team_config": cfg})
        public = generate(12, cfg)  # open mode is the public generator; closed fixtures carry the grader key
        self.assertEqual(obs["manifest"]["episode_id"], public["episode_id"])
        _, reward, terminated, _, info = env.step(act("submit", findings=oracle_findings(public)))
        self.assertTrue(terminated)
        self.assertEqual(reward, 1.0)
        self.assertEqual(info["tp"], 1)

    def test_score_episode_on_a_hand_written_fixture(self):
        """Block 3's fixture as the jury may build it: a copy of an exported episode whose truth.json holds only the
        issue A (10000 KZT, evidence {D1, D2}), written by hand without our extra truth fields."""
        fixture = os.path.join(self.tmp, "B3")
        shutil.copytree(self.c_dir, fixture)
        inv, docs = self.c["tables"]["invoices"][0], [d["doc_id"] for d in self.c["tables"]["invoices"][:2]]
        issue = {"issue_id": "A", "type": "fx_error", "affected_ids": [inv["invoice_id"]],
                 "expected_amount_minor": 10000, "currency": "KZT", "evidence_sets": [docs]}
        with open(os.path.join(fixture, "grader", "truth.json"), "w", encoding="utf-8") as fh:
            json.dump({"episode_id": self.c["episode_id"], "issues": [issue]}, fh)
        f = {"type": "fx_error", "affected_ids": [inv["invoice_id"]], "claimed_amount_minor": 10000,
             "currency": "KZT", "evidence_ids": docs, "explanation": "rate of the wrong day"}

        def score(*findings, steps=10):
            return ja.score_episode(fixture, {"episode_id": self.c["episode_id"], "findings": list(findings)}, steps)
        self.assertEqual(score(f), {"tp": 1, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0,
                                    "return": score(f)["return"]})
        self.assertAlmostEqual(score(f)["return"], 0.98, delta=1e-9)
        self.assertAlmostEqual(score(f, f)["return"], 47 / 150, delta=1e-9)  # row 5
        for changed in ({"claimed_amount_minor": 10001}, {"evidence_ids": docs[:1]},
                        {"evidence_ids": [docs[0], self.u]}, {"currency": "kzt"}):
            with self.subTest(changed):
                self.assertEqual({k: score({**f, **changed})[k] for k in ("tp", "fp", "fn")},
                                 {"tp": 0, "fp": 1, "fn": 1})

    def test_minimal_fixture_without_task_provenance_or_fx_id(self):
        """A grading fixture built from the definitions' file list only: no task.txt, no provenance.json, and the
        case's fx.csv columns (date, source_currency, target_currency, rate)."""
        fixture = os.path.join(self.tmp, "minimal")
        shutil.copytree(self.e_dir, fixture)
        os.remove(os.path.join(fixture, "public", "task.txt"))
        os.remove(os.path.join(fixture, "grader", "provenance.json"))
        fx_path = os.path.join(fixture, "public", "fx.csv")
        with open(fx_path, encoding="utf-8", newline="") as fh:
            lines = fh.read().splitlines()
        with open(fx_path, "w", encoding="utf-8", newline="") as fh:
            fh.write("\n".join(line.split(",", 1)[1] for line in lines) + "\n")
        result = ja.score_episode(fixture, oracle_findings(self.e), 10)
        self.assertEqual((result["tp"], result["fp"], result["fn"]), (1, 0, 0))
        self.assertEqual(load_episode(fixture)["tables"]["fx"], self.e["tables"]["fx"])

    def test_closed_reset_keeps_key_path_off_stderr(self):
        import contextlib
        import io
        from unittest import mock

        for path in (os.path.join(self.tmp, "fixture.key"), self.tmp):
            with self.subTest(path=path), mock.patch.object(ja, "_WARNED", False), mock.patch.dict(
                    os.environ, {"AUDITENV_SECRET": "", "AUDITENV_KEY_FILE": path}):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    ja.make_env().reset(3, {"mode": "closed"})
                self.assertNotIn(path, err.getvalue())

    def test_generate_warns_without_the_secret(self):
        import contextlib
        import io
        from unittest import mock
        ja._WARNED = False
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"AUDITENV_SECRET": ""}), contextlib.redirect_stderr(err):
            ja.generate_episode(3, {}, os.path.join(self.tmp, "warn"))
        self.assertIn("AUDITENV_SECRET", err.getvalue())
        ja._WARNED = False
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"AUDITENV_SECRET": "k"}), contextlib.redirect_stderr(err):
            ja.generate_episode(3, {}, os.path.join(self.tmp, "keyed"))
        self.assertEqual(err.getvalue(), "")
        ja._WARNED = True

    def test_score_episode(self):
        good = ja.score_episode(self.e_dir, oracle_findings(self.e), 10)
        self.assertEqual({k: good[k] for k in ("tp", "fp", "fn")}, {"tp": 1, "fp": 0, "fn": 0})
        self.assertAlmostEqual(good["return"], 0.98, delta=1e-9)
        bad = ja.score_episode(self.e_dir, {"episode_id": self.e["episode_id"], "findings": [{}] * 31}, 10)
        self.assertEqual(bad, {"tp": None, "fp": None, "fn": None, "precision": None, "recall": None, "f1": None,
                               "return": -1.0})
        self.assertFalse(ja.GRADER_LOG[-1]["valid"])
        self.assertTrue(ja.GRADER_LOG[-1]["error"])


if __name__ == "__main__":
    unittest.main()
