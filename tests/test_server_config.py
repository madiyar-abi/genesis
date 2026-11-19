"""Tests for bad reset configs over the out-of-process server."""

import json
import subprocess
import sys
import unittest


class ServerConfigTest(unittest.TestCase):
    def test_bad_reset_configs_over_server_subprocess(self):
        proc = subprocess.Popen(
            [sys.executable, "-m", "auditenv.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            bufsize=0,
        )
        bad_configs = [
            {"errors": "x"},
            {"errors": 5},
            {"interacting": [1]},
            {"foo": 1},
            {"max_steps": 0},
            {"mode": "test"},
            {"n_invoices": 9},
            {"difficulty": "expert"},
        ]
        try:
            for cfg in bad_configs:
                with self.subTest(config=cfg):
                    req = json.dumps({"cmd": "reset", "seed": 1, "config": cfg}) + "\n"
                    proc.stdin.write(req.encode("utf-8"))
                    proc.stdin.flush()
                    line = proc.stdout.readline()
                    resp = json.loads(line)
                    self.assertIsInstance(resp, dict)
                    self.assertEqual(list(resp.keys()), ["error"])
                    err = resp["error"]
                    self.assertIsInstance(err, str)
                    self.assertLessEqual(len(err), 200)
                    self.assertNotIn("Traceback", err)
                    self.assertNotIn("/", err)

            valid_req = json.dumps({"cmd": "reset", "seed": 1, "config": {}}) + "\n"
            proc.stdin.write(valid_req.encode("utf-8"))
            proc.stdin.flush()
            valid_resp = json.loads(proc.stdout.readline())
            self.assertIn("observation", valid_resp)

            # Clean close
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
