"""Optional reward for evaluating the materiality of audit findings."""

from fractions import Fraction

from .metrics import terminal_reward


def experimental_reward(result: dict, truth: dict, findings: list) -> float:
    """Score findings by amount so material misstatements matter more.

    Reuse the grader's one-to-one matches. Matched and missed issues use their
    expected amounts, and false positives use their claimed amounts, at least the mean expected amount. Pass the
    findings list in original submission order so the grader's labels index it.
    The score can be reported alongside the shared reward.
    """
    if not result["valid"]:
        return -1.0

    amounts = {
        issue["issue_id"]: issue["expected_amount_minor"]
        for issue in truth["issues"]
    }
    tp = sum(amounts[label["issue_id"]] for label in result["labels"] if label["tp"])
    fn = sum(amounts[missed["issue_id"]] for missed in result["missed"])
    # A false positive weighs at least the mean expected amount: a zero or tiny claim is not a free accusation,
    # and with every issue found the weighted F1 never exceeds the shared count-based F1. Exact arithmetic:
    # a float floor next to a huge int claim would raise OverflowError instead of scoring the answer.
    floor = Fraction(sum(amounts.values()), len(amounts)) if amounts else 0
    fp = sum(
        max(findings[label["finding"]]["claimed_amount_minor"], floor)
        for label in result["labels"] if not label["tp"]
    )
    denominator = 2 * tp + fn + fp
    f1 = float(Fraction(2 * tp, denominator)) if denominator else float(not amounts and not findings)
    return terminal_reward(f1, result["inspection_steps"])
