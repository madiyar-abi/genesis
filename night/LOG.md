2026-11-22 00:21 lead — Round 20 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/REVIEW/r19 archive. Wrote TASKS.md: independent defect hunts (codex1 chronology/policy-text/adapter reality, codex2 fresh-clone + claims audits, rb scenario adapter runs), evidence sweeps on unseen seeds for gemini workers. Baseline check running. Assumption: generator fixes stay with lead (one re-export owner) to avoid conflicting exports.
2026-11-22 00:23 lead — D: demo --seed 2003 reproduces every DEMO.md number (326 rows, 69 invoices, 21 inspections, 0.958, 286 / 351331 minor units, 0.333, 22 actions). P: sync_docs tables match, but prose on slide 7 and DESIGN §9 was stale since 20 Nov: analyze --config configs/eval_hard.json gives reconcile 20 FP (not 22), duplicate recall 2/8 (not 3/8, six missed, not five), mean 43 actions (not 43.2). Fixed PITCH.md and DESIGN.md; sync_docs does not cover prose numbers.
2026-11-22 00:30 rb — Z1 done: night/r20/scenarios_adapter.py plays all D01–D20 through judge_adapter, closed mode
  (generate_episode with the default grader key, AUDITENV_SECRET unset), seeds 32000–32004, default + hard, policies
  reconcile / reconcile_hard and flag_all driven via JuryPolicy (jury-shaped observations only; scores read from the
  grader-side env.grader_log; the script never opens truth/provenance). Command:
  `env -u AUDITENV_SECRET uv run python night/r20/scenarios_adapter.py` → exit 0, wall 7.0 s, 400 runs
  (20 scenarios × 2 difficulties × 5 seeds × 2 policies), all submissions valid, every closed step reward 0.0
  (asserted), max episode time 0.024 s of the 60 s limit. Mean grader return per scenario (min F1 over the 5 seeds):
| scenario | default reconcile return (min F1) | default flag_all return | hard reconcile_hard return (min F1) | hard flag_all return |
|---|---|---|---|---|
| D01 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D02 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D03 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D04 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D05 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D06 | 0.956 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D07 | 0.956 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D08 | 0.956 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D09 | 0.961 (1.000) | -1.000 | 0.916 (1.000) | -1.000 |
| D10 | 0.959 (1.000) | -1.000 | 0.914 (1.000) | -1.000 |
| D11 | 0.961 (1.000) | -1.000 | 0.920 (1.000) | -1.000 |
| D12 | 0.960 (1.000) | -1.000 | 0.920 (1.000) | -1.000 |
| D13 | 0.960 (1.000) | -1.000 | 0.920 (1.000) | -1.000 |
| D14 | 0.962 (1.000) | -1.000 | 0.918 (1.000) | -1.000 |
| D15 | 0.962 (1.000) | -1.000 | 0.918 (1.000) | -1.000 |
| D16 | 0.963 (1.000) | -1.000 | 0.922 (1.000) | -1.000 |
| D17 | 0.963 (1.000) | -1.000 | 0.922 (1.000) | -1.000 |
| D18 | 0.963 (1.000) | -1.000 | 0.922 (1.000) | -1.000 |
| D19 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
| D20 | 0.960 (1.000) | -1.000 | 0.915 (1.000) | -1.000 |
  Flags: 0 — reconcile/reconcile_hard F1 = 1.000 on every scenario × difficulty × seed; flag_all return −1.000
  everywhere (never > 0). Notes (return below the README jury_run mean 0.959, F1 still 1.000 — not defects):
  D06–D08 default reconcile 0.956 (22.8 mean steps vs the 21.4-scenario average; README's 0.959 is a 20-scenario
  mean on seeds 3001–3020, per-scenario return varies with the 0.002/step inspection cost); all 20 hard scenarios
  reconcile_hard 0.914–0.922 (41–44 mean steps: hard books need ~2× the inspections; README's table is default
  difficulty, no hard jury_run mean is documented). Assumptions: policies run in-process behind JuryPolicy instead
  of policy_worker subprocesses because reconcile_hard is not in policy_worker.POLICIES and product code is
  off-limits for workers — isolation is equivalent (the policy object receives only reset/step observations);
  "documented value in README" taken as the jury_run table (reconcile return 0.959 / F1 1.000, flag_all −1.000).
  Full per-seed results: /tmp/r20-rb/z1.json, full output /tmp/r20-rb/z1.out. Next: Z2.
2026-11-22 00:31 rb — Z2 done: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base <B>
  --json /tmp/r20-rb/j<B>.json` for B = 20000, 21000, 22000, 23000. All four exit 0; wall times (time -p real):
  2.75 s, 2.87 s, 2.74 s, 2.83 s. Policy tables (P/R/F1 micro, mean return, mean steps, max steps, mean/max s):
  B=20000 (seeds 20001–20020): random_explorer 0.000/0.000/0.000 −1.000 33.0/33 0.040/0.045;
    reconcile 1.000/1.000/1.000 0.960 20.8/24 0.041/0.048; flag_all 0.000/0.000/0.000 −1.000 3.5/4 0.036/0.040;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  B=21000 (seeds 21001–21020): random_explorer 0.000/0.000/0.000 −0.903 33.0/33 0.041/0.049;
    reconcile 1.000/1.000/1.000 0.960 21.1/23 0.044/0.052; flag_all 0.000/0.000/0.000 −1.000 3.6/4 0.037/0.043;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  B=22000 (seeds 22001–22020): random_explorer 0.000/0.000/0.000 −1.000 33.0/33 0.039/0.043;
    reconcile 1.000/1.000/1.000 0.960 21.0/24 0.040/0.045; flag_all 0.000/0.000/0.000 −1.000 3.6/4 0.036/0.041;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  B=23000 (seeds 23001–23020): random_explorer 0.000/0.000/0.000 −0.903 33.0/33 0.042/0.049;
    reconcile 1.000/1.000/1.000 0.960 20.9/25 0.042/0.055; flag_all 0.000/0.000/0.000 −1.000 3.6/4 0.037/0.040;
    oracle 1.000/1.000/1.000 1.000 1.0/1 0.006/0.008.
  Flags: 0 — oracle F1 = 1.000 and reconcile F1 = 1.000 in all four runs (tp/fp/fn 20/0/0 each); no run's
  random/flag_all mean return > −0.5 (worst −0.903). Note (explained, not a defect): random_explorer's mean
  −0.9032 at B=21000 and B=23000 = 19×(−1) + one clean scenario where it submitted empty findings, the correct
  answer on clean books (F1 1.0, reward 0.936 = 1 − 0.002×32 inspections). Reproduced with a scratch replay
  (/tmp/r20-rb/z2_random_check.py, public generator as jury_run uses): B=21000 → D01 seed 21001, B=23000 → D04
  seed 23004, both 0/0/0, reward 0.9360. Micro F1 stays 0.000 because a clean episode contributes no tp/fp/fn.
  JSON tables: /tmp/r20-rb/j{20000,21000,22000,23000}.json; raw outputs j<B>.out. Both rb tasks (Z1, Z2) done.
