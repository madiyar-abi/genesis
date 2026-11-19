"""Tests for Reconcile baseline policy and reconcile_findings function (T12)."""

import unittest

from auditenv.env import AuditEnv
from auditenv.generator import generate
from auditenv.matcher import match
from auditenv.policies.reconcile import Reconcile, reconcile_findings
from auditenv.run import run_episode


class TestReconcileFindings(unittest.TestCase):
    """Test the pure reconcile_findings function directly on generator output."""

    def test_clean_episodes(self):
        """Clean companies should yield no findings (F1 = 1.0)."""
        cfg = {
            "errors": {"duplicate_invoice": 0, "payment_allocation": 0, "fx_error": 0, "period_cutoff": 0},
            "interacting": {"I1": 0, "I2": 0},
        }
        for seed in range(5):
            ep = generate(seed, cfg)
            findings = reconcile_findings(ep["manifest"], ep["tables"])
            res = match(ep["truth"]["issues"], findings)
            self.assertEqual(len(findings), 0, f"Expected 0 findings on clean seed {seed}, got {len(findings)}")
            self.assertEqual(res["f1"], 1.0)

    def test_dev_seeds_direct(self):
        """reconcile_findings on dev seeds 2000-2009 achieves high F1."""
        f1_scores = []
        for seed in range(2000, 2010):
            ep = generate(seed)
            findings = reconcile_findings(ep["manifest"], ep["tables"])
            res = match(ep["truth"]["issues"], findings)
            f1_scores.append(res["f1"])
            self.assertGreaterEqual(res["recall"], 0.8, f"Seed {seed} recall low: {res['recall']}")
        mean_f1 = sum(f1_scores) / len(f1_scores)
        self.assertGreaterEqual(mean_f1, 0.8, f"Mean F1 too low: {mean_f1}")


class TestReconcilePolicy(unittest.TestCase):
    """Test the Reconcile policy interacting with AuditEnv."""

    def test_acceptance_criteria_10_dev_seeds(self):
        """Acceptance check: on 10 dev seeds mean F1 >= 0.5 and <= 6% of steps are errors."""
        env = AuditEnv()
        f1_scores = []
        total_steps = 0
        error_steps = 0

        for seed in range(2000, 2010):
            policy = Reconcile(seed=seed)
            traj = run_episode(env, policy, seed)
            res = env.result
            self.assertIsNotNone(res)
            f1_scores.append(res["f1"])

            for step in traj:
                obs = step["observation"]
                if obs.get("error") is not None:
                    error_steps += 1
            # -1 because step 0 is reset
            total_steps += len(traj) - 1

            # Each episode must terminate by submit within max_steps (100)
            self.assertTrue(traj[-1]["terminated"])
            self.assertFalse(traj[-1]["truncated"])
            self.assertLessEqual(len(traj) - 1, 50, f"Seed {seed} took too many steps: {len(traj) - 1}")

        mean_f1 = sum(f1_scores) / len(f1_scores)
        error_rate = error_steps / total_steps if total_steps > 0 else 0.0

        self.assertGreaterEqual(mean_f1, 0.5, f"Mean F1 {mean_f1} < 0.5")
        self.assertLessEqual(error_rate, 0.06, f"Error rate {error_rate:.2%} > 6%")

    def test_clean_episode_via_env(self):
        """Clean episode played through environment gives F1 = 1.0 and positive reward."""
        env = AuditEnv()
        cfg = {
            "errors": {"duplicate_invoice": 0, "payment_allocation": 0, "fx_error": 0, "period_cutoff": 0},
            "interacting": {"I1": 0, "I2": 0},
        }
        policy = Reconcile()
        traj = run_episode(env, policy, seed=123, config=cfg)
        res = env.result
        self.assertEqual(res["f1"], 1.0)
        self.assertEqual(res["tp"], 0)
        self.assertEqual(res["fp"], 0)
        self.assertEqual(res["fn"], 0)
        self.assertGreater(res["reward"], 0.0)


if __name__ == "__main__":
    unittest.main()
