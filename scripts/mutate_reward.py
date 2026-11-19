"""Measure reward test coverage against isolated, single-line source mutations."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TESTS = ("tests.test_matcher", "tests.test_reward_attacks", "tests.test_jury", "tests.test_metrics")
MUTANTS = (
    ("matcher", "exclusive amount boundary", "<= tolerance(", "< tolerance("),
    ("matcher", "wider tolerance", "expected_minor // 1000", "expected_minor // 100"),
    ("matcher", "zero tolerance floor", "max(1, expected_minor", "max(0, expected_minor"),
    ("matcher", "ignore type", 'f["type"] == issue["type"]', "True"),
    ("matcher", "ignore identifiers", 'f["affected_ids"] == sorted(issue["affected_ids"])', "True"),
    ("matcher", "ignore currency", 'f["currency"] == issue["currency"]', "True"),
    ("matcher", "ignore amount", "<= tolerance(issue[\"expected_amount_minor\"])", ">= 0"),
    ("matcher", "ignore evidence", 'any(set(s) <= set(f["evidence_ids"]) for s in issue["evidence_sets"])', "True"),
    ("matcher", "reject extra evidence", 'set(s) <= set(f["evidence_ids"])', 'set(s) == set(f["evidence_ids"])'),
    ("matcher", "allow repeat matches", "if ii not in matched and all(", "if all("),
    ("metrics", "swap precision and recall", "return precision, recall, f1", "return recall, precision, f1"),
    ("metrics", "wrong empty F1", "if predicted or actual else 1.0", "if predicted or actual else 0.0"),
    ("metrics", "ignore false negatives in F1", "(predicted + actual)", "(predicted + predicted)"),
    ("metrics", "increase step cost", "0.002 * inspection_steps", "0.005 * inspection_steps"),
    ("metrics", "remove lower reward bound", "max(-1.0, min(1.0, reward))", "min(1.0, reward)"),
)


def run_tests(directory: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", *TESTS],
        cwd=directory, capture_output=True, text=True,
    )


def main() -> int:
    sources = {module: (ROOT / "auditenv" / f"{module}.py").read_text() for module, *_ in MUTANTS}
    for module, name, original, replacement in MUTANTS:
        if sources[module].count(original) != 1:
            raise ValueError(f"{module}: {name}: expected exactly one source match")
        compile(sources[module].replace(original, replacement), f"{module}.py", "exec")

    # Disable bytecode both when copying and when running tests so successive
    # writes of equal length cannot accidentally reuse a previous mutant.
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    with tempfile.TemporaryDirectory(prefix="auditenv-mutations-") as temp:
        workspace = Path(temp)
        for directory in ("auditenv", "tests", "configs", "episodes", "trajectories", "schemas"):
            shutil.copytree(ROOT / directory, workspace / directory, ignore=ignore)

        baseline = run_tests(workspace)
        if baseline.returncode:
            print(baseline.stderr, file=sys.stderr)
            print("Unmodified reward tests failed.", file=sys.stderr)
            return 1

        print("| Module | Mutant | Result |", flush=True)
        print("|---|---|---|", flush=True)
        killed = 0
        for module, name, original, replacement in MUTANTS:
            path = workspace / "auditenv" / f"{module}.py"
            path.write_text(sources[module].replace(original, replacement))
            result = run_tests(workspace)
            path.write_text(sources[module])
            if result.returncode == 0:
                status = "survived"
            elif result.returncode == 1 and "FAILED (" in result.stderr:
                status = "killed"
                killed += 1
            else:
                status = "test runner error"
                print(result.stderr, file=sys.stderr)
            print(f"| {module} | {name} | {status} |", flush=True)

    print(f"{killed}/{len(MUTANTS)} mutants killed.")
    return int(killed != len(MUTANTS))


if __name__ == "__main__":
    raise SystemExit(main())
