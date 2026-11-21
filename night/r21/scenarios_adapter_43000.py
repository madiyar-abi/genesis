"""R20 Z1 (rb): play every jury scenario D01-D20 through judge_adapter in closed mode.

For each scenario config in auditenv/jury.py, both difficulties (default, hard), seeds 32000-32004:
generate the episode with judge_adapter.generate_episode (closed: private grader key), serve it with
reset({"mode": "closed", "episode_dir": ...}) and play it with the records-only baseline (reconcile on
default, reconcile_hard on hard) and with flag_all. Policies are driven through JuryPolicy, so they see
only the jury-shaped observations; the true score is read from the grader-side env.grader_log after the
episode, never shown to a policy. This script never opens truth.json / provenance.json itself.

Run from the repo root:
    env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py

Prints a scenario x difficulty table (mean grader return and F1 per policy) and flags:
  - any reconcile/reconcile_hard episode with F1 < 1.0 (README: reconcile solves all scenarios, F1 1.000);
  - any scenario whose reconcile mean return is below the README jury_run mean of 0.959 (note: that
    number is a 20-scenario mean on seeds 3001-3020; per-scenario return varies with inspection cost);
  - any flag_all episode with grader return > 0 (README: flag-everything return -1.000).
Exit code 0 = all 400 runs completed (flags are printed, not fatal: evidence task, the lead fixes).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import judge_adapter as ja
from auditenv.jury import SCENARIOS
from auditenv.policies.flag_all import FlagAll
from auditenv.policies.reconcile import Reconcile, ReconcileHard
from auditenv.policy_worker import JuryPolicy

SEEDS = range(43000, 43005)
SCRATCH = "/tmp/r21-rb"
README_RECONCILE_RETURN = 0.959  # README "Jury adapter" jury_run table, seeds 3001-3020, default difficulty
README_FLAG_ALL_RETURN = -1.000


def play(env, first: dict, policy) -> dict:
    """Drive one policy through the adapter; return the grader-side result plus run stats."""
    jp = JuryPolicy(policy)
    obs, steps, done = first, 0, False
    t0 = time.monotonic()
    while not done:
        obs, reward, terminated, truncated, _ = env.step(jp.act(obs))
        steps += 1
        if reward != 0.0:
            raise AssertionError(f"closed-mode step reward leaked to the policy: {reward!r}")
        done = terminated or truncated
        if steps > 200:
            raise AssertionError("policy did not finish within 200 adapter steps")
    res = dict(env.grader_log[-1])
    res["adapter_steps"] = steps
    res["wall_s"] = round(time.monotonic() - t0, 4)
    return res


def main() -> int:
    os.makedirs(SCRATCH, exist_ok=True)
    cells = {}  # (scenario, difficulty, policy_name) -> list of per-seed results
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(dir=SCRATCH, prefix="z1-") as tmp:
        for difficulty in ("default", "hard"):
            for name, cfg in SCENARIOS.items():
                config = dict(cfg)
                if difficulty == "hard":
                    config["difficulty"] = "hard"
                for seed in SEEDS:
                    path = os.path.join(tmp, f"{name}-{difficulty}-{seed}")
                    ja.generate_episode(seed, config, path)
                    runs = [("reconcile_hard" if difficulty == "hard" else "reconcile",
                             ReconcileHard(seed=0) if difficulty == "hard" else Reconcile(seed=0)),
                            ("flag_all", FlagAll(seed=0))]
                    for pname, policy in runs:
                        env = ja.make_env()
                        first, _ = env.reset(0, {"mode": "closed", "episode_dir": path, "team_config": {}})
                        res = play(env, first, policy)
                        res["seed"] = seed
                        cells.setdefault((name, difficulty, pname), []).append(res)
    wall = time.monotonic() - t0

    flags, notes = [], []
    print(f"Z1: 20 scenarios x 2 difficulties x 5 seeds (43000-43004) x 2 policies = "
          f"{sum(len(v) for v in cells.values())} closed runs through judge_adapter, {wall:.1f} s total")
    print()
    print("| scenario | difficulty | policy | mean return | mean F1 | min F1 | tp/fp/fn | mean steps | max steps | max s |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for (name, difficulty, pname), runs in sorted(cells.items()):
        n = len(runs)
        mean_ret = sum(r["reward"] for r in runs) / n
        mean_f1 = sum(r["f1"] for r in runs) / n
        min_f1 = min(r["f1"] for r in runs)
        tp = sum(r["tp"] for r in runs)
        fp = sum(r["fp"] for r in runs)
        fn = sum(r["fn"] for r in runs)
        mean_steps = sum(r["adapter_steps"] for r in runs) / n
        max_steps = max(r["adapter_steps"] for r in runs)
        max_s = max(r["elapsed_s"] for r in runs)
        print(f"| {name} | {difficulty} | {pname} | {mean_ret:.3f} | {mean_f1:.3f} | {min_f1:.3f} "
              f"| {tp}/{fp}/{fn} | {mean_steps:.1f} | {max_steps} | {max_s:.3f} |")
        for r in runs:
            if not r["valid"]:
                flags.append(f"{name} {difficulty} {pname} seed {r['seed']}: invalid submission "
                             f"({r['error']}), return {r['reward']}")
            if pname.startswith("reconcile") and r["f1"] < 1.0:
                flags.append(f"{name} {difficulty} {pname} seed {r['seed']}: F1 {r['f1']:.3f} < 1.0 "
                             f"(tp={r['tp']} fp={r['fp']} fn={r['fn']}, return {r['reward']:.3f}) "
                             f"— README documents F1 1.000")
            if pname == "flag_all" and r["reward"] > 0:
                flags.append(f"{name} {difficulty} flag_all seed {r['seed']}: return {r['reward']:.3f} > 0 "
                             f"— README documents {README_FLAG_ALL_RETURN:.3f}")
        if pname.startswith("reconcile") and mean_ret < README_RECONCILE_RETURN:
            notes.append(f"{name} {difficulty} {pname}: mean return {mean_ret:.3f} < README mean "
                         f"{README_RECONCILE_RETURN:.3f} (F1 min {min_f1:.3f}; README value is a 20-scenario "
                         f"mean, per-scenario return varies with inspection cost 0.002/step)")
        if max_s >= 60:
            flags.append(f"{name} {difficulty} {pname}: episode took {max_s:.1f} s >= 60 s limit")

    print()
    print(f"FLAGS ({len(flags)}):")
    for f in flags:
        print("  " + f)
    if not flags:
        print("  none")
    print(f"NOTES ({len(notes)}):")
    for n in notes:
        print("  " + n)
    if not notes:
        print("  none")

    out = os.path.join(SCRATCH, "z1.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"wall_s": round(wall, 1), "flags": flags, "notes": notes,
                   "cells": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in cells.items()}}, fh, indent=2, sort_keys=True)
    print(f"\nJSON: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())