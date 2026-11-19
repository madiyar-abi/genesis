"""scripts/shortcut_miner.py: the miner runs on a few seeds and reports every issue type for both labelings."""

import unittest

from auditenv.generator import ISSUE_TYPES
from scripts.shortcut_miner import LABELINGS, TABLES, markdown, mine


class ShortcutMinerTest(unittest.TestCase):
    def check(self, r: dict, episodes: int) -> None:
        self.assertEqual(r["episodes"], episodes)
        self.assertEqual(set(r["records"]), set(TABLES))
        for labeling in LABELINGS:
            self.assertEqual(set(r["labelings"][labeling]), set(ISSUE_TYPES))
            for t in ISSUE_TYPES:
                d = r["labelings"][labeling][t]
                self.assertLessEqual(len(d["top"]), 10)
                self.assertTrue(0.0 <= d["max_precision"] <= 1.0)
                for c in d["top"]:
                    self.assertGreaterEqual(c["support"], 30)
        self.assertIn("## Max precision per issue type", markdown(r, 0.0))

    def test_default(self):
        self.check(mine(list(range(20))), 40)

    def test_hard(self):
        self.check(mine(list(range(5)), hard=True), 10)


if __name__ == "__main__":
    unittest.main()
