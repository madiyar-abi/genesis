import unittest

from auditenv.env import AuditEnv
from auditenv.generator import ISSUE_TYPES, generate
from auditenv.policies.oracle import Oracle
from auditenv.run import run_episode

CFG = {"errors": {t: 1 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}


def oracle(env):
    return Oracle(env._ep["truth"])


class TransformTest(unittest.TestCase):
    def test_ids_relabelled_and_rows_permuted(self):
        a, b = generate(11, CFG), generate(11, {**CFG, "transform_seed": 3})
        for table, key in (("ledger", "row_id"), ("invoices", "invoice_id"), ("payments", "payment_id")):
            ids_a = [r[key] for r in a["tables"][table]]
            ids_b = [r[key] for r in b["tables"][table]]
            self.assertEqual(len(ids_a), len(ids_b))
            self.assertFalse(set(ids_a) & set(ids_b), table)
        self.assertNotEqual([r["timestamp"] for r in a["tables"]["ledger"]],
                            [r["timestamp"] for r in b["tables"]["ledger"]])
        self.assertEqual(sorted(r["timestamp"] for r in a["tables"]["ledger"]),
                         sorted(r["timestamp"] for r in b["tables"]["ledger"]))
        self.assertEqual([(i["type"], i["expected_amount_minor"]) for i in a["truth"]["issues"]],
                         [(i["type"], i["expected_amount_minor"]) for i in b["truth"]["issues"]])

    def test_oracle_reward_preserved(self):
        env = AuditEnv()
        for seed in range(20):
            r1 = run_episode(env, None, seed, CFG, policy_factory=oracle)[-1]["reward"]
            r2 = run_episode(env, None, seed, {**CFG, "transform_seed": 99}, policy_factory=oracle)[-1]["reward"]
            self.assertEqual(r1, r2)
            self.assertEqual(r1, 1.0)

    def test_old_answer_fails_after_relabel(self):
        env = AuditEnv()
        env.reset(7, CFG)
        old = Oracle(env._ep["truth"])
        obs, _ = env.reset(7, {**CFG, "transform_seed": 1})
        old.episode_id = obs["manifest"]["episode_id"]
        _, reward, *_ = env.step(old.act(obs))
        self.assertEqual(env.result["tp"], 0)
        self.assertLess(reward, 0)


if __name__ == "__main__":
    unittest.main()
