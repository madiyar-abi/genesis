# ROUND2 — polish run (started 2026-11-19 evening)

Round 1 is done and merged (`night/archive/r1-TASKS.md`, `r1-LOG.md`). The
environment meets every requirement of `night/SPEC.md`; this round raises the
jury score toward 100/100 (SPEC section 10) without breaking anything.

## Goal
Implement the open ideas in `HANDOFF.md` → "Ideas to improve", in jury-weight
order. Done (skip): R1, C1, D1, D3, P3, E1. Open, in this order:
1. R2 mutation testing of the reward · C3 injectable clock (60 s limit) · C2 server size/UTF-8 bounds
2. P1 golden hashes · P2 paired checks for hard mode (+ FX shuffle) · D4 shortcut miner (fix any leak found)
3. D2 decide/document "nothing allocated" evidence · R3 sensitivity table · H2 step-budget margin
4. E2 timing benchmark · E3 hard trajectories, `make fuzz`/`make stress`, CI badge · E4 chart of baseline returns (dev vs hard) for the pitch (stdlib-generated SVG, no new deps)
5. H1 "expert" difficulty (opt-in, default untouched) — only if 1–4 are done
6. E5 rule-search baseline — last, skip if short on time

Each idea is a hypothesis: reproduce/measure first. Acceptance = the "check"
column in HANDOFF plus `uv run python -m auditenv.check` and
`uv run python -m auditenv.fuzz --seeds 0-999` green.

## Rules (from HANDOFF "Rules first" — they win over anything else)
- Do not change the reset/step contract, actions, findings format or the shared
  reward. New behaviour only behind new optional config keys.
- Default-mode `episodes/` stay byte-identical unless a data fix requires it;
  then re-export `episodes/` + regenerate `trajectories/` in the same commit.
- Stdlib only, Python 3.11, `unittest`. No network, GPU, paid APIs, weight training.
- Every number in README/DESIGN/PITCH/DEMO comes from current `check`/`analyze`/`fuzz`
  output (`scripts/sync_docs.py`). Defects go to `REVIEW.md`.
- Teammates merge PRs into `main` in parallel. **Every ~30 min and before
  creating DONE: `git fetch && git merge origin/main` into the night branch**,
  resolve conflicts keeping both sides' intent, re-run check. Humans open the
  PR from the night branch into `main`.
- Write `night/TASKS.md` fresh for this round (task ids R2, C3, … as above).
  Good worker tasks: R2, P1, C2, C3, E2, E3 (self-contained, testable). Generator
  changes (D4 fixes, H1) stay with the lead.
