"""Check the public default evaluation through the official reporting entry point."""

import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from auditenv import check


class TestEvalDiagnostics(unittest.TestCase):
    def test_official_report_includes_public_default_evaluation(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            for gate in ("run_tests", "run_verifier", "run_paired", "run_remote"):
                stack.enter_context(patch.object(check, gate, return_value=True))
            stack.enter_context(patch.object(check, "run_hard", return_value=(True, {"hard": "table"})))
            baselines = stack.enter_context(patch.object(check, "baseline_table", wraps=check.baseline_table))
            path = Path(directory) / "metrics.json"
            with redirect_stdout(output):
                self.assertEqual(check.main(["--quick", "--json", str(path)]), 0)
            report = json.loads(path.read_text())
        self.assertIn("eval_example", report)
        self.assertIn("dev", report)
        self.assertEqual(report["hard"], {"hard": "table"})
        expected = check.load_episodes(Path(check.ROOT) / "configs/eval_example.json")
        self.assertEqual(len(expected), 20)
        self.assertIn(expected, [call.args[0] for call in baselines.call_args_list])
        self.assertIn("eval_example", output.getvalue())
        metrics = {"precision", "recall", "f1", "return", "steps", "time_s"}
        for name in ("random", "naive_reconcile", "reconcile", "flag_all", "oracle"):
            self.assertTrue(metrics <= report["eval_example"][name].keys())
