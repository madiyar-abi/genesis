from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from auditenv.analyze import analyze, main, markdown
from auditenv.schema import ISSUE_TYPES


_MIXED_CONFIG = {
    "mode": "eval",
    "errors": {issue_type: 1 for issue_type in ISSUE_TYPES},
    "interacting": {"I1": 1, "I2": 1},
}
_EPISODES = [(2000, _MIXED_CONFIG), (2001, {"errors": {}})]


class AnalyzeTests(unittest.TestCase):
    def test_oracle_finds_every_type_and_scenario_in_eval_mode(self):
        report = analyze("oracle", _EPISODES)
        self.assertEqual(report["episodes"], 2)
        self.assertEqual(report["by_type"], {
            "duplicate_invoice": {"tp": 1, "fn": 0, "recall": 1.0},
            "payment_allocation": {"tp": 2, "fn": 0, "recall": 1.0},
            "fx_error": {"tp": 3, "fn": 0, "recall": 1.0},
            "period_cutoff": {"tp": 2, "fn": 0, "recall": 1.0},
        })
        self.assertEqual(report["by_scenario"], {
            "single": {"tp": 4, "fn": 0, "recall": 1.0},
            "I1": {"tp": 2, "fn": 0, "recall": 1.0},
            "I2": {"tp": 2, "fn": 0, "recall": 1.0},
        })
        self.assertEqual(report["fp_total"], 0)
        self.assertEqual(report["fp_by_reason"], {})
        self.assertEqual(report["mean"], {
            "precision": 1.0, "recall": 1.0, "f1": 1.0, "return": 1.0, "steps": 1,
        })

    def test_flag_all_counts_false_positive_reasons_and_missed_issues(self):
        report = analyze("flag_all", _EPISODES)
        self.assertGreater(report["fp_total"], 0)
        self.assertEqual(report["fp_total"], sum(report["fp_by_reason"].values()))
        self.assertGreater(report["fp_by_reason"]["no_matching_issue"], 0)
        self.assertGreater(sum(row["fn"] for row in report["by_type"].values()), 0)
        for field in ("tp", "fn"):
            self.assertEqual(
                sum(row[field] for row in report["by_type"].values()),
                sum(row[field] for row in report["by_scenario"].values()),
            )

    def test_cli_selects_configured_seeds_and_outputs_matching_formats(self):
        with tempfile.TemporaryDirectory(dir=".") as tmp:
            config = Path(tmp) / "dev.json"
            config.write_text(json.dumps({
                "config_version": "1.0",
                "split": "dev",
                "episodes": [{"seed": seed, "config": cfg} for seed, cfg in _EPISODES],
            }), encoding="utf-8")
            output = Path(tmp) / "report.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = main([
                    "--policy", "random", "--seeds", "2001",
                    "--config", str(config), "--json", str(output),
                ])
            self.assertEqual(status, 0)
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(report, analyze("random", _EPISODES[1:]))
        self.assertEqual(stdout.getvalue(), markdown(report) + "\n")
        self.assertIn("| Scenario | TP | FN | Recall |", stdout.getvalue())
        self.assertEqual(report["by_scenario"]["I1"]["recall"], 0.0)
