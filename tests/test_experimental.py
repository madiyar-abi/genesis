import copy
import unittest

from auditenv.experimental import experimental_reward
from auditenv.matcher import grade

_EPISODE_ID = "ep_weighted"
_TRUTH = {
    "episode_id": _EPISODE_ID,
    "issues": [
        {
            "issue_id": f"issue_{name}",
            "type": "fx_error",
            "affected_ids": [name],
            "expected_amount_minor": amount,
            "currency": "USD",
            "evidence_sets": [[f"doc_{name}"]],
        }
        for name, amount in (("small", 100), ("large", 900))
    ],
}
_ORACLE = [
    {
        "type": issue["type"],
        "affected_ids": issue["affected_ids"],
        "claimed_amount_minor": issue["expected_amount_minor"],
        "currency": issue["currency"],
        "evidence_ids": issue["evidence_sets"][0],
    }
    for issue in _TRUTH["issues"]
]


def _grade(truth, findings, steps=0):
    return grade(truth, {"episode_id": _EPISODE_ID, "findings": findings}, _EPISODE_ID, steps)


class ExperimentalRewardTests(unittest.TestCase):
    def test_oracle(self):
        result = _grade(_TRUTH, _ORACLE)
        self.assertEqual(experimental_reward(result, _TRUTH, _ORACLE), 1.0)

    def test_clean_silence(self):
        truth = {"episode_id": _EPISODE_ID, "issues": []}
        result = _grade(truth, [])
        self.assertEqual(experimental_reward(result, truth, []), 1.0)
        zero_claim = [{**_ORACLE[0], "claimed_amount_minor": 0}]
        self.assertEqual(experimental_reward(_grade(truth, zero_claim), truth, zero_claim), -1.0)

    def test_missing_more_material_issue_costs_more(self):
        misses_large = _grade(_TRUTH, _ORACLE[:1])
        misses_small = _grade(_TRUTH, _ORACLE[1:])
        self.assertEqual(misses_large["reward"], misses_small["reward"])
        miss_large_reward = experimental_reward(misses_large, _TRUTH, _ORACLE[:1])
        miss_small_reward = experimental_reward(misses_small, _TRUTH, _ORACLE[1:])
        self.assertLess(miss_large_reward, miss_small_reward)

    def test_fp_weight_and_step_cost_leave_shared_grade_intact(self):
        findings = [*_ORACLE, {**_ORACLE[0], "claimed_amount_minor": 500}]
        result = _grade(_TRUTH, findings, steps=10)
        original = copy.deepcopy(result)
        self.assertEqual(experimental_reward(result, _TRUTH, findings), 0.58)
        self.assertEqual(result, original)
        self.assertEqual(_grade(_TRUTH, findings, steps=10), original)
        self.assertEqual(result["reward"], 0.58)  # Both F1 scores happen to be 0.8 here.

        findings[-1]["claimed_amount_minor"] = 2000
        larger_fp = _grade(_TRUTH, findings, steps=10)
        self.assertEqual(larger_fp["reward"], original["reward"])
        self.assertEqual(experimental_reward(larger_fp, _TRUTH, findings), -0.02)

    def test_zero_amount_junk_is_not_free(self):
        # Red-team round 9: claimed_amount_minor 0 made false positives weightless (oracle + junk = 1.0).
        # A false positive weighs at least the mean expected amount, so with every issue found the
        # weighted F1 is never above the shared count-based F1.
        for claimed in (0, 1, 499):
            junk = [{**_ORACLE[0], "affected_ids": [f"J{k}"], "claimed_amount_minor": claimed} for k in range(3)]
            findings = [*_ORACLE, *junk]
            result = _grade(_TRUTH, findings)
            self.assertLessEqual(experimental_reward(result, _TRUTH, findings), result["reward"])
            self.assertLess(experimental_reward(result, _TRUTH, findings), 1.0)

    def test_invalid_submission_keeps_fixed_penalty(self):
        result = grade(_TRUTH, None, _EPISODE_ID, 0)
        self.assertEqual(experimental_reward(result, _TRUTH, []), -1.0)
