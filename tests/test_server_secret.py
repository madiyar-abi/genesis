"""A closed run without AUDITENV_SECRET is reproducible from the public generator: the server must say so.

Without the key, `episode_id` is an HMAC under a public key, so a policy can enumerate seeds and recover
each hidden episode (and its truth) in seconds. The server keeps working (the public smoke runs rely on
it) but warns on stderr unless the caller marks the episode list as public on purpose with --public.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from auditenv.client import RemoteEnv
from auditenv.generator import episode_id_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIDDEN = {"seeds": [734211], "config": {"n_invoices": 30}}


def run_server(args, secret=None):
    env = {k: v for k, v in os.environ.items() if k != "AUDITENV_SECRET"}
    if secret is not None:
        env["AUDITENV_SECRET"] = secret
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "hidden.json")
        with open(path, "w") as fh:
            json.dump(HIDDEN, fh)
        proc = subprocess.run([sys.executable, "-m", "auditenv.server", "--episodes", path, *args],
                              input='{"cmd": "reset"}\n{"cmd": "close"}\n', capture_output=True, text=True,
                              env=env, cwd=ROOT, timeout=60)
    return proc, json.loads(proc.stdout.splitlines()[0])


class ServerSecretTest(unittest.TestCase):
    def test_hidden_list_without_secret_warns_and_is_recoverable(self):
        proc, first = run_server([])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("observation", first)  # still serves: backwards compatible
        self.assertIn("AUDITENV_SECRET", proc.stderr)
        # why the warning matters: the public key lets anyone map episode_id back to its seed
        self.assertEqual(first["info"]["episode_id"], episode_id_for(734211, {**HIDDEN["config"], "mode": "eval"}))

    def test_secret_set_is_silent_and_unrecoverable(self):
        proc, first = run_server([], secret="test-only-grader-key")
        self.assertEqual(proc.stderr, "")
        self.assertNotEqual(first["info"]["episode_id"], episode_id_for(734211, {**HIDDEN["config"], "mode": "eval"}))

    def test_public_flag_silences_the_warning(self):
        proc, first = run_server(["--public"])
        self.assertEqual(proc.stderr, "")
        self.assertIn("observation", first)

    def test_remote_env_public_passes_the_flag(self):
        self.assertIn("--public", RemoteEnv.command(episodes="h.json", public=True))
        self.assertNotIn("--public", RemoteEnv.command(episodes="h.json"))


if __name__ == "__main__":
    unittest.main()
