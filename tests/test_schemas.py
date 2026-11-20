"""Smoke checks for the published JSON Schemas using only the standard library."""

import json
import re
from pathlib import Path
import unittest

from auditenv.env import AuditEnv, TABLES, TOOLS
from auditenv.generator import generate
from auditenv.run import make_policy, run_episode
from auditenv.schema import ISSUE_TYPES, MAX_AFFECTED, MAX_EVIDENCE, MAX_EXPLANATION, MAX_FINDINGS

_SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"
_JSON_TYPES = {
    "array": (list,),
    "boolean": (bool,),
    "integer": (int,),
    "null": (type(None),),
    "number": (float, int),
    "object": (dict,),
    "string": (str,),
}


def _matches(value, schema, filename, schemas):
    """Check the schema subset used by these fixtures, including cross-file references."""
    if "$ref" in schema:
        target, _, pointer = schema["$ref"].partition("#")
        filename = target or filename
        definition = schemas[filename]
        for part in pointer.split("/")[1:]:
            definition = definition[part]
        return _matches(value, definition, filename, schemas)
    if "oneOf" in schema:
        return sum(_matches(value, branch, filename, schemas) for branch in schema["oneOf"]) == 1
    kinds = schema.get("type", [])
    if isinstance(kinds, str):
        kinds = [kinds]
    if kinds and not any(type(value) in _JSON_TYPES[kind] for kind in kinds):
        return False
    if "const" in schema and value != schema["const"]:
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if isinstance(value, str):
        if len(value) > schema.get("maxLength", len(value)) or ("pattern" in schema and not re.search(schema["pattern"], value)):
            return False
    if type(value) in (int, float) and not schema.get("minimum", value) <= value <= schema.get("maximum", value):
        return False
    if isinstance(value, list) and not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", len(value)):
        return False
    if isinstance(value, list) and schema.get("uniqueItems"):
        # The published schemas apply uniqueness to arrays of string IDs.
        if not all(isinstance(item, str) for item in value) or len(set(value)) != len(value):
            return False
    if isinstance(value, list) and "items" in schema:
        return all(_matches(item, schema["items"], filename, schemas) for item in value)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if not set(schema.get("required", ())) <= value.keys():
            return False
        extra = schema.get("additionalProperties", {})
        for key, item in value.items():
            definition = properties.get(key, extra)
            if definition is False or not _matches(item, definition, filename, schemas):
                return False
    return True


def load_schemas():
    """Load all JSON schemas from the repository schema directory."""
    return {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in _SCHEMA_ROOT.glob("*.schema.json")
    }


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas = load_schemas()

    def assertMatches(self, name, value):
        filename = f"{name}.schema.json"
        self.assertTrue(_matches(value, self.schemas[filename], filename, self.schemas), name)

    def test_truth_evidence_ids_are_unique_within_each_set(self):
        truth = generate(2003, {"errors": {"duplicate_invoice": 1}})["truth"]
        self.assertMatches("truth", truth)
        evidence = truth["issues"][0]["evidence_sets"][0]
        evidence.append(evidence[0])
        self.assertFalse(_matches(truth, self.schemas["truth.schema.json"], "truth.schema.json", self.schemas))

    def test_dialect_and_runtime_constants(self):
        self.assertEqual(set(self.schemas), {
            f"{name}.schema.json" for name in
            ("action", "findings", "manifest", "observation", "trajectory_step", "truth")
        })
        for schema in self.schemas.values():
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

        findings = self.schemas["findings.schema.json"]["properties"]["findings"]
        fields = findings["items"]["properties"]
        self.assertEqual(findings["maxItems"], MAX_FINDINGS)
        self.assertEqual(fields["affected_ids"]["maxItems"], MAX_AFFECTED)
        self.assertEqual(fields["evidence_ids"]["maxItems"], MAX_EVIDENCE)
        self.assertEqual(fields["explanation"]["maxLength"], MAX_EXPLANATION)
        self.assertEqual(tuple(fields["type"]["enum"]), ISSUE_TYPES)
        truth = self.schemas["truth.schema.json"]["properties"]["issues"]["items"]
        self.assertEqual(tuple(truth["properties"]["type"]["enum"]), ISSUE_TYPES)
        actions = self.schemas["action.schema.json"]["oneOf"]
        self.assertEqual(
            [branch["properties"]["type"]["const"] for branch in actions],
            [tool["type"] for tool in TOOLS],
        )
        self.assertEqual(tuple(actions[0]["properties"]["table"]["enum"]), tuple(TABLES))

    def test_generator_and_oracle_episode_match(self):
        episode = generate(1)
        self.assertMatches("manifest", episode["manifest"])
        self.assertMatches("truth", episode["truth"])

        env = AuditEnv()
        first, _ = env.reset(1)
        step, *_ = env.step({"type": "list_records", "table": "ledger"})
        self.assertMatches("observation", first)
        self.assertMatches("observation", step)

        trajectory = run_episode(env, None, 1, policy_factory=lambda e: make_policy("oracle", e))
        for entry in trajectory:
            self.assertMatches("trajectory_step", entry)
        submission = trajectory[-1]["action"]
        self.assertMatches("action", submission)
        self.assertMatches("findings", submission["findings"])
