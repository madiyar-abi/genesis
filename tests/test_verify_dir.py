import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from auditenv.verify import Books, main


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

    def test_truth_schema_and_index_metadata(self):
        split = self.example.parent
        record = next(r for r in json.loads((split / "index.json").read_text()) if r["seed"] == 2003)
        episode = shutil.copytree(split / record["episode_id"], self.root / record["episode_id"])
        index = self.root / "index.json"
        index.write_text(json.dumps([record]))
        with patch("auditenv.verify.Books", wraps=Books) as build_books:
            self.verify(0)
            self.assertEqual(build_books.call_count, 2)
        path = episode / "grader/truth.json"
        original = path.read_text()
        for field in ("scenario", "issue_id", "evidence_sets"):
            with self.subTest(field=field):
                data = json.loads(original)
                issue = data["issues"][0]
                if field == "scenario":
                    del issue[field]
                elif field == "issue_id":
                    issue[field] = " "
                else:
                    issue[field][0].append(issue[field][0][0])
                path.write_text(json.dumps(data))
                self.assertIn(field, self.verify(1))
        path.write_text(original)
        for field, value in (("seed", 2000), ("config", {"errors": {}})):
            index.write_text(json.dumps([dict(record, **{field: value})]))
            self.assertIn(field, self.verify(1))
