"""Round-2 jury-style review: strict input handling (REVIEW.md "Round 2", defects 3-5)."""

import io
import json
import unittest

from auditenv.env import AuditEnv
from auditenv.server import serve


class StrictInputTests(unittest.TestCase):
    def test_unknown_action_parameters_are_bad_params_and_cost_a_step(self):
        env = AuditEnv()
        env.reset(3, {})
        for action in ({"type": "list_records", "table": "ledger", "extra": 1},
                       {"type": "get_document", "doc_id": "X", "table": "ledger"},
                       {"type": "calculator", "expression": "1+1", "precision": 9}):
            obs, reward, term, trunc, info = env.step(action)
            self.assertEqual(obs["error"]["code"], "bad_params", action)
            self.assertFalse(term or trunc)
        self.assertEqual(obs["step"], 3)

    def test_submit_with_unknown_parameters_still_ends_the_episode_as_invalid(self):
        env = AuditEnv()
        _, info = env.reset(3, {"mode": "train"})
        obs, reward, term, trunc, info = env.step(
            {"type": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}, "x": 1})
        self.assertTrue(term)
        self.assertFalse(trunc)
        self.assertEqual(reward, -1.0)
        self.assertEqual(obs["error"]["code"], "invalid_findings")
        self.assertIn("unknown parameters for submit", obs["error"]["message"])
        self.assertFalse(env.grader_log[-1]["valid"])

    def test_exotic_finding_keys_are_an_invalid_submission_not_a_crash(self):
        env = AuditEnv()
        _, info = env.reset(3, {"mode": "train"})
        f = {"type": "fx_error", "affected_ids": ["X"], "claimed_amount_minor": 1, "currency": "USD",
             "evidence_ids": ["Y"], 1: 2, (1, 2): 3}
        obs, reward, term, _, _ = env.step({"type": "submit", "findings": {"episode_id": info["episode_id"],
                                                                           "findings": [f]}})
        self.assertTrue(term)
        self.assertEqual(reward, -1.0)
        self.assertEqual(obs["error"]["code"], "invalid_findings")
        self.assertFalse(env.grader_log[-1]["valid"])

    def test_reset_rejects_loose_seeds_and_config_values(self):
        env = AuditEnv()
        for seed, cfg in ((1.5, {}), (True, {}), (None, {}), ("7", {}), (1, {"time_limit_s": float("nan")}),
                          (1, {"time_limit_s": float("inf")}), (1, {"time_limit_s": 10 ** 400}),
                          (1, {"distractors": "no"}),
                          (1, {"transform_seed": 1.5}), (1, {"transform_seed": True})):
            with self.assertRaises(ValueError, msg=(seed, cfg)):
                env.reset(seed, cfg)
        env.reset(1, {"time_limit_s": 0.5, "distractors": False, "transform_seed": 3})

    def test_reset_rejects_config_of_the_wrong_shape(self):
        # Round 10: {"errors": "x"} raised AttributeError and {"errors": 0 | false | []} silently gave a clean company.
        env = AuditEnv()
        for cfg in ({"errors": "x"}, {"errors": 5}, {"errors": 0}, {"errors": False}, {"errors": []},
                    {"errors": None}, {"interacting": [1]}, {"interacting": 0}, {"interacting": None},
                    [("errors", {})], 5, "x"):
            with self.assertRaises(ValueError, msg=cfg):
                env.reset(1, cfg)
        env.reset(1, None)
        env.reset(1, {"errors": {}, "interacting": {}})

    def test_server_does_not_coerce_seeds(self):
        inp = io.StringIO(json.dumps({"cmd": "reset", "seed": 1.5}) + "\n" + json.dumps({"cmd": "reset", "seed": 1}) + "\n")
        out = io.StringIO()
        serve(inp, out)
        first, second = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertIn("error", first)
        self.assertIn("observation", second)


if __name__ == "__main__":
    unittest.main()
