import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

from auditenv.client import RemoteEnv
from auditenv.env import AuditEnv
from auditenv.generator import ISSUE_TYPES
from auditenv.server import MAX_LINE, serve

CFG = {"errors": {t: 1 for t in ISSUE_TYPES}}


class ScriptedPolicy:
    """Deterministic, observation-only: list two pages, read one record, submit one guess."""

    def __init__(self):
        self.n = 0

    def reset(self, obs):
        self.ep = obs["manifest"]["episode_id"]
        self.base = obs["manifest"]["base_currency"]

    def act(self, obs):
        self.n += 1
        if self.n == 1:
            return {"type": "list_records", "table": "invoices", "cursor": None, "limit": 50}
        if self.n == 2:
            self.first = obs["result"]["rows"][0]
            return {"type": "get_document", "doc_id": self.first["doc_id"]}
        if self.n == 3:
            return {"type": "get_record", "table": "ledger", "id": "missing"}
        return {"type": "submit", "findings": {"episode_id": self.ep, "findings": [
            {"type": "period_cutoff", "affected_ids": [self.first["invoice_id"]], "claimed_amount_minor": 1,
             "currency": self.base, "evidence_ids": [self.first["doc_id"]], "explanation": "guess"}]}}


def play(env, seed, config):
    pol = ScriptedPolicy()
    obs, info = env.reset(seed, config)
    pol.reset(obs)
    out = [obs]
    while True:
        obs, r, term, trunc, info = env.step(pol.act(obs))
        out.append([obs, r, term, trunc, info])
        if term or trunc:
            return json.loads(json.dumps(out))


class ServerTest(unittest.TestCase):
    def test_remote_equals_local_in_train_mode(self):
        local = play(AuditEnv(), 21, CFG)
        with RemoteEnv() as env:
            remote = play(env, 21, CFG)
        self.assertEqual(local, remote)

    def test_eval_mode_hides_reward_and_logs_grader_side(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "grader.jsonl")
            hidden = os.path.join(d, "hidden.json")
            with open(hidden, "w") as fh:
                json.dump({"seeds": [31, 32], "config": CFG}, fh)
            with RemoteEnv(grader_log=log, episodes=hidden) as env:
                for _ in range(2):
                    traj = play(env, 0, None)  # client seed is ignored
                    for obs, r, term, trunc, info in traj[1:]:
                        self.assertEqual(r, 0.0)
                        self.assertEqual(info, {})
                    text = json.dumps(traj)
                    for key in ("truth", "evidence_sets", "expected_amount_minor", "provenance", "seed"):
                        self.assertNotIn(key, text)
                with self.assertRaises(RuntimeError):
                    env.reset(0, None)
            with open(log) as fh:
                recs = [json.loads(line) for line in fh]
            self.assertEqual(len(recs), 2)
            self.assertTrue(all("reward" in r and "f1" in r for r in recs))

    def test_in_process_bytes_io(self):
        too_large = b"x" * (MAX_LINE + 10) + b"\n"
        bad_utf8 = b"\xff\xfe\xfa\n"
        reset_cmd = json.dumps({"cmd": "reset", "seed": 0, "config": {}}).encode("utf-8") + b"\n"
        close_cmd = json.dumps({"cmd": "close"}).encode("utf-8") + b"\n"

        inp = io.BytesIO(too_large + bad_utf8 + reset_cmd + close_cmd)
        out = io.BytesIO()
        serve(inp, out)

        lines = [json.loads(line) for line in out.getvalue().splitlines() if line]
        self.assertEqual(lines[0], {"error": "request too large"})
        self.assertEqual(lines[1], {"error": "invalid utf-8"})
        self.assertIn("observation", lines[2])
        self.assertIn("info", lines[2])

    def test_oversized_line_is_read_in_bounded_chunks(self):
        class Tracking(io.BytesIO):
            biggest = 0

            def readline(self, size=-1):
                line = super().readline(size)
                Tracking.biggest = max(Tracking.biggest, len(line))
                return line

        reset_cmd = json.dumps({"cmd": "reset", "seed": 0, "config": {}}).encode("utf-8") + b"\n"
        inp = Tracking(b"y" * (5 * MAX_LINE) + b"\n" + reset_cmd)
        out = io.BytesIO()
        serve(inp, out)
        lines = [json.loads(line) for line in out.getvalue().splitlines() if line]
        self.assertEqual(lines[0], {"error": "request too large"})
        self.assertIn("observation", lines[1])
        self.assertLessEqual(Tracking.biggest, MAX_LINE + 1)

    def test_in_process_string_io(self):
        too_large = "x" * (MAX_LINE + 10) + "\n"
        reset_cmd = json.dumps({"cmd": "reset", "seed": 0, "config": {}}) + "\n"
        close_cmd = json.dumps({"cmd": "close"}) + "\n"

        inp = io.StringIO(too_large + reset_cmd + close_cmd)
        out = io.StringIO()
        serve(inp, out)

        lines = [json.loads(line) for line in out.getvalue().splitlines() if line]
        self.assertEqual(lines[0], {"error": "request too large"})
        self.assertIn("observation", lines[1])
        self.assertIn("info", lines[1])

    def test_subprocess_size_and_invalid_utf8_recovery(self):
        proc = subprocess.Popen(
            [sys.executable, "-m", "auditenv.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=0,
        )
        try:
            # 1. Send 10 MB line
            ten_mb = b"x" * (10 * 1024 * 1024) + b"\n"
            proc.stdin.write(ten_mb)
            proc.stdin.flush()
            resp1 = json.loads(proc.stdout.readline())
            self.assertEqual(resp1, {"error": "request too large"})

            # 2. Send invalid UTF-8
            proc.stdin.write(b"\xff\xfe\xfa\n")
            proc.stdin.flush()
            resp2 = json.loads(proc.stdout.readline())
            self.assertEqual(resp2, {"error": "invalid utf-8"})

            # 3. Send valid reset -> server keeps serving and returns observation
            proc.stdin.write(json.dumps({"cmd": "reset", "seed": 0, "config": {}}).encode("utf-8") + b"\n")
            proc.stdin.flush()
            resp3 = json.loads(proc.stdout.readline())
            self.assertIn("observation", resp3)
            self.assertIn("info", resp3)

            # 4. Clean close
            proc.stdin.write(json.dumps({"cmd": "close"}).encode("utf-8") + b"\n")
            proc.stdin.flush()
            proc.stdin.close()
            proc.stdout.close()
            proc.wait(timeout=5)
            self.assertEqual(proc.returncode, 0)
        finally:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
            if proc.stdout and not proc.stdout.closed:
                proc.stdout.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait()


if __name__ == "__main__":
    unittest.main()
