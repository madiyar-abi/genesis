from decimal import localcontext
import unittest

from auditenv.calculator import CalculatorError, evaluate


class CalculatorTests(unittest.TestCase):
    def test_valid_arithmetic(self):
        cases = [
            ("3", "3"),
            ("  1 + 2  ", "3"),
            ("(1.10+2.205)*3", "9.915"),
            ("1/2", "0.5"),
            ("-12.3450", "-12.345"),
            ("-0.00", "0"),
            ("1 + 2 * 3", "7"),
            ("+(--42)", "42"),
            (".25 + 1.", "1.25"),
            ("(1 +\n 2)", "3"),
            ("0.1234567890123456789012345678 + 0", "0.1234567890123456789012345678"),
            (str(10**30), str(10**30)),
            ("1" + " " * 199, "1"),
        ]
        for expression, expected in cases:
            with self.subTest(expression=expression):
                self.assertEqual(evaluate(expression), expected)

    def test_decimal_context_is_independent_of_caller(self):
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(evaluate("1/3"), "0." + "3" * 28)
            self.assertEqual(context.prec, 2)

    def test_rejects_invalid_expressions(self):
        cases = [
            "__import__('os')", "2**10", "1/0", "0/0", "a+1", "1e5",
            "1E-5", "10%3", "10//3", "'12'", "1 .real", "(1, 2)", "...",
            "1_000", "1 # comment", "1++", "", "1" + " " * 200,
            str(10**30 + 1), str(-(10**30 + 1)), None,
        ]
        for expression in cases:
            with self.subTest(expression=expression):
                with self.assertRaises(CalculatorError) as caught:
                    evaluate(expression)
                self.assertLessEqual(len(str(caught.exception)), 100)

    def test_error_does_not_echo_request(self):
        expression = "private_input" * 10
        with self.assertRaises(CalculatorError) as caught:
            evaluate(expression)
        self.assertNotIn("private_input", str(caught.exception))
