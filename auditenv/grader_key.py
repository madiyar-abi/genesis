"""Grader key derivation and management for closed/hidden episodes."""

from __future__ import annotations

import os
import secrets
import sys

from .generator import secret

_WARNED = False
_PROCESS_KEY = ""


def grader_key(*, warn: bool = True, caller: str = "judge_adapter") -> str:
    """The key of closed episodes: AUDITENV_SECRET if set, else a random key read from the grader key file, which is
    created on first use (atomically, mode 0600). A public constant would let a policy recover the seed from
    episode_id or the records and regenerate the truth with this open-source generator. If the file cannot be
    used (read-only home, empty file), a random key for this process keeps the seed hidden instead."""
    global _WARNED, _PROCESS_KEY
    if secret():
        return secret()
    path = os.path.expanduser(os.environ.get("AUDITENV_KEY_FILE") or os.path.join("~", ".auditenv", "grader.key"))
    try:
        key = _key_file(path)
        note = f"closed episodes are keyed by the grader key in {path} and reproduce on this machine"
    except (OSError, ValueError) as exc:
        _PROCESS_KEY = _PROCESS_KEY or secrets.token_hex(32)
        key = _PROCESS_KEY
        note = (f"grader key file {path} is unusable ({exc}); closed episodes are keyed by a random key of this "
                "process and do not reproduce in another one")
    if warn and not _WARNED:
        _WARNED = True
        print(f"{caller}: AUDITENV_SECRET is not set; {note}. Keep the key out of the policy's reach.",
              file=sys.stderr, flush=True)
    return key


def _key_file(path: str) -> str:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path) or ".", mode=0o700, exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="ascii") as fh:
                fh.write(secrets.token_hex(32) + "\n")
            os.link(tmp, path)  # never a half-written key; if another process won the race, its key is used
        except FileExistsError:
            pass
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    with open(path, encoding="ascii") as fh:
        key = fh.read().strip()
    if not key:
        raise ValueError("empty file")
    return key
