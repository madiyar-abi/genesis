import unittest

from auditenv.metrics import prf1, terminal_reward


class MetricsTests(unittest.TestCase):
    def test_perfect_match(self):
        self.assertEqual(prf1(4, 0, 0), (1.0, 1.0, 1.0))

    def test_mixed_counts(self):
        self.assertEqual(prf1(2, 1, 2), (2 / 3, 0.5, 4 / 7))

    def test_clean_and_silent(self):
        self.assertEqual(prf1(0, 0, 0), (0.0, 0.0, 1.0))

    def test_clean_with_false_positives(self):
        self.assertEqual(prf1(0, 3, 0), (0.0, 0.0, 0.0))

    def test_dirty_and_silent(self):
        self.assertEqual(prf1(0, 0, 3), (0.0, 0.0, 0.0))

    def test_perfect_reward(self):
        self.assertEqual(terminal_reward(1.0, 0), 1.0)

    def test_inspection_step_cost(self):
        self.assertEqual(terminal_reward(0.75, 10), 0.48)

    def test_lower_clip(self):
        self.assertEqual(terminal_reward(0.0, 100), -1.0)

    def test_upper_clip(self):
        self.assertEqual(terminal_reward(1.1, 0), 1.0)

    def test_not_rounded(self):
        # the jury compares rewards to 1e-9 (47/150 = 0.31333...), so no rounding to six places
        self.assertNotEqual(terminal_reward(1 / 3, 1), -0.335333)
        self.assertAlmostEqual(terminal_reward(1 / 3, 1), -1006 / 3000, delta=1e-12)
