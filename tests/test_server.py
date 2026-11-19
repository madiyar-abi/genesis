import json
import os
import tempfile
import unittest

from auditenv.client import RemoteEnv
from auditenv.env import AuditEnv
from auditenv.generator import ISSUE_TYPES

CFG = {"errors": {t: 1 for t in ISSUE_TYPES}}


class ScriptedPolicy:
    """Deterministic, observation-only: list two pages, read one record, submit one guess."""

    def __init__(self):
        self.n = 0

    def reset(self, obs):
        self.ep = obs["manifest"]["episode_id"]
        self.base = obs["manifest"]["base_currency"]

    def act(self, obs):
        self.n += 1
        if self.n == 1:
            return {"type": "list_records", "table": "invoices", "cursor": None, "limit": 50}
        if self.n == 2:
            self.first = obs["result"]["rows"][0]
            return {"type": "get_document", "doc_id": self.first["doc_id"]}
        if self.n == 3:
            return {"type": "get_record", "table": "ledger", "id": "missing"}
        return {"type": "submit", "findings": {"episode_id": self.ep, "findings": [
            {"type": "period_cutoff", "affected_ids": [self.first["invoice_id"]], "claimed_amount_minor": 1,
             "currency": self.base, "evidence_ids": [self.first["doc_id"]], "explanation": "guess"}]}}


def play(env, seed, config):
    pol = ScriptedPolicy()
    obs, info = env.reset(seed, config)
    pol.reset(obs)
    out = [obs]
    while True:
        obs, r, term, trunc, info = env.step(pol.act(obs))
        out.append([obs, r, term, trunc, info])
        if term or trunc:
            return json.loads(json.dumps(out))


class ServerTest(unittest.TestCase):
    def test_remote_equals_local_in_train_mode(self):
        local = play(AuditEnv(), 21, CFG)
        with RemoteEnv() as env:
            remote = play(env, 21, CFG)
        self.assertEqual(local, remote)

    def test_eval_mode_hides_reward_and_logs_grader_side(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "grader.jsonl")
            hidden = os.path.join(d, "hidden.json")
            with open(hidden, "w") as fh:
                json.dump({"seeds": [31, 32], "config": CFG}, fh)
            with RemoteEnv(grader_log=log, episodes=hidden) as env:
                for _ in range(2):
                    traj = play(env, 0, None)  # client seed is ignored
                    for obs, r, term, trunc, info in traj[1:]:
                        self.assertEqual(r, 0.0)
                        self.assertEqual(info, {})
                    text = json.dumps(traj)
                    for key in ("truth", "evidence_sets", "expected_amount_minor", "provenance", "seed"):
                        self.assertNotIn(key, text)
                with self.assertRaises(RuntimeError):
                    env.reset(0, None)
            with open(log) as fh:
                recs = [json.loads(line) for line in fh]
            self.assertEqual(len(recs), 2)
            self.assertTrue(all("reward" in r and "f1" in r for r in recs))


if __name__ == "__main__":
    unittest.main()
