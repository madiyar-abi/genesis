import contextlib
import io
import unittest

from auditenv import analyze, attack, fuzz, run, verify


class SeedRangeTests(unittest.TestCase):
    def test_preserves_order_and_repeated_seeds(self):
        self.assertEqual(run.parse_seeds("7,2-4,2"), [7, 2, 3, 4, 2])

    def test_commands_reject_any_reversed_range(self):
        for command in (run, analyze, verify, fuzz, attack):
            with self.subTest(command=command.__name__), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    command.main(["--seeds", "3-1"])
                self.assertEqual(error.exception.code, 2)
        with self.assertRaises(ValueError):
            run.parse_seeds("5,3-1")
