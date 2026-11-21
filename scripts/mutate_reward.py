"""Measure reward test coverage against isolated, single-line source mutations."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TESTS = ("tests.test_matcher", "tests.test_reward_attacks", "tests.test_jury", "tests.test_metrics",
         "tests.test_judge_reward")
MUTANTS = (
    ("matcher", "exclusive amount boundary", "\"]) <= tolerance,", "\"]) < tolerance,"),
    ("matcher", "off-by-one tolerance", "\"]) <= tolerance,", "\"]) <= tolerance + 1,"),
    ("matcher", "default tolerance one", '.get("tolerance_minor", 0)', '.get("tolerance_minor", 1)'),
    ("matcher", "ignore type", 'f["type"] == issue["type"]', "True"),
    ("matcher", "ignore identifiers", 'set(f["affected_ids"]) == set(issue["affected_ids"])', "True"),
    ("matcher", "ignore currency", 'f["currency"] == issue["currency"]', "True"),
    ("matcher", "ignore amount", 'abs(f["claimed_amount_minor"] - issue["expected_amount_minor"]) <= tolerance',
     "True"),
    ("matcher", "ignore evidence", 'any(set(s) <= evidence for s in issue["evidence_sets"])', "True"),
    ("matcher", "reject extra evidence", "set(s) <= evidence for", "set(s) == evidence for"),
    ("matcher", "accept unknown evidence", "evidence <= known_ids and ", ""),
    ("matcher", "greedy first fit", "if len(fixed) + 1 + _max_matching(adj, rest, set(fixed.values()) | {f}) == best:",
     "if True:"),
    ("matcher", "tie-break in truth order", 'order = sorted(range(len(issues)), key=lambda ii: issues[ii]["issue_id"])',
     "order = list(range(len(issues)))"),
    ("matcher", "credit repeat findings", "tp = len(matched)",
     "tp = sum(1 for fi in range(len(norm)) if any(fi in a for a in adj.values()))"),
    ("schema", "strip ids", '"affected_ids": sorted(set(f["affected_ids"])),',
     '"affected_ids": sorted({a.strip() for a in f["affected_ids"]}),'),
    ("schema", "uppercase currency", '"currency": f["currency"],', '"currency": f["currency"].upper(),'),
    ("schema", "evidence limit after dedupe", 'if len(f["evidence_ids"]) > MAX_EVIDENCE:',
     'if len(set(f["evidence_ids"])) > MAX_EVIDENCE:'),
    ("metrics", "swap precision and recall", "return precision, recall, f1", "return recall, precision, f1"),
    ("metrics", "wrong empty F1", "if predicted or actual else 1.0", "if predicted or actual else 0.0"),
    ("metrics", "ignore false negatives in F1", "(predicted + actual)", "(predicted + predicted)"),
    ("metrics", "increase step cost", "0.002 * inspection_steps", "0.005 * inspection_steps"),
    ("metrics", "remove lower reward bound", "max(-1.0, min(1.0, reward))", "min(1.0, reward)"),
    ("metrics", "round reward to six places", "return max(-1.0, min(1.0, reward))",
     "return round(max(-1.0, min(1.0, reward)), 6)"),
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
