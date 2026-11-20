"""Tests for auditenv.load (T28): load exported episodes and verify roundtrip."""

from __future__ import annotations

import json
import os
import unittest

from auditenv.generator import generate
from auditenv.load import load_episode
from auditenv.verify import verify_episode


EPISODES_DIR_DEV = os.path.join(os.path.dirname(__file__), "..", "episodes", "dev")
EPISODES_DIR_TRAIN = os.path.join(os.path.dirname(__file__), "..", "episodes", "train")
EPISODES_DIR_HARD = os.path.join(os.path.dirname(__file__), "..", "episodes", "hard")


def _normalise_for_comparison(ep: dict) -> dict:
    """The full episode: the task text is exported too (public/task.txt), so nothing is stripped."""
    return ep


class TestLoadRoundtrip(unittest.TestCase):
    """For every committed episode, load_episode equals generate(seed, config), task text included."""

    def _check_split(self, split_dir: str) -> None:
        index_path = os.path.join(split_dir, "index.json")
        self.assertTrue(os.path.exists(index_path), f"index.json missing in {split_dir}")
        with open(index_path, "r") as fh:
            index = json.load(fh)
        self.assertGreater(len(index), 0, "empty index")

        for entry in index:
            seed = entry["seed"]
            config = entry["config"]
            episode_id = entry["episode_id"]
            ep_dir = os.path.join(split_dir, episode_id)

            with self.subTest(split=os.path.basename(split_dir), seed=seed, episode_id=episode_id):
                # Load from disk
                loaded = load_episode(ep_dir)

                # Generate from seed+config
                generated = _normalise_for_comparison(generate(seed, config))

                # Compare top-level keys
                self.assertEqual(sorted(loaded.keys()), sorted(generated.keys()),
                                 f"Key mismatch for {episode_id}")

                # Compare episode_id
                self.assertEqual(loaded["episode_id"], generated["episode_id"])

                # Compare manifest
                self.assertEqual(loaded["manifest"], generated["manifest"],
                                 f"manifest mismatch for {episode_id}")

                # Compare policy
                self.assertEqual(loaded["policy"], generated["policy"],
                                 f"policy mismatch for {episode_id}")

                # Compare truth
                self.assertEqual(loaded["truth"], generated["truth"],
                                 f"truth mismatch for {episode_id}")

                # Compare provenance
                self.assertEqual(loaded["provenance"], generated["provenance"],
                                 f"provenance mismatch for {episode_id}")

                # Compare tables
                for table_name in ("ledger", "invoices", "payments", "fx"):
                    loaded_rows = loaded["tables"][table_name]
                    gen_rows = generated["tables"][table_name]
                    self.assertEqual(len(loaded_rows), len(gen_rows),
                                     f"{table_name} row count mismatch for {episode_id}")
                    for i, (lr, gr) in enumerate(zip(loaded_rows, gen_rows)):
                        self.assertEqual(lr, gr,
                                         f"{table_name}[{i}] mismatch for {episode_id}")

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_DEV), "episodes/dev not found")
    def test_roundtrip_dev(self) -> None:
        self._check_split(EPISODES_DIR_DEV)

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_TRAIN), "episodes/train not found")
    def test_roundtrip_train(self) -> None:
        self._check_split(EPISODES_DIR_TRAIN)

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_HARD), "episodes/hard not found")
    def test_roundtrip_hard(self) -> None:
        self._check_split(EPISODES_DIR_HARD)


class TestVerifyLoadedEpisodes(unittest.TestCase):
    """Every loaded episode passes verify_episode."""

    def _check_split(self, split_dir: str) -> None:
        index_path = os.path.join(split_dir, "index.json")
        with open(index_path, "r") as fh:
            index = json.load(fh)

        for entry in index:
            episode_id = entry["episode_id"]
            ep_dir = os.path.join(split_dir, episode_id)

            with self.subTest(split=os.path.basename(split_dir), episode_id=episode_id):
                loaded = load_episode(ep_dir)
                problems = verify_episode(loaded)
                self.assertEqual(problems, [],
                                 f"verify_episode failed for {episode_id}: {problems}")

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_DEV), "episodes/dev not found")
    def test_verify_dev(self) -> None:
        self._check_split(EPISODES_DIR_DEV)

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_TRAIN), "episodes/train not found")
    def test_verify_train(self) -> None:
        self._check_split(EPISODES_DIR_TRAIN)

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_HARD), "episodes/hard not found")
    def test_verify_hard(self) -> None:
        self._check_split(EPISODES_DIR_HARD)


class TestVerifyDirCLI(unittest.TestCase):
    """Test the --dir option of verify.py main()."""

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_DEV), "episodes/dev not found")
    def test_verify_dir_dev(self) -> None:
        from auditenv.verify import main
        result = main(["--dir", EPISODES_DIR_DEV])
        self.assertEqual(result, 0, "--dir episodes/dev should exit 0")

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_TRAIN), "episodes/train not found")
    def test_verify_dir_train(self) -> None:
        from auditenv.verify import main
        result = main(["--dir", EPISODES_DIR_TRAIN])
        self.assertEqual(result, 0, "--dir episodes/train should exit 0")

    @unittest.skipUnless(os.path.isdir(EPISODES_DIR_HARD), "episodes/hard not found")
    def test_verify_dir_hard(self) -> None:
        from auditenv.verify import main
        result = main(["--dir", EPISODES_DIR_HARD])
        self.assertEqual(result, 0, "--dir episodes/hard should exit 0")


if __name__ == "__main__":
    unittest.main()
