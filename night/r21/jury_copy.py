"""Compare closed replay and offline scores after semantics-preserving export rewrites.

Run from the repo root: env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy
"""

import codecs
import csv
import io
import json
import random
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import judge_adapter
from auditenv.policies.reconcile import Reconcile, ReconcileHard
from auditenv.policy_worker import JuryPolicy

SCRATCH = Path("/tmp/r21-codex2")
COHORT = {"dev": (0, 2, 3, 4, 9), "hard": (0, 5, 9, 12, 19)}
VARIANTS = (
    "CSV columns shuffled", "CRLF", "CSV BOM", "JSON BOM", "JSONL BOM",
    "No final newline", "Pretty JSON", "Compact JSON", "JSONL keys reversed", "Combined",
)


def rewrite(path, variant):
    data = path.read_bytes()
    changes = VARIANTS[:-1] if variant == "Combined" else (variant,)
    if "CSV columns shuffled" in changes and path.suffix == ".csv":
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))
        columns = list(range(len(rows[0])))
        random.Random(21).shuffle(columns)
        out = io.StringIO(newline="")
        csv.writer(out).writerows([[row[i] for i in columns] for row in rows])
        data = out.getvalue().encode("utf-8")
    if path.suffix == ".json" and ("Pretty JSON" in changes or "Compact JSON" in changes):
        options = {"separators": (",", ":")} if "Compact JSON" in changes else {"indent": 4}
        data = (json.dumps(json.loads(data), ensure_ascii=False, **options) + "\n").encode("utf-8")
    if path.suffix == ".jsonl" and "JSONL keys reversed" in changes:
        lines = []
        for line in data.decode("utf-8").splitlines():
            obj = json.loads(line)
            lines.append(json.dumps(dict(reversed(list(obj.items()))), ensure_ascii=False))
        data = ("\n".join(lines) + "\n").encode("utf-8")
    if "CRLF" in changes:
        data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if "No final newline" in changes:
        data = data.removesuffix(b"\n").removesuffix(b"\r")
    if f"{path.suffix[1:].upper()} BOM" in changes:
        data = codecs.BOM_UTF8 + data
    path.write_bytes(data)


def play(path, actions=None, policy=None):
    env = judge_adapter.make_env()
    obs, _ = env.reset(0, {"mode": "closed", "episode_dir": str(path)})
    replay = iter(actions) if actions is not None else None
    transcript = []
    for _ in range(obs["remaining_steps"]):
        action = next(replay) if replay is not None else policy.act(obs)
        transcript.append(action)
        obs, reward, ended, truncated, _ = env.step(action)
        if obs["error"] or truncated or reward != 0:
            raise AssertionError(f"unexpected closed step {(obs['error'], truncated, reward)!r}")
        if ended:
            if action["name"] != "submit" or (replay is not None and len(transcript) != len(actions)):
                raise AssertionError("replay ended without consuming the reference submission")
            result = env.grader_log[-1]
            return transcript, (result["tp"], result["fp"], result["fn"], result["reward"])
    raise AssertionError("no terminal submission")


def score(path, actions):
    return judge_adapter.score_episode(str(path), actions[-1]["args"]["findings"], len(actions) - 1)


def main():
    counts = Counter()
    issues = []
    seeds = {}
    SCRATCH.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=SCRATCH, prefix="jury-copy-") as tmp:
        for split, indices in COHORT.items():
            root = Path("episodes") / split
            index = json.loads((root / "index.json").read_text(encoding="utf-8"))
            seeds[split] = [index[i]["seed"] for i in indices]
            policy = ReconcileHard if split == "hard" else Reconcile
            for i in indices:
                original = root / index[i]["episode_id"]
                actions, original_replay = play(original, policy=JuryPolicy(policy(seed=0)))
                original_score = score(original, actions)
                if original_score["f1"] != 1.0:
                    raise AssertionError(f"reference {original} did not reach F1=1: {original_score!r}")
                for variant in VARIANTS:
                    copy = Path(tmp) / original.name
                    shutil.copytree(original, copy)
                    for path in copy.glob("*/*"):
                        if path.suffix != ".txt" or variant in ("CRLF", "No final newline", "Combined"):
                            rewrite(path, variant)
                    results = {}
                    for stage in ("reset/replay", "score_episode"):
                        try:
                            if stage == "reset/replay":
                                _, results[stage] = play(copy, actions=actions)
                            else:
                                results[stage] = score(copy, actions)
                        except (ValueError, AssertionError, StopIteration) as exc:
                            issues.append(f"{variant} {split} seed {index[i]['seed']} {stage}: "
                                          f"{type(exc).__name__}: {exc}")
                    if len(results) != 2:
                        counts[variant, "rejected"] += 1
                    else:
                        counts[variant, "accepted"] += 1
                        if results == {"reset/replay": original_replay, "score_episode": original_score}:
                            counts[variant, "equal"] += 1
                        else:
                            issues.append(f"{variant} {split} seed {index[i]['seed']}: "
                                          f"scores changed to {results!r}")
                    shutil.rmtree(copy)
    print(f"Reference seeds: {seeds}")
    print("| Variant | Accepted | Rejected | Scores equal |")
    print("|---|---:|---:|---:|")
    for variant in VARIANTS:
        accepted, rejected, equal = (counts[variant, field] for field in ("accepted", "rejected", "equal"))
        print(f"| {variant} | {accepted} | {rejected} | {equal} |")
    print(f"Semantically equivalent rewrite discrepancies: {len(issues)}")
    for issue in issues:
        print(issue)


if __name__ == "__main__":
    main()
