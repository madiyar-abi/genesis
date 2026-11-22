"""Independent jury contract matrix from CASE_UPDATES Block 1 and README."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import csv
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import judge_adapter as judge


SCRATCH = Path("/tmp/r23-codex1")
KEYS = {"ledger": "row_id", "invoices": "invoice_id", "payments": "payment_id", "fx": "fx_id"}
EMPTY = {"findings": []}
POLICY = """
import json
import sys
import time

previous = None
for line in sys.stdin:
    request = json.loads(line)
    if "sleep" in request:
        time.sleep(request["sleep"])
        print('"awake"', flush=True)
        continue
    if "response" in request:
        if request.get("reset"):
            episode_id = request["response"][0]["manifest"]["episode_id"]
        previous = request["response"]
        continue
    args = request["args"]
    if args.get("cursor") == "$next":
        args["cursor"] = previous[0]["result"]["next_cursor"]
    if request["name"] == "submit" and isinstance(args["findings"], dict):
        args["findings"].setdefault("episode_id", episode_id)
    print(json.dumps(request, allow_nan=False), flush=True)
"""


def wire(value):
    return json.dumps(value, allow_nan=False, sort_keys=True)


def require(condition, stimulus, observed):
    if not condition:
        raise AssertionError(f"{stimulus} -> {observed!r}")


class Fixture:
    def __init__(self, path, seed, config):
        self.path = path
        judge.generate_episode(seed, config, str(path))
        public = path / "public"
        self.manifest = json.loads((public / "manifest.json").read_text())
        self.policy = json.loads((public / "policy.json").read_text())
        self.task = (public / "task.txt").read_text()
        self.tables = {}
        for table in KEYS:
            if table in ("ledger", "fx"):
                with (public / f"{table}.csv").open(newline="") as stream:
                    self.tables[table] = list(csv.DictReader(stream))
            else:
                self.tables[table] = [
                    json.loads(line) for line in (public / f"{table}.jsonl").read_text().splitlines()
                ]
        self.docs = {
            row["doc_id"]: row for name in ("invoices", "payments") for row in self.tables[name]
        }
        self.ids = set(self.docs)
        for table, rows in self.tables.items():
            self.ids.update(row[KEYS[table]] for row in rows)
        self.unknown = next(f"unlisted-{i}" for i in range(len(self.ids) + 1) if f"unlisted-{i}" not in self.ids)
        self.issues = json.loads((path / "grader" / "truth.json").read_text())["issues"]

    @property
    def episode_id(self):
        return self.manifest["episode_id"]

    def score(self, findings, steps):
        return judge.score_episode(str(self.path), {"episode_id": self.episode_id, **findings}, steps)

    def oracle(self):
        return {"findings": [
            {
                "type": issue["type"], "affected_ids": issue["affected_ids"],
                "claimed_amount_minor": issue["expected_amount_minor"], "currency": issue["currency"],
                "evidence_ids": issue["evidence_sets"][0], "explanation": "Jury oracle",
            }
            for issue in self.issues
        ]}


def csv_view(record):
    return {key: "" if value is None else str(value) for key, value in record.items()}


def canonical(table, record):
    if table in ("ledger", "fx"):
        return csv_view(record)
    if table == "invoices":
        return {key: value for key, value in record.items() if key != "line_items"}
    return record


def bounded_error(error, code):
    return (
        isinstance(error, dict) and set(error) == {"code", "message"}
        and error["code"] == code and isinstance(error["message"], str)
        and 0 < len(error["message"]) <= 512
        and not any(secret in error["message"].lower() for secret in ("truth", "provenance", "seed", "/"))
    )


class Session:
    def __init__(self, child, fixture, seed, mode, *, episode_path=None):
        self.child = child
        self.fixture = fixture
        self.env = judge.make_env()
        self.mode = mode
        self.first = self.env.reset(
            seed, {"mode": mode, "episode_dir": str(episode_path or fixture.path), "team_config": {}}
        )
        require(isinstance(self.first, (list, tuple)) and len(self.first) == 2, "reset pair", self.first)
        self.send({"response": self.first, "reset": True})
        self.steps = 0

    def send(self, data):
        self.child.stdin.write(wire(data) + "\n")
        self.child.stdin.flush()

    def step(self, name, *, oracle=None, **args):
        self.send({"name": name, "args": args})
        action = json.loads(self.child.stdout.readline())
        if oracle is not None:
            action["args"]["findings"].update(oracle)
        response = self.env.step(action)
        require(isinstance(response, (list, tuple)) and len(response) == 5, action, response)
        obs, reward, terminated, truncated, info = response
        require(type(terminated) is bool and type(truncated) is bool, action, response)
        require(set(obs) == {"result", "error", "remaining_steps"}, action, response)
        require(type(obs["remaining_steps"]) is int and 0 <= obs["remaining_steps"] <= 100, action, response)
        if self.mode == "closed":
            require(type(reward) in (int, float) and reward == 0 and info == {}, action, response)
        self.send({"response": response})
        self.steps += 1
        return response

    def result(self, name, **args):
        obs, _, terminated, truncated, _ = self.step(name, **args)
        require(obs["error"] is None and not terminated and not truncated, (name, args), obs)
        require(obs["remaining_steps"] == 100 - self.steps, (name, args), obs)
        return obs["result"]

    def error(self, code, name, **args):
        obs, _, terminated, truncated, _ = self.step(name, **args)
        require(
            obs["result"] is None and not terminated and not truncated
            and obs["remaining_steps"] == 100 - self.steps and bounded_error(obs["error"], code),
            (name, args, code), obs,
        )

    def page(self, table="ledger", cursor=None):
        result = self.result("list_records", table=table, cursor=cursor, limit=50)
        require(set(result) == {"records", "next_cursor"}, "page shape", result)
        require(isinstance(result["records"], list) and len(result["records"]) <= 50, "page size", result)
        require(result["next_cursor"] is None or isinstance(result["next_cursor"], str), "cursor", result)
        return result

    def scan(self, table):
        page = self.page(table)
        records = list(page["records"])
        seen = set()
        while (cursor := page["next_cursor"]) is not None:
            require(cursor not in seen, (table, "repeated cursor"), cursor)
            seen.add(cursor)
            page = self.page(table, "$next")
            records.extend(page["records"])
        expected = self.fixture.tables[table]
        actual = [canonical(table, row) for row in records]
        actual = Counter(map(wire, actual))
        expected = Counter(wire(canonical(table, row)) for row in expected)
        if actual != expected:
            require(False, (table, "page coverage"), {
                "missing": list((expected - actual).elements())[:3],
                "extra": list((actual - expected).elements())[:3],
            })
        return records

    def record(self):
        row = self.fixture.tables["ledger"][0]
        result = self.result("get_record", table="ledger", id=row["row_id"])
        require(csv_view(result) == row, "get_record R1", result)

    def document(self):
        doc_id, doc = next(iter(self.fixture.docs.items()))
        result = self.result("get_document", doc_id=doc_id)
        require(result == doc, "get_document D1", result)

    def terminal(self, findings, *, truncates, inspection_steps=None, oracle=None):
        if truncates:
            response = self.step("calculator", expression="1")
        else:
            response = self.step("submit", findings=findings, oracle=oracle)
        obs, reward, terminated, truncated, info = response
        require((terminated, truncated) == (not truncates, truncates), "terminal flags", response)
        if not truncates:
            require(obs["result"] == {"accepted": True} and obs["error"] is None, "submit result", response)
        if self.mode == "train":
            expected = self.fixture.score(EMPTY if truncates else findings, inspection_steps)
            require(reward == expected["return"] and info.get("inspection_steps") == inspection_steps
                    and {key: info.get(key) for key in expected if key != "return"}
                    == {key: value for key, value in expected.items() if key != "return"},
                    ("terminal grader metrics", expected), response)
        return response

    def after_terminal(self, remaining_steps):
        obs, reward, terminated, truncated, info = self.step("submit", findings=EMPTY, oracle=self.fixture.oracle())
        require(obs["result"] is None and obs["error"]["code"] == "episode_over"
                and obs["remaining_steps"] == remaining_steps and reward == 0,
                "late submission", (obs, reward, terminated, truncated, info))


def reset_payload(session, *, fallback=False):
    obs, info = session.first
    f = session.fixture
    task = f.task.rstrip("\n")
    if fallback:
        task = obs.get("task")
        require(isinstance(task, str) and bool(task.strip()), "closed reset without public/task.txt", task)
    require(obs == {"task": task, "manifest": f.manifest, "policy": f.policy, "remaining_steps": 100},
            "reset public payload", {key: obs.get(key) for key in obs if key not in ("task", "policy")})
    require(info == {"episode_id": f.episode_id, "mode": "closed", "max_steps": 100}, "reset info", info)


def invalid_closed_submissions(child, fixture, seed):
    # These findings are structurally valid individually. The first payload exceeds only the list limit.
    finding = {
        "type": "duplicate_invoice", "affected_ids": [fixture.unknown], "claimed_amount_minor": 1,
        "currency": fixture.manifest["base_currency"], "evidence_ids": [next(iter(fixture.docs))],
        "explanation": "Structurally valid test finding",
    }
    too_many = {"episode_id": fixture.episode_id, "findings": [finding] * 31}
    invalid_score = dict.fromkeys(("tp", "fp", "fn", "precision", "recall", "f1")) | {"return": -1}
    for label, payload in (("31 findings", too_many), ("non-object findings", [])):
        session = Session(child, fixture, seed, "closed")
        obs, _, terminated, truncated, _ = session.step("submit", findings=payload)
        require(terminated and not truncated and obs["result"] is None and obs["remaining_steps"] == 99
                and bounded_error(obs["error"], "invalid_findings"), label, obs)
        score = judge.score_episode(str(fixture.path), payload, 0)
        require(score == invalid_score, (label, "private grading"), score)


def run_case(n, child, fixtures, seed):
    clean, error, large = fixtures
    fixture = large if n in (5, 6) else error if 15 <= n <= 19 else clean
    s = Session(child, fixture, seed, "train" if n in (15, 17, 18) else "closed")
    if n == 1:
        require(all(isinstance(value, dict) for value in s.first), "reset values", s.first)
        s.page()
    elif n == 2:
        reset_payload(s)
        with tempfile.TemporaryDirectory(dir=fixture.path.parent) as temp:
            copy = Path(temp) / "without-task"
            shutil.copytree(fixture.path, copy)
            (copy / "public" / "task.txt").unlink()
            reset_payload(Session(child, fixture, seed, "closed", episode_path=copy), fallback=True)
    elif n == 3:
        manifest = s.first[0]["manifest"]
        fields = {"schema_version", "episode_id", "base_currency", "period_start", "period_end",
                  "timezone", "counts", "rounding"}
        require(fields <= manifest.keys() and all(manifest[key] for key in fields), "manifest fields", manifest)
        require(date.fromisoformat(manifest["period_start"]) <= date.fromisoformat(manifest["period_end"]),
                "manifest period", manifest)
        counts = {table: len(rows) for table, rows in fixture.tables.items()} | {"documents": len(fixture.docs)}
        require(manifest == fixture.manifest and manifest["counts"] == counts, ("manifest counts", counts), manifest)
    elif n == 4:
        s.page()
    elif n == 5:
        require(len(large.tables["ledger"]) >= 101, "L fixture row count", len(large.tables["ledger"]))
        s.scan("ledger")
        require(s.steps >= 3, "L three pages", s.steps)
    elif n == 6:
        cursor = s.page()["next_cursor"]
        require(cursor is not None, "L second cursor", cursor)
        first, second = s.page(cursor=cursor), s.page(cursor=cursor)
        require(first == second, "same cursor twice", (first, second))
    elif n == 7:
        s.record()
    elif n == 8:
        s.document()
        s.error("not_found", "get_document", doc_id="../grader/truth.json")
    elif n == 9:
        result = s.result("calculator", expression="0.1+0.2")
        require(isinstance(result, str) and Decimal(result) == Decimal("0.3"), "0.1+0.2", result)
    elif n == 10:
        s.error("calc_error", "calculator", expression="file")
    elif n == 11:
        s.error("not_found", "get_record", table="ledger", id=fixture.unknown)
        s.record()
    elif n == 12:
        s.error("not_found", "get_document", doc_id=fixture.unknown)
    elif n == 13:
        s.error("unknown_action", "unlisted_action")
    elif n == 14:
        s.record()
        s.error("not_found", "get_record", table="ledger", id=fixture.unknown)
        s.record()
    elif n == 15:
        s.record()
        response = s.terminal(EMPTY, truncates=False, inspection_steps=1)
        s.after_terminal(response[0]["remaining_steps"])
    elif n == 16:
        for _ in range(99):
            s.result("calculator", expression="1")
        response = s.terminal(EMPTY, truncates=False)
        require(response[0]["remaining_steps"] == 0, "100th action submit", response)
    elif n in (17, 18):
        count = 99 if n == 17 else 1
        for _ in range(count):
            s.result("calculator", expression="1")
        if n == 18:
            # The policy sleeps after receiving the jury's public response.
            s.send({"sleep": 60.1})
            require(s.child.stdout.readline().strip() == '"awake"', "policy resumed after 60.1 s", "no acknowledgment")
        response = s.terminal(EMPTY, truncates=True, inspection_steps=count + 1)
        s.after_terminal(response[0]["remaining_steps"])
    elif n == 19:
        s.record()
        s.document()
        s.result("calculator", expression="1")
        oracle = fixture.oracle()
        s.terminal(EMPTY, truncates=False, oracle=oracle)
        expected = {"tp": 1, "fp": 0, "fn": 0, "precision": 1, "recall": 1, "f1": 1, "return": 0.994}
        observed = fixture.score(oracle, 3)
        require(observed == expected, ("private grading", expected), observed)
        invalid_closed_submissions(child, fixture, seed)
    elif n == 20:
        for f in (clean, error):
            s = Session(child, f, seed, "closed")
            reset_payload(s)
            for table, id_key in KEYS.items():
                for row in s.scan(table)[:1]:
                    expected = next(item for item in f.tables[table] if item[id_key] == row[id_key])
                    result = s.result("get_record", table=table, id=row[id_key])
                    require((csv_view(result) if table in ("ledger", "fx") else result) == expected,
                            (table, "get_record", row[id_key]), result)
            # All docs are publicly listed. Pull each, resetting before the step budget runs out.
            for doc_id, doc in f.docs.items():
                if s.steps == 99:
                    s = Session(child, f, seed, "closed")
                result = s.result("get_document", doc_id=doc_id)
                require(result == doc, ("get_document", doc_id), result)
            s = Session(child, f, seed, "closed")
            s.error("not_found", "get_document", doc_id="../grader/provenance.json")
            s.error("not_found", "get_record", table="ledger", id=f.unknown)
            s.error("unknown_action", "unlisted_action")
            s.error("unknown_table", "list_records", table="unlisted_table", cursor=None, limit=50)
            s.error("calc_error", "calculator", expression="file")
            s.terminal(EMPTY, truncates=False)


def policy_process(directory):
    # No repo import path, inherited environment variables, episode path, key or grader handles.
    command = [str(Path(sys.executable).resolve()), "-I", "-S", "-u", "-c", POLICY]
    sandbox = shutil.which("sandbox-exec")
    if sandbox is None:
        raise RuntimeError("This matrix requires macOS sandbox-exec to isolate the policy process.")
    denied = (Path.cwd(), SCRATCH.resolve(), Path.home() / ".auditenv")
    rules = " ".join(f"(subpath {wire(str(path))})" for path in denied)
    profile = f"(version 1) (allow default) (deny network*) (deny file-read* {rules})"
    command = [sandbox, "-p", profile, *command]
    return subprocess.Popen(command, cwd=directory, env={}, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def cohort(seed, difficulty, root, cases):
    config = {"difficulty": difficulty, "errors": {}, "interacting": {"I1": 0, "I2": 0}}
    directory = root / f"{seed}-{difficulty}"
    fixtures = (
        Fixture(directory / "C", seed, config),
        Fixture(directory / "E", seed, config | {"errors": {"duplicate_invoice": 1}}),
        Fixture(directory / "L", seed, config),
    )
    require([len(f.issues) for f in fixtures] == [0, 1, 0], "fixture issue counts", config)
    passed = Counter()
    with ExitStack() as stack:
        modes = {"train" if n in (15, 17, 18) else "closed" for n in cases}
        children = {mode: stack.enter_context(policy_process(root / "policy")) for mode in modes}
        for n in cases:
            child = children["train" if n in (15, 17, 18) else "closed"]
            try:
                run_case(n, child, fixtures, seed)
            except (AssertionError, ValueError, KeyError, TypeError) as exc:
                print(f"C{n:02} seed={seed} difficulty={difficulty}: {exc}", flush=True)
            else:
                passed[n] += 1
        for child in children.values():
            child.stdin.close()
            require(child.wait() == 0, "policy process exit", child.returncode)
    print(f"Completed seed={seed} difficulty={difficulty}", flush=True)
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--difficulty", choices=("default", "hard"), action="append")
    parser.add_argument("--case", type=int, choices=range(1, 21), action="append")
    args = parser.parse_args()
    seeds = args.seed or range(70000, 70005)
    difficulties = args.difficulty or ("default", "hard")
    cases = args.case or range(1, 21)
    passed = Counter()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
        root = Path(temporary)
        (root / "policy").mkdir()
        with ThreadPoolExecutor(max_workers=10) as pool:
            runs = [pool.submit(cohort, seed, difficulty, root, cases)
                    for seed in seeds for difficulty in difficulties]
            for run in runs:
                passed.update(run.result())
    total = len(seeds) * len(difficulties)
    for n in cases:
        print(f"C{n:02} pass {passed[n]}/{total}")
    return int(any(passed[n] != total for n in cases))


if __name__ == "__main__":
    raise SystemExit(main())
