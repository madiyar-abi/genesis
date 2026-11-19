"""Deterministic checks of the episode time limit."""

import unittest

from auditenv.env import AuditEnv


class FakeClock:
    now = 100.0

    def __call__(self):
        return self.now


class ClockTests(unittest.TestCase):
    action = {"type": "list_records", "table": "ledger", "limit": 1}

    def setUp(self):
        self.clock = FakeClock()
        self.env = AuditEnv(clock=self.clock)

    def test_default_limit_truncates_and_grades_empty_answer(self):
        self.env.reset(7, {"errors": {}, "mode": "train"})
        self.clock.now = 159.9
        obs, reward, terminated, truncated, info = self.env.step(self.action)
        self.assertIsNone(obs["error"])
        self.assertEqual((reward, terminated, truncated, info), (0.0, False, False, {}))

        self.clock.now = 160.0
        self.assertIsNone(self.env.step(self.action)[0]["error"])

        self.clock.now = 160.1
        late_submit = {"type": "submit"}  # An invalid submission would be penalized if graded.
        obs, reward, terminated, truncated, info = self.env.step(late_submit)
        self.assertEqual(obs["error"]["code"], "time_limit")
        self.assertIsNone(obs["result"])
        self.assertEqual((reward, terminated, truncated), (0.994, False, True))
        self.assertTrue(info["valid"])
        self.assertEqual((info["tp"], info["fp"], info["fn"], info["inspection_steps"]), (0, 0, 0, 3))
        self.assertEqual(self.env.grader_log[-1]["elapsed_s"], 60.1)

        obs, reward, terminated, truncated, info = self.env.step(self.action)
        self.assertEqual(obs["error"]["code"], "episode_over")
        self.assertEqual((reward, terminated, truncated, info), (0.0, False, True, {}))
        self.assertEqual(len(self.env.grader_log), 1)

    def test_custom_limit_in_eval_mode_keeps_grade_private(self):
        self.env.reset(7, {"errors": {}, "mode": "eval", "time_limit_s": 2.0})
        self.clock.now = 102.0
        self.assertIsNone(self.env.step(self.action)[0]["error"])

        self.clock.now = 102.1
        obs, reward, terminated, truncated, info = self.env.step(self.action)
        self.assertEqual(obs["error"]["code"], "time_limit")
        self.assertIsNone(obs["result"])
        self.assertEqual((reward, terminated, truncated, info), (0.0, False, True, {}))
        self.assertEqual(self.env.grader_log[-1]["reward"], 0.996)
