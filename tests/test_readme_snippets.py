"""Tests that python snippets in README.md run as written without errors."""

import contextlib
import io
import os
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def extract_python_snippets(content: str):
    snippets = []
    lines = content.splitlines()
    in_block = False
    current_block = []
    current_heading = ""
    for line in lines:
        stripped = line.strip()
        if not in_block and line.startswith("#"):
            current_heading = line.lstrip("#").strip()
        elif not in_block and stripped.startswith("```python"):
            in_block = True
            current_block = []
        elif in_block and stripped == "```":
            in_block = False
            snippets.append({
                "heading": current_heading,
                "code": "\n".join(current_block),
            })
            current_block = []
        elif in_block:
            current_block.append(line)
    return snippets


class TestReadmeSnippets(unittest.TestCase):

    def test_readme_python_snippets(self):
        readme_path = REPO_ROOT / "README.md"
        self.assertTrue(readme_path.is_file(), "README.md must exist at repo root")

        content = readme_path.read_text(encoding="utf-8")
        snippets = extract_python_snippets(content)
        self.assertGreaterEqual(len(snippets), 2, "Expected at least 2 python snippets in README.md")

        for idx, item in enumerate(snippets):
            heading = item["heading"]
            code = item["code"]
            with self.subTest(snippet_idx=idx, heading=heading):
                buf = io.StringIO()
                scope = {}
                old_cwd = os.getcwd()
                try:
                    os.chdir(REPO_ROOT)
                    with contextlib.redirect_stdout(buf):
                        exec(code, scope)
                finally:
                    os.chdir(old_cwd)

                stdout = buf.getvalue()
                if "Using the environment" in heading:
                    tokens = stdout.strip().split()
                    self.assertTrue(tokens, "Output of 'Using the environment' snippet must not be empty")
                    try:
                        reward_val = float(tokens[0])
                    except ValueError:
                        self.fail(f"Expected output to start with a numeric reward, got {tokens[0]!r}")
                    self.assertTrue(
                        -1.0 <= reward_val <= 1.0,
                        f"Reward value {reward_val} out of expected range [-1, 1]"
                    )


if __name__ == "__main__":
    unittest.main()
