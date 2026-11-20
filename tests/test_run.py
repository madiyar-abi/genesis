import json
import os
import tempfile
import unittest

from auditenv import run
from auditenv.env import AuditEnv
from auditenv.policies.oracle import Oracle

FORBIDDEN = ("truth", "evidence_sets", "expected_amount_minor", "provenance", "issue_id", "\"seed\"")


class RunTest(unittest.TestCase):
    def test_episode_list_requires_integer_seeds_and_object_configs(self):
        def load(spec):
            with tempfile.NamedTemporaryFile(mode="w") as fh:
                json.dump(spec, fh)
                fh.flush()
                return run.load_episodes(fh.name)

        for spec in ([], {}, {"episodes": {}}, {"seeds": "12"}, {"episodes": [None]}, {"episodes": [{}]}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                load(spec)

        for make_spec in (lambda seed, cfg: {"episodes": [{"seed": seed, "config": cfg}]},
                          lambda seed, cfg: {"seeds": [seed], "config": cfg}):
            for seed in (True, 1.9, "7"):
                with self.subTest(spec=make_spec(seed, {})), self.assertRaises(ValueError):
                    load(make_spec(seed, {}))
            for cfg in (False, 0, "", [], [["errors", {}]]):
                with self.subTest(spec=make_spec(1, cfg)), self.assertRaises(ValueError):
                    load(make_spec(1, cfg))
            self.assertEqual(load(make_spec(-4, None)), [(-4, {})])
        self.assertEqual(load({"episodes": [{"seed": 2}, {"seed": 1}, {"seed": 2}]}),
                         [(2, {}), (1, {}), (2, {})])
        self.assertEqual(load({"seeds": [2, 1, 2]}), [(2, {}), (1, {}), (2, {})])

    def test_oracle_reaches_max_reward(self):
        env = AuditEnv()
        for seed in range(50):
            cfg = None if seed % 3 else {"errors": {}}
            traj = run.run_episode(env, None, seed, cfg, policy_factory=lambda e: Oracle(e._ep["truth"]))
            self.assertEqual(traj[-1]["reward"], 1.0)
            self.assertTrue(traj[-1]["terminated"])

    def test_trajectory_format_and_no_truth_in_observations(self):
        env = AuditEnv()
        traj = run.run_episode(env, None, 3, None, policy_factory=lambda e: Oracle(e._ep["truth"]))
        keys = {"episode_id", "step", "action", "observation", "reward", "terminated", "truncated"}
        for rec in traj:
            self.assertEqual(set(rec), keys)
            text = json.dumps(rec["observation"])
            for word in FORBIDDEN:
                self.assertNotIn(word, text)
        self.assertEqual([r["step"] for r in traj], list(range(len(traj))))

    def test_trajectory_snapshots_policy_inputs_and_actions(self):
        class MutatingPolicy:
            def reset(self, obs):
                self.episode_id = obs["manifest"]["episode_id"]
                obs["manifest"]["counts"].clear()
                self.action = {"type": "list_records", "table": "ledger", "limit": 1}

            def act(self, obs):
                if obs.get("step") == 1:
                    obs["result"]["rows"].clear()
                    self.action.clear()
                    self.action.update({"type": "submit", "findings": {"episode_id": self.episode_id, "findings": []}})
                return self.action

        policy = MutatingPolicy()
        traj = run.run_episode(AuditEnv(), policy, 7)
        policy.action["findings"]["findings"].append({})
        self.assertTrue(traj[0]["observation"]["manifest"]["counts"])
        self.assertEqual(len(traj[1]["observation"]["result"]["rows"]), 1)
        self.assertEqual(traj[1]["action"], {"type": "list_records", "table": "ledger", "limit": 1})
        self.assertEqual(traj[2]["action"]["findings"]["findings"], [])

    def test_cli_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.jsonl")
            self.assertEqual(run.main(["--policy", "oracle", "--seeds", "1-2", "--out", out]), 0)
            with open(out) as fh:
                recs = [json.loads(line) for line in fh]
            self.assertEqual(len({r["episode_id"] for r in recs}), 2)


if __name__ == "__main__":
    unittest.main()
