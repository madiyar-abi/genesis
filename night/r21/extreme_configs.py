"""Exercise extreme generator configs through the jury adapter and public baselines."""
import argparse
import json
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory

import judge_adapter as adapter
from auditenv.load import load_episode
from auditenv.policies.reconcile import Reconcile, ReconcileHard
from auditenv.policy_worker import JuryPolicy
from auditenv.verify import verify_episode

KINDS = ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")
DIFFICULTIES = ("default", "hard")


def mixed(count):
    quotient, remainder = divmod(count, len(KINDS))
    return {kind: quotient + (index < remainder) for index, kind in enumerate(KINDS)}


def configurations():
    for difficulty in DIFFICULTIES:
        tiny = {"n_invoices": 10, "difficulty": difficulty}
        for count in (0, 1, 12, 20, 50):
            for kind in KINDS:
                yield {**tiny, "errors": {kind: count}}
            yield {**tiny, "errors": mixed(count)}
        for i1, i2 in ((1, 0), (0, 1), (1, 1), (6, 0), (0, 6), (3, 3), (7, 0), (0, 7)):
            yield {**tiny, "interacting": {"I1": i1, "I2": i2}}
        yield {"n_invoices": 100, "difficulty": difficulty, "errors": mixed(12)}
        for kind in KINDS:
            yield {"n_invoices": 100, "difficulty": difficulty, "errors": {kind: 12}}

    for allocation, ensure, distractors, difficulty, transform in product(
        (None, "missing", "partial"), (False, True), (False, True), DIFFICULTIES, (None, 37)
    ):
        yield {"n_invoices": 10, "errors": {"payment_allocation": 1}, "allocation": allocation,
               "ensure_distractors": ensure, "distractors": distractors, "difficulty": difficulty,
               "transform_seed": transform}


def run_policy(seed, path, difficulty, *, empty=False):
    env = adapter.make_env()
    obs, info = env.reset(seed, {"mode": "closed", "episode_dir": path})
    episode_id = info["episode_id"]
    policy_class = ReconcileHard if difficulty == "hard" else Reconcile
    policy = JuryPolicy(policy_class(seed=0))
    for step in range(1, info["max_steps"] + 1):
        action = {"name": "submit", "args": {"findings": {"episode_id": episode_id, "findings": []}}} if empty else (
            policy.act(obs)
        )
        obs, _, terminated, truncated, _ = env.step(action)
        if truncated:
            raise RuntimeError(f"{'empty' if empty else difficulty} truncated at action {step}: {obs['error']!r}")
        if terminated:
            if action["name"] != "submit" or obs["error"]:
                raise RuntimeError(f"invalid terminal action {action['name']} at step {step}: {obs['error']!r}")
            scored = adapter.score_episode(path, action["args"]["findings"], step - 1)
            logged = env.grader_log[-1]
            if scored["f1"] != logged["f1"] or scored["return"] != logged["reward"]:
                raise RuntimeError(f"adapter grade disagrees with score_episode: {logged!r} vs {scored!r}")
            return step, scored
    raise RuntimeError(f"policy exceeded {info['max_steps']} actions")


def check(seed, config, path):
    requested = sum(config.get("errors", {}).values()) + 2 * sum(config.get("interacting", {}).values())
    try:
        adapter.generate_episode(seed, config, path)
    except ValueError as error:
        if not str(error).strip():
            return "failure", "ValueError without a message"
        return "rejected", f"ValueError: {error}"

    episode = load_episode(path)
    count = len(episode["truth"]["issues"])
    problems = [f"requested {requested} issues, got {count}"] if count != requested else []
    problems.extend(verify_episode(episode))
    steps, score = run_policy(seed, path, config["difficulty"])
    _, empty_score = run_policy(seed, path, config["difficulty"], empty=True)
    if score["f1"] != 1:
        problems.append(f"reconcile F1={score['f1']} at {steps} steps (TP/FP/FN {score['tp']}/{score['fp']}/{score['fn']})")
    expected_empty = 0.0 if count else 1.0
    if empty_score["f1"] != expected_empty:
        problems.append(f"empty findings F1={empty_score['f1']}; expected {expected_empty}")
    if problems:
        return "failure", "; ".join(problems)
    return "valid", f"{count} issues; {steps} actions; reconcile F1={score['f1']}; empty F1={empty_score['f1']}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", help="repeat to test more than one seed")
    args = parser.parse_args()
    summary = dict.fromkeys(("valid", "rejected", "failure"), 0)
    for seed in args.seed or [44000, 44001, 44002]:
        for config in configurations():
            try:
                with TemporaryDirectory(dir="/tmp/r21-codex1") as scratch:
                    status, detail = check(seed, config, str(Path(scratch) / "episode"))
            except Exception as error:
                status, detail = "failure", f"{type(error).__name__}: {error}"
            summary[status] += 1
            print(f"- seed {seed} {json.dumps(config, sort_keys=True)} — {status}: {detail}")
    print(f"\nOutcomes: {summary}. Total: {sum(summary.values())}.")
    return bool(summary["failure"])


if __name__ == "__main__":
    raise SystemExit(main())
