#!/usr/bin/env python3
"""Resolve git conflict markers in night/TASKS.md and night/LOG.md (NIGHT.md rule):
keep both sides; for task lines with the same id keep the most-done status ([x] > [!] > [ ])."""
import re
import sys

RANK = {"x": 2, "!": 1, " ": 0}


def task_id(line):
    m = re.match(r"- \[(.)\] (T\d+)\b", line)
    return (m.group(2), m.group(1)) if m else (None, None)


def resolve(text, tasks):
    out, i, lines = [], 0, text.splitlines(keepends=True)
    while i < len(lines):
        if not lines[i].startswith("<<<<<<<"):
            out.append(lines[i]); i += 1; continue
        ours, theirs, i = [], [], i + 1
        while not lines[i].startswith("======="):
            ours.append(lines[i]); i += 1
        i += 1
        while not lines[i].startswith(">>>>>>>"):
            theirs.append(lines[i]); i += 1
        i += 1
        if tasks:
            merged, pos = [], {}
            for line in ours + theirs:
                tid, st = task_id(line)
                if tid is None:
                    if line not in merged:
                        merged.append(line)
                elif tid not in pos:
                    pos[tid] = len(merged); merged.append(line)
                elif RANK.get(st, 0) > RANK.get(task_id(merged[pos[tid]])[1], 0):
                    merged[pos[tid]] = line
            out += merged
        else:
            out += ours + theirs
    return "".join(out)


for path in sys.argv[1:]:
    s = open(path).read()
    open(path, "w").write(resolve(s, path.endswith("TASKS.md")))
