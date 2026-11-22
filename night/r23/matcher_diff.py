"""Compare an independent Block 3 matcher with the documented jury scoring call."""

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import tempfile

from auditenv.jury import SCENARIOS
import judge_adapter as judge


SCRATCH = Path("/tmp/r23-codex1")
FIELDS = {"type", "affected_ids", "claimed_amount_minor", "currency", "evidence_ids", "explanation"}
METRICS = ("tp", "fp", "fn", "precision", "recall", "f1")
TYPES = ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")
MUTATIONS = (
    "original", "empty", "drop", "duplicate", "type", "affected_add", "affected_remove",
    "affected_duplicate", "affected_case", "amount_minus", "amount_plus", "currency_case",
    "currency_space", "evidence_subset", "evidence_superset", "evidence_unknown", "evidence_order",
    "evidence_10", "evidence_11", "findings_30", "findings_31", "explanation_1000", "explanation_1001",
    "explanation_unicode_1000", "explanation_unicode_1001", "amount_bool", "amount_str", "amount_float",
    "missing_field", "extra_field", "missing_envelope_key", "extra_envelope_key", "reorder", "combined",
)


@dataclass
class Fixture:
    path: Path
    episode_id: str
    issues: list
    public_ids: set
    tolerance: int

    @classmethod
    def generate(cls, path, seed, config):
        judge.generate_episode(seed, config, str(path))
        truth = json.loads((path / "grader" / "truth.json").read_text())
        public = path / "public"
        policy = json.loads((public / "policy.json").read_text())
        public_ids = set()
        for file, key in (("ledger.csv", "row_id"), ("fx.csv", "fx_id")):
            with (public / file).open(newline="") as stream:
                public_ids.update(row[key] for row in csv.DictReader(stream))
        for file, key in (("invoices.jsonl", "invoice_id"), ("payments.jsonl", "payment_id")):
            for line in (public / file).read_text().splitlines():
                row = json.loads(line)
                public_ids.update((row[key], row["doc_id"]))
        return cls(path, truth["episode_id"], truth["issues"], public_ids, policy["findings"]["tolerance_minor"])

    def oracle(self):
        return [
            {
                "type": issue["type"], "affected_ids": issue["affected_ids"],
                "claimed_amount_minor": issue["expected_amount_minor"], "currency": issue["currency"],
                "evidence_ids": issue["evidence_sets"][0], "explanation": "Audit finding",
            }
            for issue in self.issues
        ]


def strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def valid_payload(payload):
    if not isinstance(payload, dict) or set(payload) != {"episode_id", "findings"}:
        return False
    findings = payload["findings"]
    if not isinstance(payload["episode_id"], str) or not isinstance(findings, list) or len(findings) > 30:
        return False
    return all(
        isinstance(finding, dict) and set(finding) == FIELDS
        and isinstance(finding["type"], str)
        and strings(finding["affected_ids"])
        and type(finding["claimed_amount_minor"]) is int
        and isinstance(finding["currency"], str)
        and strings(finding["evidence_ids"]) and len(finding["evidence_ids"]) <= 10
        and isinstance(finding["explanation"], str) and len(finding["explanation"]) <= 1000
        for finding in findings
    )


def cardinality(edges, excluded):
    """Find augmenting paths from issues to findings and back through existing pairs."""
    owners = {}

    def assign(issue, visited):
        for finding in edges[issue]:
            if finding in visited:
                continue
            visited.add(finding)
            if finding not in owners or assign(owners[finding], visited):
                owners[finding] = issue
                return True
        return False

    for issue in edges:
        assign(issue, set(excluded))
    return len(owners)


def canonical_matching(edges):
    """Fix each pair in lexical order if the remaining graph can still complete a maximum."""
    ordered = {issue: sorted(edges[issue]) for issue in sorted(edges)}
    remaining = cardinality(ordered, set())
    used = set()
    pairs = []
    for issue, neighbors in ordered.items():
        if remaining == 0:
            break
        suffix = {other: edges for other, edges in ordered.items() if other > issue}
        for finding in neighbors:
            if finding not in used and cardinality(suffix, used | {finding}) >= remaining - 1:
                pairs.append((issue, finding))
                used.add(finding)
                remaining -= 1
                break
    return pairs


def compatible(finding, issue, evidence, tolerance):
    return (
        finding["type"] == issue["type"]
        and set(finding["affected_ids"]) == set(issue["affected_ids"])
        and finding["currency"] == issue["currency"]
        and abs(finding["claimed_amount_minor"] - issue["expected_amount_minor"]) <= tolerance
        and any(evidence.issuperset(options) for options in issue["evidence_sets"])
    )


def grade(fixture, payload, steps):
    if not valid_payload(payload):
        return dict.fromkeys(METRICS) | {"return": -1}
    edges = {issue["issue_id"]: [] for issue in fixture.issues}
    findings = payload["findings"]
    for index, finding in enumerate(findings):
        evidence = set(finding["evidence_ids"])
        if evidence <= fixture.public_ids:
            for issue in fixture.issues:
                if compatible(finding, issue, evidence, fixture.tolerance):
                    edges[issue["issue_id"]].append(index)
    tp = len(canonical_matching(edges))
    fp = len(findings) - tp
    fn = len(fixture.issues) - tp
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 1
    result = max(-1, min(1, 2 * f1 - 1 - 0.002 * steps))
    return dict(zip(METRICS, (tp, fp, fn, precision, recall, f1))) | {"return": result}


def check_reference():
    assert canonical_matching({"A": [0, 1], "B": [0]}) == [("A", 1), ("B", 0)]  # M10
    assert canonical_matching({"B": [1, 0], "A": [0, 1]}) == [("A", 0), ("B", 1)]  # M11
    assert canonical_matching({"A": [0, 1]}) == [("A", 0)]  # M12
    assert canonical_matching({"A": [1], "B": [1], "C": [0]}) == [("A", 1), ("C", 0)]
    answer = {
        "type": "fx_error", "affected_ids": ["R2", "R1", "R1"], "claimed_amount_minor": 10000,
        "currency": "KZT", "evidence_ids": ["D2", "D1", "D3"], "explanation": "M01/M03",
    }
    issue = {
        "issue_id": "A", "type": "fx_error", "affected_ids": ["R1", "R2"], "expected_amount_minor": 10000,
        "currency": "KZT", "evidence_sets": [["D1", "D2"]],
    }
    fixture = Fixture(Path(), "example", [issue], {"R1", "R2", "D1", "D2", "D3"}, 0)
    assert grade(fixture, {"episode_id": "example", "findings": [answer]}, 10)["return"] == 0.98
    assert grade(fixture, {"episode_id": "example", "findings": [answer, answer]}, 10)["tp"] == 1
    answer["claimed_amount_minor"] = 10001
    assert grade(fixture, {"episode_id": "example", "findings": [answer]}, 10)["tp"] == 0
    fixture.tolerance = 1
    assert grade(fixture, {"episode_id": "example", "findings": [answer]}, 10)["tp"] == 1
    answer["claimed_amount_minor"] = 10002
    assert grade(fixture, {"episode_id": "example", "findings": [answer]}, 10)["tp"] == 0


def modify(finding, mutation, extra, unknown, rng):
    ids = finding["affected_ids"]
    evidence = finding["evidence_ids"]
    amount = finding["claimed_amount_minor"]
    replacements = {
        "type": ("type", next(t for t in TYPES if t != finding["type"])),
        "affected_add": ("affected_ids", ids + [extra]),
        "affected_remove": ("affected_ids", ids[:-1]),
        "affected_duplicate": ("affected_ids", ids[::-1] + ids[:1]),
        "affected_case": ("affected_ids", [value.swapcase() for value in ids]),
        "amount_minus": ("claimed_amount_minor", amount - 1),
        "amount_plus": ("claimed_amount_minor", amount + 1),
        "currency_case": ("currency", finding["currency"].swapcase()),
        "currency_space": ("currency", finding["currency"] + " "),
        "evidence_subset": ("evidence_ids", evidence[:-1]),
        "evidence_superset": ("evidence_ids", evidence + [extra]),
        "evidence_unknown": ("evidence_ids", evidence + [unknown]),
        "evidence_order": ("evidence_ids", evidence[::-1]),
        "evidence_10": ("evidence_ids", (evidence + [extra] * 10)[:10]),
        "evidence_11": ("evidence_ids", (evidence + [extra] * 11)[:11]),
        "amount_bool": ("claimed_amount_minor", bool(amount)),
        "amount_str": ("claimed_amount_minor", str(amount)),
        "amount_float": ("claimed_amount_minor", float(amount)),
    }
    if mutation in replacements:
        key, value = replacements[mutation]
        finding[key] = value
    elif mutation.startswith("explanation_"):
        max_length = int(mutation.rsplit("_", 1)[1])
        char = "é" if "unicode" in mutation else "x"
        suffix = finding["explanation"]
        finding["explanation"] = char * (max_length - len(suffix)) + suffix
    elif mutation == "missing_field":
        del finding[rng.choice(sorted(FIELDS))]
    elif mutation == "extra_field":
        finding["unexpected"] = True


def submissions(fixture, count, rng):
    oracle = fixture.oracle()
    public = sorted(fixture.public_ids)
    unknown = next(f"unlisted-{i}" for i in range(len(public) + 1) if f"unlisted-{i}" not in fixture.public_ids)
    for index in range(count):
        mutation = MUTATIONS[index % len(MUTATIONS)]
        extra = rng.choice(public)
        token = f" finding {index}"
        findings = [answer | {"explanation": f"{position}{token}"} for position, answer in enumerate(oracle)]
        if not findings:
            findings.append({
                "type": "fx_error", "affected_ids": [extra], "claimed_amount_minor": 10000,
                "currency": "KZT", "evidence_ids": [extra], "explanation": token,
            })
        target = rng.randrange(len(findings))
        answer = findings[target]
        extra = next(value for value in (extra, *public[:20])
                     if value not in answer["affected_ids"] and value not in answer["evidence_ids"])
        if mutation == "empty" or (mutation == "original" and not oracle):
            findings = []
        elif mutation == "drop":
            findings.pop(target)
        elif mutation == "duplicate":
            findings.insert(rng.randrange(len(findings) + 1), answer.copy())
        elif mutation in ("findings_30", "findings_31"):
            size = int(mutation.rsplit("_", 1)[1])
            findings = (findings * size)[:size]
        elif mutation == "reorder":
            rng.shuffle(findings)
        elif mutation == "combined":
            rng.shuffle(findings)
            findings = findings[:rng.randint(1, len(findings))]
            for finding in findings:
                modify(finding, rng.choice(MUTATIONS[4:17]), extra, unknown, rng)
        else:
            modify(answer, mutation, extra, unknown, rng)

        payload = {"episode_id": fixture.episode_id, "findings": findings}
        if mutation == "missing_envelope_key":
            del payload[rng.choice(("episode_id", "findings"))]
        elif mutation == "extra_envelope_key":
            payload["unexpected"] = True
        yield index, mutation, payload, rng.randrange(101)


def differences(expected, actual):
    if expected.keys() != actual.keys():
        return ["keys"]
    discrepancies = []
    for key, value in expected.items():
        received = actual[key]
        if key in ("tp", "fp", "fn") and value is not None:
            same = type(received) is int and received == value
        elif value is None:
            same = received is None
        else:
            same = type(received) in (int, float) and math.isclose(received, value, rel_tol=0, abs_tol=1e-9)
        if not same:
            discrepancies.append(key)
    return discrepancies


def configs():
    for seed in range(71000, 71020):
        for difficulty in ("default", "hard"):
            yield f"{seed}-{difficulty}", seed, {"difficulty": difficulty}
    for number in range(6, 21):
        scenario = f"D{number:02}"
        seed = 71100 + number
        difficulty = "hard" if number % 2 else "default"
        yield scenario, seed, SCENARIOS[scenario] | {"difficulty": difficulty}


def compare_fixture(root, case, count, requested_index):
    label, seed, config = case
    fixture = Fixture.generate(root / label, seed, config)
    rng = random.Random(f"r23 matcher {label}")
    compared = 0
    failures = []
    for index, mutation, payload, steps in submissions(fixture, count, rng):
        if requested_index is not None and index != requested_index:
            continue
        expected = grade(fixture, payload, steps)
        actual = judge.score_episode(str(fixture.path), payload, steps)
        bad = differences(expected, actual)
        compared += 1
        if bad:
            failures.append({
                "fixture": label, "seed": seed, "config": config, "index": index, "mutation": mutation,
                "inspection_steps": steps, "submission": payload, "reference": expected, "adapter": actual,
                "disagreement": bad,
            })
    return label, compared, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="append", help="Limit to a named fixture, e.g. 71000-default or D06")
    parser.add_argument("--per-fixture", type=int, default=2000)
    parser.add_argument("--index", type=int, help="Score just this zero-based submission index in a fixture")
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()
    selected = [case for case in configs() if not args.fixture or case[0] in args.fixture]
    if args.per_fixture < 1 or args.jobs < 1 or not selected:
        parser.error("Select at least one fixture, one submission and one job.")
    if args.index is not None and not 0 <= args.index < args.per_fixture:
        parser.error("--index must be within the generated submission range.")
    check_reference()
    compared = failed = 0
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=SCRATCH) as temp, ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(compare_fixture, Path(temp), case, args.per_fixture, args.index) for case in selected]
        for future in futures:
            label, count, failures = future.result()
            for failure in failures:
                print(json.dumps(failure, sort_keys=True))
            compared += count
            failed += len(failures)
            print(f"{label}: cumulative submissions {compared:,}, disagreements {failed:,}", flush=True)
    print(f"{len(selected)} episodes, {compared:,} submissions compared, disagreements {failed:,}")
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
