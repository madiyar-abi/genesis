"""Committed training trajectories: required keys, no closed truth in observations."""
import glob
import json
import os
import unittest

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


if __name__ == "__main__":
    unittest.main()
