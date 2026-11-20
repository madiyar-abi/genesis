"""Committed training trajectories: required keys, no closed truth in observations, action replay."""
import contextlib
import glob
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from auditenv import run
from auditenv.env import AuditEnv
from auditenv.run import load_episodes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = {"episode_id", "step", "action", "observation", "reward", "terminated", "truncated"}
FORBIDDEN = ("truth", "evidence_sets", "expected_amount_minor", "provenance", "issue_id")
POLICIES = ("random", "naive_reconcile", "reconcile")
EXPECTED = ({f"train_{p}.jsonl" for p in POLICIES}
            | {f"train_hard_{p}.jsonl" for p in POLICIES + ("reconcile_hard",)})
HARD_MARK = "Hard mode:"  # appended to the task text of every hard episode


class TrajectoryFilesTest(unittest.TestCase):
    def test_files(self):
        files = glob.glob(os.path.join(ROOT, "trajectories", "*.jsonl"))
        self.assertTrue(EXPECTED <= {os.path.basename(f) for f in files})
        for path in files:
            with open(path) as fh:
                recs = [json.loads(line) for line in fh]
            episodes = {}
            for rec in recs:
                self.assertEqual(set(rec), KEYS, path)
                text = json.dumps(rec["observation"])
                for word in FORBIDDEN:
                    self.assertNotIn(word, text, path)
                episodes.setdefault(rec["episode_id"], []).append(rec)
            self.assertEqual(len(episodes), 10, path)
            for steps in episodes.values():
                self.assertEqual([r["step"] for r in steps], list(range(len(steps))))
                self.assertTrue(steps[-1]["terminated"] or steps[-1]["truncated"])
                self.assertTrue(all(r["reward"] == 0.0 for r in steps[:-1]))
                hard = os.path.basename(path).startswith("train_hard_")
                self.assertEqual(HARD_MARK in steps[0]["observation"]["task"], hard, path)

    def test_deterministic_action_replay(self):
        """Replay actions from all committed trajectory files against AuditEnv."""
        files = sorted(glob.glob(os.path.join(ROOT, "trajectories", "*.jsonl")))
        self.assertTrue(EXPECTED <= {os.path.basename(f) for f in files})
        env = AuditEnv()

        with mock.patch.dict(os.environ):
            os.environ.pop("AUDITENV_SECRET", None)

            for path in files:
                base = os.path.basename(path)
                cfg_name = "train_hard.json" if base.startswith("train_hard_") else "train.json"
                cfg_path = os.path.join(ROOT, "configs", cfg_name)
                episodes_spec = [(s, {**c, "mode": "train"}) for s, c in load_episodes(cfg_path)]

                with open(path) as fh:
                    recs = [json.loads(line) for line in fh]

                by_ep: list[list[dict]] = []
                curr: list[dict] = []
                for r in recs:
                    if r["step"] == 0:
                        if curr:
                            by_ep.append(curr)
                        curr = [r]
                    else:
                        curr.append(r)
                if curr:
                    by_ep.append(curr)

                self.assertEqual(len(by_ep), len(episodes_spec), f"Episode count mismatch in {base}")

                for ep_idx, ((seed, config), ep_recs) in enumerate(zip(episodes_spec, by_ep)):
                    with self.subTest(file=base, episode=ep_idx, seed=seed):
                        # Episode boundary checks
                        self.assertEqual([r["step"] for r in ep_recs], list(range(len(ep_recs))))
                        self.assertTrue(ep_recs[-1]["terminated"] or ep_recs[-1]["truncated"])
                        self.assertTrue(all(not r["terminated"] and not r["truncated"] for r in ep_recs[:-1]))
                        self.assertTrue(all(r["reward"] == 0.0 for r in ep_recs[:-1]))

                        # Reset record verification
                        obs, info = env.reset(seed, config)
                        r0 = ep_recs[0]
                        self.assertEqual(r0["step"], 0)
                        self.assertIsNone(r0["action"])
                        self.assertEqual(r0["reward"], 0.0)
                        self.assertFalse(r0["terminated"])
                        self.assertFalse(r0["truncated"])
                        self.assertEqual(info["episode_id"], r0["episode_id"])
                        self.assertEqual(obs, r0["observation"])

                        # Action replay verification
                        for step_idx, step_rec in enumerate(ep_recs[1:], start=1):
                            obs, reward, terminated, truncated, _info = env.step(step_rec["action"])
                            self.assertEqual(obs["step"], step_rec["step"])
                            self.assertEqual(obs, step_rec["observation"])
                            self.assertEqual(reward, step_rec["reward"])
                            self.assertEqual(terminated, step_rec["terminated"])
                            self.assertEqual(truncated, step_rec["truncated"])
                            self.assertEqual(env.episode_id, step_rec["episode_id"])

    def test_files_regenerate_byte_for_byte(self):
        """README: the committed files are reproduced byte-for-byte by its `auditenv.run` commands. The replay
        above cannot tell which policy produced the actions (red-team round 16: swapping two files passed it)."""
        with mock.patch.dict(os.environ), tempfile.TemporaryDirectory() as tmp:
            os.environ.pop("AUDITENV_SECRET", None)
            for name in sorted(EXPECTED):
                hard = name.startswith("train_hard_")
                policy = name[len("train_hard_" if hard else "train_"):-len(".jsonl")]
                out = os.path.join(tmp, name)
                cfg = os.path.join(ROOT, "configs", "train_hard.json" if hard else "train.json")
                with contextlib.redirect_stdout(io.StringIO()):
                    run.main(["--policy", policy, "--config", cfg, "--out", out])
                with open(out, "rb") as fresh, open(os.path.join(ROOT, "trajectories", name), "rb") as committed:
                    self.assertTrue(fresh.read() == committed.read(), f"{name} differs from a fresh run")


if __name__ == "__main__":
    unittest.main()
