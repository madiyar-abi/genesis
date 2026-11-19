import unittest

from auditenv.env import AuditEnv
from auditenv.policies.flag_all import FlagAll
from auditenv.policies.random_explorer import RandomExplorer
from auditenv.run import run_episode
from auditenv.schema import ISSUE_TYPES, MAX_FINDINGS, validate_findings


_FIRST_OBSERVATION = {
    "manifest": {"episode_id": "ep_test", "base_currency": "USD"},
    "steps_remaining": 100,
}


def _page(rows, steps_remaining, cursor=None):
    return {
        "steps_remaining": steps_remaining,
        "result": {"rows": rows, "next_cursor": cursor, "total": len(rows)},
        "error": None,
    }


class PolicyContractTests(unittest.TestCase):
    def test_flag_all_pages_both_tables_and_submits_valid_findings(self):
        policy = FlagAll()
        policy.reset(_FIRST_OBSERVATION)
        self.assertEqual(policy.act(_FIRST_OBSERVATION)["table"], "invoices")

        invoice = {"invoice_id": "inv", "doc_id": "doc1", "total_minor": 100}
        second_page = policy.act(_page([invoice], 99, cursor="more"))
        self.assertEqual((second_page["table"], second_page["cursor"]), ("invoices", "more"))

        payment_page = policy.act(_page([], 98))
        self.assertEqual((payment_page["table"], payment_page["cursor"]), ("payments", None))

        refund = {"payment_id": "pay", "doc_id": "doc2", "amount_minor": -50}
        submit = policy.act(_page([refund], 97))
        self.assertEqual(submit["type"], "submit")
        self.assertIsNone(validate_findings(submit["findings"], "ep_test"))
        findings = submit["findings"]["findings"]
        self.assertEqual([finding["type"] for finding in findings], list(ISSUE_TYPES) * 2)
        self.assertEqual(findings[-1]["affected_ids"], ["pay"])
        self.assertEqual(findings[-1]["evidence_ids"], ["doc2"])
        self.assertEqual(findings[-1]["claimed_amount_minor"], 50)

    def test_flag_all_keeps_paging_after_reaching_finding_limit(self):
        policy = FlagAll()
        policy.reset(_FIRST_OBSERVATION)
        policy.act(_FIRST_OBSERVATION)
        invoices = [
            {"invoice_id": f"inv{i}", "doc_id": f"doc{i}", "total_minor": i}
            for i in range(20)
        ]
        self.assertEqual(policy.act(_page(invoices, 99))["table"], "payments")
        submit = policy.act(_page([], 98))
        self.assertEqual(len(submit["findings"]["findings"]), MAX_FINDINGS)

    def test_both_policies_reserve_last_step_for_submit(self):
        first = {**_FIRST_OBSERVATION, "steps_remaining": 1}
        for policy in (FlagAll(), RandomExplorer()):
            with self.subTest(policy=policy.name):
                policy.reset(first)
                self.assertEqual(policy.act(first), {
                    "type": "submit",
                    "findings": {"episode_id": "ep_test", "findings": []},
                })


class BaselineIntegrationTests(unittest.TestCase):
    def test_five_seeds_reproduce_trajectories_and_flag_all_scores_poorly(self):
        flag_rewards = []
        config = {"mode": "train", "errors": {"duplicate_invoice": 1, "fx_error": 1}}
        for policy_class in (RandomExplorer, FlagAll):
            policy = policy_class(seed=17)
            for seed in range(5):
                with self.subTest(policy=policy.name, seed=seed):
                    trajectory = run_episode(AuditEnv(), policy, seed, config)
                    self.assertEqual(trajectory, run_episode(AuditEnv(), policy, seed, config))
                    terminal = trajectory[-1]
                    self.assertTrue(terminal["terminated"])
                    self.assertFalse(terminal["truncated"])
                    self.assertEqual(terminal["action"]["type"], "submit")
                    submission = terminal["action"]["findings"]
                    self.assertIsNone(validate_findings(submission, terminal["episode_id"]))
                    self.assertTrue(all(step["observation"]["error"] is None for step in trajectory[1:]))
                    if policy_class is FlagAll:
                        flag_rewards.append(terminal["reward"])
                    else:
                        self.assertTrue(20 <= terminal["step"] - 1 <= 40)
        self.assertEqual(len(flag_rewards), 5)
        self.assertLess(sum(flag_rewards) / len(flag_rewards), 0)
