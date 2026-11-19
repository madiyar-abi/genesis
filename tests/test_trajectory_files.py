"""Committed training trajectories: required keys, no closed truth in observations."""
import glob
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = {"episode_id", "step", "action", "observation", "reward", "terminated", "truncated"}
FORBIDDEN = ("truth", "evidence_sets", "expected_amount_minor", "provenance", "issue_id")


class TrajectoryFilesTest(unittest.TestCase):
    def test_files(self):
        files = glob.glob(os.path.join(ROOT, "trajectories", "*.jsonl"))
        self.assertTrue(files)
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


if __name__ == "__main__":
    unittest.main()
