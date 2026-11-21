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
        # generator_version (required, CONTRACT §2) must be a non-blank string
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


class TestReviewTampers(unittest.TestCase):
    """Single-record tampers from the adversarial review of the audit fixes: each must be reported as a problem
    (never raised) by the API, and rejected by the CLI on an exported copy."""

    def setUp(self):
        self.ep = generate(2000, {"errors": {}})

    def assertRejected(self, edit, words):
        sample = deepcopy(self.ep)
        edit(sample)
        problems = verify_episode(sample)
        self.assertTrue(any(words in p for p in problems), problems)
        code, out = _run_cli(sample)
        self.assertEqual(code, 1, out)
        self.assertIn(words, out)

    def test_manifest_schema_beyond_required_fields(self):
        def put(path, value):
            def edit(ep):
                node = ep["manifest"]
                for key in path[:-1]:
                    node = node[key]
                node[path[-1]] = value
            return edit
        cases = [(("seed",), 2000, "manifest.seed: unexpected"),  # grader data must not ride in the manifest
                 (("counts", "expenses"), 3, "manifest.counts.expenses: unexpected"),
                 (("counts", "ledger"), 355.0, "manifest.counts.ledger: expected integer"),
                 (("counts",), [1, 2], "manifest.counts: expected object"),
                 (("timezone",), "+5:00", "manifest.timezone: invalid string"),
                 (("timezone",), "Z", "manifest.timezone: invalid string"),
                 (("period_start",), "2025-13-01", "manifest.period_start: invalid date"),
                 (("period_start",), "20250501", "manifest.period_start: invalid date"),
                 (("period_start",), 20250501, "manifest.period_start: expected string"),
                 (("base_currency",), "usd", "manifest.base_currency: invalid string"),
                 (("rounding",), "ROUND_DOWN", "manifest.rounding: must be"),
                 (("amount_exponents", "usd"), 2, "manifest.amount_exponents key 'usd'"),
                 (("amount_exponents", "USD"), -1, "manifest.amount_exponents.USD: below minimum")]
        for path, value, words in cases:
            with self.subTest(path=path, value=value):
                self.assertRejected(put(path, value), words)
        self.assertRejected(lambda ep: ep["manifest"]["counts"].pop("ledger"), "manifest.counts.ledger: required")

    def test_fx_rate_spellings_a_reader_may_not_parse(self):
        for fx_id in ("2025-03-28:GBP:USD", "2025-03-02:GBP:USD"):  # used by an invoice, and unused
            for rate in ("1.2_9169", " 1.29169", "129169e-5", "+1.29169", "１.２９", "1e30", "1" + "0" * 30):
                with self.subTest(fx_id=fx_id, rate=rate):
                    def edit(ep):
                        next(r for r in ep["tables"]["fx"] if r["fx_id"] == fx_id)["rate"] = rate
                    self.assertRejected(edit, f"fx rate {fx_id}")

    def test_invoice_ref_without_a_string_invoice_id(self):
        pid = next(p["payment_id"] for p in self.ep["tables"]["payments"] if p["invoice_refs"])
        for name, change in (("missing", lambda ref: ref.pop("invoice_id")),
                             ("list", lambda ref: ref.update(invoice_id=["x"])),
                             ("int", lambda ref: ref.update(invoice_id=7))):
            with self.subTest(name):
                def edit(ep):
                    change(next(p for p in ep["tables"]["payments"] if p["payment_id"] == pid)["invoice_refs"][0])
                self.assertRejected(edit, f"payment {pid}: invoice_refs invoice_id must be a string")

    def test_blank_record_ids(self):
        def blank_row(ep):
            ep["tables"]["ledger"][0]["row_id"] = ""

        def blank_doc(ep):  # invoice doc_ids are checked by _invoice_error already
            ep["tables"]["payments"][0]["doc_id"] = " "
        for edit in (blank_row, blank_doc):
            with self.subTest(edit.__name__):
                self.assertRejected(edit, "row_id/doc_id must be a non-empty string")


if __name__ == "__main__":
    unittest.main()
