"""Tests for episode export and configuration splits (T16)."""

import hashlib
import json
import os
import tempfile
import unittest

from auditenv.export import export_split, main
from auditenv.generator import FX_FIELDS, LEDGER_FIELDS, generate
from auditenv.run import load_episodes
from auditenv.verify import verify_episode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _dir_tree_hashes(dir_path: str) -> dict[str, str]:
    hashes = {}
    for root, _, files in sorted(os.walk(dir_path)):
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, dir_path)
            hashes[rel] = _sha256(full)
    return hashes


class TestExport(unittest.TestCase):
    """Verify export byte-reproducibility, verifier compliance, and schemas."""

    def test_export_twice_byte_identical(self):
        """Exporting the same config twice produces byte-identical trees."""
        config_path = os.path.join(ROOT, "configs", "dev.json")
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1 = os.path.join(d1, "dev")
            out2 = os.path.join(d2, "dev")

            export_split(config_path, out1)
            export_split(config_path, out2)

            hashes1 = _dir_tree_hashes(out1)
            hashes2 = _dir_tree_hashes(out2)

            self.assertGreater(len(hashes1), 0)
            self.assertEqual(hashes1, hashes2, "Exported trees are not byte-identical")

    def test_all_episodes_pass_verifier(self):
        """Every episode across train, dev, eval_example, and eval_hard passes the independent verifier."""
        for split_file in ("train.json", "dev.json", "eval_example.json", "eval_hard.json"):
            cfg_path = os.path.join(ROOT, "configs", split_file)
            self.assertTrue(os.path.exists(cfg_path), f"Config file {cfg_path} missing")
            episodes = load_episodes(cfg_path)
            self.assertGreaterEqual(len(episodes), 10)
            for seed, cfg in episodes:
                ep = generate(seed, cfg)
                problems = verify_episode(ep)
                self.assertEqual(problems, [], f"{split_file} seed {seed} failed verifier: {problems}")

    def test_committed_exports_reexport_identity(self):
        """D3 + red-team round 16: every committed split (train, dev, hard) matches a fresh export byte-for-byte,
        so an extra public file or column (e.g. a leaked truth copy) cannot hide behind the loader."""
        for split, cfg in (("train", "train.json"), ("dev", "dev.json"), ("hard", "eval_hard.json")):
            with self.subTest(split=split):
                committed = os.path.join(ROOT, "episodes", split)
                self.assertTrue(os.path.isdir(committed), f"episodes/{split} missing")
                with tempfile.TemporaryDirectory() as tmp:
                    out = os.path.join(tmp, split)
                    export_split(os.path.join(ROOT, "configs", cfg), out)
                    self.assertEqual(_dir_tree_hashes(committed), _dir_tree_hashes(out),
                                     f"Re-exported {split} split is not byte-identical to committed")

    def test_exported_file_structure_and_csv_headers(self):
        """Exported directory contains all expected files with correct headers."""
        config_path = os.path.join(ROOT, "configs", "dev.json")
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dev")
            index = export_split(config_path, out)
            self.assertEqual(len(index), 10)

            # Check index.json
            index_file = os.path.join(out, "index.json")
            self.assertTrue(os.path.exists(index_file))
            with open(index_file) as fh:
                loaded_index = json.load(fh)
            self.assertEqual(loaded_index, index)

            first_ep = index[0]["episode_id"]
            ep_dir = os.path.join(out, first_ep)

            # Public files
            pub = os.path.join(ep_dir, "public")
            # task.txt: the duplicate definition and hard-mode rules live only in the task text (red-team round 16)
            for name in ("task.txt", "manifest.json", "policy.json", "ledger.csv", "invoices.jsonl", "payments.jsonl",
                         "fx.csv"):
                self.assertTrue(os.path.exists(os.path.join(pub, name)), f"Missing {name}")

            # Grader files
            grd = os.path.join(ep_dir, "grader")
            for name in ("truth.json", "provenance.json"):
                self.assertTrue(os.path.exists(os.path.join(grd, name)), f"Missing {name}")

            # Check CSV headers match CONTRACT §2 exactly
            with open(os.path.join(pub, "ledger.csv")) as fh:
                header = fh.readline().strip().split(",")
                self.assertEqual(tuple(header), LEDGER_FIELDS)

            with open(os.path.join(pub, "fx.csv")) as fh:
                header = fh.readline().strip().split(",")
                self.assertEqual(tuple(header), FX_FIELDS)

    def test_cli_invocation(self):
        """CLI entrypoint `python -m auditenv.export` runs with code 0."""
        config_path = os.path.join(ROOT, "configs", "dev.json")
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out")
            code = main(["--config", config_path, "--out", out])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "index.json")))


if __name__ == "__main__":
    unittest.main()
