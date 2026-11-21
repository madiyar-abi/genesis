"""The jury's flow end to end: our four baseline policies on the 20 Block 2 scenarios (D01-D20), through
`judge_adapter.py` exactly as the jury connects (genesis-exe.com/fintech-checks.html).

The jury side generates each episode into a directory, serves it with `reset({"mode": "closed", "episode_dir"})`
and keeps the true result. Each policy except the oracle runs in its own process and sees only the jury-shaped
observations over a pipe; `JuryPolicy` is the baseline-policy adapter that lets a policy written for `AuditEnv`
speak the jury's protocol. The oracle is grader-side by definition (it reads the truth) and submits a normal answer.
Prints P, R, F1 (micro), mean return, steps and time per policy, the diagnostics §10 of the case asks for.

Usage:
    python -m auditenv.jury_run                 # seeds 3001-3020, one per scenario
    python -m auditenv.jury_run --seed-base 7000 --json /tmp/jury_run.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

from .policy_worker import JuryPolicy, POLICIES, worker
from .jury import SCENARIOS
from .load import load_episode
from .policies.oracle import Oracle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def play(env, first: dict, policy_name: str, truth: dict | None = None, policy_image: str | None = None) -> int:
    """Run one episode on the jury side; returns the number of actions."""
    if policy_name == "oracle":  # grader-side: it reads the truth, as in the jury's definitions
        oracle = JuryPolicy(Oracle(truth))
        steps, obs = 1, first
        env.step(oracle.act(obs))
        return steps
    command = [sys.executable, "-m", "auditenv.policy_worker", policy_name]
    if policy_image:
        command = ["docker", "run", "--pull=never", "--rm", "-i", "--network", "none", "--read-only", "--cap-drop=ALL",
                   "--security-opt=no-new-privileges", "--user", "65534:65534", policy_image, policy_name]
    proc = subprocess.Popen(command, cwd=ROOT,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                            env={k: v for k, v in os.environ.items() if k != "AUDITENV_SECRET"})
    steps, obs, done = 0, first, False
    try:
        while not done:
            proc.stdin.write(json.dumps(obs) + "\n")
            proc.stdin.flush()
            obs, _, terminated, truncated, _ = env.step(json.loads(proc.stdout.readline()))
            steps, done = steps + 1, terminated or truncated
    finally:
        proc.stdin.close()
        proc.wait(timeout=30)
    return steps


def run(seed_base: int = 3000, policy_image: str | None = None) -> dict:
    import judge_adapter as ja  # repository root

    ja._WARNED = True  # a deliberately public run on published seeds: no grader-key warning
    rows = {}
    with tempfile.TemporaryDirectory() as tmp:
        episodes = []
        for n, (name, cfg) in enumerate(SCENARIOS.items(), start=1):
            path = os.path.join(tmp, name)
            ja.generate_episode(seed_base + n, cfg, path)
            episodes.append((name, path, load_episode(path)["truth"]))
        for policy_name in (*POLICIES, "oracle"):
            tp = fp = fn = 0
            returns, steps, times = [], [], []
            for name, path, truth in episodes:
                env = ja.make_env()
                t0 = time.monotonic()
                first, _ = env.reset(0, {"mode": "closed", "episode_dir": path, "team_config": {}})
                steps.append(play(env, first, policy_name, truth, policy_image))
                times.append(time.monotonic() - t0)
                res = env.grader_log[-1]  # the true result stays on the jury side
                tp, fp, fn = tp + res["tp"], fp + res["fp"], fn + res["fn"]
                returns.append(res["reward"])
            p = tp / (tp + fp) if tp + fp else 0.0
            r = tp / (tp + fn) if tp + fn else 0.0
            rows[policy_name] = {"episodes": len(episodes), "tp": tp, "fp": fp, "fn": fn, "precision": p,
                                 "recall": r, "f1": 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 1.0,
                                 "mean_return": sum(returns) / len(returns), "mean_steps": sum(steps) / len(steps),
                                 "max_steps": max(steps), "mean_time_s": sum(times) / len(times),
                                 "max_time_s": max(times)}
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-base", type=int, default=3000, help="scenario Dnn uses seed seed_base + nn")
    ap.add_argument("--json", default=None, help="also write the table as JSON")
    ap.add_argument("--policy-image", help="run each public baseline inside the specified policy-only Docker image")
    ap.add_argument("--policy-worker", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.policy_worker:
        return worker(args.policy_worker)
    rows = run(args.seed_base, args.policy_image)
    print(f"20 jury scenarios D01-D20 (seeds {args.seed_base + 1}-{args.seed_base + 20}) through judge_adapter, "
          "closed mode, policies in their own process (oracle grader-side)")
    print(f"{'policy':<16}{'P':>7}{'R':>7}{'F1':>7}{'return':>9}{'steps':>8}{'max':>6}{'time s':>9}{'max s':>8}")
    for name, row in rows.items():
        print(f"{name:<16}{row['precision']:7.3f}{row['recall']:7.3f}{row['f1']:7.3f}{row['mean_return']:9.3f}"
              f"{row['mean_steps']:8.1f}{row['max_steps']:6d}{row['mean_time_s']:9.3f}{row['max_time_s']:8.3f}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
