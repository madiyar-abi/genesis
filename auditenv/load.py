"""Read exported episodes for closed reset, scoring, and offline verification."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import stat
from pathlib import Path

from .generator import FX_FIELDS, LEDGER_FIELDS
from .verify import _invoice_error, _schema, _schema_error, _structure, ledger_balance_problems

_LEDGER_INT_FIELDS = {"debit_minor", "credit_minor"}
_LEDGER_NULLABLE = {"entity_id", "invoice_id", "payment_id"}
_FX_WITHOUT_ID = tuple(field for field in FX_FIELDS if field != "fx_id")


def _read_text(path: Path, default: str | None = None) -> str:
    try:
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode):
            raise ValueError(f"{path.name}: expected a regular file")
        text = path.read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        if default is not None:
            return default
        raise ValueError(f"{path.name}: required file is missing") from None
    except (OSError, UnicodeError):
        raise ValueError(f"{path.name}: cannot read UTF-8 text") from None
    if "\0" in text:
        raise ValueError(f"{path.name}: NUL byte in text")
    return text


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def _finite_float(literal):
    value = float(literal)
    if not math.isfinite(value):
        raise ValueError("nonfinite JSON number")
    return value


def _json_object(text: str, filename: str) -> dict:
    try:
        obj = json.loads(text, object_pairs_hook=_unique_object, parse_float=_finite_float,
                         parse_constant=_finite_float)
    except (ValueError, RecursionError):
        raise ValueError(f"{filename}: invalid JSON") from None
    if not isinstance(obj, dict):
        raise ValueError(f"{filename}: expected a JSON object")
    return obj


def _read_json(path: Path, default: str | None = None) -> dict:
    return _json_object(_read_text(path, default), path.name)


def _read_jsonl(path: Path) -> list[dict]:
    return [_json_object(line, path.name) for line in _read_text(path).split("\n") if line.strip()]


def _read_csv(path: Path, columns: tuple[str, ...]) -> list[dict]:
    rows = []
    reader = csv.reader(io.StringIO(_read_text(path), newline=""), strict=True)
    try:
        header = next(reader, [])
        duplicates = sorted({name for name in columns if header.count(name) > 1})
        if duplicates:
            raise ValueError(f"{path.name}: duplicate CSV columns: {', '.join(duplicates)}")
        expected = _FX_WITHOUT_ID if columns == FX_FIELDS and "fx_id" not in header else columns
        if len(header) != len(expected) or set(header) != set(expected):
            raise ValueError(f"{path.name}: missing or unexpected CSV columns")
        for values in reader:
            if not values:
                continue
            if len(values) != len(header):
                raise ValueError(f"{path.name}: wrong number of cells in row {reader.line_num}")
            row = dict(zip(header, values))
            if columns == LEDGER_FIELDS:
                for key in _LEDGER_INT_FIELDS:
                    if not re.fullmatch(r"[+-]?[0-9]+", row[key].strip()):
                        raise ValueError(f"{path.name}: {key} must be an integer")
                    try:
                        row[key] = int(row[key])
                    except ValueError:
                        raise ValueError(f"{path.name}: {key} is too large to parse") from None
                for key in _LEDGER_NULLABLE:
                    if row[key] == "":
                        row[key] = None
            rows.append(row)
    except csv.Error:
        raise ValueError(f"{path.name}: invalid CSV") from None
    return rows


def load_episode(path: str) -> dict:
    """Load an exported episode, allowing the jury's minimal grading fixture."""
    try:
        path = Path(path)
    except TypeError:
        raise ValueError("episode_dir must be a path") from None
    public = path / "public"
    grader = path / "grader"
    if public.is_symlink() or grader.is_symlink():
        raise ValueError("episode subdirectories must not be symlinks")

    # The jury's case file list omits task.txt, provenance.json and the CSV fx_id column.
    task = _read_text(public / "task.txt", default="")
    if not task.strip() and (task or (public / "task.txt").exists()):
        raise ValueError("public task text must contain instructions")
    manifest = _read_json(public / "manifest.json")
    policy = _read_json(public / "policy.json")
    ledger = _read_csv(public / "ledger.csv", LEDGER_FIELDS)
    invoices = _read_jsonl(public / "invoices.jsonl")
    payments = _read_jsonl(public / "payments.jsonl")
    fx = _read_csv(public / "fx.csv", FX_FIELDS)
    for row in fx:
        row.setdefault("fx_id", f"{row['date']}:{row['source_currency']}:{row['target_currency']}")

    truth = _read_json(grader / "truth.json")
    provenance = _read_json(grader / "provenance.json", default='{"injections": []}')
    if not isinstance(provenance.get("injections"), list):
        raise ValueError("provenance.json: injections must be an array")
    issues = truth.get("issues")
    if not isinstance(issues, list) or any(not isinstance(issue, dict) for issue in issues):
        raise ValueError("truth.json: issues must be an array of objects")
    # An external fixture can omit scenario. The export verifier still requires the full schema.
    gradeable_truth = {**truth, "issues": [{"scenario": "single", **issue} for issue in issues]}
    error = _schema_error(gradeable_truth, _schema("truth.schema.json"), "truth")
    if error:
        raise ValueError("truth.json: unexpected field" if "unexpected field" in error else error)
    if truth["episode_id"] != manifest.get("episode_id"):
        raise ValueError("truth.json: episode_id differs from manifest")

    tables = {"ledger": ledger, "invoices": invoices, "payments": payments, "fx": fx}
    episode = {"episode_id": manifest.get("episode_id"), "task": task,
               "manifest": manifest, "policy": policy, "tables": tables,
               "truth": truth, "provenance": provenance}
    for invoice in invoices:
        error = _invoice_error(invoice)
        if error:
            raise ValueError(error)
    problems = _structure(episode, strict_export=False)
    if problems:
        raise ValueError(problems[0])
    invoice_ids = {invoice["invoice_id"] for invoice in invoices}
    for payment in payments:
        if any(ref["invoice_id"] not in invoice_ids for ref in payment["invoice_refs"] or []):
            raise ValueError("payments.jsonl: reference to an unknown invoice")
    problems = ledger_balance_problems(ledger)
    if problems:
        raise ValueError(problems[0])
    return episode
