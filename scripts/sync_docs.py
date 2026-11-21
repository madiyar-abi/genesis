#!/usr/bin/env python3
"""Sync documentation result tables with measured metrics from auditenv.check --json.

Usage:
    # Update documentation tables from measured data:
    python scripts/sync_docs.py --json /tmp/check.json

    # CI check: verify docs match measured data without drift (exit 0 = match, 1 = drift):
    python scripts/sync_docs.py --check --json /tmp/check.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys


def format_num(val: float, decimals: int = 3) -> str:
    """Format a float with the given number of decimal places.

    Negative numbers are formatted with the Unicode minus sign (\u2212)
    consistent with project documentation convention.
    """
    s = f"{val:.{decimals}f}"
    if s.startswith("-"):
        return "\u2212" + s[1:]
    return s


def validate_finite_nonnegative(val_str: str) -> bool:
    """Validate that val_str represents a finite, non-negative float."""
    try:
        val = float(val_str.strip())
        return math.isfinite(val) and val >= 0.0
    except (ValueError, TypeError):
        return False


def render_readme_table(dev: dict) -> str:
    """Render the dev split results table for README.md."""
    rows = [
        ("oracle (grader-side)", dev["oracle"]),
        ("reconcile (policy-aware rules)", dev["reconcile"]),
        ("naive reconcile", dev["naive_reconcile"]),
        ("random explorer", dev["random"]),
        ("flag-everything", dev["flag_all"]),
    ]
    lines = [
        "| policy | P | R | F1 | mean return | mean steps |",
        "|---|---|---|---|---|---|",
    ]
    for label, d in rows:
        p = format_num(d["precision"], 3)
        r = format_num(d["recall"], 3)
        f1 = format_num(d["f1"], 3)
        ret = format_num(d["return"], 3)
        steps = format_num(d["steps"], 1)
        lines.append(f"| {label} | {p} | {r} | {f1} | {ret} | {steps} |")
    return "\n".join(lines) + "\n"


def render_design_dev_table(dev: dict, time_s_override: dict[str, str] | None = None) -> str:
    """Render the dev split results table for docs/DESIGN.md."""
    rows = [
        ("random explorer (seeded)", dev["random"]),
        ("naive reconciliation", dev["naive_reconcile"]),
        ("reconciliation (policy-aware)", dev["reconcile"]),
        ("flag-everything attack", dev["flag_all"]),
        ("oracle (grader-side)", dev["oracle"]),
    ]
    lines = [
        "| policy | seeds | P | R | F1 | return | steps | time s | exp. return* |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label, d in rows:
        p = format_num(d["precision"], 3)
        r = format_num(d["recall"], 3)
        f1 = format_num(d["f1"], 3)
        ret = format_num(d["return"], 3)
        steps = format_num(d["steps"], 1)
        t = time_s_override.get(label, f"{d['time_s']:.3f}") if time_s_override else f"{d['time_s']:.3f}"
        exp = format_num(d["experimental_return"], 3)
        lines.append(f"| {label} | 2000–2009 | {p} | {r} | {f1} | {ret} | {steps} | {t} | {exp} |")
    return "\n".join(lines) + "\n"


def render_design_hard_table(hard: dict) -> str:
    """Render the hard mode results table for docs/DESIGN.md."""
    rows = [
        ("random explorer (seeded)", hard["random"]),
        ("naive reconciliation", hard["naive_reconcile"]),
        ("reconciliation (default rules)", hard["reconcile"]),
        ("reconciliation + hard rules (`reconcile_hard`)", hard["reconcile_hard"]),
        ("flag-everything attack", hard["flag_all"]),
        ("oracle (grader-side)", hard["oracle"]),
    ]
    lines = [
        "| policy | P | R | F1 | return | steps | exp. return* |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, d in rows:
        p = format_num(d["precision"], 3)
        r = format_num(d["recall"], 3)
        f1 = format_num(d["f1"], 3)
        ret = format_num(d["return"], 3)
        steps = format_num(d["steps"], 1)
        exp = format_num(d["experimental_return"], 3)
        lines.append(f"| {label} | {p} | {r} | {f1} | {ret} | {steps} | {exp} |")
    return "\n".join(lines) + "\n"


def render_pitch_table(data: dict) -> str:
    """Render the compact results table for docs/PITCH.md Section 7."""
    dev = data["dev"]
    hard = data["hard"]
    rows = [
        ("oracle (grader-side)", "dev", dev["oracle"]),
        ("reconcile (policy-aware)", "dev", dev["reconcile"]),
        ("naive reconcile", "dev", dev["naive_reconcile"]),
        ("random explorer", "dev", dev["random"]),
        ("flag-everything", "dev", dev["flag_all"]),
        ("reconcile_hard", "hard", hard["reconcile_hard"]),
        ("reconcile (default)", "hard", hard["reconcile"]),
        ("oracle (grader-side)", "hard", hard["oracle"]),
    ]
    lines = [
        "| policy | split | P | R | F1 | return |",
        "|---|---|---|---|---|---|",
    ]
    for label, split, d in rows:
        p = format_num(d["precision"], 3)
        r = format_num(d["recall"], 3)
        f1 = format_num(d["f1"], 3)
        ret = format_num(d["return"], 3)
        lines.append(f"| {label} | {split} | {p} | {r} | {f1} | {ret} |")
    return "\n".join(lines) + "\n"


def extract_table_block(content: str, header_pattern: str) -> tuple[int, int, str] | None:
    """Find start index, end index, and table block matching header_pattern."""
    m_header = re.search(header_pattern, content)
    if not m_header:
        return None
    start = m_header.start(0)
    end = start
    lines = content[start:].splitlines(keepends=True)
    table_lines = []
    for line in lines:
        if line.startswith("|"):
            table_lines.append(line)
            end += len(line)
        else:
            break
    return start, end, "".join(table_lines)


def sync_readme(content: str, data: dict) -> tuple[str, bool]:
    """Update README.md results table. Return (new_content, was_changed)."""
    header_pattern = r"\| policy \| P \| R \| F1 \| mean return \| mean steps \|"
    block = extract_table_block(content, header_pattern)
    if not block:
        raise ValueError("Could not find results table in README.md")
    start, end, current_table = block
    new_table = render_readme_table(data["dev"])
    if current_table == new_table:
        return content, False
    return content[:start] + new_table + content[end:], True


def extract_design_dev_times(content: str) -> dict[str, str]:
    """Extract existing time_s snapshot values from docs/DESIGN.md dev table."""
    header_pattern = r"\| policy \| seeds \| P \| R \| F1 \| return \| steps \| time s \| exp\. return\* \|"
    block = extract_table_block(content, header_pattern)
    if not block:
        return {}
    _, _, table_str = block
    times = {}
    for line in table_str.splitlines():
        if line.startswith("|") and not line.startswith("|---") and not line.startswith("| policy"):
            parts = [c.strip() for c in line.split("|")[1:-1]]
            if len(parts) >= 8:
                times[parts[0]] = parts[7]
    return times


def sync_design(content: str, data: dict, time_s_override: dict[str, str] | None = None) -> tuple[str, bool]:
    """Update docs/DESIGN.md dev and hard results tables. Return (new_content, was_changed)."""
    changed = False

    # 1. Dev results table
    dev_header_pattern = r"\| policy \| seeds \| P \| R \| F1 \| return \| steps \| time s \| exp\. return\* \|"
    dev_block = extract_table_block(content, dev_header_pattern)
    if not dev_block:
        raise ValueError("Could not find dev results table in docs/DESIGN.md")
    d_start, d_end, current_dev = dev_block
    new_dev = render_design_dev_table(data["dev"], time_s_override=time_s_override)
    if current_dev != new_dev:
        content = content[:d_start] + new_dev + content[d_end:]
        changed = True

    # 2. Hard mode results table
    hard_header_pattern = r"\| policy \| P \| R \| F1 \| return \| steps \| exp\. return\* \|"
    hard_block = extract_table_block(content, hard_header_pattern)
    if not hard_block:
        raise ValueError("Could not find hard mode results table in docs/DESIGN.md")
    h_start, h_end, current_hard = hard_block
    new_hard = render_design_hard_table(data["hard"])
    if current_hard != new_hard:
        content = content[:h_start] + new_hard + content[h_end:]
        changed = True

    return content, changed


def sync_pitch(content: str, data: dict) -> tuple[str, bool]:
    """Update or insert docs/PITCH.md Section 7 results table. Return (new_content, was_changed)."""
    pitch_header_pattern = r"\| policy \| split \| P \| R \| F1 \| return \|"
    block = extract_table_block(content, pitch_header_pattern)
    new_table = render_pitch_table(data)

    if block:
        start, end, current_table = block
        if current_table == new_table:
            return content, False
        return content[:start] + new_table + content[end:], True
    else:
        # Insert table under Section 7
        m = re.search(r"## 7\. Results\s*\n*", content)
        if not m:
            raise ValueError("Could not find ## 7. Results in docs/PITCH.md")
        after_heading = content[:m.start(0)] + "## 7. Results\n\n"
        idx = m.end(0)
        new_content = after_heading + new_table + "\n" + content[idx:]
        return new_content, True


def _updates(repo_root, data, *, preserve_time):
    for name, render in (("README.md", sync_readme), ("docs/DESIGN.md", sync_design), ("docs/PITCH.md", sync_pitch)):
        path = Path(repo_root) / name
        content = path.read_text(encoding="utf-8")
        if name == "docs/DESIGN.md" and preserve_time:
            times = extract_design_dev_times(content)
            if not all(validate_finite_nonnegative(value) for value in times.values()):
                raise ValueError("docs/DESIGN.md: invalid time s")
            updated, changed = render(content, data, time_s_override=times)
        else:
            updated, changed = render(content, data)
        yield path, updated, changed
    chart_path = Path(repo_root) / "docs" / "baselines.svg"
    if chart_path.exists():  # the slide-7 chart is rendered from the same metrics
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import chart
        content = chart_path.read_text(encoding="utf-8")
        updated = chart.render(data, chart.episode_counts())
        yield chart_path, updated, updated != content


def check_docs(repo_root: str, data: dict) -> list[str]:
    errors = []
    try:
        for path, _, changed in _updates(repo_root, data, preserve_time=True):
            if changed:
                errors.append(f"{path.name}: results table differs from measured data" if path.suffix == ".md"
                              else f"{path.name}: chart differs from measured data")
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    return errors


def sync_all(repo_root: str, data: dict, preserve_time: bool = False) -> dict[str, bool]:
    updates = list(_updates(repo_root, data, preserve_time=preserve_time))
    for path, updated, changed in updates:
        if changed:
            path.write_text(updated, encoding="utf-8")
    return {str(path): changed for path, _, changed in updates}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True, help="Path to JSON metrics produced by python -m auditenv.check --json PATH")
    ap.add_argument("--check", action="store_true", help="Check for documentation drift without modifying files (exit 1 on drift)")
    ap.add_argument("--repo-root", help="Root directory of the repository")
    ap.add_argument("--preserve-time", action="store_true", help="Preserve existing time s values in DESIGN.md during sync")
    args = ap.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root) if args.repo_root else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    json_path = args.json
    if not json_path or not os.path.exists(json_path):
        print(f"Error: metrics JSON file not found (tried {json_path}). Run python -m auditenv.check --json <path> first or pass --json <path>", file=sys.stderr)
        return 1

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if args.check:
        errors = check_docs(repo_root, data)
        if errors:
            print("Documentation drift detected:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print("All documentation tables match measured data.")
        return 0
    else:
        results = sync_all(repo_root, data, preserve_time=args.preserve_time)
        for path, was_changed in results.items():
            rel = os.path.relpath(path, repo_root)
            status = "updated" if was_changed else "up to date"
            print(f"{rel}: {status}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
