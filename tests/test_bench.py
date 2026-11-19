import json
import tempfile
import unittest
from pathlib import Path

from scripts.bench import main, render_markdown, run_bench


class BenchTest(unittest.TestCase):
    def test_run_bench_subset(self):
        data = run_bench(seeds=[0, 1], n_runs=1, policies=["oracle", "random"])

        self.assertIn("python_version", data)
        self.assertIn("platform", data)
        self.assertEqual(data["seeds_count"], 2)
        self.assertEqual(data["n_runs"], 1)

        self.assertGreater(data["generator_default_s"], 0.0)
        self.assertGreater(data["generator_hard_s"], 0.0)
        self.assertGreater(data["verify_seeds_s"], 0.0)

        for split in ("policies_dev", "policies_hard"):
            self.assertIn(split, data)
            self.assertIn("oracle", data[split])
            self.assertIn("random", data[split])
            self.assertGreater(data[split]["oracle"]["time_ms"], 0.0)
            self.assertGreaterEqual(data[split]["oracle"]["steps"], 1)

        md = render_markdown(data)
        self.assertIn("## Timing Benchmark", md)
        self.assertIn(data["python_version"], md)
        self.assertIn("oracle", md)
        self.assertIn("random", md)

    def test_bench_cli_smoke(self):
        with tempfile.TemporaryDirectory() as d:
            out_json = Path(d) / "bench.json"
            # Fast test running main with --json
            # Note: runs=1 with default seeds takes ~2s
            rc = main(["--json", str(out_json), "--runs", "1"])
            self.assertEqual(rc, 0)
            self.assertTrue(out_json.is_file())
            with open(out_json, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertIn("generator_default_s", saved)
            self.assertIn("policies_dev", saved)


if __name__ == "__main__":
    unittest.main()
