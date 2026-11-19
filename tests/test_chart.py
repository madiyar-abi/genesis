"""Tests for scripts/chart.py: well-formed SVG, policy rows, negative bars left of zero, determinism."""

import re
import unittest
import xml.dom.minidom

from scripts.chart import render


def _m(ret):
    return {"return": ret, "precision": 0.0, "recall": 0.0, "f1": 0.0, "steps": 1.0}


METRICS = {
    "dev": {"oracle": _m(1.0), "reconcile": _m(0.957), "flag_all": _m(-1.0)},
    "hard": {"oracle": _m(1.0), "reconcile_hard": _m(0.9167), "reconcile": _m(-0.0948), "flag_all": _m(-1.0)},
}


class ChartTest(unittest.TestCase):
    def setUp(self):
        self.svg = render(METRICS, {"dev": 10, "hard": 20})
        self.dom = xml.dom.minidom.parseString(self.svg)

    def test_parses_and_names_every_policy(self):
        texts = [t.firstChild.data for t in self.dom.getElementsByTagName("text") if t.firstChild]
        for p in ("oracle", "reconcile_hard", "reconcile", "flag_all"):
            self.assertIn(p, texts)
        self.assertIn("not run on dev", texts)
        self.assertTrue(any("(20 episodes)" in t for t in texts))

    def test_negative_bar_left_of_zero_axis(self):
        zero = next(line for line in self.dom.getElementsByTagName("line")
                    if line.getAttribute("stroke-width") == "1.25")
        x0 = float(zero.getAttribute("x1"))
        bars = {(b.getAttribute("data-split"), b.getAttribute("data-policy")): b
                for b in self.dom.getElementsByTagName("path")}
        self.assertEqual(len(bars), 7)

        def xs(key):
            return [float(x) for x in re.findall(r"[MHQ ]([\d.]+),", bars[key].getAttribute("d"))
                    + re.findall(r"H([\d.]+)", bars[key].getAttribute("d"))]

        self.assertLess(min(xs(("dev", "flag_all"))), x0 - 1)
        self.assertLessEqual(max(xs(("dev", "flag_all"))), x0 + 1e-6)
        self.assertGreater(max(xs(("dev", "oracle"))), x0 + 1)
        self.assertGreaterEqual(min(xs(("dev", "oracle"))), x0 - 1e-6)

    def test_counts_optional(self):
        self.assertNotIn("episodes", render(METRICS))

    def test_deterministic(self):
        self.assertEqual(render(METRICS, {"dev": 10, "hard": 20}), self.svg)


if __name__ == "__main__":
    unittest.main()
