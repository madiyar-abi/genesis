"""Exercise framing, recovery and closed-mode responses through real pipes."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from auditenv.client import RemoteEnv


RESET = b'{"cmd":"reset","seed":42}\n'
STEP = b'{"cmd":"step","action":{"type":"calculator","expression":"1+1"}}\n'


class ServerPipeRedTeam(unittest.TestCase):
    def server(self, data, *args, secret=None, status=0):
        env = dict(os.environ)
        env.pop("AUDITENV_SECRET", None)
        env["PYTHONINTMAXSTRDIGITS"] = "4300"
        if secret is not None:
            env["AUDITENV_SECRET"] = secret
        proc = subprocess.run([sys.executable, "-m", "auditenv.server", *map(str, args)],
                              input=data, capture_output=True, timeout=30, env=env)
        self.assertEqual(proc.returncode, status, proc.stderr.decode(errors="replace"))
        self.assertNotIn(b"Traceback", proc.stderr + proc.stdout)
        self.assertNotIn(os.fsencode(Path.cwd()), proc.stderr + proc.stdout)
        return [json.loads(line) for line in proc.stdout.splitlines()], proc.stderr.decode()

    def test_invalid_wire_lines_leave_the_server_synchronized(self):
        bad_lines = [
            (b"\xff\xfd\n", "invalid utf-8"),
            (b"x" * (10 * 1024 * 1024) + b"\n", "request too large"),
            (b'{"cmd":"reset","seed":NaN}\n', "invalid json"),
            (b'{"cmd":"reset","seed":Infinity}\n', "invalid json"),
            (b'{"cmd":"reset","seed":-Infinity}\n', "invalid json"),
            (b'{"cmd":"reset","seed":42,"config":{"x":1e999}}\n', "invalid json"),
            (b'{"cmd":"reset","cmd":"step"}\n', "invalid json"),
            (b'{"cmd":"reset","seed":42,"config":{"mode":"eval","mode":"train"}}\n', "invalid json"),
            (b"[" * 10000 + b"]" * 10000 + b"\n", "invalid json"),
            (b'{"cmd":"reset","seed":1' + b"0" * 5000 + b"}\n", "invalid json"),
            (b"\n", "invalid json"),
            (b" \t\r\n", "invalid json"),
        ]
        request = b"".join(line for line, _ in bad_lines)
        request += RESET.replace(b"\n", b"\r\n") + STEP * 64 + b'{"cmd":'
        replies, err = self.server(request)
        self.assertEqual(err, "")
        self.assertEqual(replies[:len(bad_lines)], [{"error": error} for _, error in bad_lines])
        self.assertIn("manifest", replies[len(bad_lines)]["observation"])
        steps = replies[len(bad_lines) + 1:-1]
        self.assertEqual([step["observation"]["step"] for step in steps], list(range(1, 65)))
        self.assertEqual(replies[-1], {"error": "invalid json"})

    def test_complete_request_at_eof(self):
        replies, err = self.server(RESET.rstrip(b"\n"))
        self.assertEqual(err, "")
        self.assertEqual(len(replies), 1)
        self.assertIn("observation", replies[0])

    def test_rejected_reset_and_terminal_calls_do_not_spend_steps(self):
        data = (b'{"cmd":"reset","seed":42,"config":{"mode":"eval","max_steps":2}}\n' + STEP
                + b'{"cmd":"reset","seed":77,"config":{"/tmp/test-unknown-config":true}}\n' + STEP * 3)
        replies, err = self.server(data)
        self.assertEqual(err, "")
        self.assertEqual(len(replies), 6)
        self.assertEqual(replies[2], {"error": "ValueError: unknown config keys"})
        self.assertEqual(replies[1]["observation"]["steps_remaining"], 1)
        self.assertEqual(replies[3]["observation"]["steps_remaining"], 0)
        self.assertTrue(replies[3]["truncated"])
        for reply in replies[4:]:
            self.assertEqual(reply["observation"]["error"]["code"], "episode_over")
            self.assertEqual(reply["observation"]["steps_remaining"], 0)
            self.assertEqual(reply["info"], {})

    def test_hidden_queue_ignores_client_config_and_hides_terminal_grading(self):
        for key in (None, "redteam-test-key"):
            with self.subTest(keyed=key is not None), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                hidden, log = root / "hidden.json", root / "grader.jsonl"
                hidden.write_text(json.dumps({"seeds": [734211], "config": {"mode": "train", "max_steps": 1}}))
                request = b'{"cmd":"reset","seed":42,"config":{"mode":"train","max_steps":50}}\n' + STEP * 2 + RESET
                replies, err = self.server(request, "--episodes", hidden, "--grader-log", log, secret=key)
                self.assertNotIn(temp, err)
                self.assertEqual(len(replies), 4)
                self.assertEqual(replies[0]["info"]["mode"], "eval")
                self.assertEqual(replies[0]["info"]["max_steps"], 1)
                self.assertEqual((replies[1]["reward"], replies[1]["info"], replies[1]["truncated"]), (0, {}, True))
                self.assertEqual(replies[2]["observation"]["error"]["code"], "episode_over")
                self.assertEqual(replies[3], {"error": "no more episodes"})
                wire = json.dumps(replies, allow_nan=False)
                for field in ("truth", "provenance", "seed", "issues", "evidence_sets", "expected_amount_minor"):
                    self.assertNotIn(f'"{field}":', wire)
                self.assertNotIn("734211", wire)
                self.assertEqual(len(log.read_text().splitlines()), 1)

    def test_startup_io_errors_hide_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for flag, path in (("--episodes", root / "missing.json"), ("--grader-log", root)):
                with self.subTest(flag=flag):
                    replies, err = self.server(RESET + STEP, flag, path, status=2)
                    self.assertEqual(replies, [])
                    self.assertNotIn(temp, err)

    def test_client_reports_eof_and_closes_both_pipe_handles(self):
        client = RemoteEnv()
        try:
            client.proc.stdin.write('{"cmd":"close"}\n')
            client.proc.stdin.flush()
            client.proc.wait(timeout=30)
            with self.assertRaisesRegex(RuntimeError, "server closed"):
                client.reset(42)
            client.close()
            client.close()
            self.assertTrue(client.proc.stdin.closed)
            self.assertTrue(client.proc.stdout.closed)
        finally:
            client.close()


class UnexpectedErrorTest(unittest.TestCase):
    def test_an_unexpected_exception_type_is_a_bounded_error_and_serving_continues(self):
        import io
        from unittest import mock
        from auditenv.env import AuditEnv
        from auditenv.server import serve
        out = io.StringIO()
        with mock.patch.object(AuditEnv, "step", side_effect=KeyError("/secret/path")):
            serve(io.StringIO(RESET.decode() + STEP.decode() + RESET.decode()), out)
        responses = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(len(responses), 3)
        self.assertEqual(responses[1], {"error": "internal error"})
        self.assertIn("observation", responses[2])
