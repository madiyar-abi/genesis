"""Tests for auditenv.schema — findings validation and normalisation."""

import unittest

from auditenv.schema import (
    ISSUE_TYPES,
    MAX_AFFECTED,
    MAX_EVIDENCE,
    MAX_EXPLANATION,
    MAX_FINDINGS,
    normalize_finding,
    validate_findings,
)


def _good_finding(**overrides):
    """Return a valid finding dict, optionally overridden."""
    base = {
        "type": "fx_error",
        "affected_ids": ["INV-1"],
        "claimed_amount_minor": 1234,
        "currency": "USD",
        "evidence_ids": ["D-1", "L-7"],
        "explanation": "short reason",
    }
    base.update(overrides)
    return base


def _wrap(findings, episode_id="ep_test"):
    """Wrap a list of findings into a submission object."""
    return {"episode_id": episode_id, "findings": findings}


class TestValidateFindings(unittest.TestCase):
    """≥ 15 cases per acceptance criterion."""

    # --- valid cases ---

    def test_valid_minimal(self):
        obj = _wrap([_good_finding()])
        self.assertIsNone(validate_findings(obj, "ep_test"))

    def test_valid_no_findings(self):
        """Empty findings list is valid."""
        obj = _wrap([])
        self.assertIsNone(validate_findings(obj, "ep_test"))

    def test_valid_all_types(self):
        for t in ISSUE_TYPES:
            obj = _wrap([_good_finding(type=t)])
            self.assertIsNone(validate_findings(obj, "ep_test"), msg=t)

    def test_valid_explanation_missing(self):
        """explanation is optional (defaults to '')."""
        f = _good_finding()
        del f["explanation"]
        obj = _wrap([f])
        self.assertIsNone(validate_findings(obj, "ep_test"))

    # --- wrong episode_id ---

    def test_wrong_episode_id(self):
        obj = _wrap([_good_finding()], episode_id="ep_wrong")
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("episode_id", err)

    def test_missing_episode_id(self):
        obj = {"findings": [_good_finding()]}
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- too many findings (31) ---

    def test_too_many_findings(self):
        obj = _wrap([_good_finding() for _ in range(MAX_FINDINGS + 1)])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("too many", err)

    # --- too many evidence_ids (11) ---

    def test_too_many_evidence(self):
        ids = [f"E-{i}" for i in range(MAX_EVIDENCE + 1)]
        obj = _wrap([_good_finding(evidence_ids=ids)])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("too many", err)

    # --- amount: bool ---

    def test_bool_amount(self):
        obj = _wrap([_good_finding(claimed_amount_minor=True)])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("int", err)

    # --- amount: negative ---

    def test_negative_amount(self):
        obj = _wrap([_good_finding(claimed_amount_minor=-5)])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn(">= 0", err)

    # --- amount: float ---

    def test_float_amount(self):
        obj = _wrap([_good_finding(claimed_amount_minor=12.5)])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("int", err)

    # --- lowercase currency ---

    def test_lowercase_currency(self):
        obj = _wrap([_good_finding(currency="usd")])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("uppercase", err)

    # --- unknown type ---

    def test_unknown_type(self):
        obj = _wrap([_good_finding(type="fraud")])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("unknown type", err)

    # --- non-dict submission ---

    def test_non_dict_submission(self):
        err = validate_findings("not a dict", "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("dict", err)

    # --- non-dict finding ---

    def test_non_dict_finding(self):
        obj = _wrap(["not a dict"])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("not a dict", err)

    # --- missing keys ---

    def test_missing_type(self):
        f = _good_finding()
        del f["type"]
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    def test_missing_affected_ids(self):
        f = _good_finding()
        del f["affected_ids"]
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    def test_missing_evidence_ids(self):
        f = _good_finding()
        del f["evidence_ids"]
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    def test_missing_currency(self):
        f = _good_finding()
        del f["currency"]
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    def test_missing_amount(self):
        f = _good_finding()
        del f["claimed_amount_minor"]
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- empty affected_ids ---

    def test_empty_affected_ids(self):
        obj = _wrap([_good_finding(affected_ids=[])])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("non-empty", err)

    # --- too many affected_ids ---

    def test_too_many_affected_ids(self):
        ids = [f"INV-{i}" for i in range(MAX_AFFECTED + 1)]
        obj = _wrap([_good_finding(affected_ids=ids)])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("too many", err)

    # --- extra unknown keys ---

    def test_extra_keys(self):
        f = _good_finding()
        f["unknown_key"] = 42
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("unknown keys", err)

    # --- explanation too long ---

    def test_explanation_too_long(self):
        f = _good_finding(explanation="x" * (MAX_EXPLANATION + 1))
        obj = _wrap([f])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("too long", err)

    # --- findings not a list ---

    def test_findings_not_list(self):
        obj = {"episode_id": "ep_test", "findings": "oops"}
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)
        self.assertIn("list", err)

    # --- affected_ids contains non-string ---

    def test_affected_ids_non_string(self):
        obj = _wrap([_good_finding(affected_ids=[123])])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- affected_ids contains empty string ---

    def test_affected_ids_empty_string(self):
        obj = _wrap([_good_finding(affected_ids=[""])])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- evidence_ids contains empty string ---

    def test_evidence_ids_empty_string(self):
        obj = _wrap([_good_finding(evidence_ids=[""])])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- currency wrong length ---

    def test_currency_two_letters(self):
        obj = _wrap([_good_finding(currency="US")])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- currency numeric ---

    def test_currency_numeric(self):
        obj = _wrap([_good_finding(currency="123")])
        err = validate_findings(obj, "ep_test")
        self.assertIsNotNone(err)

    # --- amount zero (valid) ---

    def test_zero_amount(self):
        obj = _wrap([_good_finding(claimed_amount_minor=0)])
        self.assertIsNone(validate_findings(obj, "ep_test"))

    # --- exactly at limits (edge cases) ---

    def test_exactly_30_findings(self):
        obj = _wrap([_good_finding() for _ in range(MAX_FINDINGS)])
        self.assertIsNone(validate_findings(obj, "ep_test"))

    def test_exactly_10_evidence(self):
        ids = [f"E-{i}" for i in range(MAX_EVIDENCE)]
        obj = _wrap([_good_finding(evidence_ids=ids)])
        self.assertIsNone(validate_findings(obj, "ep_test"))


class TestNormalizeFinding(unittest.TestCase):
    """Tests for normalize_finding."""

    def test_uppercase_currency(self):
        f = _good_finding(currency="usd")
        n = normalize_finding(f)
        self.assertEqual(n["currency"], "USD")

    def test_sort_affected_ids(self):
        f = _good_finding(affected_ids=["B", "A", "C"])
        n = normalize_finding(f)
        self.assertEqual(n["affected_ids"], ["A", "B", "C"])

    def test_dedupe_affected_ids(self):
        f = _good_finding(affected_ids=["A", "A", "B"])
        n = normalize_finding(f)
        self.assertEqual(n["affected_ids"], ["A", "B"])

    def test_strip_affected_ids(self):
        f = _good_finding(affected_ids=[" A ", "B "])
        n = normalize_finding(f)
        self.assertEqual(n["affected_ids"], ["A", "B"])

    def test_sort_dedupe_evidence_ids(self):
        f = _good_finding(evidence_ids=["Z", "A", "Z"])
        n = normalize_finding(f)
        self.assertEqual(n["evidence_ids"], ["A", "Z"])

    def test_strip_evidence_ids(self):
        f = _good_finding(evidence_ids=[" D-1 "])
        n = normalize_finding(f)
        self.assertEqual(n["evidence_ids"], ["D-1"])

    def test_default_explanation(self):
        f = _good_finding()
        del f["explanation"]
        n = normalize_finding(f)
        self.assertEqual(n["explanation"], "")

    def test_preserves_type(self):
        for t in ISSUE_TYPES:
            n = normalize_finding(_good_finding(type=t))
            self.assertEqual(n["type"], t)

    def test_preserves_amount(self):
        f = _good_finding(claimed_amount_minor=99999)
        n = normalize_finding(f)
        self.assertEqual(n["claimed_amount_minor"], 99999)


if __name__ == "__main__":
    unittest.main()
