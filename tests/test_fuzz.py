"""Seeded randomized checks for the JSON step contract."""

from collections import Counter
import json
import random
import platform
import time
import unittest

from auditenv.env import AuditEnv, TABLES
from tests.test_schemas import _matches, load_schemas

_SCHEMAS = load_schemas()
_ACTION_SCHEMA = _SCHEMAS["action.schema.json"]
_OBSERVATION_SCHEMA = _SCHEMAS["observation.schema.json"]
_FINDINGS_SCHEMA = _SCHEMAS["findings.schema.json"]

_BRANCHES = {
    branch["properties"]["type"]["const"]: branch
    for branch in _ACTION_SCHEMA["oneOf"]
}
_TABLES = tuple(_BRANCHES["list_records"]["properties"]["table"]["enum"])
_CALC_MAX_LEN = _BRANCHES["calculator"]["properties"]["expression"]["maxLength"]

_FINDINGS_ITEMS = _FINDINGS_SCHEMA["properties"]["findings"]["items"]["properties"]
_ISSUE_TYPES = tuple(_FINDINGS_ITEMS["type"]["examples"])

_INPUTS = (
    None, True, False, 0, -1, 3.5, [], ["ledger"], {"a": {"b": 1}},
    "", "🧾", "x" * 5000,
)
_ERROR_CODES = {
    "unknown_action", "bad_params", "unknown_table", "not_found", "calc_error",
    "episode_over", "time_limit", "invalid_findings",
}


def _make_valid_action(kind, rng, episode_id, seen_records, seen_docs):
    if kind == "list_records":
        act = {"type": "list_records", "table": rng.choice(_TABLES)}
        act["limit"] = rng.choice((1, 2, 3, 5, 10))
        if rng.random() < 0.25:
            act["cursor"] = rng.choice((None, "invoices:0", "ledger:1"))
        return act
    if kind == "get_record":
        tbl = rng.choice(_TABLES)
        pool = seen_records.get(tbl) or ["missing-record"]
        return {"type": "get_record", "table": tbl, "id": rng.choice(pool)}
    if kind == "get_document":
        pool = seen_docs or ["missing-document"]
        return {"type": "get_document", "doc_id": rng.choice(pool)}
    if kind == "calculator":
        expr = rng.choice(["1+1", "(1.10 + 2.205) * 3", "100 - 45", "1/0", "3e1", "2 * (3 + 4)"])
        return {"type": "calculator", "expression": expr}
    if kind == "submit":
        finding = {
            "type": rng.choice(_ISSUE_TYPES),
            "affected_ids": ["guess-id"],
            "claimed_amount_minor": rng.randrange(100_000),
            "currency": "USD",
            "evidence_ids": [],
        }
        return {
            "type": "submit",
            "findings": {
                "episode_id": episode_id,
                "findings": [finding] if rng.random() < 0.5 else [],
            },
        }
    raise ValueError(f"Unknown action kind: {kind}")


def _make_invalid_action(kind, rng, episode_id, seen_records, seen_docs):
    if kind == "list_records":
        return rng.choice([
            {"type": "list_records"},
            {"type": "list_records", "table": "unknown_table"},
            {"type": "list_records", "table": rng.choice(_TABLES), "limit": -1},
            {"type": "list_records", "table": rng.choice(_TABLES), "limit": "fifty"},
            {"type": "list_records", "table": rng.choice(_TABLES), "cursor": 12345},
            {"type": "list_records", "table": rng.choice(_TABLES), "extra_key": True},
        ])
    if kind == "get_record":
        return rng.choice([
            {"type": "get_record", "id": "rec-1"},
            {"type": "get_record", "table": rng.choice(_TABLES)},
            {"type": "get_record", "table": "unknown_table", "id": "rec-1"},
            {"type": "get_record", "table": rng.choice(_TABLES), "id": ""},
            {"type": "get_record", "table": rng.choice(_TABLES), "id": 12345},
            {"type": "get_record", "table": rng.choice(_TABLES), "id": "rec-1", "extra": 1},
        ])
    if kind == "get_document":
        return rng.choice([
            {"type": "get_document"},
            {"type": "get_document", "doc_id": ""},
            {"type": "get_document", "doc_id": None},
            {"type": "get_document", "doc_id": 999},
            {"type": "get_document", "doc_id": "doc-1", "extra": 1},
        ])
    if kind == "calculator":
        return rng.choice([
            {"type": "calculator"},
            {"type": "calculator", "expression": 12345},
            {"type": "calculator", "expression": "7" * (_CALC_MAX_LEN + 1)},
            {"type": "calculator", "expression": "1+1", "mode": "deg"},
        ])
    if kind == "submit":
        return rng.choice([
            {"type": "submit"},
            {"type": "submit", "findings": None},
            {"type": "submit", "findings": "not_a_dict"},
            {"type": "submit", "findings": {"findings": []}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": None}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": [{"type": 7, "affected_ids": ["g"], "claimed_amount_minor": 10, "currency": "USD", "evidence_ids": []}]}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": [{"type": rng.choice(_ISSUE_TYPES), "affected_ids": "g", "claimed_amount_minor": 10, "currency": "USD", "evidence_ids": []}]}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": [{"type": rng.choice(_ISSUE_TYPES), "affected_ids": ["g"], "claimed_amount_minor": "10", "currency": "USD", "evidence_ids": []}]}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": [{"type": rng.choice(_ISSUE_TYPES), "affected_ids": ["g"], "claimed_amount_minor": 10, "evidence_ids": []}]}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": [{"type": rng.choice(_ISSUE_TYPES), "affected_ids": ["g"], "claimed_amount_minor": 10, "currency": "USD", "evidence_ids": ["e"] * 11}]}},
            {"type": "submit", "findings": {"episode_id": episode_id, "findings": [{"type": rng.choice(_ISSUE_TYPES), "affected_ids": ["g"], "claimed_amount_minor": 10, "currency": "USD", "evidence_ids": [], "extra": 1}]}},
        ])
    raise ValueError(f"Unknown action kind: {kind}")


class EnvFuzzTests(unittest.TestCase):
    def test_seeded_actions_preserve_step_contract(self):
        start = time.monotonic()
        rng = random.Random(20261119)
        env = AuditEnv()
        failures = Counter()
        examples = {}
        action_counts = Counter()
        step_actions_attempted = 0
        total_executed = 0

        num_episodes = 205
        for episode in range(num_episodes):
            first, _ = env.reset(episode, {"mode": "train" if episode % 2 else "eval", "n_invoices": 10})
            self.assertTrue(_matches(first, _OBSERVATION_SCHEMA, "observation.schema.json", _SCHEMAS))
            json.dumps(first, allow_nan=False)
            episode_id = first["manifest"]["episode_id"]

            seen_records = {t: [] for t in _TABLES}
            seen_docs = []

            submit_at = rng.randrange(98, 101) if episode % 10 != 0 else None
            submit_is_valid = (episode % 2 == 0)

            for step in range(1, 101):
                if step == submit_at:
                    kind = "submit"
                    is_valid = submit_is_valid
                    action = (
                        _make_valid_action("submit", rng, episode_id, seen_records, seen_docs)
                        if is_valid
                        else _make_invalid_action("submit", rng, episode_id, seen_records, seen_docs)
                    )
                else:
                    if rng.random() < 0.10:
                        action = rng.choice((*_INPUTS, {}, {"type": rng.choice(_INPUTS)}))
                        kind = "generic"
                        is_valid = False
                    else:
                        kind = rng.choice(("list_records", "get_record", "get_document", "calculator"))
                        is_valid = rng.random() < 0.80
                        action = (
                            _make_valid_action(kind, rng, episode_id, seen_records, seen_docs)
                            if is_valid
                            else _make_invalid_action(kind, rng, episode_id, seen_records, seen_docs)
                        )

                self.assertEqual(_matches(action, _ACTION_SCHEMA, "action.schema.json", _SCHEMAS), is_valid, (kind, action))
                action_counts[(kind, "valid" if is_valid else "invalid")] += 1
                step_actions_attempted += 1
                total_executed += 1

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
                self.assertTrue(_matches(observation, _OBSERVATION_SCHEMA, "observation.schema.json", _SCHEMAS))
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
                    total_executed += 1
                    self.assertTrue(_matches(after, _OBSERVATION_SCHEMA, "observation.schema.json", _SCHEMAS))
                    json.dumps(after, allow_nan=False)
                    self.assertEqual(after["error"]["code"], "episode_over")
                    self.assertEqual(after["steps_remaining"], observation["steps_remaining"])
                    self.assertEqual((after_terminated, after_truncated), (terminated, truncated))
                    break

                self.assertEqual(reward, 0.0)
                result = observation["result"] or {}
                if result.get("rows") and isinstance(action, dict) and action.get("table") in _TABLES:
                    tbl = action["table"]
                    for row in result["rows"][:3]:
                        seen_records[tbl].append(row[TABLES[tbl]])
                        if "doc_id" in row:
                            seen_docs.append(row["doc_id"])

        if __name__ == "__main__":
            print(f"Python {platform.python_version()}, {step_actions_attempted} episode actions, "
                  f"{total_executed} total step calls in {time.monotonic() - start:.3f} s")
        self.assertGreaterEqual(step_actions_attempted, 20000)
        self.assertGreaterEqual(total_executed, 20000)
        for kind in ("list_records", "get_record", "get_document", "calculator", "submit"):
            self.assertGreater(action_counts[(kind, "valid")], 0, f"Missing valid actions for {kind}")
            self.assertGreater(action_counts[(kind, "invalid")], 0, f"Missing invalid actions for {kind}")

        self.assertFalse(failures, "\n".join(
            f"{count} × {kind}: {message}; first (episode, step, action)={examples[key]!r}"
            for key, count in failures.items() for kind, message in [key]
        ))


if __name__ == "__main__":
    unittest.main()
