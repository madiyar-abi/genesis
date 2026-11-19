"""Client for auditenv.server: same reset/step API as AuditEnv, environment in a subprocess."""

from __future__ import annotations

import json
import subprocess
import sys


class RemoteEnv:
    def __init__(self, grader_log: str | None = None, episodes: str | None = None, python: str = sys.executable):
        cmd = [python, "-m", "auditenv.server"]
        if grader_log:
            cmd += ["--grader-log", grader_log]
        if episodes:
            cmd += ["--episodes", episodes]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def _call(self, req: dict) -> dict:
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        resp = json.loads(self.proc.stdout.readline())
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp

    def reset(self, seed: int | None = None, config: dict | None = None):
        resp = self._call({"cmd": "reset", "seed": seed, "config": config})
        return resp["observation"], resp["info"]

    def step(self, action: dict):
        r = self._call({"cmd": "step", "action": action})
        return r["observation"], r["reward"], r["terminated"], r["truncated"], r["info"]

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.stdin.write(json.dumps({"cmd": "close"}) + "\n")
            self.proc.stdin.flush()
            self.proc.wait(timeout=10)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
