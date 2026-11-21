"""The jury's published matcher and reward checks (genesis-exe.com/fintech-checks.html): Block 3 rows 1-20 and the
open examples M01-M12, built exactly as described there, plus the rule-8 cases ("a structurally valid finding with a
wrong type, ids, currency, amount or evidence is a false positive, not a structural error").

Block 3 fixture: one issue A of type T on record R1, 10000 KZT, evidence {D1, D2}, tolerance 0, 10 inspection steps.
M fixture: A on {R1, R2}, otherwise the same; D3 is a public extra document, U is not in the public data.
"""

from fractions import Fraction
import unittest

from auditenv.matcher import grade

EP = "ep_judge"
T, T2 = "duplicate_invoice", "fx_error"
KNOWN = {"R1", "R2", "R3", "R4", "R5", "D1", "D2", "D3"}
TYPES = ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")


def issue(issue_id="A", type_=T, affected=("R1",), amount=10000, currency="KZT", evidence=(("D1", "D2"),)):
    return {"issue_id": issue_id, "type": type_, "affected_ids": list(affected), "expected_amount_minor": amount,
            "currency": currency, "evidence_sets": [list(s) for s in evidence]}


def finding(type_=T, affected=("R1",), amount=10000, currency="KZT", evidence=("D1", "D2"), **extra):
    return {"type": type_, "affected_ids": list(affected), "claimed_amount_minor": amount, "currency": currency,
            "evidence_ids": list(evidence), **extra}


A = issue()
B = issue("B", T2, ("R2",), 20000, "KZT", (("D3",),))
MA = issue(affected=("R1", "R2"))
MF = dict(affected=("R1", "R2"))


class JudgeCase(unittest.TestCase):
    def run_grade(self, issues, findings, steps=10, tolerance=0, submission=None):
        sub = {"episode_id": EP, "findings": findings} if submission is None else submission
        return grade({"issues": issues}, sub, EP, steps, KNOWN, tolerance)

    def assertScore(self, r, tp, fp, fn, p, rec, f1, reward):
        self.assertTrue(r["valid"], r["error"])
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (tp, fp, fn))
        for key, want in (("precision", p), ("recall", rec), ("f1", f1), ("reward", reward)):
            self.assertLessEqual(abs(r[key] - float(want)), 1e-9, (key, r[key], want))

    def assertMiss(self, r):
        """One finding against one issue that does not match: TP0 FP1 FN1, F1 0, reward -1."""
        self.assertScore(r, 0, 1, 1, 0, 0, 0, -1)

    def assertStructural(self, r):
        self.assertFalse(r["valid"])
        self.assertIsInstance(r["error"], str)
        self.assertTrue(r["error"])
        self.assertEqual(r["reward"], -1.0)


class Block3(JudgeCase):
    def test_b3_01_one_correct_finding(self):
        self.assertScore(self.run_grade([A], [finding()]), 1, 0, 0, 1, 1, 1, Fraction(98, 100))

    def test_b3_02_issue_and_empty_findings(self):
        self.assertScore(self.run_grade([A], []), 0, 0, 1, 0, 0, 0, -1)

    def test_b3_03_empty_truth_empty_findings(self):
        self.assertScore(self.run_grade([], []), 0, 0, 0, 0, 0, 1, Fraction(98, 100))

    def test_b3_04_empty_truth_one_false_finding(self):
        self.assertScore(self.run_grade([], [finding()]), 0, 1, 0, 0, 0, 0, -1)

    def test_b3_05_two_identical_correct_findings(self):
        self.assertScore(self.run_grade([A], [finding(), finding()]), 1, 1, 0,
                         Fraction(1, 2), 1, Fraction(2, 3), Fraction(47, 150))

    def test_b3_06_wrong_type(self):
        self.assertMiss(self.run_grade([A], [finding(type_=T2)]))

    def test_b3_07_other_existing_unaffected_record(self):
        for affected in (("R3",), ("R1", "R3")):
            with self.subTest(affected=affected):
                self.assertMiss(self.run_grade([A], [finding(affected=affected)]))

    def test_b3_08_amount_off_by_one_at_zero_tolerance(self):
        self.assertMiss(self.run_grade([A], [finding(amount=10001)]))

    def test_b3_09_other_currency(self):
        self.assertMiss(self.run_grade([A], [finding(currency="USD")]))

    def test_b3_10_only_d1(self):
        self.assertMiss(self.run_grade([A], [finding(evidence=("D1",))]))

    def test_b3_11_unknown_evidence_instead_of_d2(self):
        self.assertMiss(self.run_grade([A], [finding(evidence=("D1", "U"))]))

    def test_b3_12_five_records_times_four_types(self):
        findings = [finding(type_=t, affected=(r,)) for r in ("R1", "R2", "R3", "R4", "R5") for t in TYPES]
        self.assertEqual(len(findings), 20)
        self.assertScore(self.run_grade([A], findings), 1, 19, 0,
                         Fraction(1, 20), 1, Fraction(2, 21), Fraction(-871, 1050))

    def test_b3_13_two_issues_only_a_found(self):
        self.assertScore(self.run_grade([A, B], [finding()]), 1, 0, 1, 1, Fraction(1, 2), Fraction(2, 3),
                         Fraction(47, 150))

    def test_b3_14_two_issues_a_found_plus_false(self):
        self.assertScore(self.run_grade([A, B], [finding(), finding(type_=T2)]), 1, 1, 1,
                         Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(-2, 100))

    def test_b3_15_zero_inspection_steps(self):
        self.assertScore(self.run_grade([A], [finding()], steps=0), 1, 0, 0, 1, 1, 1, 1)

    def test_b3_16_fifty_inspection_steps(self):
        self.assertScore(self.run_grade([A], [finding()], steps=50), 1, 0, 0, 1, 1, 1, Fraction(90, 100))

    def test_b3_17_hundred_inspection_steps(self):
        self.assertScore(self.run_grade([A], [finding()], steps=100), 1, 0, 0, 1, 1, 1, Fraction(80, 100))

    def test_b3_18_thirty_one_findings(self):
        self.assertStructural(self.run_grade([A], [finding()] * 31))

    def test_b3_19_eleven_distinct_evidence_ids(self):
        self.assertStructural(self.run_grade([A], [finding(evidence=[f"D{i}" for i in range(1, 12)])]))

    def test_b3_20_explanation_1001_ascii(self):
        self.assertStructural(self.run_grade([A], [finding(explanation="x" * 1001)]))


class OpenExamples(JudgeCase):
    def test_m01_affected_reordered_and_repeated(self):
        self.assertScore(self.run_grade([MA], [finding(affected=("R2", "R1", "R1"))]), 1, 0, 0, 1, 1, 1,
                         Fraction(98, 100))

    def test_m02_extra_existing_unaffected_record(self):
        self.assertMiss(self.run_grade([MA], [finding(affected=("R1", "R2", "R3"))]))

    def test_m03_evidence_reordered_with_public_extra(self):
        self.assertScore(self.run_grade([MA], [finding(**MF, evidence=("D2", "D1", "D3"))]), 1, 0, 0, 1, 1, 1,
                         Fraction(98, 100))

    def test_m04_evidence_with_unknown_id(self):
        self.assertMiss(self.run_grade([MA], [finding(**MF, evidence=("D1", "D2", "U"))]))

    def test_m05_eleven_evidence_ids_before_dedupe(self):
        self.assertStructural(self.run_grade([MA], [finding(**MF, evidence=["D1"] * 10 + ["D2"])]))

    def test_m06_currency_case_or_whitespace(self):
        for cur in ("kzt", "Kzt", " KZT", "KZT ", "KZT\n"):
            with self.subTest(currency=cur):
                self.assertMiss(self.run_grade([MA], [finding(**MF, currency=cur)]))

    def test_m07_off_by_one_at_zero_tolerance(self):
        self.assertMiss(self.run_grade([MA], [finding(**MF, amount=10001)]))

    def test_m08_published_tolerance_one(self):
        for amount in (9999, 10000, 10001):
            with self.subTest(amount=amount):
                self.assertScore(self.run_grade([MA], [finding(**MF, amount=amount)], tolerance=1), 1, 0, 0, 1, 1, 1,
                                 Fraction(98, 100))
        for amount in (9998, 10002):
            with self.subTest(amount=amount):
                self.assertMiss(self.run_grade([MA], [finding(**MF, amount=amount)], tolerance=1))

    def test_m09_amount_string_bool_or_float(self):
        for amount in ("10000", True, False, 10000.0, None):
            with self.subTest(amount=amount):
                self.assertStructural(self.run_grade([MA], [finding(**MF, amount=amount)]))

    def test_m10_maximum_matching_not_greedy(self):
        a = issue("A", affected=("R1", "R2"), evidence=(("D1", "D2"),))
        b = issue("B", affected=("R1", "R2"), evidence=(("D3",),))
        f0 = finding(**MF, evidence=("D1", "D2", "D3"))  # fits A and B
        f1 = finding(**MF, evidence=("D1", "D2"))  # fits A only
        r = self.run_grade([a, b], [f0, f1])
        self.assertScore(r, 2, 0, 0, 1, 1, 1, Fraction(98, 100))
        self.assertEqual({lab["finding"]: lab.get("issue_id") for lab in r["labels"]}, {0: "B", 1: "A"})

    def test_m11_both_fit_both_tie_break(self):
        a = issue("A", affected=("R1", "R2"), evidence=(("D1", "D2"),))
        b = issue("B", affected=("R1", "R2"), evidence=(("D3",),))
        both = finding(**MF, evidence=("D1", "D2", "D3"))
        for issues in ([a, b], [b, a]):  # truth order must not matter: issue ids sort by code point
            with self.subTest(order=[i["issue_id"] for i in issues]):
                r = self.run_grade(issues, [both, dict(both)])
                self.assertScore(r, 2, 0, 0, 1, 1, 1, Fraction(98, 100))
                self.assertEqual({lab["finding"]: lab.get("issue_id") for lab in r["labels"]}, {0: "A", 1: "B"})

    def test_m12_two_identical_correct(self):
        r = self.run_grade([MA], [finding(**MF), finding(**MF)])
        self.assertScore(r, 1, 1, 0, Fraction(1, 2), 1, Fraction(2, 3), Fraction(47, 150))
        self.assertEqual([lab["tp"] for lab in r["labels"]], [True, False])


class Rule8(JudgeCase):
    """Structurally valid but wrong values are false positives; only value type, missing field or a limit is
    structural."""

    def test_rule8_value_errors_are_false_positives(self):
        for name, f in (("unknown type", finding(type_="not_a_type")), ("empty type", finding(type_="")),
                        ("negative amount", finding(amount=-10000)), ("empty affected", finding(affected=())),
                        ("blank affected id", finding(affected=(" ",))), ("padded id", finding(affected=(" R1",))),
                        ("lowercase id", finding(affected=("r1",))), ("blank evidence", finding(evidence=("", "D1"))),
                        ("empty evidence", finding(evidence=())), ("long currency", finding(currency="KZTX"))):
            with self.subTest(name):
                self.assertMiss(self.run_grade([A], [f]))

    def test_rule8_structural_errors(self):
        good = finding()
        cases = {"missing type": {k: v for k, v in good.items() if k != "type"},
                 "missing evidence": {k: v for k, v in good.items() if k != "evidence_ids"},
                 "type not str": {**good, "type": 1}, "affected not list": {**good, "affected_ids": "R1"},
                 "affected item not str": {**good, "affected_ids": [1]}, "currency not str": {**good, "currency": 398},
                 "evidence item not str": {**good, "evidence_ids": ["D1", None]},
                 "explanation not str": {**good, "explanation": 5}, "unknown key": {**good, "note": "x"}}
        for name, f in cases.items():
            with self.subTest(name):
                self.assertStructural(self.run_grade([A], [f]))

    def test_rule8_explanation_counts_code_points(self):
        self.assertScore(self.run_grade([A], [finding(explanation="ж" * 1000)]), 1, 0, 0, 1, 1, 1, Fraction(98, 100))
        self.assertStructural(self.run_grade([A], [finding(explanation="ж" * 1001)]))

    def test_rule8_many_affected_ids_are_not_structural(self):
        self.assertMiss(self.run_grade([A], [finding(affected=[f"R{i}" for i in range(1, 12)])]))


if __name__ == "__main__":
    unittest.main()
