"""Client for auditenv.server: same reset/step API as AuditEnv, environment in a subprocess."""

from __future__ import annotations

import json
import subprocess
import sys


class RemoteEnv:
    def __init__(self, grader_log: str | None = None, episodes: str | None = None, python: str = sys.executable,
                 public: bool = False):
        cmd = self.command(grader_log, episodes, python, public)
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    @staticmethod
    def command(grader_log: str | None = None, episodes: str | None = None, python: str = sys.executable,
                public: bool = False) -> list[str]:
        """Server command line; `public=True` marks a deliberately public episode list (no missing-key warning)."""
        cmd = [python, "-m", "auditenv.server"]
        if grader_log:
            cmd += ["--grader-log", grader_log]
        if episodes:
            cmd += ["--episodes", episodes]
        if public:
            cmd.append("--public")
        return cmd

    def _call(self, req: dict) -> dict:
        if self.proc.poll() is not None or self.proc.stdin.closed:
            raise RuntimeError("server closed")
        try:
            self.proc.stdin.write(json.dumps(req) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise RuntimeError("server closed") from None
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("server closed")
        resp = json.loads(line)
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
        try:
            if self.proc.poll() is None and not self.proc.stdin.closed:
                try:
                    self.proc.stdin.write(json.dumps({"cmd": "close"}) + "\n")
                    self.proc.stdin.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                self.proc.wait(timeout=10)
        finally:
            try:
                self.proc.stdin.close()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                self.proc.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
