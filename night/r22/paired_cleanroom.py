"""Replay the organizer's Block 4 matrix and a combined transform on every pair."""

import csv
import json
import random
import re
import tempfile
from collections import Counter
from copy import deepcopy
from pathlib import Path
from statistics import mean

import judge_adapter
from auditenv.export import export_episode
from auditenv.generator import generate
from auditenv.jury import SCENARIOS
from auditenv.policy_worker import JuryPolicy
from auditenv.run import make_policy

SCRATCH = Path("/tmp/r22-codex2")
TABLES = ("ledger.csv", "invoices.jsonl", "payments.jsonl", "fx.csv")
DOCUMENTS = ("manifest.json", "policy.json", "task.txt")
ID_FIELDS = {key: key for key in (
    "row_id", "doc_id", "entity_id", "invoice_id", "payment_id", "episode_id", "issue_id"
)}
MULTI_IDS = {"affected_ids", "evidence_ids", "evidence_sets", "documents_added"}
SCORE_FIELDS = ("tp", "fp", "fn", "precision", "recall", "f1")


def read(path):
    with path.open(encoding="utf-8", newline="") as source:
        if path.suffix == ".csv":
            reader = csv.DictReader(source)
            return reader.fieldnames, list(reader)
        if path.suffix == ".jsonl":
            return None, [json.loads(line) for line in source]
        if path.suffix == ".json":
            return None, json.load(source)
        return None, source.read()


def write(path, headers, value):
    with path.open("w", encoding="utf-8", newline="") as out:
        if headers is not None:
            writer = csv.DictWriter(out, headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(value)
        elif path.suffix == ".jsonl":
            for row in value:
                print(json.dumps(row, ensure_ascii=False), file=out)
        elif path.suffix == ".json":
            print(json.dumps(value, ensure_ascii=False, indent=2), file=out)
        else:
            out.write(value)


def strings(value, path=""):
    """Visit string leaves without flattening ordered lists in the rewritten value."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield from strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for child in value:
            yield from strings(child, path + "[]")
    elif isinstance(value, str) and value:
        yield path, value


class Bijection:
    def __init__(self, records, rng):
        self.by_field = {}
        sources = {}
        for record in records:
            for path, value in strings(record):
                field = path.rsplit(".", 1)[-1]
                namespace = ID_FIELDS.get(field)
                if namespace:
                    sources.setdefault(value, set()).add(namespace)
        reserved = set(sources)
        for value, namespaces in sorted(sources.items()):
            for namespace in sorted(namespaces):
                fresh = f"{namespace}-{rng.getrandbits(96):024x}"
                while fresh in reserved:
                    fresh = f"{namespace}-{rng.getrandbits(96):024x}"
                self.by_field[namespace, value] = fresh
                reserved.add(fresh)
        self.sources = sources
        self.pattern = re.compile(
            r"(?<![\w])(?:" + "|".join(map(re.escape, sorted(sources, key=lambda s: (-len(s), s)))) + r")(?![\w])"
        )

    def lookup(self, value):
        namespaces = self.sources[value]
        if len(namespaces) != 1:
            raise ValueError(f"Unqualified ID {value!r} matches namespaces {sorted(namespaces)}")
        return self.by_field[next(iter(namespaces)), value]

    def rewrite(self, value, field="", rename=True):
        if isinstance(value, dict):
            return {key: self.rewrite(child, key, rename) for key, child in value.items()}
        if isinstance(value, list):
            return [self.rewrite(child, field, rename) for child in value]
        if not rename or not isinstance(value, str) or not value:
            return value
        if field in ID_FIELDS:
            return self.by_field[ID_FIELDS[field], value]
        if field == "fx_id":
            return value
        return self.pattern.sub(lambda match: self.lookup(match[0]), value)


def oracle_answer(truth):
    """Build the reference submission inside the grader, using one complete evidence set."""
    return {"episode_id": truth["episode_id"], "findings": [
        {"type": issue["type"], "affected_ids": issue["affected_ids"],
         "claimed_amount_minor": issue["expected_amount_minor"], "currency": issue["currency"],
         "evidence_ids": issue["evidence_sets"][0], "explanation": "oracle"}
        for issue in truth["issues"]
    ]}


def permute(rows, rng):
    if len(rows) < 2:
        return rows
    shuffled = rows[:]
    rng.shuffle(shuffled)
    return shuffled if shuffled != rows else shuffled[1:] + shuffled[:1]


def reset(env, path):
    obs, _ = env.reset(0, {"mode": "closed", "episode_dir": str(path)})
    return obs


def play(path, policy_name, actions=None):
    env = judge_adapter.make_env()
    obs = reset(env, path)
    trace = [deepcopy(obs)]
    replay = iter(actions) if actions is not None else None
    actor = JuryPolicy(make_policy(policy_name, env)) if replay is None else None
    submitted = []
    for _ in range(obs["remaining_steps"]):
        action = next(replay) if replay is not None else actor.act(obs)
        submitted.append(deepcopy(action))
        step = env.step(action)
        trace.append(deepcopy(step))
        obs, reward, ended, truncated, _ = step
        if obs["error"] or truncated or reward != 0:
            raise AssertionError(f"Unexpected closed step {step!r} for {action!r}")
        if ended:
            if action["name"] != "submit" or (actions is not None and len(actions) != len(submitted)):
                raise AssertionError("Replay ended before the expected submission")
            grade = env.grader_log[-1]
            return submitted, trace, {**{key: grade[key] for key in SCORE_FIELDS}, "return": grade["reward"]}
    raise AssertionError("No terminal submission")


def check_adapter(path, expected, evidence_documents):
    """Read every shuffled table through the adapter to verify record order and reachable evidence."""
    env = judge_adapter.make_env()
    first = reset(env, path)
    for name, expected_records in expected.items():
        cursor = None
        actual = []
        while True:
            action = {"name": "list_records", "args": {"table": name, "cursor": cursor}}
            obs, reward, ended, truncated, _ = env.step(action)
            if obs["error"] or reward or ended or truncated:
                raise AssertionError(f"Cannot read copied {name}: {obs!r}")
            result = obs["result"]
            actual.extend(result["records"])
            cursor = result["next_cursor"]
            if cursor is None:
                break
        if actual != expected_records:
            raise AssertionError(f"Adapter returned different copied {name} records")
    for doc_id, document in evidence_documents.items():
        obs, reward, ended, truncated, _ = env.step({"name": "get_document", "args": {"doc_id": doc_id}})
        if obs["error"] or reward or ended or truncated or obs["result"] != document:
            raise AssertionError(f"Adapter returned different copied evidence document {doc_id}: {obs!r}")
    return first


def adapter_records(name, rows):
    if name == "ledger":
        return [{key: int(value) if key in {"debit_minor", "credit_minor"} else value or None
                 for key, value in row.items()} for row in rows]
    if name == "invoices":
        return [{key: value for key, value in row.items() if key != "line_items"} for row in rows]
    return rows


def compare_episode(original, copies, policy_name, rng, variants, scanned, embedded):
    public = {name: read(original / "public" / name) for name in (*TABLES, *DOCUMENTS)}
    # Grader files are only used here to build the oracle and translate the private copy.
    grader = {path.name: read(path) for path in (original / "grader").glob("*.json")}
    bijection = Bijection([value for _, value in (*public.values(), *grader.values())], rng)
    for name, (_, value) in public.items():
        for path, string in strings(value):
            field = path.rsplit(".", 1)[-1]
            if field not in ID_FIELDS and field not in MULTI_IDS and field != "fx_id":
                label = f"{name}{path.removeprefix('[]')}"
                scanned.add(label)
                embedded.update({label: len(bijection.pattern.findall(string))})
    oracle = oracle_answer(grader["truth.json"][1])
    actions, trace, closed = play(original, policy_name)
    _, repeated, repeated_score = play(original, policy_name, actions)
    if trace != repeated or closed != repeated_score:
        raise AssertionError("Same-action original replay changed observable transitions")
    policy_submission = actions[-1]["args"]["findings"]
    steps = len(actions) - 1
    reference = {
        policy_name: judge_adapter.score_episode(str(original), policy_submission, steps),
        "oracle": judge_adapter.score_episode(str(original), oracle, 0),
    }
    if closed != reference[policy_name] or reference["oracle"]["f1"] != 1 or reference["oracle"]["return"] != 1:
        raise AssertionError(f"Unexpected reference scores: {reference!r}; closed {closed!r}")
    results = {}
    for variant, (shuffle, rename) in variants.items():
        copy = copies / variant
        (copy / "public").mkdir(parents=True)
        (copy / "grader").mkdir()
        expected = {}
        mapped_oracle = bijection.rewrite(oracle, rename=rename)
        evidence = {evidence_id for finding in mapped_oracle["findings"] for evidence_id in finding["evidence_ids"]}
        evidence_documents = {}
        for name, (headers, value) in public.items():
            transformed = bijection.rewrite(value, rename=rename)
            if name in TABLES:
                if shuffle:
                    transformed = permute(transformed, rng)
                table = Path(name).stem
                expected[table] = adapter_records(table, transformed)
                if table in {"invoices", "payments"}:
                    evidence_documents.update((row["doc_id"], row) for row in transformed if row["doc_id"] in evidence)
            write(copy / "public" / name, headers, transformed)
        for name, (headers, value) in grader.items():
            write(copy / "grader" / name, headers, bijection.rewrite(value, rename=rename))
        first = check_adapter(copy, expected, evidence_documents)
        for name, field in (("manifest.json", "manifest"), ("policy.json", "policy"), ("task.txt", "task")):
            if first[field] != bijection.rewrite(public[name][1], rename=rename):
                raise AssertionError(f"Adapter returned different copied {name}")
        mapped_actions = bijection.rewrite(actions, rename=rename)
        _, _, copied_closed = play(copy, policy_name, mapped_actions)
        _, _, oracle_closed = play(copy, "oracle", [{"name": "submit", "args": {"findings": mapped_oracle}}])
        copied = {
            policy_name: judge_adapter.score_episode(str(copy), mapped_actions[-1]["args"]["findings"], steps),
            "oracle": judge_adapter.score_episode(str(copy), mapped_oracle, 0),
        }
        if copied_closed != copied[policy_name]:
            raise AssertionError(f"{variant} replay score {copied_closed!r} differs from offline {copied[policy_name]!r}")
        if oracle_closed != copied["oracle"]:
            raise AssertionError(f"{variant} oracle score {oracle_closed!r} differs from offline {copied['oracle']!r}")
        results[variant] = copied
    return reference, results


def main():
    SCRATCH.mkdir(exist_ok=True)
    failures = []
    scanned, embedded = set(), Counter()
    print("| Scenario | Reconcile original F1 / return | Combined copy F1 / return | Oracle original → copy | "
          "Combined equal | Matrix equal |", flush=True)
    print("|---|---:|---:|---:|---:|---:|", flush=True)
    for number, (scenario, config) in enumerate(SCENARIOS.items(), start=1):
        variants = {"combined": (True, True)}
        matrix = "combined"
        if number <= 10:
            matrix = "matrix"
            variants[matrix] = (number <= 5, number > 5)
        means = [[], [], [], [], [], []]
        equal = Counter()
        for difficulty, policy in (("default", "reconcile"), ("hard", "reconcile_hard")):
            for seed in range(55000, 55010):
                with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
                    original = Path(tmp) / "original"
                    try:
                        export_episode(generate(seed, {**config, "difficulty": difficulty}), str(original))
                        source, results = compare_episode(
                            original, Path(tmp), policy, random.Random(seed), variants, scanned, embedded
                        )
                        combined = results["combined"]
                        for values, score in zip(means, (
                            source[policy]["f1"], source[policy]["return"],
                            combined[policy]["f1"], combined[policy]["return"],
                            source["oracle"]["return"], combined["oracle"]["return"],
                        )):
                            values.append(score)
                        for variant, copied in results.items():
                            if source == copied:
                                equal[variant] += 1
                            else:
                                failures.append(f"{scenario} {difficulty} seed {seed} {variant}: "
                                                f"original={source!r} copy={copied!r}")
                    except (AssertionError, ValueError, KeyError, StopIteration) as exc:
                        failures.append(f"{scenario} {difficulty} seed {seed}: {type(exc).__name__}: {exc}")
        values = [f"{mean(series):.4f}" if series else "—" for series in means]
        a, b, c, d, e, f = values
        print(f"| {scenario} | {a} / {b} | {c} / {d} | {e} → {f} | {equal['combined']}/20 | "
              f"{equal[matrix]}/20 |", flush=True)
    print("Free-text locations searched:", ", ".join(sorted(scanned)))
    print("Embedded IDs:", dict(sorted((path, count) for path, count in embedded.items() if count)) or "none found")
    for failure in failures:
        print(failure)
    print(f"Discrepancies: {len(failures)}")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
