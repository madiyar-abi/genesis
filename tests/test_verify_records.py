"""Tests for record-level verifier checks: FX rates, manifest required fields, and timestamp diagnostics."""

import contextlib
import io
import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from auditenv.export import export_episode
from auditenv.generator import generate
from auditenv.verify import main as verify_main, verify_episode


def _run_cli(sample: dict) -> tuple[int, str]:
    buf = io.StringIO()
    with TemporaryDirectory() as tmp:
        export_episode(sample, Path(tmp) / sample["episode_id"])
        with contextlib.redirect_stdout(buf):
            code = verify_main(["--dir", tmp])
    return code, buf.getvalue()


class TestVerifyRecords(unittest.TestCase):
    def setUp(self):
        self.ep = generate(2000, {"errors": {}})

    # Task 1: every published FX rate must be a finite positive decimal

    def test_fx_rate_valid_control(self):
        sample = deepcopy(self.ep)
        self.assertEqual(verify_episode(sample), [])
        code, out = _run_cli(sample)
        self.assertEqual(code, 0)
        self.assertIn("1/1 episodes valid", out)

    def test_fx_rate_invalid_values(self):
        for bad_rate in ("not-a-rate", "0", "-1.2", "NaN", "Infinity"):
            with self.subTest(bad_rate=bad_rate):
                sample = deepcopy(self.ep)
                row = next(r for r in sample["tables"]["fx"] if r["fx_id"] == "2025-03-02:GBP:USD")
                row["rate"] = bad_rate

                problems = verify_episode(sample)
                self.assertTrue(
                    any("2025-03-02:GBP:USD" in p for p in problems),
                    f"Expected problem containing '2025-03-02:GBP:USD' for rate {bad_rate!r}, got: {problems}"
                )

                code, out = _run_cli(sample)
                self.assertEqual(code, 1, f"Expected CLI exit 1 for rate {bad_rate!r}, got {code}")
                self.assertIn("2025-03-02:GBP:USD", out)

    def test_fx_rate_corrupt_in_episode_with_fx_errors_does_not_raise(self):
        ep2003 = generate(2003)
        sample = deepcopy(ep2003)
        row = next(r for r in sample["tables"]["fx"] if r["fx_id"] == "2025-05-01:KZT:GBP")
        row["rate"] = "not-a-rate"
        problems = verify_episode(sample)
        self.assertTrue(
            any("2025-05-01:KZT:GBP" in p for p in problems),
            f"Expected problem for corrupted rate, got: {problems}"
        )

    # Task 2: manifest must carry its required fields

    def test_manifest_control(self):
        sample = deepcopy(self.ep)
        self.assertEqual(verify_episode(sample), [])
        code, out = _run_cli(sample)
        self.assertEqual(code, 0)

    def test_manifest_deleting_required_fields(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas/manifest.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required_fields = schema["required"]

        for field in required_fields:
            with self.subTest(field=field):
                sample = deepcopy(self.ep)
                del sample["manifest"][field]

                problems = verify_episode(sample)
                self.assertTrue(
                    any(field in p for p in problems),
                    f"Expected problem naming field {field!r}, got: {problems}"
                )

                code, out = _run_cli(sample)
                self.assertEqual(code, 1, f"Expected CLI exit 1 for missing {field!r}, got {code}")
                self.assertIn(field, out, f"Expected CLI output to name field {field!r}, got: {out}")
                self.assertNotIn("Traceback (most recent call last)", out)

    def test_manifest_schema_version_invalid_values(self):
        for bad_val in ("", 3):
            with self.subTest(bad_val=bad_val):
                sample = deepcopy(self.ep)
                sample["manifest"]["schema_version"] = bad_val

                problems = verify_episode(sample)
                self.assertTrue(
                    any("schema_version" in p for p in problems),
                    f"Expected problem naming 'schema_version' for value {bad_val!r}, got: {problems}"
                )

                code, out = _run_cli(sample)
                self.assertEqual(code, 1, f"Expected CLI exit 1 for schema_version={bad_val!r}, got {code}")
                self.assertIn("schema_version", out)
                self.assertNotIn("Traceback (most recent call last)", out)

    def test_manifest_string_fields(self):
        # generator_version: optional, but if present must be a non-blank string
        sample = deepcopy(self.ep)
        del sample["manifest"]["generator_version"]
        self.assertEqual(verify_episode(sample), [])
        code, _ = _run_cli(sample)
        self.assertEqual(code, 0)

        for bad_val in ("", 42):
            sample = deepcopy(self.ep)
            sample["manifest"]["generator_version"] = bad_val
            problems = verify_episode(sample)
            self.assertTrue(any("manifest.generator_version" in p for p in problems))
            code, out = _run_cli(sample)
            self.assertEqual(code, 1)
            self.assertIn("generator_version", out)

        # episode_id must be a non-blank string
        for bad_val in ("", 123):
            sample = deepcopy(self.ep)
            sample["manifest"]["episode_id"] = bad_val
            problems = verify_episode(sample)
            self.assertTrue(any("manifest.episode_id" in p for p in problems))

    # Task 3: regression test only (the fix already exists)

    def test_ledger_malformed_timestamp_diagnostics(self):
        sample = deepcopy(self.ep)
        row_id = sample["tables"]["ledger"][0]["row_id"]
        sample["tables"]["ledger"][0]["timestamp"] = "not-a-date"

        problems = verify_episode(sample)
        self.assertTrue(
            any(row_id in p and "timestamp" in p for p in problems),
            f"Expected problem with row_id {row_id!r} and 'timestamp', got: {problems}"
        )

        code, out = _run_cli(sample)
        self.assertEqual(code, 1)
        self.assertIn(row_id, out)
        self.assertNotIn("Traceback (most recent call last)", out)


if __name__ == "__main__":
    unittest.main()
