"""Every tests/<file>.py::<Class>::<method> reference in docs/CHECKS.md must resolve.

The verification map is the jury's index into our test suite; a renamed or deleted
test silently breaks the map. This test parses every reference, imports the module
and checks the class and method exist, failing with the full list of broken ones.
"""

import importlib
from pathlib import Path
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CHECKS_PATH = REPO_ROOT / "docs" / "CHECKS.md"

REFERENCE_RE = re.compile(r"(tests/[A-Za-z_0-9]+\.py)::([A-Za-z_0-9]+)::([A-Za-z_0-9]+)")


def extract_references(text):
    """Return the sorted unique (file, class, method) triples referenced in *text*."""
    return sorted({(m.group(1), m.group(2), m.group(3)) for m in REFERENCE_RE.finditer(text)})


def find_broken_references(text):
    """Return a list of human-readable problems for references that do not resolve."""
    problems = []
    for rel_path, class_name, method_name in extract_references(text):
        ref = f"{rel_path}::{class_name}::{method_name}"
        if not (REPO_ROOT / rel_path).is_file():
            problems.append(f"{ref}: file does not exist")
            continue
        module_name = rel_path[:-3].replace("/", ".")
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report any import failure as a broken reference
            problems.append(f"{ref}: cannot import {module_name}: {exc!r}")
            continue
        cls = getattr(module, class_name, None)
        if cls is None:
            problems.append(f"{ref}: class {class_name} not found in {module_name}")
            continue
        if getattr(cls, method_name, None) is None:
            problems.append(f"{ref}: method {method_name} not found on {class_name}")
    return problems


class ChecksMapTests(unittest.TestCase):

    def test_checks_map_references_resolve(self):
        self.assertTrue(CHECKS_PATH.is_file(), "docs/CHECKS.md must exist at the repo root")
        text = CHECKS_PATH.read_text(encoding="utf-8")
        references = extract_references(text)
        self.assertGreaterEqual(len(references), 50, "docs/CHECKS.md should map at least 50 test references")
        problems = find_broken_references(text)
        self.assertEqual(problems, [], "broken docs/CHECKS.md references:\n" + "\n".join(problems))

    def test_renamed_method_is_detected(self):
        """A renamed referenced method (simulated on a scratch copy) must be reported."""
        text = CHECKS_PATH.read_text(encoding="utf-8")
        references = extract_references(text)
        self.assertTrue(references)
        rel_path, class_name, method_name = references[0]
        broken_name = method_name + "_renamed_away"
        scratch = text.replace(f"{rel_path}::{class_name}::{method_name}",
                               f"{rel_path}::{class_name}::{broken_name}")
        problems = find_broken_references(scratch)
        self.assertTrue(
            any(broken_name in p and "not found" in p for p in problems),
            f"renaming {method_name} must be detected, got: {problems}",
        )


if __name__ == "__main__":
    unittest.main()
