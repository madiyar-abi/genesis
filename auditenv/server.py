"""Out-of-process environment/grader: JSON lines over stdin/stdout.

The policy process only ever sees observations. Truth, provenance, seeds and grading
results stay in this process; results are appended to --grader-log (JSONL).

    python -m auditenv.server --grader-log grader.jsonl [--episodes hidden.json]

Requests:  {"cmd": "reset", "seed": int, "config": {...}}   (seed/config ignored with --episodes)
           {"cmd": "step", "action": {...}}
           {"cmd": "close"}
Responses: {"observation", "info"} | {"observation", "reward", "terminated", "truncated", "info"}
           | {"error": "..."}
With --episodes FILE (kept secret from the agent) — either the configs/*.json format
`{"episodes": [{"seed": int, "config": {...}}, ...]}` (per-episode configs, e.g. 5 clean + 5 interacting)
or `{"seeds": [...], "config": {...}}` —
every reset loads the next hidden episode; after the last one reset returns {"error": "no more episodes"}.
"""

from __future__ import annotations

import argparse
import json
import sys

from .env import AuditEnv
from .run import load_episodes

MAX_LINE: int = 1 << 20  # 1 MiB


def serve(inp, out, grader_log: str | None = None, episodes: list[tuple[int, dict]] | None = None) -> None:
    env = AuditEnv()
    queue = list(episodes) if episodes is not None else None
    logged = 0

    def flush_log():
        nonlocal logged
        if grader_log and len(env.grader_log) > logged:
            with open(grader_log, "a") as fh:
                for rec in env.grader_log[logged:]:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
            logged = len(env.grader_log)

    def send_resp(resp: dict) -> None:
        data = json.dumps(resp) + "\n"
        try:
            out.write(data)
        except TypeError:
            out.write(data.encode("utf-8"))
        out.flush()

    for line in inp:
        if isinstance(line, bytes):
            if len(line) > MAX_LINE:
                send_resp({"error": "request too large"})
                continue
            try:
                line_str = line.decode("utf-8")
            except UnicodeDecodeError:
                send_resp({"error": "invalid utf-8"})
                continue
        elif isinstance(line, str):
            if len(line) > MAX_LINE or len(line.encode("utf-8")) > MAX_LINE:
                send_resp({"error": "request too large"})
                continue
            line_str = line
        else:
            send_resp({"error": "invalid input type"})
            continue

        line_str = line_str.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
            cmd = req.get("cmd")
            if cmd == "reset":
                env.abandon()
                flush_log()
                if queue is not None:
                    if not queue:
                        send_resp({"error": "no more episodes"})
                        continue
                    seed, config = queue.pop(0)
                    config = {**config, "mode": config.get("mode", "eval")}
                else:
                    seed, config = int(req["seed"]), req.get("config") or {}
                obs, info = env.reset(seed, config)
                resp = {"observation": obs, "info": info}
            elif cmd == "step":
                obs, reward, terminated, truncated, info = env.step(req.get("action"))
                resp = {"observation": obs, "reward": reward, "terminated": terminated,
                        "truncated": truncated, "info": info}
                flush_log()
            elif cmd == "close":
                break
            else:
                resp = {"error": "unknown cmd"}
        except Exception as e:  # bounded error, never a traceback with internals
            resp = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        send_resp(resp)
    env.abandon()  # close / EOF with an open episode: graded as truncated, empty answer
    flush_log()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grader-log", help="append grading results here (JSONL)")
    ap.add_argument("--episodes", help="hidden episode list {seeds, config}; resets ignore client seeds")
    args = ap.parse_args(argv)
    episodes = load_episodes(args.episodes) if args.episodes else None
    inp = getattr(sys.stdin, "buffer", sys.stdin)
    serve(inp, sys.stdout, args.grader_log, episodes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
