"""Closed reset and directory verification must handle malformed exported files."""

import csv
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

import judge_adapter
from auditenv.generator import TASK_HARD, TASK_TEXT
from auditenv.verify import main


EXAMPLE = Path(__file__).resolve().parents[1] / "episodes/dev"
FILES = (
    "public/task.txt", "public/manifest.json", "public/policy.json", "public/ledger.csv",
    "public/invoices.jsonl", "public/payments.jsonl", "public/fx.csv", "grader/truth.json",
    "grader/provenance.json",
)
RESET = {"mode": "closed"}
CALCULATE = {"name": "calculator", "args": {"expression": "1"}}


def csv_edit(path, edit):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    edit(rows)
    with path.open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows(rows)


def csv_cell(path, key, value):
    csv_edit(path, lambda rows: rows[1].__setitem__(rows[0].index(key), value))


def json_field(path, key, value):
    lines = path.read_text(encoding="utf-8").splitlines() if path.suffix == ".jsonl" else [
        path.read_text(encoding="utf-8")
    ]
    record = json.loads(lines[0])
    record[key] = value
    path.write_text("\n".join([json.dumps(record), *lines[1:]]) + "\n", encoding="utf-8")


def replace_file(path, replacement):
    path.unlink()
    replacement(path)


class ExportLoaderRedTeam(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        entry = next(e for e in json.loads((EXAMPLE / "index.json").read_text()) if e["seed"] == 2003)
        self.example = EXAMPLE / entry["episode_id"]
        self.episode = self.root / self.example.name

    def check_case(self, filename, edit, adapter_ok=False, verify_ok=False):
        if self.episode.exists():
            shutil.rmtree(self.episode)
        shutil.copytree(self.example, self.episode)
        edit(self.episode / filename)
        env = judge_adapter.make_env()
        original, _ = env.reset(0, {**RESET, "episode_dir": self.example})
        env.step(CALCULATE)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            if adapter_ok:
                observation, _ = env.reset(0, {**RESET, "episode_dir": self.episode})
                json.dumps(observation, allow_nan=False)
                self.assertEqual(observation["manifest"], original["manifest"])
            else:
                with self.assertRaises(ValueError) as rejected:
                    env.reset(0, {**RESET, "episode_dir": self.episode})
                self.assertNotIn(str(self.root), str(rejected.exception))
                self.assertNotIn("Traceback", str(rejected.exception))
                obs, reward, terminated, truncated, info = env.step(CALCULATE)
                self.assertEqual((obs["remaining_steps"], reward, terminated, truncated, info),
                                 (98, 0, False, False, {}))
        self.assertEqual(out.getvalue() + err.getvalue(), "")
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            status = main(["--dir", str(self.root)])
        self.assertEqual(status, 0 if verify_ok else 1, out.getvalue())
        self.assertNotIn("Traceback", out.getvalue() + err.getvalue())
        if verify_ok:
            self.assertIn("1/1 episodes valid", out.getvalue())
        else:
            self.assertIn("0/1 episodes valid", out.getvalue())

    def test_file_presence_and_encoding(self):
        for filename in FILES:
            operations = {
                "missing": Path.unlink,
                "empty": lambda p: p.write_bytes(b""),
                "invalid utf8": lambda p: p.write_bytes(b"\xff" + p.read_bytes()),
                "NUL": lambda p: p.write_bytes(p.read_bytes().replace(b"USD", b"USD\0", 1)
                                                if b"USD" in p.read_bytes() else p.read_bytes() + b"\0"),
                "directory": lambda p: replace_file(p, Path.mkdir),
                "symlink": lambda p: replace_file(p, lambda f: f.symlink_to(self.example / filename)),
                "BOM": lambda p: p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes()),
                "CRLF": lambda p: p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n")),
                "trailing blanks": lambda p: p.write_bytes(p.read_bytes() + b"\n\n"),
            }
            for label, operation in operations.items():
                with self.subTest(file=filename, edit=label):
                    verify_ok = label in ("BOM", "CRLF", "trailing blanks")
                    adapter_ok = verify_ok or (filename in ("public/task.txt", "grader/provenance.json")
                                                and label == "missing")
                    self.check_case(filename, operation, adapter_ok, verify_ok)

    def test_csv_columns(self):
        for filename in ("public/ledger.csv", "public/fx.csv"):
            operations = {
                "header only": lambda rows: rows.__delitem__(slice(1, None)),
                "extra column": lambda rows: [row.append("extra") for row in rows],
                "missing column": lambda rows: [row.pop() for row in rows],
                "duplicate column": lambda rows: [row.append(row[0]) for row in rows],
                "reordered columns": lambda rows: [row.reverse() for row in rows],
                "extra cell": lambda rows: rows[1].append("extra"),
                "missing cell": lambda rows: rows[1].pop(),
            }
            for label, operation in operations.items():
                with self.subTest(file=filename, edit=label):
                    valid = label == "reordered columns"
                    self.check_case(filename, lambda p: csv_edit(p, operation), valid, valid)

    def test_ledger_amount_spellings(self):
        column = "debit_minor"
        with (self.example / "public/ledger.csv").open(newline="") as stream:
            original = int(next(csv.DictReader(stream))[column])
        for value in ("1.5", "1e3", str(10**30), " " + str(original), "+" + str(original),
                      "0" + str(original), "-0"):
            with self.subTest(amount=value):
                valid = value in (" " + str(original), "+" + str(original), "0" + str(original), "-0")
                field = column if value != "-0" or original == 0 else "credit_minor"
                self.check_case("public/ledger.csv", lambda p: csv_cell(p, field, value), valid, valid)

    def test_json_and_record_fields(self):
        for filename in ("public/manifest.json", "public/policy.json"):
            for name, raw in (("duplicate", '"base_currency":"ignored",'),
                              ("NaN", '"extra": NaN,'), ("infinity", '"extra": 1e999,')):
                with self.subTest(file=filename, edit=name):
                    self.check_case(filename, lambda p: p.write_text("{" + raw + p.read_text()[1:]))
        for filename, field, value in (
            ("public/manifest.json", "counts", []),
            ("public/policy.json", "period", []),
            ("public/policy.json", "findings", {"tolerance_minor": 1.5}),
            ("public/ledger.csv", "invoice_id", "unknown"),
            ("public/invoices.jsonl", "issued_at", "2026-02-30T00:00:00+00:00"),
            ("public/invoices.jsonl", "issued_at", "2026-2-3T00:00:00+00:00"),
            ("public/payments.jsonl", "invoice_refs", [{"invoice_id": "unknown", "amount_minor": 1}]),
            ("public/fx.csv", "date", "2026-02-30"),
            ("public/fx.csv", "date", "2026-2-3"),
            ("grader/truth.json", "issues", {}),
            ("grader/provenance.json", "injections", {}),
        ):
            with self.subTest(file=filename, field=field, value=value):
                edit = csv_cell if filename.endswith(".csv") else json_field
                self.check_case(filename, lambda p: edit(p, field, value))
        for filename in ("public/invoices.jsonl", "public/payments.jsonl"):
            for contents in ("invoice_id,doc_id\n", None):
                with self.subTest(file=filename, duplicated=contents is None):
                    self.check_case(filename, lambda p: p.write_text(
                        contents if contents else "\n".join([p.read_text().splitlines()[0], *p.read_text().splitlines()[:-1]]) + "\n"
                    ))


    def test_minimal_policy_and_optional_jury_files(self):
        shutil.copytree(self.example, self.episode)
        public = self.episode / "public"
        (public / "task.txt").unlink()
        (self.episode / "grader" / "provenance.json").unlink()

        def omit_fx_id(rows):
            index = rows[0].index("fx_id")
            for row in rows:
                del row[index]

        csv_edit(public / "fx.csv", omit_fx_id)
        policy = public / "policy.json"
        policy.write_text('  { "findings": { "tolerance_minor": 1 } } \n', encoding="utf-8")
        first, _ = judge_adapter.make_env().reset(0, {**RESET, "episode_dir": self.episode})
        fx = public / "fx.csv"
        fx.write_text(" \t\n" + fx.read_text(encoding="utf-8") + "  \t\n", encoding="utf-8")
        again, _ = judge_adapter.make_env().reset(0, {**RESET, "episode_dir": self.episode})
        self.assertEqual(again, first)
        self.assertEqual(first["task"], TASK_TEXT)  # C02: the case's file list has no task.txt; the task stays
        self.assertEqual(first["policy"], {"findings": {"tolerance_minor": 1}})
        answer = {"episode_id": first["manifest"]["episode_id"], "findings": []}
        self.assertGreater(judge_adapter.score_episode(self.episode, answer, 0)["fn"], 0)

    def test_missing_task_text_falls_back_to_the_published_task(self):
        """C02 needs a task in the first observation; the case's file list has no task.txt (hard keeps its rule)."""
        for split, expected in (("dev", TASK_TEXT), ("hard", TASK_TEXT + TASK_HARD)):
            with self.subTest(split=split):
                episode = self.episode.parent / f"no-task-{split}"
                shutil.copytree(sorted((EXAMPLE.parent / split).glob("ep_*"))[0], episode)
                self.assertEqual((episode / "public/task.txt").read_text(encoding="utf-8"), expected)
                (episode / "public/task.txt").unlink()
                first, _ = judge_adapter.make_env().reset(0, {**RESET, "episode_dir": str(episode)})
                self.assertEqual(first["task"], expected)

    def test_grading_accepts_finite_positive_decimal_spellings(self):
        for rate in (" +1.25 ", ".125", "1.25e-1", "1000000000"):
            with self.subTest(rate=rate):
                self.check_case("public/fx.csv", lambda p: csv_cell(p, "rate", rate), adapter_ok=True)
        for rate in ("NaN", "Infinity", "0", "-0.1", "1_000"):
            with self.subTest(rate=rate):
                self.check_case("public/fx.csv", lambda p: csv_cell(p, "rate", rate))

    def test_expense_timestamp_can_use_an_equivalent_timezone_offset(self):
        def shift_expense(rows):
            timestamp, invoice, payment = [rows[0].index(name) for name in ("timestamp", "invoice_id", "payment_id")]
            row = next(row for row in rows[1:] if not row[invoice] and not row[payment])
            instant = datetime.fromisoformat(row[timestamp])
            offset = timezone(timedelta(hours=1) if instant.utcoffset() != timedelta(hours=1) else timedelta())
            row[timestamp] = instant.astimezone(offset).isoformat()

        self.check_case("public/ledger.csv", lambda p: csv_edit(p, shift_expense), adapter_ok=True, verify_ok=True)


class SeparateIdSpaces(unittest.TestCase):
    """The jury renames each id space on its own, so "identical strings in different tables" are legal
    (published check definitions, paired block): a ledger row_id equal to a document's doc_id still loads."""

    def test_row_id_equal_to_a_doc_id_loads_in_closed_reset(self):
        entry = next(e for e in json.loads((EXAMPLE / "index.json").read_text()) if e["seed"] == 2003)
        with tempfile.TemporaryDirectory() as temp:
            episode = Path(temp) / entry["episode_id"]
            shutil.copytree(EXAMPLE / entry["episode_id"], episode)
            truth = json.loads((episode / "grader/truth.json").read_text())
            cited = {i for issue in truth["issues"] for s in issue["evidence_sets"] for i in s}
            doc_id = json.loads((episode / "public/invoices.jsonl").read_text().splitlines()[0])["doc_id"]

            def rename(rows):
                col = rows[0].index("row_id")
                next(r for r in rows[1:] if r[col] not in cited)[col] = doc_id

            csv_edit(episode / "public/ledger.csv", rename)
            observation, _ = judge_adapter.make_env().reset(0, {**RESET, "episode_dir": str(episode)})
            self.assertEqual(observation["manifest"]["episode_id"], entry["episode_id"])
