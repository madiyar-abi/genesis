"""Export generated episodes to disk (CONTRACT §2-3, T16).

Usage:
    python -m auditenv.export --config configs/dev.json --out episodes/dev

Output structure:
    <out>/
      index.json
      <episode_id>/
        public/
          manifest.json
          ledger.csv
          invoices.jsonl
          payments.jsonl
          fx.csv
          policy.json
        grader/
          truth.json
          provenance.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

from .generator import FX_FIELDS, LEDGER_FIELDS, generate
from .run import load_episodes


def _write_json(path: str, data: object) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _write_jsonl(path: str, records: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")


def _write_csv(path: str, fields: tuple[str, ...], rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(fields)
        for r in rows:
            writer.writerow([r.get(f) if r.get(f) is not None else "" for f in fields])


def export_episode(episode: dict, ep_dir: str) -> None:
    """Write one episode into public/ and grader/ subdirectories."""
    pub_dir = os.path.join(ep_dir, "public")
    grd_dir = os.path.join(ep_dir, "grader")

    # public files (task.txt: the agent's instructions, incl. the duplicate definition and hard-mode rules)
    os.makedirs(pub_dir, exist_ok=True)
    with open(os.path.join(pub_dir, "task.txt"), "w", encoding="utf-8", newline="") as fh:
        fh.write(episode["task"])
    _write_json(os.path.join(pub_dir, "manifest.json"), episode["manifest"])
    _write_json(os.path.join(pub_dir, "policy.json"), episode["policy"])
    _write_csv(os.path.join(pub_dir, "ledger.csv"), LEDGER_FIELDS, episode["tables"]["ledger"])
    _write_jsonl(os.path.join(pub_dir, "invoices.jsonl"), episode["tables"]["invoices"])
    _write_jsonl(os.path.join(pub_dir, "payments.jsonl"), episode["tables"]["payments"])
    _write_csv(os.path.join(pub_dir, "fx.csv"), FX_FIELDS, episode["tables"]["fx"])

    # grader files
    _write_json(os.path.join(grd_dir, "truth.json"), episode["truth"])
    _write_json(os.path.join(grd_dir, "provenance.json"), episode["provenance"])


def export_split(config_path: str, out_dir: str) -> list[dict]:
    """Export all episodes defined in a config file into out_dir."""
    episodes = load_episodes(config_path)
    os.makedirs(out_dir, exist_ok=True)
    index: list[dict] = []

    for seed, cfg in episodes:
        ep = generate(seed, cfg)
        ep_id = ep["episode_id"]
        ep_dir = os.path.join(out_dir, ep_id)
        export_episode(ep, ep_dir)
        index.append({"config": cfg, "episode_id": ep_id, "seed": seed})

    index_path = os.path.join(out_dir, "index.json")
    _write_json(index_path, index)
    return index


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="path to config JSON (e.g. configs/dev.json)")
    ap.add_argument("--out", required=True, help="output directory (e.g. episodes/dev)")
    args = ap.parse_args(argv)

    index = export_split(args.config, args.out)
    print(f"Exported {len(index)} episodes to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
