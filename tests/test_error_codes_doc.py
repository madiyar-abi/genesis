"""Every error code the jury path can return must be documented in README.md, and vice versa.

A policy talks to us only through `judge_adapter.py` -> `auditenv/env.py`, so the set of
`{"code", "message"}` codes it can see is a public interface: README.md "Jury adapter" lists
them and promises that no error carries paths, seeds or truth. An undocumented code is a
broken promise, a documented code that no longer exists is a wrong claim.

The source side is collected with `ast` (not a hand-maintained list) from `auditenv/env.py`,
`auditenv/calculator.py` and `judge_adapter.py`: every string literal used as the `code` value
of an error object (`{"code": "<x>", ...}`) or passed to `ToolError("<x>", ...)`. The dynamic
`{"code": e.code, ...}` path takes its value from those `ToolError` literals, so it is covered
too. The README side is the "Errors are ..." paragraph of the "Jury adapter" section; only
identifier-shaped backticked tokens are codes, so the `{"code", "message"}` shape is ignored.
"""

import ast
from pathlib import Path
import re
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILES = ("auditenv/env.py", "auditenv/calculator.py", "judge_adapter.py")
README_PATH = REPO_ROOT / "README.md"

SECTION_RE = re.compile(r"^(#{1,6})\s+Jury adapter\b")
HEADING_RE = re.compile(r"^(#{1,6})\s")
BACKTICK_RE = re.compile(r"`([^`]+)`")
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
CODE_KEY = "code"
ERROR_CTOR = "ToolError"
PARAGRAPH_START = "Errors are"


def _string_constant(node):
    """The value of a string literal node, else None (a computed value is not enumerable here)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_name(node):
    """The bare name of the called function (`ToolError` both as a name and as `mod.ToolError`)."""
    return node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)


def error_codes_in_source(source, filename="<string>"):
    """Return `{code: line}` for every error code literal in one Python source text.

    Codes are found in two shapes: the `code` value of a `{"code": ..., "message": ...}` object
    literal, and the first positional (or `code=`) argument of a `ToolError(...)` call. A computed
    value such as `e.code` is skipped: its values come from the `ToolError` literals collected here.
    """
    found = {}
    for node in ast.walk(ast.parse(source, filename=filename)):
        code = None
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if _string_constant(key) == CODE_KEY:
                    code = _string_constant(value)
        elif isinstance(node, ast.Call) and _call_name(node) == ERROR_CTOR:
            code = _string_constant(node.args[0]) if node.args else None
            for keyword in node.keywords:
                if keyword.arg == CODE_KEY:
                    code = _string_constant(keyword.value)
        if code is not None:
            found.setdefault(code, node.lineno)
    return found


def jury_adapter_section(text):
    """The lines of README.md's "Jury adapter" section: its heading up to the next same-or-higher one."""
    lines = text.splitlines()
    for start, line in enumerate(lines):
        match = SECTION_RE.match(line)
        if match:
            level = len(match.group(1))
            for end in range(start + 1, len(lines)):
                heading = HEADING_RE.match(lines[end])
                if heading and len(heading.group(1)) <= level:
                    return lines[start:end]
            return lines[start:]
    raise AssertionError('README.md has no "Jury adapter" section')


def documented_codes(text):
    """The error codes README.md documents in the section's "Errors are ..." paragraph."""
    section = jury_adapter_section(text)
    for start, line in enumerate(section):
        if line.startswith(PARAGRAPH_START):
            end = start
            while end < len(section) and section[end].strip():
                end += 1
            paragraph = "\n".join(section[start:end])
            return {token for token in BACKTICK_RE.findall(paragraph) if IDENTIFIER_RE.match(token)}
    raise AssertionError('README.md\'s "Jury adapter" section has no "Errors are ..." paragraph')


def collect_source_codes():
    """Return `{code: "<file>:<line>"}` for every error code the jury path can return."""
    producers = {}
    for rel_path in SOURCE_FILES:
        path = REPO_ROOT / rel_path
        source = path.read_text(encoding="utf-8")
        for code, line in error_codes_in_source(source, rel_path).items():
            producers.setdefault(code, f"{rel_path}:{line}")
    return producers


class ErrorCodesDocTests(unittest.TestCase):

    def test_error_codes_match_readme(self):
        producers = collect_source_codes()
        documented = documented_codes(README_PATH.read_text(encoding="utf-8"))
        missing = sorted(set(producers) - documented)
        extra = sorted(documented - set(producers))
        problems = []
        if missing:
            problems.append("returned by the code but missing from README.md (\"Jury adapter\" -> \"Errors are\"):\n"
                            + "\n".join(f"  {code} ({producers[code]})" for code in missing))
        if extra:
            problems.append("documented in README.md but never returned by auditenv/env.py, "
                            "auditenv/calculator.py or judge_adapter.py:\n"
                            + "\n".join(f"  {code}" for code in extra))
        self.assertEqual(problems, [], "\n".join(problems))

    def test_both_sides_are_found(self):
        # Guards against a vacuous pass: a refactor that renames ToolError (or edits the README
        # paragraph) must not leave the comparison above with two empty sets.
        producers = collect_source_codes()
        documented = documented_codes(README_PATH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(producers), 5, f"only {sorted(producers)} found in the sources")
        self.assertGreaterEqual(len(documented), 5, f"only {sorted(documented)} found in README.md")
        self.assertIn("bad_params", producers, "the malformed-request code must stay discoverable")

    def test_source_collection_finds_dict_and_tool_error_literals(self):
        source = (
            "raise ToolError('alpha_code', 'message')\n"
            "raise ToolError(code='beta_code', message='message')\n"
            "error = {'code': 'gamma_code', 'message': 'message'}\n"
            "error = {'code': exc.code, 'message': exc.message}  # computed: not enumerable here\n"
            "other = {'message': 'delta_code'}\n"
        )
        self.assertEqual(error_codes_in_source(source), {"alpha_code": 1, "beta_code": 2, "gamma_code": 3})

    def test_documented_codes_ignore_the_shape_and_stop_at_the_section(self):
        text = (
            "# Title\n\n## Errors elsewhere\n\n`not_a_jury_code`\n\n"
            "### Jury adapter (`judge_adapter.py`)\n\n"
            "Errors are `{\"code\", \"message\"}` with no paths, and every one costs a step:\n"
            "`bad_params`, `unknown_action`. Only `episode_over` is free.\n\n"
            "### Next section\n\n`not_a_jury_code_either`\n"
        )
        self.assertEqual(documented_codes(text), {"bad_params", "unknown_action", "episode_over"})

    def test_missing_section_is_an_error_not_an_empty_pass(self):
        with self.assertRaises(AssertionError):
            documented_codes("## Something else\n\n### Errors are `here`\n")

    def test_missing_errors_paragraph_is_an_error_not_an_empty_pass(self):
        # The section exists but the "Errors are ..." sentence was renamed or moved away.
        with self.assertRaises(AssertionError):
            documented_codes("## Jury adapter\n\nSome prose with `bad_params` but no paragraph start.\n")


if __name__ == "__main__":
    unittest.main()