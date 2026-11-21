"""The jury does not know our AUDITENV_SECRET. Without it, `judge_adapter` must still keep the seed out of the policy's
reach: hidden episodes are keyed by a random grader key kept in a file on the jury side, so neither `episode_id` nor
the records match the public generator, and the same seed and config give the same episode again on that machine."""

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import judge_adapter as ja
from auditenv.generator import episode_id_for, generate
from auditenv.load import load_episode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GraderKeyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.key_file = os.path.join(self.tmp, "keys", "grader.key")
        patcher = mock.patch.dict(os.environ, {"AUDITENV_SECRET": "", "AUDITENV_KEY_FILE": self.key_file})
        patcher.start()
        self.addCleanup(patcher.stop)
        ja._WARNED = True

    def generate(self, seed, config, name):
        path = os.path.join(self.tmp, name)
        ja.generate_episode(seed, config, path)
        return load_episode(path)

    def test_seed_is_not_recoverable_without_the_secret(self):
        ep = self.generate(3, {}, "a")
        public = generate(3, {})
        self.assertNotEqual(ep["manifest"]["episode_id"], episode_id_for(3, {}))
        self.assertNotEqual(ep["tables"], public["tables"])
        self.assertEqual(stat.S_IMODE(os.stat(self.key_file).st_mode), 0o600)

    def test_same_seed_and_config_reproduce_in_a_new_process(self):
        first = self.generate(4, {"errors": {"fx_error": 1}}, "first")
        code = "import judge_adapter as j, sys; j.generate_episode(4, {'errors': {'fx_error': 1}}, sys.argv[1])"
        again = os.path.join(self.tmp, "again")
        subprocess.run([sys.executable, "-c", code, again], cwd=ROOT, check=True, capture_output=True)
        second = load_episode(again)
        for part in ("manifest", "tables", "truth", "policy"):
            self.assertEqual(json.dumps(first[part], sort_keys=True), json.dumps(second[part], sort_keys=True), part)

    def test_secret_keeps_priority_and_creates_no_key_file(self):
        with mock.patch.dict(os.environ, {"AUDITENV_SECRET": "grader-only"}):
            ep = self.generate(5, {}, "keyed")
            expected = generate(5, {})
        self.assertEqual(ep["manifest"]["episode_id"], expected["episode_id"])
        self.assertEqual(ep["tables"], expected["tables"])
        self.assertFalse(os.path.exists(self.key_file))

    def test_closed_reset_without_episode_dir_is_keyed(self):
        _, info = ja.make_env().reset(6, {"mode": "closed"})
        self.assertNotEqual(info["episode_id"], episode_id_for(6, {}))
        _, info = ja.make_env().reset(6, {"mode": "train"})
        self.assertEqual(info["episode_id"], episode_id_for(6, {}))  # open mode stays the public generator

    def test_warning_names_the_key_file_once(self):
        import contextlib
        import io
        ja._WARNED = False
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.generate(7, {}, "w1")
            self.generate(8, {}, "w2")
        self.assertEqual(err.getvalue().count(self.key_file), 1)

    def test_unusable_key_file_falls_back_to_a_process_key(self):
        import contextlib
        import io
        os.makedirs(os.path.dirname(self.key_file))
        open(self.key_file, "w").close()  # empty: unusable
        blocked = os.path.join(self.tmp, "file-not-dir")
        open(blocked, "w").close()
        ja._WARNED = False
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            first = self.generate(9, {}, "empty")
            with mock.patch.dict(os.environ, {"AUDITENV_KEY_FILE": os.path.join(blocked, "grader.key")}):
                second = self.generate(9, {}, "no-dir")
        self.assertIn("unusable", err.getvalue())
        self.assertNotEqual(first["manifest"]["episode_id"], episode_id_for(9, {}))
        self.assertEqual(first["manifest"]["episode_id"], second["manifest"]["episode_id"])  # one key per process


if __name__ == "__main__":
    unittest.main()
