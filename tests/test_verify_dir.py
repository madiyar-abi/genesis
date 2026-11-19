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

    def test_invalid_index(self):
        shutil.copytree(self.example, self.root / self.example.name)
        index = self.root / "index.json"
        for contents in ("[", "{}", "[{}]", "[]", json.dumps([{"episode_id": self.example.name}] * 2)):
            with self.subTest(contents=contents):
                index.write_text(contents)
                self.assertIn("index.json", self.verify(1))
