"""Summarize grader-side policy failures across a reproducible set of episodes."""

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean

from .env import AuditEnv
from .run import POLICIES, make_policy, parse_seeds, run_episode
from .schema import ISSUE_TYPES

_SCENARIOS = ("single", "I1", "I2")


def analyze(policy: str, episodes: list[tuple[int, dict]]) -> dict:
    """Run the selected policy and aggregate the grader's terminal results."""
    if not episodes:
        raise ValueError("select at least one episode")

    env = AuditEnv()
    by_type = {issue_type: {"tp": 0, "fn": 0} for issue_type in ISSUE_TYPES}
    by_scenario = {scenario: {"tp": 0, "fn": 0} for scenario in _SCENARIOS}
    fp_reasons = Counter()
    scores = []

    for seed, config in episodes:
        trajectory = run_episode(
            env, None, seed, config,
            policy_factory=lambda grader: make_policy(policy, grader, seed),
        )
        result = env.result
        issues = {issue["issue_id"]: issue for issue in env._ep["truth"]["issues"]}
        for label in result["labels"]:
            if label["tp"]:
                issue = issues[label["issue_id"]]
                by_type[issue["type"]]["tp"] += 1
                by_scenario[issue.get("scenario", "single")]["tp"] += 1
            else:
                fp_reasons[label["reason"]] += 1
        for missed in result["missed"]:
            issue = issues[missed["issue_id"]]
            by_type[issue["type"]]["fn"] += 1
            by_scenario[issue.get("scenario", "single")]["fn"] += 1
        scores.append({
            "precision": result["precision"],
            "recall": result["recall"],
            "f1": result["f1"],
            "return": result["reward"],
            "steps": trajectory[-1]["step"],
        })

    for counts in (*by_type.values(), *by_scenario.values()):
        support = counts["tp"] + counts["fn"]
        counts["recall"] = counts["tp"] / support if support else 0.0

    return {
        "policy": policy,
        "episodes": len(scores),
        "mean": {key: mean(score[key] for score in scores) for key in scores[0]},
        "by_type": by_type,
        "by_scenario": by_scenario,
        "fp_total": sum(fp_reasons.values()),
        "fp_by_reason": dict(sorted(fp_reasons.items())),
    }


def _markdown_table(headers, rows) -> str:
    def row(values):
        return "| " + " | ".join(map(str, values)) + " |"

    return "\n".join([row(headers), row(["---"] * len(headers)), *(row(values) for values in rows)])


def markdown(report: dict) -> str:
    """Render the same aggregates written to JSON."""
    averages = report["mean"]
    return "\n\n".join([
        _markdown_table(
            ("Policy", "Episodes", "Mean P", "Mean R", "Mean F1", "Mean return", "Mean steps"),
            [(report["policy"], report["episodes"], *averages.values())],
        ),
        _markdown_table(
            ("Issue type", "TP", "FN", "Recall"),
            ((key, counts["tp"], counts["fn"], counts["recall"])
             for key, counts in report["by_type"].items()),
        ),
        _markdown_table(
            ("Scenario", "TP", "FN", "Recall"),
            ((key, counts["tp"], counts["fn"], counts["recall"])
             for key, counts in report["by_scenario"].items()),
        ),
        _markdown_table(
            ("False-positive reason", "Count"),
            [*report["fp_by_reason"].items(), ("Total", report["fp_total"])],
        ),
    ])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=sorted(POLICIES), default="reconcile")
    parser.add_argument("--seeds", help="Comma-separated seeds and inclusive ranges")
    parser.add_argument("--config", type=Path, help="Episode configuration file")
    parser.add_argument("--json", type=Path, help="Write the report as JSON")
    args = parser.parse_args(argv)

    if args.config is None:
        configs = None
    else:
        try:
            spec = json.loads(args.config.read_text(encoding="utf-8"))
            configs = {entry["seed"]: entry["config"] for entry in spec["episodes"]}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(f"cannot read episode configuration: {exc}")

    try:
        if args.seeds is not None:
            seeds = parse_seeds(args.seeds)
        else:
            seeds = list(configs) if configs is not None else parse_seeds("2000-2009")
    except ValueError as exc:
        parser.error(f"invalid --seeds: {exc}")
    if not seeds:
        parser.error("select at least one seed")
    if configs is not None:
        missing = [seed for seed in seeds if seed not in configs]
        if missing:
            parser.error(f"seeds missing from --config: {missing}")

    episodes = [(seed, configs[seed] if configs is not None else {}) for seed in seeds]
    report = analyze(args.policy, episodes)
    if args.json is not None:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
