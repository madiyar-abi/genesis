"""Run policies on episodes and write trajectories.jsonl (CONTRACT §7).

    uv run python -m auditenv.run --policy reconcile --seeds 2000-2009 --out /tmp/dev_reconcile.jsonl
    uv run python -m auditenv.run --policy reconcile_hard --config configs/train.json --config configs/train_hard.json \
        --out trajectories.jsonl    # the committed trajectories.jsonl (README)
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import importlib
import json
import time

from .env import AuditEnv

POLICIES = {  # name -> (module, class); the oracle is built grader-side from truth
    "random": ("auditenv.policies.random_explorer", "RandomExplorer"),
    "flag_all": ("auditenv.policies.flag_all", "FlagAll"),
    "reconcile": ("auditenv.policies.reconcile", "Reconcile"),
    "reconcile_hard": ("auditenv.policies.reconcile", "ReconcileHard"),
    "naive_reconcile": ("auditenv.policies.naive_reconcile", "NaiveReconcile"),
    "oracle": ("auditenv.policies.oracle", "Oracle"),
}


def make_policy(name: str, env: AuditEnv, seed: int = 0):
    module, cls = POLICIES[name]
    klass = getattr(importlib.import_module(module), cls)
    if name == "oracle":
        return klass(env._ep["truth"])  # grader-side only
    return klass(seed=seed)


def run_episode(env: AuditEnv, policy, seed: int, config: dict | None = None, policy_factory=None) -> list[dict]:
    """Play one episode. If `policy_factory(env)` is given it builds the policy after reset."""
    obs, info = env.reset(seed, config)
    if policy_factory is not None:
        policy = policy_factory(env)
    ep = info["episode_id"]
    traj = [{"episode_id": ep, "step": 0, "action": None, "observation": deepcopy(obs), "reward": 0.0,
             "terminated": False, "truncated": False}]
    policy.reset(obs)
    while True:
        action = policy.act(obs)
        recorded_action = deepcopy(action)
        obs, reward, terminated, truncated, info = env.step(action)
        traj.append({"episode_id": ep, "step": obs["step"], "action": recorded_action, "observation": deepcopy(obs),
                     "reward": reward, "terminated": terminated, "truncated": truncated})
        if terminated or truncated:
            return traj


def parse_seeds(text: str) -> list[int]:
    seeds = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            start, end = int(a), int(b)
            if end < start:
                raise ValueError(f"reversed seed range {part!r}")
            seeds.extend(range(start, end + 1))
        else:
            seeds.append(int(part))
    return seeds


def load_episodes(path: str) -> list[tuple[int, dict]]:
    """configs/*.json -> [(seed, config)]. Format: {config_version, split, episodes:[{seed, config}]}."""
    with open(path) as fh:
        spec = json.load(fh)
    if not isinstance(spec, dict):
        raise ValueError("episode list must be an object")
    if "episodes" in spec:
        entries = spec["episodes"]
        if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
            raise ValueError("episodes must be a list of objects")
    else:
        seeds = spec.get("seeds")
        if not isinstance(seeds, list):
            raise ValueError("seeds must be a list of integers")
        entries = [{"seed": seed, "config": spec.get("config")} for seed in seeds]

    episodes = []
    for entry in entries:
        seed = entry.get("seed")
        if type(seed) is not int:
            raise ValueError("seed must be an int")
        cfg = entry.get("config")
        if cfg is not None and not isinstance(cfg, dict):
            raise ValueError("config must be an object or null")
        episodes.append((seed, dict(cfg or {})))
    return episodes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--policy", choices=sorted(POLICIES), default="reconcile")
    ap.add_argument("--seeds", type=parse_seeds, default=None, help="e.g. 2000-2009 or 1,2,3 (default 2000-2009)")
    ap.add_argument("--config", action="append",
                    help="configs/*.json episode list; repeat to run several in order (ignored if --seeds is given)")
    ap.add_argument("--mode", choices=("train", "eval"), default="train")
    ap.add_argument("--out", help="write trajectories.jsonl here")
    ap.add_argument("--policy-seed", type=int, default=0)
    args = ap.parse_args(argv)
    if args.config and args.seeds is None:
        episodes = [episode for path in args.config for episode in load_episodes(path)]
    else:
        episodes = [(s, {}) for s in (args.seeds if args.seeds is not None else parse_seeds("2000-2009"))]
    episodes = [(s, {**c, "mode": args.mode}) for s, c in episodes]
    env = AuditEnv()
    out = open(args.out, "w") if args.out else None
    print(f"{'episode':<16} {'P':>5} {'R':>5} {'F1':>5} {'return':>7} {'steps':>5} {'time_s':>6}")
    for seed, config in episodes:
        t0 = time.monotonic()
        traj = run_episode(env, None, seed, config,
                           policy_factory=lambda e, s=seed: make_policy(args.policy, e, args.policy_seed + s))
        res = env.result
        if out:
            for rec in traj:
                out.write(json.dumps(rec, sort_keys=True) + "\n")
        print(f"{traj[0]['episode_id']:<16} {res['precision']:5.2f} {res['recall']:5.2f} {res['f1']:5.2f} "
              f"{res['reward']:7.3f} {traj[-1]['step']:5d} {time.monotonic() - t0:6.2f}")
    if out:
        out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
