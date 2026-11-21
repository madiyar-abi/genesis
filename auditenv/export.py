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
import shutil
import sys
import tempfile
from pathlib import Path

from .generator import FX_FIELDS, LEDGER_FIELDS, episode_id_for, generate
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
    if not episodes:
        raise ValueError("cannot export an empty split")
    expected = set()
    for seed, cfg in episodes:
        name = episode_id_for(seed, cfg)
        if name in expected:
            raise ValueError(f"duplicate episode {name} for seed {seed}")
        expected.add(name)
    dest = Path(out_dir).resolve()
    if dest.exists():
        stale = sorted(p.name for p in dest.iterdir() if (p / "public").is_dir() and p.name not in expected)
        if stale:
            raise ValueError(f"destination contains episodes outside the requested split: {', '.join(stale)}")
    # generate everything first: a generation error must not touch the destination
    generated = [(seed, cfg, generate(seed, cfg)) for seed, cfg in episodes]
    index = [{"config": cfg, "episode_id": ep["episode_id"], "seed": seed} for seed, cfg, ep in generated]

    # write into a working directory on dest's filesystem, so publishing is renames only. An existing dest holds
    # it itself: dest must be writable anyway, its parent need not be, and dest may be a mount point. It has no
    # public/, so neither the stale check nor `verify --dir` takes it for an episode, and _swap_entries moves only
    # the names written into it.
    if dest.exists():
        work = Path(tempfile.mkdtemp(prefix=f".{dest.name}.export-", dir=dest))
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f".{dest.name}.export-", dir=dest.parent))
    old = work / "old"
    try:
        new = work / "new"
        for _, _, ep in generated:
            export_episode(ep, os.path.join(new, ep["episode_id"]))
        _write_json(os.path.join(new, "index.json"), index)
        if dest.exists():
            _swap_entries(dest, new, old)
        else:
            os.replace(new, dest)
    except BaseException as exc:
        if not (old.is_dir() and any(old.iterdir())):
            shutil.rmtree(work, ignore_errors=True)
            raise
        # the rollback failed or was interrupted (exc; the export failure is its context): keep the previous files
        # and say where they are
        causes = [str(e) or type(e).__name__ for e in (exc.__context__, exc) if e is not None]
        message = f"export to {dest} failed and was not undone ({'; then '.join(causes)}); " \
                  f"the previous files are in {old}"
        if isinstance(exc, Exception):
            raise OSError(message) from exc
        print(message, file=sys.stderr)  # e.g. a second Ctrl-C: keep the interrupt, but name the path
        raise
    shutil.rmtree(work, ignore_errors=True)
    return index


def _swap_entries(dest: Path, new: Path, old: Path) -> None:
    """Replace dest's export entries (episode dirs, index.json last) with those in `new`; other files stay put.
    Old entries go to `old` first. On failure every rename is undone in reverse, so dest is as before."""
    names = sorted(p.name for p in new.iterdir() if p.name != "index.json") + ["index.json"]
    old.mkdir()
    done: list[tuple[Path, Path]] = []
    try:
        for name in names:
            if os.path.lexists(dest / name):
                os.replace(dest / name, old / name)
                done.append((dest / name, old / name))
        for name in names:
            os.replace(new / name, dest / name)
            done.append((new / name, dest / name))
    except BaseException:
        # any failure or interrupt from here on leaves files in `old`; export_split then keeps it and names it
        for src, dst in reversed(done):
            os.replace(dst, src)
        old.rmdir()  # empty again; rmdir cannot remove anything that was restored too late
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="path to config JSON (e.g. configs/dev.json)")
    ap.add_argument("--out", required=True, help="output directory (e.g. episodes/dev)")
    args = ap.parse_args(argv)

    try:
        index = export_split(args.config, args.out)
    except (OSError, ValueError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Exported {len(index)} episodes to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
