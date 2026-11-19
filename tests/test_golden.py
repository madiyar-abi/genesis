import hashlib
import json
import unittest
from pathlib import Path

from auditenv.generator import generate

ROOT_DIR = Path(__file__).resolve().parent.parent
GOLDEN_FILE = ROOT_DIR / "tests" / "golden_hashes.json"

SEEDS = list(range(20))
CONFIGS = [
    {},
    {"errors": {}},
    {"difficulty": "hard"},
    {"transform_seed": 7},
]


class GoldenHashesTest(unittest.TestCase):
    def test_generator_golden_hashes(self):
        self.assertTrue(GOLDEN_FILE.is_file(), f"Golden hashes file missing at {GOLDEN_FILE}")
        with open(GOLDEN_FILE, "r", encoding="utf-8") as fh:
            expected = json.load(fh)

        mismatches = []
        count = 0
        for config in CONFIGS:
            ck = json.dumps(config, sort_keys=True, separators=(",", ":"))
            for seed in SEEDS:
                key = f"{ck}|{seed}"
                data = generate(seed, config)
                h = hashlib.sha256(
                    json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
                exp_h = expected.get(key)
                if h != exp_h:
                    mismatches.append(f"{key}: expected {exp_h}, got {h}")
                count += 1

        self.assertEqual(count, 80)
        self.assertEqual(
            mismatches,
            [],
            (
                f"\nGenerator drifted on {len(mismatches)} of {count} configurations:\n"
                + "\n".join(f"  - {m}" for m in mismatches)
                + "\nIf this generator change was intentional, recompute golden hashes with:\n"
                + "    uv run python scripts/golden.py\n"
                + "and re-export episodes per CLAUDE.md:\n"
                + "    uv run python -m auditenv.export --config configs/dev.json --out episodes/dev\n"
                + "    uv run python -m auditenv.export --config configs/train.json --out episodes/train\n"
            ),
        )


if __name__ == "__main__":
    unittest.main()
