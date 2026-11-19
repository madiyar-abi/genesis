"""Gymnasium-style JSON environment (CONTRACT §4). Read-only tools over one generated episode."""

from __future__ import annotations

import copy
import time

from . import calculator
from .generator import generate
from .experimental import experimental_reward
from .matcher import grade, public_summary

TABLES = {"ledger": "row_id", "invoices": "invoice_id", "payments": "payment_id", "fx": "fx_id"}
PAGE_MAX = 50
DEFAULTS = {"mode": "train", "max_steps": 100, "time_limit_s": 60.0}
CONFIG_KEYS = {"mode", "max_steps", "time_limit_s", "errors", "interacting", "n_invoices", "distractors",
               "transform_seed"}
TOOLS = [
    {"type": "list_records", "params": {"table": "ledger|invoices|payments|fx", "cursor": "null|str",
                                        "limit": "int<=50"},
     "returns": "{rows, next_cursor, total}; invoice rows omit line_items"},
    {"type": "get_record", "params": {"table": "ledger|invoices|payments|fx", "id": "str"},
     "returns": "{record}"},
    {"type": "get_document", "params": {"doc_id": "str"}, "returns": "{kind, document}"},
    {"type": "calculator", "params": {"expression": "str: + - * / ( ) and decimals only"},
     "returns": "{value}"},
    {"type": "submit", "params": {"findings": "{episode_id, findings:[...]}"}, "returns": "ends the episode"},
]


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


class AuditEnv:
    """One episode at a time. `grader_log` is grader-side state; never send it to a policy."""

    def __init__(self):
        self._ep = None
        self.grader_log: list[dict] = []

    # ------------------------------------------------------------------ API
    def reset(self, seed: int, config: dict | None = None):
        config = dict(config or {})
        unknown = set(config) - CONFIG_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        cfg = {**DEFAULTS, **config}
        if cfg["mode"] not in ("train", "eval"):
            raise ValueError("mode must be 'train' or 'eval'")
        if isinstance(cfg["max_steps"], bool) or not (isinstance(cfg["max_steps"], int) and 1 <= cfg["max_steps"] <= 100):
            raise ValueError("max_steps must be an int in [1, 100]")
        tl = cfg["time_limit_s"]
        if isinstance(tl, bool) or not isinstance(tl, (int, float)) or tl < 0:
            raise ValueError("time_limit_s must be a non-negative number")
        self._cfg = cfg
        self._ep = generate(seed, config)
        t = self._ep["tables"]
        self._index = {name: {r[key]: r for r in t[name]} for name, key in TABLES.items()}
        self._docs = {d["doc_id"]: ("invoice", d) for d in t["invoices"]}
        self._docs.update({d["doc_id"]: ("payment", d) for d in t["payments"]})
        self._steps = 0
        self._done = False
        self._terminated = self._truncated = False
        self._start = time.monotonic()
        self.result = None
        obs = {"task": self._ep["task"], "manifest": copy.deepcopy(self._ep["manifest"]),
               "policy": copy.deepcopy(self._ep["policy"]), "tools": copy.deepcopy(TOOLS),
               "steps_remaining": cfg["max_steps"]}
        info = {"episode_id": self._ep["episode_id"], "mode": cfg["mode"], "max_steps": cfg["max_steps"]}
        return obs, info

    def abandon(self) -> None:
        """Grade an open episode as truncated with an empty answer (server: reset/close mid-episode),
        so a policy cannot skip hard hidden episodes without a score."""
        if self._ep is not None and not self._done:
            self._done, self._truncated = True, True
            self._finish({"episode_id": self.episode_id, "findings": []}, self._steps, "abandoned")

    @property
    def episode_id(self) -> str:
        return self._ep["episode_id"]

    def step(self, action):
        if self._ep is None:
            raise RuntimeError("call reset() first")
        max_steps = self._cfg["max_steps"]
        if self._done:
            obs = {"step": self._steps, "steps_remaining": max_steps - self._steps, "result": None,
                   "error": {"code": "episode_over", "message": "episode has ended; call reset()"}}
            return obs, 0.0, self._terminated, self._truncated, {}
        self._steps += 1
        result, error, reward, terminated, truncated, info = None, None, 0.0, False, False, {}
        timed_out = time.monotonic() - self._start > float(self._cfg["time_limit_s"])
        if timed_out:
            error = {"code": "time_limit", "message": "time limit reached"}
        else:
            try:
                kind = action.get("type") if isinstance(action, dict) else None
                if kind == "submit":
                    terminated = True
                    res = self._finish(action.get("findings"), self._steps - 1, "submit")
                    if self._cfg["mode"] == "train":
                        reward, info = res["reward"], public_summary(res)
                        result = {"submitted": True, "accepted": res["valid"]}
                        if not res["valid"]:
                            error = {"code": "invalid_findings", "message": res["error"]}
                    else:
                        result = {"submitted": True}
                else:
                    result = self._tool(kind, action)
            except ToolError as e:
                error = {"code": e.code, "message": e.message}
            except Exception:  # never crash on malformed input: bounded error, the step still counts
                error = {"code": "bad_params", "message": "malformed action"}
        if not terminated and (timed_out or self._steps >= max_steps):
            truncated = True
            res = self._finish({"episode_id": self.episode_id, "findings": []}, self._steps,
                               "time_limit" if timed_out else "step_limit")
            if self._cfg["mode"] == "train":
                reward, info = res["reward"], public_summary(res)
        self._done = terminated or truncated
        self._terminated, self._truncated = terminated, truncated
        obs = {"step": self._steps, "steps_remaining": max_steps - self._steps, "result": result, "error": error}
        return obs, reward, terminated, truncated, info

    # ------------------------------------------------------------------ internals
    def _finish(self, submission, inspection_steps: int, how: str) -> dict:
        res = grade(self._ep["truth"], submission, self.episode_id, inspection_steps)
        # experimental materiality-weighted reward: grader-side only, reported next to the shared one
        res["experimental_reward"] = experimental_reward(
            res, self._ep["truth"], submission["findings"] if res["valid"] else [])
        self.result = res
        self.grader_log.append({"episode_id": self.episode_id, "end": how, "steps": self._steps,
                                "elapsed_s": round(time.monotonic() - self._start, 4), **res})
        return res

    def _tool(self, kind, action: dict):
        if kind == "list_records":
            return self._list(action)
        if kind == "get_record":
            table = self._table(action.get("table"))
            rid = action.get("id")
            if not isinstance(rid, str):
                raise ToolError("bad_params", "id must be a string")
            rec = self._index[table].get(rid)
            if rec is None:
                raise ToolError("not_found", f"no record with this id in table '{table}'")
            return {"record": copy.deepcopy(rec)}
        if kind == "get_document":
            doc_id = action.get("doc_id")
            if not isinstance(doc_id, str):
                raise ToolError("bad_params", "doc_id must be a string")
            hit = self._docs.get(doc_id)
            if hit is None:
                raise ToolError("not_found", "no document with this doc_id")
            return {"kind": hit[0], "document": copy.deepcopy(hit[1])}
        if kind == "calculator":
            expr = action.get("expression")
            try:
                return {"value": calculator.evaluate(expr)}
            except calculator.CalculatorError as e:
                raise ToolError("calc_error", str(e)[:100]) from None
        raise ToolError("unknown_action", "unknown action type; see tools in the first observation")

    def _table(self, table):
        if not isinstance(table, str) or table not in TABLES:
            raise ToolError("unknown_table", "table must be one of ledger, invoices, payments, fx")
        return table

    def _list(self, action: dict) -> dict:
        table = self._table(action.get("table"))
        limit = action.get("limit", PAGE_MAX)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ToolError("bad_params", "limit must be a positive int")
        limit = min(limit, PAGE_MAX)
        rows = self._ep["tables"][table]
        cursor = action.get("cursor")
        offset = 0
        if cursor is not None:
            if not (isinstance(cursor, str) and cursor.startswith(table + ":") and cursor[len(table) + 1:].isascii()
                    and cursor[len(table) + 1:].isdigit()):
                raise ToolError("bad_params", "invalid cursor")
            offset = int(cursor[len(table) + 1:])
            if offset > len(rows):
                raise ToolError("bad_params", "invalid cursor")
        page = copy.deepcopy(rows[offset:offset + limit])
        if table == "invoices":
            for r in page:
                r.pop("line_items", None)
        end = offset + len(page)
        return {"rows": page, "next_cursor": f"{table}:{end}" if end < len(rows) else None, "total": len(rows)}
