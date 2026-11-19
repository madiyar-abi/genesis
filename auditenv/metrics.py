"""Compute audit finding metrics and the shared terminal reward."""


def prf1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Return precision, recall, and F1 for the given finding counts."""
    predicted = tp + fp
    actual = tp + fn
    precision = tp / predicted if predicted else 0.0
    recall = tp / actual if actual else 0.0
    f1 = 2 * tp / (predicted + actual) if predicted or actual else 1.0
    return precision, recall, f1


def terminal_reward(f1: float, inspection_steps: int) -> float:
    """Subtract inspection cost, clip the reward, and round to six places."""
    reward = 2 * f1 - 1 - 0.002 * inspection_steps
    return round(max(-1.0, min(1.0, reward)), 6)
