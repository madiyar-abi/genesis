import json
import os
import tempfile
import unittest

from auditenv import run
from auditenv.env import AuditEnv
from auditenv.policies.oracle import Oracle

FORBIDDEN = ("truth", "evidence_sets", "expected_amount_minor", "provenance", "issue_id", "\"seed\"")


class RunTest(unittest.TestCase):
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
