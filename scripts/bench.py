"""Timing benchmark for generator, verification, and policy execution.

Measures wall time (time.perf_counter, median of 3 runs) of:
(a) generate() for seeds 0–99 (default and hard)
(b) one full episode per policy on configs/dev.json and configs/eval_hard.json
(c) auditenv.verify over seeds 0–99

Usage:
    python scripts/bench.py [--json metrics.json]
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from auditenv.env import AuditEnv
from auditenv.generator import generate
from auditenv.run import POLICIES, load_episodes, make_policy, run_episode
from auditenv.verify import verify_episode

POLICY_ORDER = ["oracle", "reconcile_hard", "reconcile", "naive_reconcile", "random", "flag_all"]


def measure_median(fn, n_runs: int = 3) -> float:
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def bench_generator(seeds: list[int], config: dict, n_runs: int = 3) -> float:
    def run():
        for s in seeds:
            generate(s, config)

    return measure_median(run, n_runs=n_runs)


def bench_verify(seeds: list[int], n_runs: int = 3) -> float:
    configs = (
        None,
        {"errors": {}},
        {
            "errors": {"duplicate_invoice": 2, "payment_allocation": 2, "fx_error": 2, "period_cutoff": 2},
            "interacting": {"I1": 1, "I2": 1},
        },
    )

    def run():
        for s in seeds:
            for cfg in configs:
                verify_episode(generate(s, cfg))

    return measure_median(run, n_runs=n_runs)


def bench_policy(
    policy_name: str,
    seed: int,
    config: dict,
    n_runs: int = 3,
) -> dict:
    env = AuditEnv()
    times = []
    last_res = None
    last_traj = None
    for _ in range(n_runs):
        t0 = time.perf_counter()
        traj = run_episode(
            env,
            None,
            seed,
            config,
            policy_factory=lambda e, pol=policy_name, s=seed: make_policy(pol, e, s),
        )
        times.append(time.perf_counter() - t0)
        last_res = env.result
        last_traj = traj

    med_s = statistics.median(times)
    return {
        "time_s": med_s,
        "time_ms": med_s * 1000.0,
        "steps": last_traj[-1]["step"] if last_traj else 0,
        "f1": last_res.get("f1", 0.0) if last_res else 0.0,
        "precision": last_res.get("precision", 0.0) if last_res else 0.0,
        "recall": last_res.get("recall", 0.0) if last_res else 0.0,
        "return": last_res.get("reward", 0.0) if last_res else 0.0,
    }


def run_bench(
    seeds: list[int] = list(range(100)),
    dev_config_path: Path | str = ROOT_DIR / "configs" / "dev.json",
    hard_config_path: Path | str = ROOT_DIR / "configs" / "eval_hard.json",
    n_runs: int = 3,
    policies: list[str] | None = None,
) -> dict:
    if policies is None:
        policies = [p for p in POLICY_ORDER if p in POLICIES]

    dev_episodes = load_episodes(str(dev_config_path))
    dev_seed, dev_cfg = dev_episodes[0]

    hard_episodes = load_episodes(str(hard_config_path))
    hard_seed, hard_cfg = hard_episodes[0]

    # (a) Generator default and hard
    gen_def_time = bench_generator(seeds, {}, n_runs=n_runs)
    gen_hard_time = bench_generator(seeds, {"difficulty": "hard"}, n_runs=n_runs)

    # (b) Policies on dev and hard
    dev_policy_res = {}
    hard_policy_res = {}
    for pol in policies:
        dev_policy_res[pol] = bench_policy(pol, dev_seed, dev_cfg, n_runs=n_runs)
        hard_policy_res[pol] = bench_policy(pol, hard_seed, hard_cfg, n_runs=n_runs)

    # (c) Verifier
    ver_time = bench_verify(seeds, n_runs=n_runs)

    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "seeds_count": len(seeds),
        "n_runs": n_runs,
        "generator_default_s": gen_def_time,
        "generator_hard_s": gen_hard_time,
        "verify_seeds_s": ver_time,
        "policies_dev": dev_policy_res,
        "policies_hard": hard_policy_res,
    }


def render_markdown(data: dict) -> str:
    n_seeds = data["seeds_count"]
    gen_def = data["generator_default_s"]
    gen_hard = data["generator_hard_s"]
    ver = data["verify_seeds_s"]

    lines = [
        "## Timing Benchmark",
        "",
        f"- **Python:** {data['python_version']}",
        f"- **Platform:** {data['platform']}",
        f"- **Runs:** median of {data['n_runs']}",
        "",
        "### Generator and Verifier",
        "",
        "| Operation | Workload | Median time | Per-episode |",
        "|---|---|---|---|",
        f"| `generate()` (default) | {n_seeds} seeds | {gen_def:.3f} s | {gen_def / n_seeds * 1000:.2f} ms |",
        f"| `generate()` (hard) | {n_seeds} seeds | {gen_hard:.3f} s | {gen_hard / n_seeds * 1000:.2f} ms |",
        f"| `auditenv.verify` | {n_seeds} seeds × 3 configs ({n_seeds * 3} eps) | {ver:.3f} s | {ver / (n_seeds * 3) * 1000:.2f} ms |",
        "",
        "### Policy Execution (1 Episode)",
        "",
        "| Policy | Split | Time (ms) | Steps | Return | F1 |",
        "|---|---|---|---|---|---|",
    ]

    for pol, res in data["policies_dev"].items():
        lines.append(f"| {pol} | dev | {res['time_ms']:.2f} | {res['steps']} | {res['return']:.3f} | {res['f1']:.3f} |")

    for pol, res in data["policies_hard"].items():
        lines.append(f"| {pol} | hard | {res['time_ms']:.2f} | {res['steps']} | {res['return']:.3f} | {res['f1']:.3f} |")

    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None, help="write benchmark numbers to JSON file")
    parser.add_argument("--runs", type=int, default=3, help="number of runs for median (default 3)")
    args = parser.parse_args(argv)

    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}\n")

    bench_data = run_bench(n_runs=args.runs)
    table = render_markdown(bench_data)
    print(table)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(bench_data, fh, indent=2)
            fh.write("\n")
        print(f"\nWrote benchmark metrics to {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
