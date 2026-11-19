"""Tests for scripts/sensitivity.py: the default re-grade reproduces the env reward, a larger step cost never
raises a return, the tolerance override is live and the matcher is restored afterwards."""

import copy
import unittest

from auditenv import matcher, metrics
from auditenv.env import AuditEnv
from auditenv.run import load_episodes
from scripts.sensitivity import DEFAULT_COST, DEFAULT_TOL, SPLITS, STEP_COSTS, TOLERANCES, params, play, regrade

DEV_POLICIES = SPLITS[0][2]


class SensitivityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        episodes = load_episodes("configs/dev.json")[2:4]  # two dev episodes with injected errors
        env = AuditEnv()
        cls.runs = {name: [play(env, name, s, c) for s, c in episodes] for name in DEV_POLICIES}

    def test_default_parameters_reproduce_env_reward(self):
        for name, runs in self.runs.items():
            for run in runs:
                self.assertEqual(regrade(run, DEFAULT_COST, TOLERANCES[DEFAULT_TOL]), run["reward"],
                                 f"{name} {run['episode_id']}")

    def test_larger_step_cost_never_increases_return(self):
        for name, runs in self.runs.items():
            for run in runs:
                for tol in TOLERANCES.values():
                    rewards = [regrade(run, c, tol) for c in sorted(STEP_COSTS)]
                    self.assertEqual(rewards, sorted(rewards, reverse=True), f"{name} {run['episode_id']}")

    def test_tolerance_override_is_live_and_restored(self):
        run = copy.deepcopy(self.runs["oracle"][0])
        f = run["submission"]["findings"][0]
        self.assertGreaterEqual(f["claimed_amount_minor"], 10_000)
        f["claimed_amount_minor"] += f["claimed_amount_minor"] // 200  # 0.5 % off: outside 0.1 %, inside 1 %
        self.assertLess(regrade(run, DEFAULT_COST, TOLERANCES["0 (exact)"]), 1.0)
        self.assertLess(regrade(run, DEFAULT_COST, TOLERANCES[DEFAULT_TOL]), 1.0)
        self.assertEqual(regrade(run, DEFAULT_COST, TOLERANCES["1 %"]), 1.0)
        self.assertIs(matcher.tolerance, TOLERANCES[DEFAULT_TOL])
        self.assertIs(matcher.terminal_reward, metrics.terminal_reward)


if __name__ == "__main__":
    unittest.main()
