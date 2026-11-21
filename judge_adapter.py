"""Jury adapter (genesis-exe.com/fintech-checks.html, "Единый способ подключения").

A thin translation layer over `auditenv`: it maps the jury's action envelope and observation shapes to the
environment's JSON contract (docs/CONTRACT.md) and back, and never chooses actions for a policy. Run it from the
repository root (the container's WORKDIR, /app), for example:

    python -c "import judge_adapter as j; j.generate_episode(7, {}, '/tmp/ep7'); env = j.make_env(); \
print(env.reset(0, {'mode': 'closed', 'episode_dir': '/tmp/ep7'})[0]['remaining_steps'])"

Grader side only (the jury process): `generate_episode`, `score_episode`, episode paths, seeds, truth and provenance.
A policy runs in its own process and receives only what `reset` and `step` return. Set `AUDITENV_SECRET` in the jury
process that generates hidden episodes: without it `episode_id` is keyed by a public constant and a policy can
recover the seed and regenerate the truth (a warning is printed on stderr).
"""

from __future__ import annotations

import json
import os
import sys

from auditenv.env import AuditEnv
from auditenv.export import export_episode
from auditenv.generator import generate, secret
from auditenv.load import load_episode
from auditenv.matcher import grade, public_ids, tolerance_of

ACTIONS = ("list_records", "get_record", "get_document", "calculator", "submit")
LIMIT_KEYS = ("max_steps", "time_limit_s")  # the only team_config keys that apply to a loaded episode
_WARNED = False
GRADER_LOG: list[dict] = []  # grader-side journal of score_episode; also appended to $AUDITENV_GRADER_LOG if set


def generate_episode(seed: int, config: dict, output_dir: str) -> None:
    """Write one episode into `output_dir`: public/ (task.txt, manifest.json, ledger.csv, invoices.jsonl,
    payments.jsonl, fx.csv, policy.json) and grader/ (truth.json, provenance.json). `config` is the generator
    config of CONTRACT §4 (errors, interacting, n_invoices, distractors, difficulty, ...)."""
    global _WARNED
    if not secret() and not _WARNED:
        _WARNED = True
        print("judge_adapter: warning: AUDITENV_SECRET is not set, so generated episodes are public: a policy can "
              "recover the seed from episode_id and regenerate the truth. Set it in the jury process that calls "
              "generate_episode (never in the policy's process).", file=sys.stderr, flush=True)
    export_episode(generate(seed, config or None), output_dir)


def make_env() -> "JudgeEnv":
    return JudgeEnv()


class JudgeEnv:
    """reset(seed, config) -> (observation, info); step({"name", "args"}) -> (observation, reward, terminated,
    truncated, info). Observations use the jury's shapes; errors are `{code, message}` with a public code."""

    def __init__(self):
        self._env = AuditEnv()

    @property
    def grader_log(self) -> list[dict]:
        """Grader-side results of finished episodes (true reward of closed runs). Never give it to a policy."""
        return self._env.grader_log

    def reset(self, seed, config: dict | None = None):
        started_at = self._env._clock()
        config = dict(config or {})
        unknown = set(config) - {"mode", "episode_dir", "team_config"}
        if unknown:
            raise ValueError(f"unknown adapter config keys: {sorted(unknown)}")
        mode = config.get("mode", "train")
        if mode not in ("train", "closed"):
            raise ValueError("mode must be 'train' or 'closed'")
        team = config.get("team_config") or {}
        if not isinstance(team, dict):
            raise ValueError("team_config must be an object")
        env_mode = "eval" if mode == "closed" else "train"  # closed: reward 0 and empty info for the policy
        if config.get("episode_dir") is not None:
            limits = {k: team[k] for k in LIMIT_KEYS if k in team}
            obs, info = self._env.reset_episode(load_episode(config["episode_dir"]), {**limits, "mode": env_mode},
                                                started_at=started_at)
        else:
            obs, info = self._env.reset(seed, {**team, "mode": env_mode}, started_at=started_at)
        first = {"task": obs["task"], "manifest": obs["manifest"], "policy": obs["policy"],
                 "remaining_steps": obs["steps_remaining"]}
        return first, {"episode_id": info["episode_id"], "mode": mode, "max_steps": info["max_steps"]}

    def step(self, action):
        name = action.get("name") if isinstance(action, dict) else None
        args = action.get("args", {}) if isinstance(action, dict) else None
        if not isinstance(name, str) or not isinstance(args, dict) or set(action) - {"name", "args"} or "type" in args:
            inner = {"type": None}  # a malformed envelope is still one step with a bounded error
        else:
            inner = {**args, "type": name}
        obs, reward, terminated, truncated, info = self._env.step(inner)
        return ({"result": _result(name, obs["result"]) if obs["error"] is None else None, "error": obs["error"],
                 "remaining_steps": obs["steps_remaining"]}, reward, terminated, truncated, info)


def _result(name, result):
    """The environment's result object -> the value the jury's protocol names for each action."""
    if result is None:
        return None
    if name == "list_records":
        return {"records": result["rows"], "next_cursor": result["next_cursor"]}
    if name == "get_record":
        return result["record"]
    if name == "get_document":
        return result["document"]
    if name == "calculator":
        return result["value"]
    if name == "submit":
        return {"accepted": True}  # no correctness signal; train mode also reports an invalid structure as an error
    return result


def score_episode(episode_dir: str, findings: dict, inspection_steps: int) -> dict:
    """Grade `findings` (a findings.json object) against the episode's truth with the shared matcher and reward
    (CONTRACT §6). Invalid structure: return -1, the other fields null, the error goes to the grader log."""
    if isinstance(inspection_steps, bool) or not isinstance(inspection_steps, int) or inspection_steps < 0:
        raise ValueError("inspection_steps must be a non-negative int")
    ep = load_episode(episode_dir)
    res = grade(ep["truth"], findings, ep["manifest"]["episode_id"], inspection_steps,
                public_ids(ep["tables"]), tolerance_of(ep["policy"]))
    entry = {"episode_id": ep["manifest"]["episode_id"], "inspection_steps": inspection_steps,
             **{k: res[k] for k in ("valid", "error", "tp", "fp", "fn", "precision", "recall", "f1", "reward")}}
    GRADER_LOG.append(entry)
    path = os.environ.get("AUDITENV_GRADER_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
    if not res["valid"]:
        return {"tp": None, "fp": None, "fn": None, "precision": None, "recall": None, "f1": None, "return": -1.0}
    return {"tp": res["tp"], "fp": res["fp"], "fn": res["fn"], "precision": res["precision"],
            "recall": res["recall"], "f1": res["f1"], "return": res["reward"]}
