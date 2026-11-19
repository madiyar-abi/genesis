#!/usr/bin/env python3
"""Render baseline mean returns from `auditenv.check --json` as a stdlib SVG bar chart.

Usage:
    uv run python -m auditenv.check --json /tmp/auditenv-metrics.json
    uv run python scripts/chart.py --json /tmp/auditenv-metrics.json --out docs/baselines.svg

Same JSON -> byte-identical SVG.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["oracle", "reconcile_hard", "reconcile", "naive_reconcile", "random", "flag_all"]
SPLITS = [("dev", "configs/dev.json", "#3e6fb0"), ("hard", "configs/eval_hard.json", "#c98500")]
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
INK, INK_2, INK_3, GRID, AXIS = "#1f2328", "#57606a", "#8c959f", "#e6e8eb", "#57606a"

W, H = 800, 420
PLOT_L, PLOT_R = 150, W - 30    # policy names live left of PLOT_L
LABEL_PAD = 52                  # room inside the plot for value labels beyond the domain
PLOT_T, PLOT_B = 104, H - 40    # tick labels below PLOT_B
BAR_H, BAR_GAP = 15, 2


def fmt(v: float) -> str:
    s = f"{v:.3f}"
    return "−" + s[1:] if s.startswith("-") else s


def tick(v: float) -> str:
    s = f"{v:g}"
    return "−" + s[1:] if s.startswith("-") else s


def bar_path(x0: float, x1: float, y: float, h: float, r: float = 4.0) -> str:
    """Bar from the zero axis x0 to x1, rounded only at the far (data) end."""
    r = min(r, abs(x1 - x0), h / 2)
    if r <= 0:
        return f"M{x0:.1f},{y:.1f}H{x1:.1f}V{y + h:.1f}H{x0:.1f}Z"
    s = 1 if x1 >= x0 else -1
    return (f"M{x0:.1f},{y:.1f}H{x1 - s * r:.1f}"
            f"Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f}V{y + h - r:.1f}"
            f"Q{x1:.1f},{y + h:.1f} {x1 - s * r:.1f},{y + h:.1f}H{x0:.1f}Z")


def text(x: float, y: float, s: str, size: int = 12, fill: str = INK, anchor: str = "start", weight: str = "") -> str:
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}"{w}>{escape(s)}</text>')


def render(metrics: dict, counts: dict | None = None) -> str:
    """Return the SVG document. `counts` maps split -> episode count (optional)."""
    policies = [p for p in ORDER if any(p in metrics.get(k, {}) for k, _, _ in SPLITS)]
    values = [metrics[k][p]["return"] for k, _, _ in SPLITS for p in policies if p in metrics.get(k, {})]
    lo = min(0.0, math.floor(min(values, default=0.0) * 4) / 4)
    hi = max(0.0, math.ceil(max(values, default=1.0) * 4) / 4)
    if hi == lo:
        hi = lo + 1.0
    x_lo, x_hi = PLOT_L + LABEL_PAD, PLOT_R - LABEL_PAD

    def sx(v: float) -> float:
        return x_lo + (v - lo) / (hi - lo) * (x_hi - x_lo)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="{escape(FONT)}" role="img" aria-labelledby="t">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    title = "Mean episode return by baseline policy"
    out.append(f'<title id="t">{escape(title)}</title>')
    out.append(text(24, 34, title, 18, INK, weight="600"))
    parts = []
    for k, path, _ in SPLITS:
        n = (counts or {}).get(k)
        parts.append(f"{k} = {path}" + (f" ({n} episodes)" if n else ""))
    out.append(text(24, 56, " · ".join(parts), 12, INK_2))

    # legend
    lx = 24
    for k, _, colour in SPLITS:
        out.append(f'<rect x="{lx}" y="72" width="12" height="12" rx="2" fill="{colour}"/>')
        out.append(text(lx + 18, 82, k, 12, INK_2))
        lx += 18 + 7 * len(k) + 28

    # gridlines and ticks every 0.25
    steps = int(round((hi - lo) / 0.25))
    for i in range(steps + 1):
        v = lo + i * 0.25
        x = sx(v)
        colour, width = (AXIS, 1.25) if abs(v) < 1e-9 else (GRID, 1)
        out.append(f'<line x1="{x:.1f}" y1="{PLOT_T - 6}" x2="{x:.1f}" y2="{PLOT_B}" '
                   f'stroke="{colour}" stroke-width="{width}"/>')
        out.append(text(x, PLOT_B + 18, tick(v), 11, INK_3, "middle"))

    # rows
    row_h = (PLOT_B - PLOT_T) / max(len(policies), 1)
    group_h = len(SPLITS) * BAR_H + (len(SPLITS) - 1) * BAR_GAP
    x0 = sx(0.0)
    for r, p in enumerate(policies):
        y = PLOT_T + r * row_h + (row_h - group_h) / 2
        out.append(text(PLOT_L - 12, y + group_h / 2 + 4, p, 13, INK, "end"))
        for j, (k, _, colour) in enumerate(SPLITS):
            by = y + j * (BAR_H + BAR_GAP)
            if p not in metrics.get(k, {}):
                out.append(text(x0 + 6, by + BAR_H - 3, f"not run on {k}", 11, INK_3))
                continue
            v = metrics[k][p]["return"]
            x1 = sx(v)
            out.append(f'<path class="bar" data-split="{k}" data-policy="{escape(p)}" d="{bar_path(x0, x1, by, BAR_H)}" '
                       f'fill="{colour}"><title>{escape(f"{p}, {k}: {fmt(v)}")}</title></path>')
            if v < 0:
                out.append(text(x1 - 6, by + BAR_H - 3, fmt(v), 11, INK_2, "end"))
            else:
                out.append(text(x1 + 6, by + BAR_H - 3, fmt(v), 11, INK_2))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def episode_counts() -> dict:
    counts = {}
    for k, path, _ in SPLITS:
        try:
            with open(os.path.join(ROOT, path)) as fh:
                counts[k] = len(json.load(fh)["episodes"])
        except (OSError, KeyError, ValueError):
            pass
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default="/tmp/auditenv-metrics.json", help="metrics from auditenv.check --json")
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "baselines.svg"))
    args = ap.parse_args()
    with open(args.json) as fh:
        metrics = json.load(fh)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(metrics, episode_counts()))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
