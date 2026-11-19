"""Single official check command (offline, CPU only):

    uv run python -m auditenv.check            # or: make check / docker run auditenv
    uv run python -m auditenv.check --quick    # fewer seeds

1. unit tests (unittest discover)
2. independent verifier on generated episodes (truth == recomputed discrepancies)
3. four baseline policies on the dev split -> P / R / F1 / return / steps / time per policy
4. 20 paired checks: seed+actions replay is exact; relabel+permute keeps the oracle answer and reward
5. out-of-process eval run: rewards hidden from the policy, results only in the grader log
6. hard mode (configs/eval_hard.json): verifier on hard episodes, baseline table, gates: oracle 1.0,
   reconcile_hard (rules from the policy) solves it from the records, plain reconcile does not
Exit code 0 only if every gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import unittest

from .env import AuditEnv
from .generator import ISSUE_TYPES, generate
from .metrics import prf1
from .run import POLICIES, load_episodes, make_policy, run_episode
from .verify import verify_episode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAVY = {"errors": {t: 2 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}
FALLBACK_DEV = [(2000 + i, c) for i, c in enumerate(
    [{"errors": {}}, {"errors": {}}, {"errors": {"fx_error": 1}, "interacting": {"I1": 1}},
     {"errors": {"duplicate_invoice": 1}, "interacting": {"I2": 1}}] + [None] * 6)]


def _gate(name: str, ok: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return ok


def run_tests() -> bool:
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"), top_level_dir=ROOT)
    with open(os.devnull, "w") as devnull:
        stdout, sys.stdout = sys.stdout, devnull
        try:
            result = unittest.TextTestRunner(stream=devnull, verbosity=0).run(suite)
        finally:
            sys.stdout = stdout
    return _gate("unit tests", result.wasSuccessful(),
                 f"{result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")


def run_verifier(n_seeds: int) -> bool:
    bad, total = [], 0
    for seed in range(n_seeds):
        for cfg in (None, {"errors": {}}, HEAVY, {**HEAVY, "transform_seed": seed}):
            total += 1
            probs = verify_episode(generate(seed, cfg))
            if probs:
                bad.append((seed, cfg, probs[:2]))
    for b in bad[:5]:
        print("   ", b)
    return _gate("data & truth verifier", not bad, f"{total - len(bad)}/{total} episodes valid "
                 "(balanced journals, correct pre-injection books, truth == recomputed discrepancies)")


def available_policies() -> list[str]:
    import importlib.util
    return [n for n in ("random", "naive_reconcile", "reconcile", "flag_all", "oracle")
            if importlib.util.find_spec(POLICIES[n][0]) is not None]


def baseline_table(episodes, names) -> dict:
    env = AuditEnv()
    table = {}
    print(f"\n{'policy':<16} {'P':>6} {'R':>6} {'F1':>6} {'return':>8} {'steps':>6} {'time_s':>7} {'exp_ret*':>9}")
    for name in names:
        rows = []
        for seed, cfg in episodes:
            t0 = time.monotonic()
            traj = run_episode(env, None, seed, {**(cfg or {}), "mode": "train"},
                               policy_factory=lambda e, s=seed: make_policy(name, e, s))
            res = env.result
            rows.append((res["tp"], res["fp"], res["fn"], res["reward"], traj[-1]["step"], time.monotonic() - t0,
                         res["experimental_reward"]))
        tp, fp, fn = (sum(r[i] for r in rows) for i in range(3))
        p, r, f1 = prf1(tp, fp, fn)
        ret, steps, secs, exp = (sum(row[i] for row in rows) / len(rows) for i in (3, 4, 5, 6))
        table[name] = {"precision": p, "recall": r, "f1": f1, "return": ret, "steps": steps, "time_s": secs,
                       "tp": tp, "fp": fp, "fn": fn, "experimental_return": exp}
        print(f"{name:<16} {p:6.3f} {r:6.3f} {f1:6.3f} {ret:8.3f} {steps:6.1f} {secs:7.3f} {exp:9.3f}")
    return table


def run_baselines(episodes) -> tuple[bool, dict]:
    table = baseline_table(episodes, available_policies())
    print(f"(dev split, {len(episodes)} episodes; P/R/F1 micro-averaged; return/steps/time means; "
          "*exp_ret = experimental materiality-weighted reward, reported separately)\n")
    ok = _gate("oracle reaches the maximum reward", table["oracle"]["return"] == 1.0)
    ok &= _gate("flag-all attack is penalised", table["flag_all"]["return"] < 0,
                f"mean return {table['flag_all']['return']:.3f}")
    if "random" in table:
        ok &= _gate("random explorer stays below oracle", table["random"]["return"] < table["oracle"]["return"])
    return ok, table


HARD_POLICIES = ("random", "naive_reconcile", "reconcile", "reconcile_hard", "flag_all", "oracle")


def run_hard(n_verify: int) -> tuple[bool, dict]:
    """Hard mode: the episodes stay valid, solvable from the records, and beat the default rules."""
    bad = []
    for seed in range(n_verify):
        for cfg in ({"difficulty": "hard"}, {**HEAVY, "difficulty": "hard", "transform_seed": seed}):
            probs = verify_episode(generate(seed, cfg))
            if probs:
                bad.append((seed, cfg, probs[:2]))
    for b in bad[:5]:
        print("   ", b)
    ok = _gate("hard-mode verifier", not bad, f"{2 * n_verify - len(bad)}/{2 * n_verify} hard episodes valid")
    path = os.path.join(ROOT, "configs", "eval_hard.json")
    episodes = load_episodes(path)
    table = baseline_table(episodes, HARD_POLICIES)
    print(f"(hard mode, configs/eval_hard.json, {len(episodes)} episodes; same columns as above)\n")
    ok &= _gate("hard: oracle reaches the maximum reward", table["oracle"]["return"] == 1.0)
    ok &= _gate("hard: solvable from the records", table["reconcile_hard"]["f1"] >= 0.95,
                f"reconcile_hard F1 {table['reconcile_hard']['f1']:.3f}")
    ok &= _gate("hard: default rules no longer suffice", table["reconcile"]["f1"] <= 0.8,
                f"reconcile F1 {table['reconcile']['f1']:.3f}")
    ok &= _gate("hard: flag-all attack is penalised", table["flag_all"]["return"] < 0)
    return ok, table


def _digest(traj) -> str:
    return hashlib.sha256(json.dumps(traj, sort_keys=True).encode()).hexdigest()


def run_paired(n: int = 20) -> bool:
    env = AuditEnv()
    names = [p for p in ("reconcile", "random") if p in available_policies()]
    failures = []
    for i in range(n):
        seed, cfg = 5000 + i, (HEAVY if i % 4 == 0 else ({"errors": {}} if i % 4 == 1 else None))
        # (a) replay: same seed, config, version and actions -> identical records, transitions, rewards
        for name in names:
            t1 = run_episode(env, None, seed, cfg, policy_factory=lambda e: make_policy(name, e, 7))
            t2 = run_episode(env, None, seed, cfg, policy_factory=lambda e: make_policy(name, e, 7))
            if _digest(t1) != _digest(t2):
                failures.append((seed, name, "replay differs"))
        # (b) benign transform: oracle answer under new ids keeps the reward; old ids do not transfer
        t_cfg = {**(cfg or {}), "transform_seed": 100 + i}
        r1 = run_episode(env, None, seed, cfg, policy_factory=lambda e: make_policy("oracle", e))[-1]["reward"]
        ep1 = env._ep
        r2 = run_episode(env, None, seed, t_cfg, policy_factory=lambda e: make_policy("oracle", e))[-1]["reward"]
        ep2 = env._ep
        same = [(x["type"], x["expected_amount_minor"]) for x in ep1["truth"]["issues"]] == \
               [(x["type"], x["expected_amount_minor"]) for x in ep2["truth"]["issues"]]
        if r1 != r2 or not same:
            failures.append((seed, "oracle", f"transform changed reward {r1} -> {r2}"))
        if "reconcile" in names:
            a = run_episode(env, None, seed, cfg, policy_factory=lambda e: make_policy("reconcile", e))[-1]["reward"]
            b = run_episode(env, None, seed, t_cfg, policy_factory=lambda e: make_policy("reconcile", e))[-1]["reward"]
            if a != b:
                failures.append((seed, "reconcile", f"transform changed reward {a} -> {b}"))
    for f in failures[:5]:
        print("   ", f)
    return _gate("paired checks (replay + relabel/permute)", not failures,
                 f"{n - len({f[0] for f in failures})}/{n} pairs pass; policies: oracle, {', '.join(names)}")


def run_remote() -> bool:
    from .client import RemoteEnv
    with tempfile.TemporaryDirectory() as d:
        log, hidden = os.path.join(d, "grader.jsonl"), os.path.join(d, "hidden.json")
        with open(hidden, "w") as fh:
            json.dump({"seeds": [7001, 7002], "config": HEAVY}, fh)
        leaked = False
        with RemoteEnv(grader_log=log, episodes=hidden) as env:
            for _ in range(2):
                obs, info = env.reset()
                pol = make_policy("flag_all", None)
                pol.reset(obs)
                while True:
                    obs, reward, term, trunc, info = env.step(pol.act(obs))
                    text = json.dumps([obs, info])
                    leaked |= reward != 0.0 or any(k in text for k in ("truth", "evidence_sets", "expected_amount"))
                    if term or trunc:
                        break
        with open(log) as fh:
            n = sum(1 for _ in fh)
    return _gate("out-of-process eval run", not leaked and n == 2,
                 "policy saw no reward/truth; 2 results in the grader log")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="fewer verifier seeds")
    ap.add_argument("--json", help="write the metrics table here")
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    dev_path = os.path.join(ROOT, "configs", "dev.json")
    episodes = load_episodes(dev_path) if os.path.exists(dev_path) else FALLBACK_DEV
    ok = run_tests()
    ok &= run_verifier(15 if args.quick else 50)
    base_ok, table = run_baselines(episodes)
    ok &= base_ok
    ok &= run_paired(20)
    ok &= run_remote()
    hard_ok, hard_table = run_hard(10 if args.quick else 25)
    ok &= hard_ok
    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"dev": table, "hard": hard_table}, fh, indent=2, sort_keys=True)
    print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'} in {time.monotonic() - t0:.1f} s")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
