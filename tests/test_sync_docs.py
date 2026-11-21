"""Tests for scripts/sync_docs.py: stale detection, fixing, idempotence, prose preservation, and timing tolerance."""

import json
import math
import os
import shutil
import tempfile
import unittest

from scripts.sync_docs import (
    check_docs,
    extract_design_dev_times,
    format_num,
    render_design_dev_table,
    render_design_hard_table,
    render_pitch_table,
    render_readme_table,
    sync_all,
    sync_design,
    sync_pitch,
    sync_readme,
    validate_finite_nonnegative,
    main,
)

SAMPLE_METRICS = {
    "dev": {
        "flag_all": {
            "experimental_return": -1.0,
            "f1": 0.0,
            "fn": 30,
            "fp": 150,
            "precision": 0.0,
            "recall": 0.0,
            "return": -1.0,
            "steps": 3.8,
            "time_s": 0.020,
            "tp": 0,
        },
        "naive_reconcile": {
            "experimental_return": -0.210,
            "f1": 0.273,
            "fn": 9,
            "fp": 103,
            "precision": 0.169,
            "recall": 0.700,
            "return": -0.506,
            "steps": 17.2,
            "time_s": 0.024,
            "tp": 21,
        },
        "oracle": {
            "experimental_return": 1.0,
            "f1": 1.0,
            "fn": 0,
            "fp": 0,
            "precision": 1.0,
            "recall": 1.0,
            "return": 1.0,
            "steps": 1.0,
            "time_s": 0.017,
            "tp": 30,
        },
        "random": {
            "experimental_return": -0.807,
            "f1": 0.0,
            "fn": 30,
            "fp": 15,
            "precision": 0.0,
            "recall": 0.0,
            "return": -0.807,
            "steps": 31.0,
            "time_s": 0.023,
            "tp": 0,
        },
        "reconcile": {
            "experimental_return": 0.957,
            "f1": 1.0,
            "fn": 0,
            "fp": 0,
            "precision": 1.0,
            "recall": 1.0,
            "return": 0.957,
            "steps": 22.5,
            "time_s": 0.026,
            "tp": 30,
        },
    },
    "hard": {
        "flag_all": {
            "experimental_return": -1.0,
            "f1": 0.0,
            "fn": 92,
            "fp": 300,
            "precision": 0.0,
            "recall": 0.0,
            "return": -1.0,
            "steps": 3.8,
            "time_s": 0.062,
            "tp": 0,
        },
        "naive_reconcile": {
            "experimental_return": -0.656,
            "f1": 0.159,
            "fn": 42,
            "fp": 487,
            "precision": 0.093,
            "recall": 0.543,
            "return": -0.747,
            "steps": 33.2,
            "time_s": 0.182,
            "tp": 50,
        },
        "oracle": {
            "experimental_return": 1.0,
            "f1": 1.0,
            "fn": 0,
            "fp": 0,
            "precision": 1.0,
            "recall": 1.0,
            "return": 1.0,
            "steps": 1.0,
            "time_s": 0.065,
            "tp": 92,
        },
        "random": {
            "experimental_return": -0.806,
            "f1": 0.0,
            "fn": 92,
            "fp": 33,
            "precision": 0.0,
            "recall": 0.0,
            "return": -0.806,
            "steps": 33.1,
            "time_s": 0.058,
            "tp": 0,
        },
        "reconcile": {
            "experimental_return": -0.341,
            "f1": 0.611,
            "fn": 12,
            "fp": 90,
            "precision": 0.471,
            "recall": 0.870,
            "return": -0.095,
            "steps": 42.6,
            "time_s": 0.086,
            "tp": 80,
        },
        "reconcile_hard": {
            "experimental_return": 0.917,
            "f1": 1.0,
            "fn": 0,
            "fp": 0,
            "precision": 1.0,
            "recall": 1.0,
            "return": 0.917,
            "steps": 42.6,
            "time_s": 0.073,
            "tp": 92,
        },
    },
}


class TestSyncDocs(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = self.tmpdir.name
        os.makedirs(os.path.join(self.repo_root, "docs"), exist_ok=True)

        self.json_path = os.path.join(self.repo_root, "metrics.json")
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_METRICS, f)

        # Write initial sample markdown documents
        self.readme_path = os.path.join(self.repo_root, "README.md")
        with open(self.readme_path, "w", encoding="utf-8") as f:
            f.write(
                "# Title\n\nIntro prose.\n\n"
                "## Results (from the check, dev split = `configs/dev.json`, 10 episodes)\n\n"
                "| policy | P | R | F1 | mean return | mean steps |\n"
                "|---|---|---|---|---|---|\n"
                "| oracle (grader-side) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |\n"
                "| reconcile (policy-aware rules) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |\n"
                "| naive reconcile | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |\n"
                "| random explorer | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |\n"
                "| flag-everything | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |\n\n"
                "Trailing prose.\n"
            )

        self.design_path = os.path.join(self.repo_root, "docs", "DESIGN.md")
        with open(self.design_path, "w", encoding="utf-8") as f:
            f.write(
                "# Design\n\n## 9. Results\n\n"
                "`uv run python -m auditenv.check` (dev split; P/R/F1 micro-averaged; return, steps, time = means):\n\n"
                "| policy | seeds | P | R | F1 | return | steps | time s | exp. return* |\n"
                "|---|---|---|---|---|---|---|---|---|\n"
                "| random explorer (seeded) | 2000–2009 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.001 | 0.000 |\n"
                "| naive reconciliation | 2000–2009 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.001 | 0.000 |\n"
                "| reconciliation (policy-aware) | 2000–2009 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.001 | 0.000 |\n"
                "| flag-everything attack | 2000–2009 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.001 | 0.000 |\n"
                "| oracle (grader-side) | 2000–2009 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.001 | 0.000 |\n\n"
                "Middle design prose.\n\n"
                "### Hard mode (`{\"difficulty\": \"hard\"}`, `configs/eval_hard.json`)\n\n"
                "Hard prose.\n\n"
                "| policy | P | R | F1 | return | steps | exp. return* |\n"
                "|---|---|---|---|---|---|---|\n"
                "| random explorer (seeded) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 |\n"
                "| naive reconciliation | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 |\n"
                "| reconciliation (default rules) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 |\n"
                "| reconciliation + hard rules (`reconcile_hard`) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 |\n"
                "| flag-everything attack | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 |\n"
                "| oracle (grader-side) | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.000 |\n\n"
                "Ending design prose.\n"
            )

        self.pitch_path = os.path.join(self.repo_root, "docs", "PITCH.md")
        with open(self.pitch_path, "w", encoding="utf-8") as f:
            f.write(
                "# Pitch\n\n## 7. Results\n"
                "- Dev split (micro P/R/F1 · mean return): oracle 1.0/1.0/1.0 · 1.000\n"
                "- Hard split: reconcile drops to 0.47\n\n"
                "## 8. Team\n"
            )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_format_num(self):
        self.assertEqual(format_num(1.0, 3), "1.000")
        self.assertEqual(format_num(-0.506, 3), "−0.506")  # uses \u2212
        self.assertEqual(format_num(-1.0, 3), "−1.000")
        self.assertEqual(format_num(22.5, 1), "22.5")
        self.assertEqual(format_num(0.0, 3), "0.000")

    def test_validate_finite_nonnegative(self):
        self.assertTrue(validate_finite_nonnegative("0.023"))
        self.assertTrue(validate_finite_nonnegative("0"))
        self.assertTrue(validate_finite_nonnegative("0.0"))
        self.assertTrue(validate_finite_nonnegative("100.5"))
        self.assertFalse(validate_finite_nonnegative("-0.01"))
        self.assertFalse(validate_finite_nonnegative("NaN"))
        self.assertFalse(validate_finite_nonnegative("inf"))
        self.assertFalse(validate_finite_nonnegative("-inf"))
        self.assertFalse(validate_finite_nonnegative("abc"))

    def test_stale_detection(self):
        # Before syncing, files have stale 0.000 numbers or missing pitch table
        errors = check_docs(self.repo_root, SAMPLE_METRICS)
        self.assertTrue(len(errors) >= 3)
        self.assertTrue(any("README.md" in e for e in errors))
        self.assertTrue(any("DESIGN.md" in e for e in errors))
        self.assertTrue(any("PITCH.md" in e for e in errors))

    def test_fix_and_check(self):
        # Running sync_all fixes all documents
        changed = sync_all(self.repo_root, SAMPLE_METRICS)
        self.assertTrue(all(changed.values()))

        # Now check_docs should pass with 0 errors
        errors = check_docs(self.repo_root, SAMPLE_METRICS)
        self.assertEqual(errors, [])

    def test_stale_chart_is_drift(self):
        # docs/baselines.svg (slide 7) is rendered from the same metrics; an old rendering is drift
        sync_all(self.repo_root, SAMPLE_METRICS)
        chart = os.path.join(self.repo_root, "docs", "baselines.svg")
        with open(chart, "w", encoding="utf-8") as f:
            f.write("<svg>old</svg>\n")
        self.assertEqual(check_docs(self.repo_root, SAMPLE_METRICS), ["baselines.svg: chart differs from measured data"])
        sync_all(self.repo_root, SAMPLE_METRICS)
        self.assertEqual(check_docs(self.repo_root, SAMPLE_METRICS), [])

    def test_idempotence(self):
        # First sync
        sync_all(self.repo_root, SAMPLE_METRICS)
        with open(self.readme_path) as f:
            readme_1 = f.read()
        with open(self.design_path) as f:
            design_1 = f.read()
        with open(self.pitch_path) as f:
            pitch_1 = f.read()

        # Second sync with identical input
        changed_second = sync_all(self.repo_root, SAMPLE_METRICS)
        self.assertFalse(any(changed_second.values()))

        with open(self.readme_path) as f:
            readme_2 = f.read()
        with open(self.design_path) as f:
            design_2 = f.read()
        with open(self.pitch_path) as f:
            pitch_2 = f.read()

        self.assertEqual(readme_1, readme_2)
        self.assertEqual(design_1, design_2)
        self.assertEqual(pitch_1, pitch_2)

    def test_unchanged_prose(self):
        # Sync the documents
        sync_all(self.repo_root, SAMPLE_METRICS)

        with open(self.readme_path) as f:
            readme = f.read()
        self.assertTrue(readme.startswith("# Title\n\nIntro prose.\n\n"))
        self.assertTrue(readme.endswith("\n\nTrailing prose.\n"))

        with open(self.design_path) as f:
            design = f.read()
        self.assertTrue(design.startswith("# Design\n\n## 9. Results\n\n"))
        self.assertIn("\n\nMiddle design prose.\n\n### Hard mode", design)
        self.assertTrue(design.endswith("\n\nEnding design prose.\n"))

        with open(self.pitch_path) as f:
            pitch = f.read()
        self.assertTrue(pitch.startswith("# Pitch\n\n## 7. Results\n\n"))
        self.assertIn("- Dev split (micro P/R/F1 · mean return): oracle 1.0/1.0/1.0 · 1.000\n", pitch)
        self.assertTrue(pitch.endswith("## 8. Team\n"))

    def test_timing_tolerance_in_check(self):
        sync_all(self.repo_root, SAMPLE_METRICS)
        self.assertEqual(check_docs(self.repo_root, SAMPLE_METRICS), [])

        # Alter time_s in docs/DESIGN.md to a different valid finite non-negative float
        with open(self.design_path) as f:
            content = f.read()
        # Change 0.023 to 0.999
        content = content.replace("0.023", "0.999")
        with open(self.design_path, "w") as f:
            f.write(content)

        # check_docs must still pass because timing differences are ignored
        errors = check_docs(self.repo_root, SAMPLE_METRICS)
        self.assertEqual(errors, [])

    def test_timing_invalid_fails(self):
        sync_all(self.repo_root, SAMPLE_METRICS)
        with open(self.design_path) as f:
            content = f.read()
        # Change 0.023 to invalid negative or string
        content = content.replace("0.023", "-0.500")
        with open(self.design_path, "w") as f:
            f.write(content)

        errors = check_docs(self.repo_root, SAMPLE_METRICS)
        self.assertTrue(any("invalid time s" in e for e in errors))

    def test_cli_entrypoint(self):
        # Test CLI check
        ret = main(["--check", "--json", self.json_path, "--repo-root", self.repo_root])
        self.assertEqual(ret, 1)  # initial stale docs fail check

        # Test CLI sync
        ret = main(["--json", self.json_path, "--repo-root", self.repo_root])
        self.assertEqual(ret, 0)

        # Test CLI check passes after sync
        ret = main(["--check", "--json", self.json_path, "--repo-root", self.repo_root])
        self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
