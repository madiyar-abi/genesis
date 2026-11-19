import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

CHILD_CODE = """
import hashlib
import json
from auditenv.env import AuditEnv
from auditenv.generator import generate
from auditenv.run import make_policy, run_episode

digests = []
for s in (0, 1, 2):
    d = generate(s, {})
    digests.append(hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest())

for s in (0, 1, 2):
    d = generate(s, {"difficulty": "hard"})
    digests.append(hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest())

env = AuditEnv()
policy = make_policy("reconcile", env, seed=2001)
traj = run_episode(env, policy, seed=2001, config={"mode": "train"})
digests.append(hashlib.sha256(json.dumps(traj, sort_keys=True).encode("utf-8")).hexdigest())

print(" ".join(digests))
"""


class TestHashseedIndependence(unittest.TestCase):
    def test_hashseed_independence(self):
        outputs = {}
        for h in ("0", "1", "4242"):
            env = {k: v for k, v in os.environ.items() if k != "AUDITENV_SECRET"}
            env["PYTHONHASHSEED"] = h
            proc = subprocess.run(
                [sys.executable, "-c", CHILD_CODE],
                cwd=str(ROOT_DIR),
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            line = proc.stdout.strip()
            self.assertTrue(line, f"Child produced empty output for PYTHONHASHSEED={h}")
            outputs[h] = line

        lines = set(outputs.values())
        self.assertEqual(
            len(lines),
            1,
            f"Hash-randomisation outputs differed across PYTHONHASHSEED: {outputs}",
        )


if __name__ == "__main__":
    unittest.main()
