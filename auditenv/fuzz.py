"""Seed sweep (phase-4 fuzzing): many seeds × configs, every episode checked end to end.

    uv run python -m auditenv.fuzz --seeds 0-999            # default difficulty
    uv run python -m auditenv.fuzz --seeds 0-199 --hard     # hard mode
    uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299        # solvability stress test
    uv run python -m auditenv.fuzz --stress reconcile_hard --seeds 0-299 --hard

Per episode: generation and the verifier raise nothing and find no problem (balanced journals
before/after, truth == recomputed discrepancies, every evidence set sufficient); the oracle reaches
reward > 0.9 on dirty books and 1.0 on clean ones; random explorer and flag-everything are played
through the env without an exception. Aggregates: share of episodes where random scores > 0 and
where flag-everything scores < 0. Exit code 0 only if no episode has a problem and the shortcut
policies stay bad (random > 0 on < 25 % of all and < 1 % of dirty episodes, flag-all < 0 on > 90 %).
"""

from __future__ import annotations

import argparse
import time

from .env import AuditEnv
from .generator import ISSUE_TYPES, generate
from .run import make_policy, parse_seeds, run_episode
from .verify import verify_episode

HEAVY = {"errors": {t: 2 for t in ISSUE_TYPES}, "interacting": {"I1": 1, "I2": 1}}
CONFIGS = {"random_mix": {}, "clean": {"errors": {}}, "heavy": HEAVY}


def sweep(seeds: list[int], hard: bool = False) -> dict:
    env = AuditEnv()
    problems: list[tuple] = []
    n = random_pos = random_pos_dirty = flag_neg = dirty = 0
    for seed in seeds:
        for name, base in CONFIGS.items():
            cfg = {**base, "difficulty": "hard"} if hard else dict(base)
            n += 1
            try:
                ep = generate(seed, cfg)
                bad = verify_episode(ep)
                if bad:
                    problems.append((seed, name, "verifier", bad[:2]))
                rewards = {}
                for policy in ("oracle", "random", "flag_all"):
                    traj = run_episode(env, None, seed, cfg, policy_factory=lambda e, p=policy: make_policy(p, e, seed))
                    rewards[policy] = traj[-1]["reward"]
                issues = len(ep["truth"]["issues"])
                dirty += bool(issues)
                if (issues and rewards["oracle"] <= 0.9) or (not issues and rewards["oracle"] != 1.0):
                    problems.append((seed, name, "oracle", rewards["oracle"]))
                random_pos += rewards["random"] > 0
                random_pos_dirty += bool(issues) and rewards["random"] > 0
                flag_neg += rewards["flag_all"] < 0
            except Exception as exc:  # a crash is a finding, not a stop
                problems.append((seed, name, "exception", f"{type(exc).__name__}: {exc}"[:200]))
    return {"episodes": n, "dirty": dirty, "clean": n - dirty, "problems": problems,
            "random_positive": random_pos, "random_positive_dirty": random_pos_dirty, "flag_all_negative": flag_neg}


STRESS = {"random_mix": {}, "clean": {"errors": {}}, "12_issues": {"errors": {t: 3 for t in ISSUE_TYPES}},
          "12_issues_100_invoices": {"errors": {t: 3 for t in ISSUE_TYPES}, "n_invoices": 100}}


def stress(policy: str, seeds: list[int], hard: bool = False) -> dict:
    """Is every truth issue findable from the records within the budget? Run a rule policy everywhere."""
    env = AuditEnv()
    imperfect, max_steps, truncated, n = [], 0, 0, 0
    for seed in seeds:
        for name, base in STRESS.items():
            cfg = {**base, "difficulty": "hard"} if hard else dict(base)
            traj = run_episode(env, None, seed, cfg, policy_factory=lambda e: make_policy(policy, e, seed))
            n += 1
            max_steps = max(max_steps, traj[-1]["step"])
            truncated += traj[-1]["truncated"]
            if env.result["f1"] < 1.0:
                imperfect.append((seed, name, env.result["tp"], env.result["fp"], env.result["fn"]))
    return {"episodes": n, "imperfect": imperfect, "max_steps": max_steps, "truncated": truncated}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="0-999")
    ap.add_argument("--hard", action="store_true", help="difficulty: hard")
    ap.add_argument("--stress", metavar="POLICY", help="stress test a rule policy instead of the sweep")
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    if args.stress:
        r = stress(args.stress, parse_seeds(args.seeds), args.hard)
        for p in r["imperfect"][:20]:
            print("   ", p)
        print(f"{args.stress} on {r['episodes']} {'hard' if args.hard else 'default'} episodes (seeds {args.seeds} x "
              f"{', '.join(STRESS)}): imperfect {len(r['imperfect'])}, max steps {r['max_steps']}, "
              f"truncated {r['truncated']} ({time.monotonic() - t0:.1f} s)")
        return 0 if not r["imperfect"] and not r["truncated"] else 1
    r = sweep(parse_seeds(args.seeds), args.hard)
    for p in r["problems"][:20]:
        print("   ", p)
    n = r["episodes"]
    ok = (not r["problems"] and r["random_positive"] < 0.25 * n and r["random_positive_dirty"] < 0.01 * r["dirty"]
          and r["flag_all_negative"] > 0.9 * n)
    print(f"{'hard' if args.hard else 'default'} mode, seeds {args.seeds}: {n} episodes ({r['dirty']} dirty, "
          f"{r['clean']} clean) in {time.monotonic() - t0:.1f} s")
    print(f"  episodes with a problem (exception / verifier / oracle): {len(r['problems'])}")
    print(f"  random explorer reward > 0: {r['random_positive']}/{n} episodes, of them on dirty books: "
          f"{r['random_positive_dirty']} (on clean books submitting nothing is the correct answer)")
    print(f"  flag-all reward < 0: {r['flag_all_negative']}/{n}")
    print("FUZZ PASSED" if ok else "FUZZ FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
