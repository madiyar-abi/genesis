# Round 22

Open improvement round (freeze 2026-11-22 18:00). Round 21's balance re-derivation found the one accounting artefact
left in clean books: a full foreign-currency refund debits 2900 at the refund-date rate after the receipt credited it
at the receipt-date rate, so the customer's 2900 balance in base currency ends below zero (920 rows in clean D01–D05
configs on 300 seeds, up to 7.3 % of the refund). Every jury clean episode D01–D05 is generated with
`ensure_distractors` and therefore contains a refund; the jury checks "бухгалтерские равенства" on them. This round
fixes it at the root (lead): the refund debits 2900 at the rate of the receipt it returns, the difference goes to
7900 (realised FX), as a real ledger does. Workers re-check everything on the fixed generator.

**FIX COMMIT** = the lead's commit whose message starts with `generator: realised FX on refunds` on
`origin/night/2026-11-22-r22`. Tasks marked *after FIX* must not start before it is there (`git fetch && git log
origin/night/2026-11-22-r22 --oneline | grep "realised FX on refunds"`); if it is not there, do your other tasks
first, or stop with `IDLE`.

Rules for workers: run from the repo root, prefix every module with `env -u AUDITENV_SECRET uv run python -m ...`.
`git fetch && git merge origin/night/2026-11-22-r22` before each task. Touch only your listed files plus
night/TASKS.md (your own `[x]`) and night/LOG.md (append, `date '+%F %H:%M'` timestamp). Never edit README.md,
HANDOFF.md, REVIEW.md, docs/, auditenv/, episodes/, trajectories/ unless your task lists them. Scratch files only
under /tmp/r22-<your name>/. Evidence tasks: record exact command, exit code, wall time and the summary line(s);
quote any failure verbatim. If something fails, do NOT fix product code — log it with a reproduction; the lead fixes.
Audit scripts read only public data: they may import `auditenv.generator` (to generate), `auditenv.jury`,
`judge_adapter` and `auditenv.money`, never truth/provenance, `verify.py`, `inject.py` or `auditenv/policies/`.

## codex1 (strong)
- [x] X1 (codex1) Clean-room Block 2 matrix check, written only from night/CASE_UPDATES.md lines 100–115 (the D01–D20
  table, column "Что должно различаться") and README "Jury adapter": `night/r22/d_matrix.py`. For each scenario,
  generate seeds 50000–50199 × both difficulties via `judge_adapter.generate_episode(seed, auditenv.jury.SCENARIOS[D],
  dir)` and check from public data + the episode's truth count only (truth file may be read *only* for the number and
  type of issues): D01–D05 truth empty and the episode really contains a correct split payment, a correct refund,
  legitimate equal totals, records on the period's first/last day; D06–D08 the duplicate pair has different ids and
  documents (and equal totals elsewhere in the books are not duplicates); D09–D11 across the three at least one
  missing and one partial allocation over the seed range; D12–D13 the wrong rate is a published rate of another date;
  D14–D15 period boundary + timezone from manifest/policy decide; D16–D18 / D19–D20 the scenario parameters (not just
  values) vary across seeds — list which parameters vary. — files: night/r22/d_matrix.py, night/LOG.md — accept: LOG
  table scenario × requirement → holds in N/400 episodes; every requirement that fails in any episode quoted with
  seed, difficulty and ids.
- [ ] X2 (codex1, after FIX) Update `night/r21/ledger_identity.py` to the new refund rule (policy.json
  `ledger.payment`: a refund debits 2900 at the payment-date rate of the receipt it returns, difference to 7900) and run
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 41000-41299` and
  `--seeds 53000-53299` — files: night/r21/ledger_identity.py, night/LOG.md — accept: per check × config counts; the
  refund class (a) must be 0 in clean configs; any remaining violation quoted with seed and row ids.
- [ ] X3 (codex1, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor --seeds
  54000-54099` (update the auditor only if it relies on the old refund rule; say so in LOG) — files:
  night/r21/text_auditor.py, night/LOG.md — accept: table + discrepancy count (expected F1 1.000, 0 discrepancies).

## codex2 (strong)
- [x] Y1 (codex2) Clean-room Block 4 paired transform written only from night/CASE_UPDATES.md lines 140–160
  (P01–P20): `night/r22/paired_cleanroom.py`. Do NOT read auditenv/transform.py or tests/test_judge_paired.py.
  Copy an exported/generated episode, permute record order in every table, and replace every id by a fresh one
  through a bijection in *every* place it occurs — including ids embedded inside free-text fields (descriptions,
  memo/remittance text, task.txt, policy.json) if any. Serve the copy via `judge_adapter` reset on `episode_dir`,
  replay `reconcile`/`reconcile_hard` findings re-mapped through the bijection (and the original oracle answer
  re-mapped), score with `score_episode`. D01–D20 × seeds 55000–55009 × both difficulties. — files:
  night/r22/paired_cleanroom.py, night/LOG.md — accept: table scenario → original score, copy score, equal?; list
  every place an id occurs in free text (or "none found" with the fields searched); any score difference quoted.
- [x] Y2 (codex2, after FIX) Update `night/r20/policy_text.py` and `night/r20/chronology.py` to the new refund rule
  only where they test the old one, then run `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/policy_text.py
  --seeds 56000-56199` and `... night/r20/chronology.py --seeds 56000-56299` — files: night/r20/policy_text.py,
  night/r20/chronology.py, night/LOG.md — accept: exit codes, final lines verbatim, 0 unexpected failures and 0
  unexplained violations in clean configs; say which checks you changed and why.
- [ ] Y3 (codex2, after FIX) Read the FIX COMMIT diff as a strict reviewer: does policy.json / docs/CONTRACT.md §2
  state the new rule so that an auditor can derive the 2900 and 7900 amounts of every refund from public data alone
  (which receipt, which rate, rounding)? Try to construct a public-data case where the rule is ambiguous (two
  candidate receipts) and check with seeds 0–999 × default/hard/D01–D05 whether it ever happens. — files:
  night/LOG.md (script under /tmp/r22-codex2/) — accept: LOG: verdict + count of ambiguous refunds (expected 0) +
  any wording fix proposed as exact replacement text.

## rb (medium)
- [x] Z1 (rb) `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B> --json /tmp/r22-rb/j<B>.json`
  for B in 28000, 29000 — files: night/LOG.md — accept: per run the policy table; call out oracle F1 < 1, reconcile
  F1 < 1, or random/flag_all return > -0.5.
- [ ] Z2 (rb, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` and
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs` — files: night/LOG.md — accept:
  exit codes + summary tables; reconcile below README value or flag_all > 0 called out.
- [ ] Z3 (rb, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy` and the Z1
  commands for B in 30000, 31000 — files: night/LOG.md — accept: as Z1 + jury_copy summary.

## gemini1a (evidence only, files: night/LOG.md)
- [ ] G1 (gemini1a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 16000-16999` and the
  same with `--hard` — accept: both summaries + wall times; any problem line verbatim.
- [ ] G2 (gemini1a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 78000`
  — accept: summary + wall time + max steps.

## gemini1b (evidence only, files: night/LOG.md)
- [ ] G3 (gemini1b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds
  12000-12299` and `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds
  12000-12299` — accept: per command the summary line + wall time.
- [ ] G4 (gemini1b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 17000-17999` and the same
  with `--hard` — accept: both summaries + wall times.

## gemini2a (evidence only, files: night/LOG.md)
- [ ] G5 (gemini2a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 6000-7999` — accept:
  last line + wall time.
- [ ] G6 (gemini2a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 81000`
  — accept: summary + wall time + max steps.

## gemini2b (evidence only, files: night/LOG.md)
- [ ] G7 (gemini2b, after FIX) Re-export into scratch dirs and diff against the committed exports: for each split
  (dev → configs/dev.json, train → configs/train.json, hard → configs/eval_hard.json)
  `env -u AUDITENV_SECRET uv run python -m auditenv.export --config <cfg> --out /tmp/r22-gemini2b/<split>` then
  `diff -r episodes/<split> /tmp/r22-gemini2b/<split>` — accept: per split the diff exit code (expected 0).
- [ ] G8 (gemini2b, after FIX) `uv run python scripts/golden.py --check`, `uv run python scripts/mutate_reward.py`,
  `uv run python scripts/shortcut_miner.py --seeds 5000-5999 --report-only` and the same with `--hard` — accept:
  summary lines + exit codes; any miner value with precision > 0.5 that is NOT in docs/DESIGN.md §10 called out.

## gemini3a (evidence only, files: night/LOG.md)
- [ ] G9 (gemini3a, after FIX) Four jury modules 3 times: `env -u AUDITENV_SECRET uv run python -m unittest
  tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired` — accept: per
  run `Ran N tests` + result.
- [ ] G10 (gemini3a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.attack` and
  `uv run python scripts/sensitivity.py` — accept: summaries + exit codes.

## gemini3b (evidence only, files: night/LOG.md)
- [ ] G11 (gemini3b, after FIX) `uv run python -m auditenv.verify --dir episodes/<split>` for every directory under
  episodes/ — accept: per split the `N/N episodes valid` line.
- [ ] G12 (gemini3b, after FIX) `yes '' | uv run python -m auditenv.demo` — accept: exit code, final reward/score lines
  quoted; compare with the numbers in docs/DEMO.md and call out any difference.
- [ ] G13 (gemini3b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r22-gemini3b/c.json`
  then `uv run python scripts/sync_docs.py --check --json /tmp/r22-gemini3b/c.json` — accept: both exit codes; drift
  lines verbatim.

## lead
- [x] L0 (lead) Baseline on round start `774570d`: `env -u AUDITENV_SECRET uv run python -m auditenv.check` → exit 0, 50.6 s.
- [x] L1 (lead) FIX: refund debits 2900 at the payment-date rate of the receipt it returns, difference to 7900 —
  test first (clean D01–D05 seeds: every customer's 2900 balance in base currency returns to its pre-overpayment
  value), then CONTRACT §2 → generator + policy text → verify.py → re-export episodes/trajectories/golden — files:
  docs/CONTRACT.md, auditenv/generator.py, auditenv/verify.py, tests/, episodes/, trajectories*, scripts/golden data
  — accept: `env -u AUDITENV_SECRET uv run python -m auditenv.check` exit 0; `night/r21/ledger_identity.py
  --classify` refund class 0.
- [ ] L2 (lead) Merge worker branches, review, fix real defects; REVIEW.md "Round 22", DESIGN §10 / README limitation
  text updated (refund artefact removed, rounding residue stays), sync_docs, HANDOFF — accept: sync_docs --check no
  drift.
- [ ] D (lead) `docs/DEMO.md` re-verified against the actual demo output — accept: every number reproduced.
- [ ] P (lead) `docs/PITCH.md` re-verified against the current check output — accept: every number matches.
