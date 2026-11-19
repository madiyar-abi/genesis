"""Evaluate bounded decimal arithmetic without executing Python code."""

import ast
from decimal import Context, Decimal, DecimalException, DivisionByZero, localcontext
import operator
import re


class CalculatorError(ValueError):
    """The calculator could not evaluate the expression."""


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_ALLOWED_CHARACTERS = re.compile(r"[0-9. +*/()\t\r\n-]+")
_MAX_RESULT = Decimal("1e30")


def _evaluate_node(node: ast.expr, source: str) -> Decimal:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        # Read the literal as written to avoid a round trip through binary float.
        literal = ast.get_source_segment(source, node)
        return Decimal(literal)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](
            _evaluate_node(node.left, source), _evaluate_node(node.right, source)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _evaluate_node(node.operand, source)
        return operand.copy_negate() if isinstance(node.op, ast.USub) else operand
    raise CalculatorError("Only decimal arithmetic is allowed")


def evaluate(expression: str) -> str:
    """Return a plain decimal string or raise CalculatorError."""
    if not isinstance(expression, str) or len(expression) > 200:
        raise CalculatorError("Expected an expression of at most 200 characters")
    source = expression.strip()
    if not _ALLOWED_CHARACTERS.fullmatch(source):
        raise CalculatorError("Only decimal arithmetic is allowed")

    try:
        tree = ast.parse(source, mode="eval")
        with localcontext(Context(prec=28)):
            value = _evaluate_node(tree.body, source)
    except DivisionByZero:
        raise CalculatorError("Division by zero") from None
    except (SyntaxError, DecimalException):
        raise CalculatorError("Invalid arithmetic expression") from None

    if value.copy_abs() > _MAX_RESULT:
        raise CalculatorError("Result magnitude exceeds 1e30")
    if value.is_zero():
        return "0"
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result
