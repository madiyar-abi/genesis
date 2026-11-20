"""Diagnostics and caller state around the official unittest gate."""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from auditenv import check


class CheckFailuresTest(unittest.TestCase):
    def test_failure_reports_test_and_assertion(self):
        class Synthetic(unittest.TestCase):
            def test_example(self):
                print("suppressed test chatter")
                self.assertEqual(17, 19)

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Synthetic)
        output = io.StringIO()
        with patch.object(unittest.defaultTestLoader, "discover", return_value=suite), redirect_stdout(output):
            self.assertFalse(check.run_tests())
        self.assertIn("test_example", output.getvalue())
        self.assertIn("17 != 19", output.getvalue())
        self.assertNotIn("suppressed test chatter", output.getvalue())

    def test_discovery_exception_restores_caller_state(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"AUDITENV_SECRET": "test-value"}), redirect_stdout(output):
            with patch.object(unittest.defaultTestLoader, "discover", side_effect=RuntimeError("discovery")):
                with self.assertRaisesRegex(RuntimeError, "discovery"):
                    check.run_tests()
            self.assertEqual(os.environ.get("AUDITENV_SECRET"), "test-value")
            self.assertIs(sys.stdout, output)
