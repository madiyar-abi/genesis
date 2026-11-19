from statistics import mean
import unittest

from auditenv.env import AuditEnv
from auditenv.policies.naive_reconcile import NaiveReconcile
from auditenv.policies.reconcile import Reconcile
from auditenv.run import run_episode


class NaiveReconcileTests(unittest.TestCase):
    def test_clean_distractors_attract_false_positives(self):
        env = AuditEnv()
        affected = 0
        config = {"errors": {}, "distractors": True}
        for seed in range(2000, 2010):
            with self.subTest(seed=seed):
                trajectory = run_episode(env, NaiveReconcile(), seed, config)
                self.assertTrue(env.result["valid"])
                self.assertEqual(env.result["tp"] + env.result["fn"], 0)
                self.assertEqual(trajectory, run_episode(env, NaiveReconcile(), seed, config))
                inspection_types = {entry["action"]["type"] for entry in trajectory[1:-1]}
                self.assertEqual(inspection_types, {"list_records"})
                listed_tables = {entry["action"]["table"] for entry in trajectory[1:-1]}
                self.assertEqual(listed_tables, {"ledger", "invoices", "payments", "fx"})
                affected += env.result["fp"] > 0
        self.assertGreaterEqual(affected, 5)

    def test_naive_means_lower_f1_on_dirty_episodes(self):
        env = AuditEnv()
        naive_f1, reconcile_f1 = [], []
        config = {
            "distractors": True,
            "errors": {"duplicate_invoice": 1, "payment_allocation": 1,
                       "period_cutoff": 1, "fx_error": 1},
            "interacting": {"I1": 1, "I2": 1},
        }
        for seed in range(2000, 2010):
            with self.subTest(seed=seed):
                run_episode(env, NaiveReconcile(), seed, config)
                self.assertTrue(env.result["valid"])
                naive_f1.append(env.result["f1"])
                run_episode(env, Reconcile(), seed, config)
                self.assertTrue(env.result["valid"])
                reconcile_f1.append(env.result["f1"])
        self.assertEqual(len(naive_f1), 10)
        self.assertLess(mean(naive_f1), mean(reconcile_f1))
