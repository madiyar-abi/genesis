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
- [x] X2 (codex1, after FIX) Update `night/r21/ledger_identity.py` to the new refund rule (policy.json
  `ledger.payment`: a refund debits 2900 at the payment-date rate of the receipt it returns, difference to 7900) and run
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.ledger_identity --classify --seeds 41000-41299` and
  `--seeds 53000-53299` — files: night/r21/ledger_identity.py, night/LOG.md — accept: per check × config counts; the
  refund class (a) must be 0 in clean configs; any remaining violation quoted with seed and row ids.
- [x] X3 (codex1, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.text_auditor --seeds
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
- [x] Y3 (codex2, after FIX) Read the FIX COMMIT diff as a strict reviewer: does policy.json / docs/CONTRACT.md §2
  state the new rule so that an auditor can derive the 2900 and 7900 amounts of every refund from public data alone
  (which receipt, which rate, rounding)? Try to construct a public-data case where the rule is ambiguous (two
  candidate receipts) and check with seeds 0–999 × default/hard/D01–D05 whether it ever happens. — files:
  night/LOG.md (script under /tmp/r22-codex2/) — accept: LOG: verdict + count of ambiguous refunds (expected 0) +
  any wording fix proposed as exact replacement text.

## rb (medium)
- [x] Z1 (rb) `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B> --json /tmp/r22-rb/j<B>.json`
  for B in 28000, 29000 — files: night/LOG.md — accept: per run the policy table; call out oracle F1 < 1, reconcile
  F1 < 1, or random/flag_all return > -0.5.
- [x] Z2 (rb, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` and
  `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.extreme_configs` — files: night/LOG.md — accept:
  exit codes + summary tables; reconcile below README value or flag_all > 0 called out.
- [x] Z3 (rb, after FIX) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r21.jury_copy` and the Z1
  commands for B in 30000, 31000 — files: night/LOG.md — accept: as Z1 + jury_copy summary.

## gemini1a (evidence only, files: night/LOG.md)
- [x] G1 (gemini1a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 16000-16999` and the
  same with `--hard` — accept: both summaries + wall times; any problem line verbatim.
- [x] G2 (gemini1a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 78000`
  — accept: summary + wall time + max steps.

## gemini1b (evidence only, files: night/LOG.md)
- [x] G3 (gemini1b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds
  12000-12299` and `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds
  12000-12299` — accept: per command the summary line + wall time.
- [x] G4 (gemini1b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 17000-17999` and the same
  with `--hard` — accept: both summaries + wall times.

## gemini2a (evidence only, files: night/LOG.md)
- [x] G5 (gemini2a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 6000-7999` — accept:
  last line + wall time.
- [x] G6 (gemini2a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 81000`
  — accept: summary + wall time + max steps.

## gemini2b (evidence only, files: night/LOG.md)
- [x] G7 (gemini2b, after FIX) Re-export into scratch dirs and diff against the committed exports: for each split
  (dev → configs/dev.json, train → configs/train.json, hard → configs/eval_hard.json)
  `env -u AUDITENV_SECRET uv run python -m auditenv.export --config <cfg> --out /tmp/r22-gemini2b/<split>` then
  `diff -r episodes/<split> /tmp/r22-gemini2b/<split>` — accept: per split the diff exit code (expected 0).
- [x] G8 (gemini2b, after FIX) `uv run python scripts/golden.py --check`, `uv run python scripts/mutate_reward.py`,
  `uv run python scripts/shortcut_miner.py --seeds 5000-5999 --report-only` and the same with `--hard` — accept:
  summary lines + exit codes; any miner value with precision > 0.5 that is NOT in docs/DESIGN.md §10 called out.

## gemini3a (evidence only, files: night/LOG.md)
- [x] G9 (gemini3a, after FIX) Four jury modules 3 times: `env -u AUDITENV_SECRET uv run python -m unittest
  tests.test_judge_contract tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired` — accept: per
  run `Ran N tests` + result.
- [x] G10 (gemini3a, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.attack` and
  `uv run python scripts/sensitivity.py` — accept: summaries + exit codes.

## gemini3b (evidence only, files: night/LOG.md)
- [x] G11 (gemini3b, after FIX) `uv run python -m auditenv.verify --dir episodes/<split>` for every directory under
  episodes/ — accept: per split the `N/N episodes valid` line.
- [x] G12 (gemini3b, after FIX) `yes '' | uv run python -m auditenv.demo` — accept: exit code, final reward/score lines
  quoted; compare with the numbers in docs/DEMO.md and call out any difference.
- [x] G13 (gemini3b, after FIX) `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r22-gemini3b/c.json`
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

## Top-up 1 (05:40) — final generator = `d0fbb34` or later (FIX1 refunds + FIX2 completing payment closes the
receivable + FIX3 one overpayment per merged receipt). Rules as above; no gate, start now.
FIX2 rule (CONTRACT §2, policy.json `ledger.payment`): the ref that completes an invoice — with the refs of earlier
payments (by timestamp) it adds up to `total_minor` — credits `convert(total_minor) − Σ convert(earlier refs)` at the
invoice-date rate; the cash difference goes to 7900. The allocation injector never picks such a last part.
- [ ] X4 (codex1) Update `night/r21/ledger_identity.py` to the FIX2 rule (keep class (b) as the detector of the old
  per-application residue) and run `--classify --seeds 41000-41299` and `--seeds 57000-57299` — files:
  night/r21/ledger_identity.py, night/LOG.md — accept: clean configs (a) 0, (b) 0, (c) 0; anything else quoted with
  seed and row ids.
- [ ] X5 (codex1) Update `night/r21/text_auditor.py` to the FIX2 rule only if it needs it (a per-ref expected credit
  now gives ±1 false payment_allocation findings on completing parts), run `--seeds 58000-58099` — files:
  night/r21/text_auditor.py, night/LOG.md — accept: table, F1 1.000, 0 discrepancies; say whether you changed it.
- [ ] Y4 (codex2) Update `night/r20/policy_text.py` to the FIX2 rule where it checks AR credits, run `--seeds
  59000-59199`; run `night/r20/chronology.py --seeds 59000-59299` — files: night/r20/policy_text.py,
  night/r20/chronology.py, night/LOG.md — accept: 0 unexpected failures; 0 unexplained violations in clean configs.
- [ ] Y5 (codex2) Review the FIX2 commit (`7efcfb7`) as a strict reviewer, like Y3: can an auditor derive every
  completing ref's AR credit from public data alone? Hunt for ambiguous cases on seeds 0–999 × default/hard/D01–D20:
  two payments at the same instant referencing one invoice, a completing ref in an out-of-period payment, prior-period
  invoices (no AR debit in the ledger), hard-mode credit notes/re-issues, duplicate copies, over-payment refs (ref =
  total). Script under /tmp/r22-codex2/ — files: night/LOG.md — accept: counts per case; any ambiguity or posting
  mismatch quoted with seed/ids; exact replacement wording if the text is unclear.
- [ ] Y6 (codex2) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r22.paired_cleanroom` on seeds
  60000–60009 (add a `--seeds` flag if missing) — files: night/r22/paired_cleanroom.py, night/LOG.md — accept: table,
  0 discrepancies.
- [ ] Z4 (rb) On the final generator: `PYTHONPATH=. env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py`,
  `... -m night.r21.extreme_configs`, `... -m night.r21.jury_copy`, `env -u AUDITENV_SECRET uv run python -m
  auditenv.jury_run --seed-base <B>` for B in 32000, 33000 — files: night/LOG.md — accept: exit codes + summaries;
  call-outs as in Z1/Z2.
- [ ] G14 (gemini1a) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 18000-18999` and the same with
  `--hard` — files: night/LOG.md — accept: both summaries + wall times.
- [ ] G15 (gemini1b) `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 13000-13299` and
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 13000-13299` — files:
  night/LOG.md — accept: per command the summary line + wall time.
- [ ] G16 (gemini2a) `env -u AUDITENV_SECRET uv run python -m auditenv.verify --seeds 8000-9999` and
  `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 84000` — files: night/LOG.md — accept:
  last lines + wall times.
- [ ] G17 (gemini2b) Re-export diff (as G7, scratch dir /tmp/r22-gemini2b/final/<split>), then
  `uv run python scripts/golden.py --check`, `uv run python scripts/mutate_reward.py` — files: night/LOG.md — accept:
  diff exit codes 0, golden 80/80, mutants 22/22.
- [ ] G18 (gemini3a) Four jury modules twice (as G9), `env -u AUDITENV_SECRET uv run python -m auditenv.attack`,
  `uv run python scripts/sensitivity.py` — files: night/LOG.md — accept: `Ran N tests` + OK per run; summaries; compare
  sensitivity tables with docs/DESIGN.md "Sensitivity" table and call out any difference.
- [ ] G19 (gemini3b) `PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r22.d_matrix` (if it has a seed flag,
  seeds 61000–61199), `yes '' | uv run python -m auditenv.demo`, then `env -u AUDITENV_SECRET uv run python -m
  auditenv.check --json /tmp/r22-gemini3b/c2.json` and `uv run python scripts/sync_docs.py --check --json
  /tmp/r22-gemini3b/c2.json` — files: night/LOG.md — accept: exit codes + summary lines; d_matrix 0 failed checks.
