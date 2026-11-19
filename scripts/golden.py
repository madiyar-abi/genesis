"""Compute or verify golden hashes of generated episodes to detect unintended generator drift.

Usage:
    python scripts/golden.py           # recomputes and writes tests/golden_hashes.json
    python scripts/golden.py --check   # compares against tests/golden_hashes.json; exit 1 on drift
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from auditenv.generator import generate

DEFAULT_SEEDS = list(range(20))
CONFIGS: list[dict] = [
    {},
    {"errors": {}},
    {"difficulty": "hard"},
    {"transform_seed": 7},
]

DEFAULT_HASH_FILE = ROOT_DIR / "tests" / "golden_hashes.json"


def config_key(config: dict) -> str:
    return json.dumps(config, sort_keys=True, separators=(",", ":"))


def compute_hash(seed: int, config: dict) -> str:
    data = generate(seed, config)
    canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_all_hashes(seeds: list[int] = DEFAULT_SEEDS, configs: list[dict] = CONFIGS) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for config in configs:
        ck = config_key(config)
        for seed in seeds:
            key = f"{ck}|{seed}"
            hashes[key] = compute_hash(seed, config)
    return hashes


def check_hashes(path: Path | str = DEFAULT_HASH_FILE) -> tuple[bool, list[str]]:
    path = Path(path)
    if not path.is_file():
        return False, [f"Golden hash file not found: {path}"]
    with open(path, "r", encoding="utf-8") as fh:
        expected = json.load(fh)
    actual = compute_all_hashes()
    mismatches = []
    for k, exp_h in expected.items():
        act_h = actual.get(k)
        if act_h != exp_h:
            mismatches.append(f"Drift for {k}: expected {exp_h}, got {act_h}")
    for k in actual:
        if k not in expected:
            mismatches.append(f"Unexpected extra key in actual: {k}")
    return len(mismatches) == 0, mismatches


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify against existing hashes and exit 1 on drift")
    parser.add_argument("--file", type=Path, default=DEFAULT_HASH_FILE, help="path to golden_hashes.json")
    args = parser.parse_args(argv)

    if args.check:
        ok, mismatches = check_hashes(args.file)
        if not ok:
            print("Generator drift detected!", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            print("\nIf this change was intentional, update golden hashes with:", file=sys.stderr)
            print("    uv run python scripts/golden.py", file=sys.stderr)
            print("and re-export episodes per CLAUDE.md.", file=sys.stderr)
            return 1
        print(f"All {len(DEFAULT_SEEDS) * len(CONFIGS)} golden hashes match {args.file}.")
        return 0

    hashes = compute_all_hashes()
    args.file.parent.mkdir(parents=True, exist_ok=True)
    with open(args.file, "w", encoding="utf-8") as fh:
        json.dump(hashes, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {len(hashes)} golden hashes to {args.file}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
