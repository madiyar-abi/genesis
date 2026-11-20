"""Closed-run guarantees that must hold even when the policy process dies or the organiser's list has a typo.

CONTRACT / server docstring: on close or EOF the open episode and every hidden episode not yet reset are graded
as abandoned, so a policy cannot skip hidden episodes. That must also hold when the policy closes its pipes
abruptly (the server's next write fails with EPIPE), and a hidden list with an invalid config must be refused
before serving instead of crashing at close with nothing logged.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

from auditenv.server import serve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def server(d, hidden):
    path, log = os.path.join(d, "hidden.json"), os.path.join(d, "grader.jsonl")
    with open(path, "w") as fh:
        json.dump(hidden, fh)
    env = {k: v for k, v in os.environ.items() if k != "AUDITENV_SECRET"}
    proc = subprocess.Popen([sys.executable, "-m", "auditenv.server", "--grader-log", log, "--episodes", path,
                             "--public"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=ROOT, env=env)
    return proc, log


def log_ends(log):
    if not os.path.exists(log):
        return []
    with open(log) as fh:
        return [json.loads(line)["end"] for line in fh]


class ServerRobustnessTest(unittest.TestCase):
    def test_policy_dying_mid_request_still_grades_every_hidden_episode(self):
        with tempfile.TemporaryDirectory() as d:
            proc, log = server(d, {"seeds": [21, 22, 23, 24, 25], "config": {"n_invoices": 10}})
            proc.stdin.write(b'{"cmd":"reset"}\n')
            proc.stdin.flush()
            ep = json.loads(proc.stdout.readline())["observation"]["manifest"]["episode_id"]
            submit = {"cmd": "step", "action": {"type": "submit", "findings": {"episode_id": ep, "findings": []}}}
            proc.stdin.write((json.dumps(submit) + "\n").encode())
            proc.stdin.flush()
            proc.stdout.readline()
            proc.stdin.write(b'{"cmd":"reset"}\n')
            proc.stdin.flush()
            proc.stdout.readline()
            # the policy dies with a request in flight: the server's answer hits a closed pipe
            proc.stdin.write(b'{"cmd":"step","action":{"type":"calculator","expression":"1+1"}}\n')
            proc.stdin.flush()
            proc.stdout.close()
            proc.stdin.close()
            proc.wait(timeout=60)
            proc.stderr.close()
            self.assertEqual(log_ends(log), ["submit"] + ["abandoned"] * 4)

    def test_invalid_hidden_config_is_refused_before_serving(self):
        with tempfile.TemporaryDirectory() as d:
            hidden = {"episodes": [{"seed": 1, "config": {}}, {"seed": 2, "config": {"max_steps": 0}},
                                   {"seed": 3, "config": {}}]}
            proc, log = server(d, hidden)
            out, err = proc.communicate(b'{"cmd":"close"}\n', timeout=60)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(out, b"")
            self.assertIn("hidden episode 2", err.decode())
            self.assertIn("max_steps", err.decode())

    def test_unreadable_hidden_list_is_refused_without_a_traceback(self):
        for name, text in (("missing", None), ("seed typo", '{"seeds": ["1"], "config": {}}'),
                           ("bad json", '{"seeds": [1,')):
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "hidden.json")
                if text is not None:
                    with open(path, "w") as fh:
                        fh.write(text)
                proc = subprocess.run([sys.executable, "-m", "auditenv.server", "--episodes", path, "--public"],
                                      input=b'{"cmd":"close"}\n', capture_output=True, cwd=ROOT, timeout=60)
                self.assertEqual(proc.returncode, 2)
                self.assertNotIn(b"Traceback", proc.stderr)
                self.assertIn(b"hidden episode list", proc.stderr)

    def test_reset_without_seed_is_a_contract_error(self):
        out = io.StringIO()
        serve(io.StringIO('{"cmd": "reset"}\n'), out)
        self.assertEqual(json.loads(out.getvalue().splitlines()[0]), {"error": "ValueError: seed must be an int"})


if __name__ == "__main__":
    unittest.main()
