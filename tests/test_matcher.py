"""Unit tests for auditenv.matcher (CONTRACT §5, §6) on small hand-built truth."""

import copy
import json
import unittest

from auditenv.matcher import grade, match, public_ids, public_summary, tolerance_of

EP = "ep_x"
# every id the hand-built issues and findings below cite as evidence exists in the (imagined) public tables
KNOWN = {"D-1", "D-2", "D-3", "D-4", "D-9", "L-1", "L-2", "L-3", "L-4", "L-9", "L-10", "L-99", "X-1"}

DUP = {"issue_id": "ISS-1", "type": "duplicate_invoice", "affected_ids": ["INV-1", "INV-2"],
       "expected_amount_minor": 5000, "currency": "USD",
       "evidence_sets": [["D-1", "D-2"], ["L-1", "L-2"]]}
FX = {"issue_id": "ISS-2", "type": "fx_error", "affected_ids": ["INV-3"],
      "expected_amount_minor": 1234567, "currency": "USD", "evidence_sets": [["D-3", "L-3"]]}
CUT = {"issue_id": "ISS-3", "type": "period_cutoff", "affected_ids": ["INV-4"],
       "expected_amount_minor": 500, "currency": "USD", "evidence_sets": [["D-4", "L-4"]]}


def truth(*issues):
    return {"episode_id": EP, "issues": [copy.deepcopy(i) for i in issues]}


def finding(issue, **over):
    f = {"type": issue["type"], "affected_ids": list(issue["affected_ids"]),
         "claimed_amount_minor": issue["expected_amount_minor"], "currency": issue["currency"],
         "evidence_ids": list(issue["evidence_sets"][0]), "explanation": "test"}
    f.update(over)
    return f


def sub(*findings, episode_id=EP):
    return {"episode_id": episode_id, "findings": list(findings)}


class MatcherTests(unittest.TestCase):
    def g(self, t, s, steps=0, tolerance=0):
        return grade(t, s, EP, steps, KNOWN, tolerance)

    # ---------------------------------------------------------------- TP / FP basics
    def test_exact_tp(self):
        r = self.g(truth(DUP), sub(finding(DUP)))
        self.assertTrue(r["valid"])
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (1, 0, 0))
        self.assertEqual(r["f1"], 1.0)
        self.assertEqual(r["reward"], 1.0)
        self.assertEqual(r["labels"], [{"finding": 0, "tp": True, "issue_id": "ISS-1"}])

    def test_affected_ids_order_and_duplicates_normalised(self):
        f = finding(DUP, affected_ids=["INV-2", "INV-1", "INV-1"])
        r = self.g(truth(DUP), sub(f))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (1, 0, 0))

    def test_affected_ids_whitespace_is_significant(self):
        f = finding(DUP, affected_ids=[" INV-2 ", "INV-1", "INV-1\t"])
        r = self.g(truth(DUP), sub(f))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 1))

    def test_evidence_ids_whitespace_is_significant(self):
        f = finding(DUP, evidence_ids=[" D-2", "D-1 "])
        r = self.g(truth(DUP), sub(f))
        self.assertEqual(r["tp"], 0)
        self.assertEqual(r["labels"][0]["reason"], "unknown_evidence")

    def test_wrong_affected_ids_is_fp(self):
        r = self.g(truth(DUP), sub(finding(DUP, affected_ids=["INV-1"])))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 1))

    def test_wrong_type_fp_and_fn(self):
        r = self.g(truth(DUP), sub(finding(DUP, type="fx_error")))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 1))
        self.assertEqual(r["labels"][0]["reason"], "wrong_type")
        self.assertEqual(r["missed"], [{"issue_id": "ISS-1", "type": "duplicate_invoice"}])

    def test_wrong_currency_fp(self):
        r = self.g(truth(DUP), sub(finding(DUP, currency="EUR")))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 1))
        self.assertEqual(r["labels"][0]["reason"], "wrong_currency")

    # ---------------------------------------------------------------- amount tolerance
    def test_tolerance_of_policy(self):
        self.assertEqual(tolerance_of({"findings": {}}), 0)
        self.assertEqual(tolerance_of({"findings": {"tolerance_minor": 0}}), 0)
        self.assertEqual(tolerance_of({"findings": {"tolerance_minor": 1234}}), 1234)
        for bad in (True, -1, 1.0, "1", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tolerance_of({"findings": {"tolerance_minor": bad}})

    def test_amount_published_tolerance(self):
        exp = FX["expected_amount_minor"]
        for claimed, tp in ((exp + 1234, 1), (exp - 1234, 1), (exp + 1235, 0), (exp - 1235, 0)):
            with self.subTest(claimed=claimed):
                r = self.g(truth(FX), sub(finding(FX, claimed_amount_minor=claimed)), tolerance=1234)
                self.assertEqual((r["tp"], r["fp"]), (tp, 1 - tp))
                if not tp:
                    self.assertEqual(r["labels"][0]["reason"], "wrong_amount")

    def test_amount_exact_by_default(self):
        for claimed, tp in ((500, 1), (501, 0), (499, 0), (502, 0)):
            with self.subTest(claimed=claimed):
                r = self.g(truth(CUT), sub(finding(CUT, claimed_amount_minor=claimed)))
                self.assertEqual(r["tp"], tp)

    # ---------------------------------------------------------------- evidence
    def test_evidence_superset_tp(self):
        f = finding(DUP, evidence_ids=["D-1", "D-2", "L-99", "X-1"])
        self.assertEqual(self.g(truth(DUP), sub(f))["tp"], 1)

    def test_partial_evidence_fp(self):
        r = self.g(truth(DUP), sub(finding(DUP, evidence_ids=["D-1", "L-2"])))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 1))
        self.assertEqual(r["labels"][0]["reason"], "wrong_evidence")

    def test_empty_evidence_fp(self):
        self.assertEqual(self.g(truth(DUP), sub(finding(DUP, evidence_ids=[])))["tp"], 0)

    def test_alternative_evidence_set_accepted(self):
        f = finding(DUP, evidence_ids=["L-2", "L-1"])
        self.assertEqual(self.g(truth(DUP), sub(f))["tp"], 1)

    # ---------------------------------------------------------------- one-to-one
    def test_duplicate_finding_is_fp(self):
        r = self.g(truth(DUP), sub(finding(DUP), finding(DUP, evidence_ids=["L-1", "L-2"])))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (1, 1, 0))
        self.assertTrue(r["labels"][0]["tp"])
        self.assertEqual(r["labels"][1], {"finding": 1, "tp": False, "reason": "duplicate"})
        self.assertLess(r["reward"], 1.0)

    def test_maximum_matching_independent_of_submission_order(self):
        # Two truth issues with the same fields, differing only in evidence.
        x = {"issue_id": "ISS-X", "type": "fx_error", "affected_ids": ["PAY-1"],
             "expected_amount_minor": 100, "currency": "USD", "evidence_sets": [["D-9", "L-9"]]}
        y = dict(x, issue_id="ISS-Y", evidence_sets=[["D-9", "L-10"]])
        both = finding(x, evidence_ids=["D-9", "L-9", "L-10"])  # satisfies X and Y
        only_x = finding(x, evidence_ids=["D-9", "L-9"])        # satisfies only X
        # "both" first: a greedy first fit would give it X and leave Y unmatched; the maximum matching gets both.
        r = match(truth(x, y)["issues"], [both, only_x], KNOWN)
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (2, 0, 0))
        self.assertEqual([lab["issue_id"] for lab in r["labels"]], ["ISS-Y", "ISS-X"])
        self.assertEqual(r["missed"], [])
        # Reverse submission order: same counts, the smallest (issue_id, finding index) pairs win.
        r = match(truth(x, y)["issues"], [only_x, both], KNOWN)
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (2, 0, 0))
        self.assertEqual([lab["issue_id"] for lab in r["labels"]], ["ISS-X", "ISS-Y"])

    def test_public_ids(self):
        tables = {"ledger": [{"row_id": "R1", "invoice_id": "INV-REF"}],
                  "invoices": [{"invoice_id": "I1", "doc_id": "D1"}], "payments": [{"payment_id": "P1", "doc_id": "D2"}], "fx": [{"fx_id": "2026-01-01:USD:KZT"}]}
        self.assertEqual(public_ids(tables), {"R1", "I1", "D1", "P1", "D2", "2026-01-01:USD:KZT"})

    def test_mixed_counts(self):
        s = sub(finding(DUP), finding(CUT, claimed_amount_minor=900), finding(FX))
        r = self.g(truth(DUP, FX, CUT), s)
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (2, 1, 1))
        self.assertAlmostEqual(r["precision"], 2 / 3)
        self.assertAlmostEqual(r["recall"], 2 / 3)
        self.assertAlmostEqual(r["f1"], 4 / 6)

    # ---------------------------------------------------------------- empty cases
    def test_empty_truth_empty_findings(self):
        r = self.g(truth(), sub())
        self.assertTrue(r["valid"])
        self.assertEqual(r["f1"], 1.0)
        self.assertEqual(r["reward"], 1.0)

    def test_empty_truth_with_findings(self):
        r = self.g(truth(), sub(finding(DUP)))
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 1, 0))
        self.assertEqual(r["f1"], 0.0)
        self.assertEqual(r["reward"], -1.0)

    def test_dirty_truth_empty_findings(self):
        r = self.g(truth(DUP, FX), sub())
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (0, 0, 2))
        self.assertEqual(r["f1"], 0.0)
        self.assertEqual(r["reward"], -1.0)

    # ---------------------------------------------------------------- invalid structure
    def assertInvalid(self, submission):
        r = self.g(truth(DUP), submission, steps=3)
        self.assertFalse(r["valid"])
        self.assertEqual(r["reward"], -1.0)
        self.assertIsInstance(r["error"], str)
        self.assertLessEqual(len(r["error"]), 200)
        self.assertEqual((r["tp"], r["fn"]), (0, 1))

    def test_invalid_wrong_episode_id(self):
        self.assertInvalid(sub(finding(DUP), episode_id="ep_other"))

    def test_invalid_31_findings(self):
        self.assertInvalid(sub(*[finding(DUP) for _ in range(31)]))

    def test_30_findings_valid(self):
        self.assertTrue(self.g(truth(DUP), sub(*[finding(DUP) for _ in range(30)]))["valid"])

    def test_invalid_float_amount(self):
        self.assertInvalid(sub(finding(DUP, claimed_amount_minor=5000.0)))

    def test_invalid_bool_amount(self):
        self.assertInvalid(sub(finding(DUP, claimed_amount_minor=True)))

    def test_invalid_not_a_dict(self):
        self.assertInvalid(None)
        self.assertInvalid([finding(DUP)])

    def test_invalid_long_episode_id_error_is_bounded(self):
        r = self.g(truth(DUP), sub(episode_id="z" * 5000))
        self.assertFalse(r["valid"])
        self.assertLessEqual(len(r["error"]), 200)

    # ---------------------------------------------------------------- reward formula
    def test_reward_formula(self):
        r = self.g(truth(DUP, FX), sub(finding(DUP)), steps=10)
        self.assertAlmostEqual(r["f1"], 2 / 3)
        self.assertAlmostEqual(r["reward"], 2 * (2 / 3) - 1 - 0.002 * 10, places=6)
        self.assertEqual(r["inspection_steps"], 10)

    def test_reward_step_cost_small(self):
        r0 = self.g(truth(DUP), sub(finding(DUP)), steps=0)["reward"]
        r20 = self.g(truth(DUP), sub(finding(DUP)), steps=20)["reward"]
        self.assertEqual(r0, 1.0)
        self.assertAlmostEqual(r20, 0.96, places=6)

    def test_reward_clipped_at_minus_one(self):
        r = self.g(truth(DUP), sub(), steps=50)
        self.assertEqual(r["reward"], -1.0)

    # ---------------------------------------------------------------- public summary
    def test_public_summary_has_no_truth_content(self):
        s = sub(finding(DUP), finding(FX, claimed_amount_minor=1), finding(DUP))
        r = self.g(truth(DUP, FX, CUT), s, steps=7)
        ps = public_summary(r)
        self.assertEqual(set(ps), {"valid", "tp", "fp", "fn", "precision", "recall", "f1", "reward",
                                   "inspection_steps"})
        text = json.dumps(ps)
        for needle in ("ISS-", "issue_id", "evidence", "labels", "missed", "D-", "L-", "INV-",
                       "period_cutoff", "duplicate"):
            self.assertNotIn(needle, text)
        values = set(ps.values())
        for issue in (DUP, FX, CUT):
            self.assertNotIn(issue["expected_amount_minor"], values)

    def test_public_summary_of_invalid_result(self):
        r = self.g(truth(DUP), sub(episode_id="bad"))
        ps = public_summary(r)
        self.assertFalse(ps["valid"])
        self.assertNotIn("ISS-", json.dumps(ps))


if __name__ == "__main__":
    unittest.main()
