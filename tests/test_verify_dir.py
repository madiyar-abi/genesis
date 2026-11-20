import csv
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from auditenv.verify import main


class VerifyDirectoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.example = next((Path(__file__).resolve().parents[1] / "episodes/dev").glob("ep_*"))

    def verify(self, expected_status):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["--dir", str(self.root)]), expected_status)
        return output.getvalue()

    def test_duplicate_csv_columns(self):
        public = shutil.copytree(self.example, self.root / self.example.name) / "public"
        for filename, field in (("ledger.csv", "debit_minor"), ("fx.csv", "rate")):
            with self.subTest(filename=filename):
                path = public / filename
                original = path.read_text()
                header, *rows = csv.reader(io.StringIO(original))
                column = header.index(field)
                for row in rows:
                    row.append(row[column])
                rows[0][column] = "123456789"
                with path.open("w", newline="") as output:
                    csv.writer(output).writerows([[*header, field], *rows])
                error = self.verify(1)
                self.assertIn(filename, error)
                self.assertIn("duplicate CSV columns: " + field, error)
                path.write_text(original)
        self.verify(0)

    def test_public_invoice_fields(self):
        public = shutil.copytree(self.example, self.root / self.example.name) / "public"
        path = public / "invoices.jsonl"
        original = path.read_text().splitlines()
        for field, value in (("due_at", None), ("due_at", "2026-01-01"), ("total_minor", 100.0),
                             ("total_minor", True), ("quantity", 1.0)):
            with self.subTest(field=field, value=value):
                invoice = json.loads(original[0])
                target = invoice["line_items"][0] if field == "quantity" else invoice
                if value is None:
                    del target[field]
                else:
                    target[field] = value
                path.write_text("\n".join([json.dumps(invoice), *original[1:]]) + "\n")
                error = self.verify(1)
                self.assertIn(invoice["invoice_id"], error)
                self.assertIn(field, error)

    def test_empty_directory(self):
        self.verify(1)

    def test_missing_indexed_episode(self):
        shutil.copytree(self.example, self.root / self.example.name)
        (self.root / "index.json").write_text(json.dumps([
            {"episode_id": self.example.name}, {"episode_id": "ep_missing"}]))
        self.assertIn("ep_missing", self.verify(1))

    def test_unreadable_episode(self):
        episode = shutil.copytree(self.example, self.root / self.example.name)
        (episode / "grader/truth.json").unlink()
        self.assertIn("truth.json", self.verify(1))

    def test_valid_unindexed_episode(self):
        shutil.copytree(self.example, self.root / self.example.name)
        self.assertIn("1/1 episodes valid", self.verify(0))

    def test_blank_task(self):
        episode = shutil.copytree(self.example, self.root / self.example.name)
        for contents in ("", " \t\n"):
            with self.subTest(contents=contents):
                (episode / "public/task.txt").write_text(contents, encoding="utf-8")
                self.assertIn("task", self.verify(1))

    def test_invalid_index(self):
        shutil.copytree(self.example, self.root / self.example.name)
        index = self.root / "index.json"
        for contents in ("[", "{}", "[{}]", "[]", json.dumps([{"episode_id": self.example.name}] * 2)):
            with self.subTest(contents=contents):
                index.write_text(contents)
                self.assertIn("index.json", self.verify(1))
