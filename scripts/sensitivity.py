#!/usr/bin/env python3
"""Reward sensitivity: does the baseline ranking survive other step costs and amount tolerances?

Each policy plays each episode once with the real env (train mode); the submitted findings and the
inspection step count are then re-graded grader-side with `matcher.grade` under alternative
parameters. With the default parameters the re-grade must reproduce the env's reward exactly
(asserted for every episode). The shared reward code is not changed.

    uv run python scripts/sensitivity.py [--json /tmp/sensitivity.json]
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auditenv import matcher  # noqa: E402
from auditenv.env import AuditEnv  # noqa: E402
from auditenv.run import load_episodes, make_policy, run_episode  # noqa: E402

DEFAULT_COST = 0.002  # auditenv/metrics.py terminal_reward
STEP_COSTS = (0.001, DEFAULT_COST, 0.005)
TOLERANCES = {  # label -> tolerance(expected_minor) in minor units; "0.1 %" is the real matcher.tolerance
    "0 (exact)": lambda expected: 0,
    "0.1 %": matcher.tolerance,
    "1 %": lambda expected: max(1, expected // 100),
}
DEFAULT_TOL = "0.1 %"
SPLITS = [
    ("dev", "configs/dev.json", ("oracle", "reconcile", "naive_reconcile", "random", "flag_all")),
    ("hard", "configs/eval_hard.json",
     ("oracle", "reconcile_hard", "reconcile", "naive_reconcile", "random", "flag_all")),
]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _reward(cost: float):
    """metrics.terminal_reward with the per-step cost as a parameter (same formula, clip and rounding)."""
    def terminal_reward(f1: float, inspection_steps: int) -> float:
        reward = 2 * f1 - 1 - cost * inspection_steps
        return round(max(-1.0, min(1.0, reward)), 6)
    return terminal_reward


@contextlib.contextmanager
def params(cost: float, tol):
    """Temporarily swap the matcher's tolerance and reward functions; always restored."""
    saved = matcher.tolerance, matcher.terminal_reward
    matcher.tolerance, matcher.terminal_reward = tol, _reward(cost)
    try:
        yield
    finally:
        matcher.tolerance, matcher.terminal_reward = saved


def play(env: AuditEnv, name: str, seed: int, cfg: dict) -> dict:
    """One real episode -> what the grader needs to re-grade it offline."""
    traj = run_episode(env, None, seed, {**(cfg or {}), "mode": "train"},
                       policy_factory=lambda e: make_policy(name, e, seed))
    last = traj[-1]
    if last["terminated"]:  # submit: steps before the submit count
        submission, steps = last["action"].get("findings"), last["step"] - 1
    else:  # truncated: the env grades an empty submission with all steps
        submission, steps = {"episode_id": env.episode_id, "findings": []}, last["step"]
    return {"truth": env._ep["truth"], "submission": submission, "episode_id": env.episode_id,
            "steps": steps, "reward": env.result["reward"]}


def regrade(run: dict, cost: float, tol) -> float:
    with params(cost, tol):
        return matcher.grade(run["truth"], run["submission"], run["episode_id"], run["steps"])["reward"]


def check_default(runs: list[dict]) -> None:
    for run in runs:
        got = regrade(run, DEFAULT_COST, TOLERANCES[DEFAULT_TOL])
        assert got == run["reward"], f"{run['episode_id']}: re-grade {got} != env reward {run['reward']}"


def settings():
    """(column label, cost, tolerance label): vary cost at default tolerance, then tolerance at default cost."""
    cost_cols = [(f"cost {c:g}", c, DEFAULT_TOL) for c in STEP_COSTS]
    tol_cols = [(f"tol {t}", DEFAULT_COST, t) for t in TOLERANCES]
    return cost_cols, tol_cols


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def analyse(runs_by_policy: dict[str, list[dict]]) -> dict:
    cost_cols, tol_cols = settings()
    means = {}
    for name, runs in runs_by_policy.items():
        check_default(runs)
        means[name] = {label: round(sum(regrade(r, c, TOLERANCES[t]) for r in runs) / len(runs), 6)
                       for label, c, t in cost_cols + tol_cols}
    default = f"cost {DEFAULT_COST:g}"
    names = list(runs_by_policy)
    swaps = []  # (setting, a, b): a vs b order (>, =, <) differs from the default setting
    for label, _, _ in cost_cols + tol_cols:
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if _sign(means[a][label] - means[b][label]) != _sign(means[a][default] - means[b][default]):
                    swaps.append({"setting": label, "pair": [a, b]})
    ranking = sorted(names, key=lambda n: -means[n][default])
    return {"means": means, "cost_columns": [c[0] for c in cost_cols], "tol_columns": [c[0] for c in tol_cols],
            "default_ranking": ranking, "ranking_unchanged": not swaps, "swaps": swaps}


def _table(means: dict, cols: list[str], head: list[str]) -> list[str]:
    lines = ["| policy | " + " | ".join(head) + " |", "|---|" + "---:|" * len(cols)]
    for name, row in means.items():
        lines.append(f"| {name} | " + " | ".join(f"{row[c]:.4f}" for c in cols) + " |")
    return lines


def markdown(split: str, n: int, res: dict) -> str:
    dc, dt = f"{DEFAULT_COST:g}", DEFAULT_TOL
    cost_head = [f"{c:g}" + (" (default)" if f"{c:g}" == dc else "") for c in STEP_COSTS]
    tol_head = [t + (" (default)" if t == dt else "") for t in TOLERANCES]
    out = [f"### {split} ({n} episodes): mean return", "",
           f"Step cost varied (tolerance {dt}):", ""] + _table(res["means"], res["cost_columns"], cost_head)
    out += ["", f"Amount tolerance varied (step cost {dc}):", ""] + _table(res["means"], res["tol_columns"], tol_head)
    order = " > ".join(res["default_ranking"])
    if res["ranking_unchanged"]:
        out += ["", f"Ranking unchanged across all settings: {order}."]
    else:
        pairs = "; ".join(f"{s['pair'][0]} vs {s['pair'][1]} under {s['setting']}" for s in res["swaps"])
        out += ["", f"Ranking changes (default: {order}). Pairs that swap or tie: {pairs}."]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", help="also write the results as JSON here")
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    env, report, parts = AuditEnv(), {}, []
    for split, path, names in SPLITS:
        episodes = load_episodes(os.path.join(ROOT, path))
        runs = {name: [play(env, name, s, c) for s, c in episodes] for name in names}
        report[split] = {"config": path, "episodes": len(episodes), **analyse(runs)}
        parts.append(markdown(split, len(episodes), report[split]))
    print("\n\n".join(parts))
    print(f"\n(re-grade with default parameters reproduced every env reward exactly; "
          f"tolerance '0 (exact)' = 0 minor units, '1 %' = max(1, expected // 100); "
          f"{time.monotonic() - t0:.1f} s)")
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
