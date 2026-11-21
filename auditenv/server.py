"""Out-of-process environment/grader: JSON lines over stdin/stdout.

The policy process only ever sees observations. Truth, provenance, seeds and grading
results stay in this process; results are appended to --grader-log (JSONL).

    AUDITENV_SECRET=<grader key> python -m auditenv.server --grader-log grader.jsonl [--episodes hidden.json]

Set AUDITENV_SECRET in this process for any hidden run: without it the generator and episode_id are
public, so a policy can recover each seed from episode_id and regenerate the truth. The server then
warns on stderr; --public silences that for episode lists that are public on purpose (smoke tests, demo).

Requests:  {"cmd": "reset", "seed": int, "config": {...}}   (seed/config ignored with --episodes)
           {"cmd": "step", "action": {...}}
           {"cmd": "close"}
Responses: {"observation", "info"} | {"observation", "reward", "terminated", "truncated", "info"}
           | {"error": "..."}
With --episodes FILE (kept secret from the agent) — either the configs/*.json format
`{"episodes": [{"seed": int, "config": {...}}, ...]}` (per-episode configs, e.g. 5 clean + 5 interacting)
or `{"seeds": [...], "config": {...}}` —
every reset loads the next hidden episode in eval mode; after the last one reset returns {"error": "no more episodes"}.
On close or EOF the open episode and every hidden episode not yet reset are logged as abandoned (empty answer).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

from .env import AuditEnv
from .generator import secret
from .run import load_episodes

MAX_LINE: int = 1 << 20  # 1 MiB
TOO_LARGE = object()


def _finite_float(literal: str) -> float:
    value = float(literal)
    if not math.isfinite(value):
        raise ValueError("nonfinite number")
    return value


def _unique_object(pairs: list[tuple]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate object key")
        obj[key] = value
    return obj


def _hidden_config(config: dict) -> dict:
    if config.get("mode", "eval") not in ("train", "eval"):
        raise ValueError("mode must be 'train' or 'eval'")
    return {**config, "mode": "eval"}


def _validation_error(error: ValueError) -> str:
    # Unknown config keys are client-supplied and can contain paths or control characters.
    message = str(error)
    if message.startswith("unknown config keys:"):
        return "unknown config keys"
    return message[:160]


def _lines(inp):
    """Request lines, reading at most MAX_LINE + 1 bytes/chars at a time: an over-long line is drained in
    bounded chunks and yielded as TOO_LARGE, so memory stays bounded whatever the client sends."""
    if not hasattr(inp, "readline"):
        yield from inp
        return
    while True:
        line = inp.readline(MAX_LINE + 1)
        if not line:
            return
        nl = b"\n" if isinstance(line, bytes) else "\n"
        if len(line) > MAX_LINE:
            while not line.endswith(nl):
                line = inp.readline(MAX_LINE)
                if not line:
                    break
            yield TOO_LARGE
        else:
            yield line


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
            try:
                out.write(data)
            except TypeError:
                out.write(data.encode("utf-8"))
            out.flush()
        except (BrokenPipeError, ConnectionResetError) as e:  # the policy process is gone
            raise _ClientGone from e

    try:
        _serve_lines(inp, env, queue, flush_log, send_resp)
    except _ClientGone:
        pass  # graded below like a close: the policy cannot skip episodes by killing its pipes
    finally:
        env.abandon()  # close / EOF with an open episode: graded as truncated, empty answer
        for seed, config in queue or ():  # hidden episodes never reset: graded the same way, so none is skipped
            env.reset(seed, _hidden_config(config))
            env.abandon()
        flush_log()


class _ClientGone(Exception):
    """The policy closed its end of the pipe; stop serving and grade what is left."""


def _serve_lines(inp, env, queue, flush_log, send_resp) -> None:
    for line in _lines(inp):
        if line is TOO_LARGE:
            send_resp({"error": "request too large"})
            continue
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
        try:
            req = json.loads(line_str, object_pairs_hook=_unique_object,
                             parse_float=_finite_float, parse_constant=_finite_float)
        except (ValueError, RecursionError):
            send_resp({"error": "invalid json"})
            continue
        if not isinstance(req, dict):
            send_resp({"error": "request must be a JSON object"})
            continue
        try:
            cmd = req.get("cmd")
            if cmd == "reset":
                if queue is not None:
                    if not queue:
                        env.abandon()
                        flush_log()
                        send_resp({"error": "no more episodes"})
                        continue
                    seed, config = queue.pop(0)
                    config = _hidden_config(config)
                else:
                    seed, config = req.get("seed"), req.get("config")
                obs, info = env.reset(seed, config, abandon_open=True)  # a rejected reset keeps the open episode
                flush_log()
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
        except ValueError as e:
            resp = {"error": f"ValueError: {_validation_error(e)}"}
        except RuntimeError:
            resp = {"error": "RuntimeError: call reset() first"}
        send_resp(resp)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grader-log", help="append grading results here (JSONL)")
    ap.add_argument("--episodes", help="hidden episode list {seeds, config}; resets ignore client seeds")
    ap.add_argument("--public", action="store_true",
                    help="the episode list is public on purpose: no warning when AUDITENV_SECRET is unset")
    args = ap.parse_args(argv)
    if args.episodes and not secret() and not args.public:
        print("auditenv.server: warning: AUDITENV_SECRET is not set, so these episodes are public: a policy can "
              "recover each seed from episode_id and regenerate the truth. Set it in the grader process "
              "(README, closed run) or pass --public for a deliberately public list.", file=sys.stderr, flush=True)
    try:
        episodes = load_episodes(args.episodes) if args.episodes else None
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print("auditenv.server: cannot read the hidden episode list", file=sys.stderr, flush=True)
        return 2
    for i, (seed, config) in enumerate(episodes or (), start=1):  # fail fast: a typo must not surface at close
        try:
            AuditEnv().reset(seed, _hidden_config(config))
        except ValueError as e:
            print(f"auditenv.server: hidden episode {i}: {_validation_error(e)}", file=sys.stderr, flush=True)
            return 2
    inp = getattr(sys.stdin, "buffer", sys.stdin)
    try:
        if args.grader_log:
            with open(args.grader_log, "a"):
                pass
        serve(inp, sys.stdout, args.grader_log, episodes)
    except OSError:
        print("auditenv.server: cannot write the grader log or response", file=sys.stderr, flush=True)
        return 2
    try:
        sys.stdout.flush()
    except BrokenPipeError:  # the policy is gone; keep the interpreter's exit flush quiet
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
