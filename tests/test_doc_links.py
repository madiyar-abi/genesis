"""Every relative markdown link in README.md and docs/*.md must resolve.

The jury navigates the repo through these documents; a link to a renamed or
deleted file is a dead end. This test extracts every inline `[text](path)`
link (images included), strips `#anchor` fragments, skips external URLs
(http/https/mailto/... and protocol-relative `//`) and pure anchors, and
asserts the target exists in the repo. Relative paths resolve against the
document's own directory; root-relative `/path` against the repo root
(GitHub's convention).
"""

from pathlib import Path
import re
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent

# [text](target) — also matches the bracket part of an image ![text](target).
# The target may be wrapped in <> and followed by an optional "title".
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[^)]*)?\)")
EXTERNAL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def doc_paths():
    """README.md plus every docs/*.md, in stable order."""
    return [REPO_ROOT / "README.md"] + sorted((REPO_ROOT / "docs").glob("*.md"))


def extract_links(text):
    """Yield (target, line_no, line) for every inline markdown link in *text*."""
    entries = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for match in LINK_RE.finditer(line):
            entries.append((match.group(1), line_no, line.strip()))
    return entries


def link_path(target):
    """Return the repo-relative path a link points to, or None if it is not a repo file link."""
    if EXTERNAL_RE.match(target) or target.startswith("//"):
        return None  # external URL (https:, mailto:, ...) — not ours to check
    path = target.split("#", 1)[0]
    if not path:
        return None  # pure in-page anchor
    return path.lstrip("/") if path.startswith("/") else path


def find_broken_links(sources):
    """Check (base_dir, name, text) doc sources; return a list of readable problems."""
    problems = []
    for base_dir, name, text in sources:
        for target, line_no, line in extract_links(text):
            path = link_path(target)
            if path is None:
                continue
            resolved = (REPO_ROOT / path) if target.startswith("/") else (base_dir / path)
            if not resolved.exists():
                problems.append(f"{name}:{line_no}: [{target}] -> {resolved} does not exist\n  {line}")
    return problems


class DocLinkTests(unittest.TestCase):

    def test_all_relative_links_resolve(self):
        sources = []
        count = 0
        for path in doc_paths():
            self.assertTrue(path.is_file(), f"{path} must exist")
            text = path.read_text(encoding="utf-8")
            sources.append((path.parent, path.name, text))
            count += sum(1 for target, _, _ in extract_links(text) if link_path(target) is not None)
        self.assertGreaterEqual(count, 10, "docs should contain at least 10 relative file links")
        problems = find_broken_links(sources)
        self.assertEqual(problems, [], "broken relative markdown links:\n" + "\n".join(problems))

    def test_broken_link_is_detected(self):
        scratch = "See [the design](docs/no_such_file.md) for details.\n"
        problems = find_broken_links([(REPO_ROOT, "scratch.md", scratch)])
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("docs/no_such_file.md", problems[0])
        self.assertIn("does not exist", problems[0])

    def test_anchor_is_stripped_and_pure_anchors_skipped(self):
        scratch = "[design](docs/DESIGN.md#results) and [section](#run-a-policy) and [cast](docs/demo.cast#L1)\n"
        self.assertEqual(find_broken_links([(REPO_ROOT, "scratch.md", scratch)]), [])
        targets = [link_path(t) for t, _, _ in extract_links(scratch)]
        self.assertEqual(targets, ["docs/DESIGN.md", None, "docs/demo.cast"])

    def test_external_links_are_skipped(self):
        scratch = ("[ci](https://github.com/madiyar-abi/genesis/actions) [mail](mailto:team@example.com)\n"
                   "[proto](//example.com/x.png)\n")
        self.assertEqual(find_broken_links([(REPO_ROOT, "scratch.md", scratch)]), [])

    def test_links_resolve_relative_to_the_document_directory(self):
        # docs/DESIGN.md links to CONTRACT.md (same directory), README.md to docs/CONTRACT.md.
        self.assertEqual(find_broken_links([(REPO_ROOT / "docs", "scratch.md", "[c](CONTRACT.md)\n")]), [])
        problems = find_broken_links([(REPO_ROOT, "scratch.md", "[c](CONTRACT.md)\n")])
        self.assertEqual(len(problems), 1, "CONTRACT.md does not exist at the repo root")


if __name__ == "__main__":
    unittest.main()