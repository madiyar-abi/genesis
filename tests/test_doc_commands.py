"""Every auditenv/script command in README.md and docs/*.md fenced blocks must be real.

The jury copies commands out of the docs. This test extracts each
`python -m auditenv.<mod>` and `python scripts/<x>.py` invocation from fenced
code blocks, asserts the module/script exists, and checks that every
`--long-flag` on the command line appears in the program's `--help` output
(run with sys.executable from the repo root). Shell comments are stripped
before matching so prose like `# runs python -m auditenv.check` or flags of a
different program mentioned in a comment are not treated as invocations.
"""

from functools import lru_cache
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# python / python3 / python3.11 -m auditenv.<mod>  or  python ... scripts/<x>.py
COMMAND_RE = re.compile(
    r"python(?:3(?:\.\d+)?)?\s+(?:-m\s+(auditenv\.[A-Za-z_0-9]+)|(scripts/[A-Za-z_0-9]+\.py))"
)
FLAG_RE = re.compile(r"--[A-Za-z][A-Za-z0-9-]*")
HELP_TIMEOUT_S = 30


def doc_paths():
    """README.md plus every docs/*.md, in stable order."""
    return [REPO_ROOT / "README.md"] + sorted((REPO_ROOT / "docs").glob("*.md"))


def extract_commands(text):
    """Yield (program, flags, line_no, line) for each invocation in fenced blocks.

    Flags are the `--long-flag` tokens between this command and the next
    command on the same line, a shell comment (`#`), or a `&&`, `;`, `|`
    separator — so flags of neighbouring commands are never mixed in.
    """
    entries = []
    in_fence = False
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        code = line.split("#", 1)[0]
        matches = list(COMMAND_RE.finditer(code))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
            args = code[match.end():end]
            for separator in ("&&", ";", "|"):
                args = args.split(separator, 1)[0]
            program = match.group(1) or match.group(2)
            flags = sorted(set(FLAG_RE.findall(args)))
            entries.append((program, flags, line_no, line.strip()))
    return entries


def program_exists(program):
    if program.startswith("auditenv."):
        try:
            return importlib.util.find_spec(program) is not None
        except (ImportError, ValueError):
            return False
    return (REPO_ROOT / program).is_file()


@lru_cache(maxsize=None)
def help_text(program):
    """Return (returncode, combined output) of `<program> --help` from the repo root."""
    if program.startswith("auditenv."):
        cmd = [sys.executable, "-m", program, "--help"]
    else:
        cmd = [sys.executable, program, "--help"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=HELP_TIMEOUT_S)
    return proc.returncode, proc.stdout + proc.stderr


def find_problems(sources):
    """Check (name, text) doc sources; return a list of human-readable problems."""
    problems = []
    flagged_programs = set()
    all_entries = []
    for name, text in sources:
        for program, flags, line_no, line in extract_commands(text):
            all_entries.append((name, program, flags, line_no, line))
            if flags:
                flagged_programs.add(program)
    helps = {}
    for program in sorted(flagged_programs):
        if program_exists(program):
            try:
                helps[program] = help_text(program)
            except (OSError, subprocess.TimeoutExpired) as exc:
                problems.append(f"{program}: --help failed to run: {exc!r}")
    for name, program, flags, line_no, line in all_entries:
        where = f"{name}:{line_no}: {line}"
        if not program_exists(program):
            problems.append(f"{where}\n  program {program} does not exist")
            continue
        if not flags:
            continue
        if program not in helps:
            continue  # --help itself already reported as a problem
        returncode, output = helps[program]
        if returncode != 0:
            problems.append(f"{where}\n  {program} --help exited {returncode}")
            continue
        for flag in flags:
            if flag not in output:
                problems.append(f"{where}\n  {program} --help does not mention {flag}")
    return problems


class DocCommandTests(unittest.TestCase):

    def test_documented_commands_exist_and_accept_their_flags(self):
        sources = []
        for path in doc_paths():
            self.assertTrue(path.is_file(), f"{path} must exist")
            sources.append((path.name, path.read_text(encoding="utf-8")))
        total = sum(len(extract_commands(text)) for _, text in sources)
        self.assertGreaterEqual(total, 25, "docs should contain at least 25 auditenv/script command lines")
        problems = find_problems(sources)
        self.assertEqual(problems, [], "broken documented commands:\n" + "\n".join(problems))

    def test_fake_flag_is_detected(self):
        """A --no-such-flag added to a real doc command (scratch copy) must be caught."""
        scratch = (
            "```sh\n"
            "uv run python -m auditenv.check --json /tmp/metrics.json --no-such-flag\n"
            "```\n"
        )
        problems = find_problems([("scratch.md", scratch)])
        self.assertTrue(
            any("--no-such-flag" in p and "auditenv.check" in p for p in problems),
            f"a fake flag must be detected, got: {problems}",
        )

    def test_missing_program_is_detected(self):
        scratch = "```sh\npython -m auditenv.no_such_module --seeds 0-9\npython scripts/no_such_script.py\n```\n"
        problems = find_problems([("scratch.md", scratch)])
        self.assertTrue(any("auditenv.no_such_module does not exist" in p for p in problems), problems)
        self.assertTrue(any("scripts/no_such_script.py does not exist" in p for p in problems), problems)

    def test_comment_and_separator_flags_are_not_mixed_between_commands(self):
        scratch = (
            "```sh\n"
            "docker run --rm --network none auditenv  # runs python -m auditenv.check offline\n"
            "uv run python -m auditenv.verify --seeds 0-9 && uv run python -m auditenv.attack\n"
            "```\n"
        )
        entries = extract_commands(scratch)
        self.assertEqual([(p, f) for p, f, _, _ in entries],
                         [("auditenv.verify", ["--seeds"]), ("auditenv.attack", [])])
        self.assertEqual(find_problems([("scratch.md", scratch)]), [])


if __name__ == "__main__":
    unittest.main()