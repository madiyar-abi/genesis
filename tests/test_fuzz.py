"""Seeded randomized checks for the JSON step contract."""

from collections import Counter
import json
import random
import unittest

from auditenv.env import AuditEnv
from auditenv.schema import ISSUE_TYPES

_TABLES = ("ledger", "invoices", "payments", "fx")
_PARAMS = {
    "table": _TABLES,
    "id": ("missing-record",),
    "doc_id": ("missing-document",),
    "cursor": (None, "ledger:0", "invoices:1", "ledger:999", "ledger:²"),
    "limit": (1, 50, 200),
    "expression": ("(1.10 + 2.205) * 3", "1/0", "3e1", "7" * 201),
}
_ACTION_FIELDS = {
    "list_records": ("table", "cursor", "limit"),
    "get_record": ("table", "id"),
    "get_document": ("doc_id",),
    "calculator": ("expression",),
}
_INPUTS = (None, True, False, 0, -1, 3.5, [], ["ledger"], {"a": {"b": 1}},
           "", "🧾", "x" * 5000)
_ERROR_CODES = {
    "unknown_action", "bad_params", "unknown_table", "not_found", "calc_error",
    "episode_over", "time_limit", "invalid_findings",
}


def _action(rng, seen):
    if rng.random() < 0.15:
        return rng.choice(seen)
    if rng.random() < 0.15:
        return rng.choice((*_INPUTS, {}, {"type": rng.choice(_INPUTS)}))

    kind = rng.choice(tuple(_ACTION_FIELDS))
    action = {"type": kind}
    for field in _ACTION_FIELDS[kind]:
        if rng.random() < 0.85:
            action[field] = rng.choice((*_PARAMS[field], *_INPUTS))
    return action


def _submission(rng, episode_id):
    finding = {
        "type": rng.choice(ISSUE_TYPES),
        "affected_ids": ["guess"],
        "claimed_amount_minor": rng.randrange(100_000),
        "currency": "USD",
        "evidence_ids": [],
    }
    payload = {"episode_id": episode_id, "findings": rng.choice(([], [finding]))}
    if rng.random() < 0.5:
        key = rng.choice(("episode_id", "findings"))
        payload[key] = rng.choice((None, {"wrong": "shape"}, 123, [None]))
    return {"type": "submit", "findings": payload}


class EnvFuzzTests(unittest.TestCase):
    def test_seeded_actions_preserve_step_contract(self):
        rng = random.Random(20261119)
        env = AuditEnv()
        failures = Counter()
        examples = {}
        attempted = 0
        for episode in range(40):
            first, _ = env.reset(episode, {"mode": "train" if episode % 2 else "eval"})
            episode_id = first["manifest"]["episode_id"]
            seen = [
                {"type": "list_records", "table": "invoices", "limit": 3},
                {"type": "calculator", "expression": "1/3"},
            ]
            submit_at = rng.randrange(90, 101) if episode % 4 else None
            for step in range(1, 101):
                action = _submission(rng, episode_id) if step == submit_at else _action(rng, seen)
                attempted += 1
                try:
                    observation, reward, terminated, truncated, _ = env.step(action)
                except Exception as exc:
                    key = (type(exc).__name__, str(exc))
                    failures[key] += 1
                    examples.setdefault(key, (episode, step, action))
                    continue

                self.assertEqual(set(observation), {"step", "steps_remaining", "result", "error"})
                self.assertEqual(observation["step"], step)
                self.assertEqual(observation["steps_remaining"], first["steps_remaining"] - step)
                json.dumps(observation, allow_nan=False)
                error = observation["error"]
                if error is not None:
                    self.assertEqual(set(error), {"code", "message"})
                    self.assertIn(error["code"], _ERROR_CODES)
                    self.assertIsInstance(error["message"], str)
                    self.assertLessEqual(len(error["message"]), 200)

                if terminated or truncated:
                    self.assertGreaterEqual(reward, -1.0)
                    self.assertLessEqual(reward, 1.0)
                    after, _, after_terminated, after_truncated, _ = env.step(None)
                    self.assertEqual(after["error"]["code"], "episode_over")
                    self.assertEqual(after["steps_remaining"], observation["steps_remaining"])
                    self.assertEqual((after_terminated, after_truncated), (terminated, truncated))
                    break

                self.assertEqual(reward, 0.0)
                result = observation["result"] or {}
                if result.get("rows") and action.get("table") == "invoices":
                    row = result["rows"][0]
                    seen.extend((
                        {"type": "get_record", "table": "invoices", "id": row["invoice_id"]},
                        {"type": "get_document", "doc_id": row["doc_id"]},
                    ))

        self.assertGreaterEqual(attempted, 3000)
        self.assertFalse(failures, "\n".join(
            f"{count} × {kind}: {message}; first (episode, step, action)={examples[key]!r}"
            for key, count in failures.items() for kind, message in [key]
        ))
