# Round 18 log

2026-11-21 21:42 lead (Claude) — Round 18 started (open improvement round, freeze 2026-11-22 18:00). No TASKS.md existed, so this is the first lead of the round. Wrote night/TASKS.md: 3 tasks per worker (gemini1a–3b evidence sweeps/doc integrity on new seeds, codex1/codex2 red-team the four jury blocks with fixes, rb doc-consistency tests). Assumption: the memory note "red-team passes beat sweeps" (r16) → the strong workers get red-team tasks, the Gemini workers get evidence on new seed ranges. Next: lead review (T30) while the check runs.

2026-11-21 21:48 gemini1b — T4 stress solvability on seeds 5000–5299.
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --stress reconcile --seeds 5000-5299`
  Exit code: 0
  Wall time: 22.21 s
  Summary: reconcile on 1200 default episodes (seeds 5000-5299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 32, truncated 0 (22.0 s)
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 5000-5299`
  Exit code: 0
  Wall time: 70.77 s
  Summary: reconcile_hard on 1200 hard episodes (seeds 5000-5299 x random_mix, clean, 12_issues, 12_issues_100_invoices): imperfect 0, max steps 57, truncated 0 (70.7 s)
Result: 0 imperfect, 0 truncated across 2,400 episodes. Max steps: 32 (default), 57 (hard).
Next: T5 (jury_run on seed bases 7000, 8000, 9000).
2026-11-21 21:48 gemini3a — T13 complete: verified relative markdown links and backticked repo paths across README.md, docs/CHECKS.md, docs/DESIGN.md, docs/CONTRACT.md, docs/DEMO.md, docs/PITCH.md.
Command: python3 /tmp/r18-gemini3a/check_links.py (exit 0)
- README.md: 14 markdown links checked, 85 repo paths checked; 0 missing
- docs/CHECKS.md: 0 markdown links checked, 201 repo paths checked; 0 missing
- docs/DESIGN.md: 1 markdown links checked, 13 repo paths checked; 0 missing
- docs/CONTRACT.md: 0 markdown links checked, 11 repo paths checked; 0 missing
- docs/DEMO.md: 0 markdown links checked, 1 repo paths checked; 0 missing
- docs/PITCH.md: 0 markdown links checked, 2 repo paths checked; 0 missing
Total: 15 markdown links, 313 repo paths checked across 6 files. 0 missing.
Next: T14.

2026-11-21 21:49 gemini3a — T14 complete: verified all CLI command lines and flags in README.md and docs/*.md.
Command: python3 /tmp/r18-gemini3a/check_flags.py (exit 0)
Number of command lines checked: 67 across 6 files (README.md, docs/CHECKS.md, docs/CONTRACT.md, docs/DEMO.md, docs/DESIGN.md, docs/PITCH.md).
Result: 0 unknown flags.
Next: T15.
2026-11-21 21:49 codex1 — T20. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/pairs.py` exited 0 in 52.61 s. Seeds 0–49 in each mode. All surrogate IDs were renamed across the exported files. Because CONTRACT §2 defines fx_id by date and currencies, shifted all dates forward one 400-year Gregorian cycle to change every FX ID while preserving weekdays, periods and rate lookups. Shuffled all four tables. Both runs of `python -m auditenv.verify --dir <transformed split>` reported `50/50 episodes valid; episodes with problems: 0`. Closed rewards and grader-side oracle rewards matched across all 100 pairs, zero mismatches. No code fix required. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 173.15 s, `ALL CHECKS PASSED in 172.9 s`. Next: defensive contract and isolation checks.

2026-11-21 21:49 lead — T98: fresh `auditenv.demo --seed 2003` matches every number in docs/DEMO.md (326 rows, 69 invoices, 21 inspection steps, 0.958, 0.333, 286 / 351331 minor units, 22 actions, TP 4) and the check (dev reconcile F1 1.000, hard 0.752). No edit needed.

2026-11-21 21:49 lead — T99: `sync_docs --check` clean against a fresh `check --json`. Found one untracked stale number: `scripts/mutate_reward.py` now runs 22 mutants (22/22 killed, re-run tonight) but PITCH slide 8, CHECKS.md, README "Other commands" and HANDOFF "How to run" said 15. Fixed all four; historical round notes in HANDOFF left as they were.

2026-11-21 21:50 lead — T30 (part): engineering/§09 review subagent scored Engineering 10/10, no blocking issue; Docker job green in CI run 44925790975. Gap fixed: 10 of the 20 episode ids in trajectories.jsonl (hard train, seeds 1100–1109) are not under episodes/, so a juror cross-checking sees unknown ids. README now says where they come from with the export command; checked that the 20 trajectory ids = episodes/train ∪ a fresh export of configs/train_hard.json. Not done (optional, no point at stake): stamping generator/config versions into check --json.

2026-11-21 21:54 lead — T30 (part): docs-claims review subagent checked ~150 claims in README, CHECKS, DESIGN, CONTRACT; fixed the 10 verified defects: README + CONTRACT said `episode_over` costs a step (env.step returns before counting it — now "free and changes nothing"); README said jury_run scenarios come from `judge_adapter.generate_episode` (it uses the public generator, seeds 3001–3020); README's invalid-submission list lacked unknown key and wrong episode_id; CHECKS test counts 69→70 (jury blocks), 10→12 (verify_semantics), 10→11 (verify_redteam), 2→3 README snippets, 11→14 limitations; DESIGN fuzz actions 20 312→20 319, hard random>0 50→47 (re-ran `fuzz --seeds 0-199 --hard`: 47/600, 0 dirty), and the 0.964 payment_allocation cue (2900 amount repeated in ≥4 ledger rows, 217/225) that DESIGN §10 omitted.
2026-11-21 21:52 codex1 — T21. Closed reset without a supplied secret printed the test grader key path to stderr on both file success and fallback. Regression `JudgeContractTest.test_closed_reset_keeps_key_path_off_stderr` failed both subcases before the fix. Suppressed this grader diagnostic during closed reset; offline grader generation retains its existing warning contract. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/privacy.py` exited 0 in 3.26 s: `40 fixtures, identical private-data differential transcripts; 80 expected reset errors; stream canaries absent`. Seeds 0–19 default and hard, all four tables paged, document lookup, tool errors, invalid submit. Changed truth and provenance while keeping public records fixed and compared every observation, reward, flag and info dict. Checked bad-directory and malformed-grader-file exceptions, stdout and stderr using synthetic markers. This distinguishes public invoice IDs and amounts from private annotations. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 114.07 s: `ALL CHECKS PASSED in 114.0 s`. Next: T19.
2026-11-21 21:52 rb — T25 done: new tests/test_checks_map.py parses all 102 `tests/<file>.py::<Class>::<method>` references in docs/CHECKS.md (unique triples), imports each module and asserts class+method exist; fails with the full list of broken references. `env -u AUDITENV_SECRET uv run python -m unittest tests.test_checks_map` → Ran 2 tests, OK (0.109 s). Scratch-copy proof: copied docs/CHECKS.md to /tmp/r18-rb/CHECKS-scratch.md, renamed `test_c01_reset_returns_json_pair` → `..._RENAMED`; find_broken_references reported `tests/test_judge_contract.py::JudgeContractTest::test_c01_reset_returns_json_pair_RENAMED: method ... not found on JudgeContractTest` (also covered by the in-suite test_renamed_method_is_detected). `env -u AUDITENV_SECRET uv run python -m auditenv.check` exit 0, ALL CHECKS PASSED in 173.2 s. Assumption: reference regex only matches the documented `tests/<file>.py::Class::method` form (no bare module::method refs exist in CHECKS.md). Next: T26.
2026-11-21 21:50 gemini1b — T5 jury_run baseline evaluation on seed bases 7000, 8000, 9000.
Command 1: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 7000 --json /tmp/r18-gemini1b/j7000.json` (exit 0, wall time 3.85 s)
```
policy                P      R     F1   return   steps   max   time s   max s
random_explorer   0.000  0.000  0.000   -1.000    33.0    33    0.059   0.071
reconcile         1.000  1.000  1.000    0.961    20.6    24    0.057   0.066
flag_all          0.000  0.000  0.000   -1.000     3.4     4    0.051   0.059
oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.008
Command 2: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 8000 --json /tmp/r18-gemini1b/j8000.json` (exit 0, wall time 3.81 s)
random_explorer   0.000  0.000  0.000   -0.903    33.0    33    0.056   0.062
reconcile         1.000  1.000  1.000    0.961    20.5    26    0.057   0.065
flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.049   0.055
oracle            1.000  1.000  1.000    1.000     1.0     1    0.005   0.007
Command 3: `env -u AUDITENV_SECRET uv run python -m auditenv.jury_run --seed-base 9000 --json /tmp/r18-gemini1b/j9000.json` (exit 0, wall time 3.71 s)
random_explorer   0.000  0.000  0.000   -1.000    33.0    33    0.054   0.058
reconcile         1.000  1.000  1.000    0.962    20.1    23    0.055   0.059
flag_all          0.000  0.000  0.000   -1.000     3.5     4    0.049   0.051
oracle            1.000  1.000  1.000    1.000     1.0     1    0.006   0.010
F1 stability analysis:
- No policy differed in F1 across runs (random_explorer: 0.000, reconcile: 1.000, flag_all: 0.000, oracle: 1.000 in all 3 runs; max diff = 0.000, well below threshold 0.2).
- Reconcile achieved F1 1.000 with mean return ~0.961 and average steps 20.1–20.6 (max steps 26).
Next: T6 (fuzz 3000 configs starting at 50000).
2026-11-21 21:54 gemini1b — T6 fuzz 3000 configs starting at 50000.
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --configs 3000 --start 50000`
  Exit code: 0
  Wall time: 211.31 s (3m 31.31s)
  Summary: config sweep, cases 50000-52999: 3000 random configs (1222 hard) in 211.2 s; problems (exception / verifier / issue count / oracle or rule policy F1 < 1): 0; max steps 55
  FUZZ PASSED
Result: 0 problems across 3,000 random configurations (1,222 hard). Max steps: 55.
All gemini1b tasks (T4, T5, T6) complete.
2026-11-21 21:51 gemini3a — T15 complete: checked all `tests/<file>.py::<Class>::<method>` references in docs/CHECKS.md.
Command: python3 /tmp/r18-gemini3a/check_test_refs.py (exit 0)
Checked 138 `tests/<file>.py::<Class>::<method>` references (and 9 class references).
Result: 0 missing.
All assigned gemini3a tasks (T13, T14, T15) complete.
2026-11-21 21:50 gemini3b — T16: Fresh clone in path with spaces ('/tmp/r18 gemini3b clone'). Ran: (1) `env -u AUDITENV_SECRET uv run python -m auditenv.check` — exit 0, wall 177.55s, last line: 'ALL CHECKS PASSED in 177.4 s'; (2) `env -u AUDITENV_SECRET uv run python -m auditenv.demo` — exit 0, wall 0.30s, last line: 'Done. Full check: uv run python -m auditenv.check'; (3) `env -u AUDITENV_SECRET uv run python judge_adapter.py --help` — exit 0, wall 0.07s, no CLI implemented (exits 0 with empty output). Removed clone. Next: T17.

2026-11-21 21:56 lead — Merged codex1 (T20, T21 + fix), rb (T25), gemini1b (T4–T6), gemini3a (T13–T15), gemini3b (T16); reviewed each diff (only codex1 touched code: closed reset no longer prints the grader key path; regression test added). `auditenv.check` on the merged tip: 526 tests, ALL CHECKS PASSED in 101.0 s. REVIEW.md → "Round 18" written. Topped up gemini1b (T40–T42) and gemini3a (T43–T44).

2026-11-21 21:57 lead — T30 (part): data-ambiguity review subagent — independent definition-only checker matched truth on 44 000 episodes (seeds 20000–20999 × default, hard, heavy, D01–D20 × 2 difficulties), 0 contradictory/ambiguous episodes. The 0.4 % duplicate-cue misses are equal totals with different line items (legitimately not duplicates). Recorded in REVIEW; added a DESIGN §10 bullet on the baseline's unstated 3-day duplicate window (never changes a result) and bumped CHECKS' limitation count to 15. T30 done.
2026-11-21 21:54 codex1 — T19. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python /tmp/r18-codex1/contract_cases.py` exited 0 in 0.15 s: `116 total contract cases passed; peak step time 0.000241 s`. Independent fixed-input reset/step checks covered malformed envelopes and argument types, extra and missing keys, cursor/limit extremes, long Unicode/NUL IDs, calculator grammar/length boundaries, malformed submissions, interleaved adapters, reset while open, and calls after both terminal states. JSON serialization with allow_nan=False succeeded. Active steps cost one; after the episode ended its balance remained fixed as required by C15/C17. Zero defects found. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0 in 117.17 s: `ALL CHECKS PASSED in 117.0 s`. No queued codex1 tasks.
2026-11-21 21:55 gemini1a — T1: seed sweeps on seeds 7000-7999 (default + hard).
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 7000-7999`
  Exit code: 0
  Wall time: 193.53 s
  Summary:
  default mode, seeds 7000-7999: 3000 episodes (1986 dirty, 1014 clean) in 193.4 s
    episodes with a problem (exception / verifier / oracle): 0
    random explorer reward > 0: 254/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
    flag-all reward < 0: 3000/3000
  FUZZ PASSED
- Command: `env -u AUDITENV_SECRET uv run python -m auditenv.fuzz --seeds 7000-7999 --hard`
  Wall time: 350.80 s
  hard mode, seeds 7000-7999: 3000 episodes (1986 dirty, 1014 clean) in 350.6 s
    random explorer reward > 0: 268/3000 episodes, of them on dirty books: 0 (on clean books submitting nothing is the correct answer)
Problems: 0 problems found across 6,000 episodes (default + hard).
Next: T2 (config fuzz sweep: 3000 configs starting at 40000).
2026-11-21 21:55 gemini3b — T17: Other Python versions (3.12, 3.13) in fresh clone. Command `env -u AUDITENV_SECRET uv run --python 3.12 python -m auditenv.check` exited 2 in 9.17s; last line: 'error: The requested interpreter resolved to Python 3.12.12, which is incompatible with the project\'s Python requirement: `==3.11.*` (from `project.requires-python`)'. Command `env -u AUDITENV_SECRET uv run --python 3.13 python -m auditenv.check` exited 2 in 0.04s; last line: 'error: The requested interpreter resolved to Python 3.13.9, which is incompatible with the project\'s Python requirement: `==3.11.*` (from `project.requires-python`)'. Verified with `--no-project` that the codebase itself is fully compatible with both: all 521 unit tests and all gates pass cleanly on Python 3.12.12 (113.3s, exit 0, 'ALL CHECKS PASSED in 113.3 s') and Python 3.13.9 (111.3s, exit 0, 'ALL CHECKS PASSED in 111.3 s'). Removed worktree. Next: T18.
2026-11-21 21:55 gemini2a — T7: full unit suite ran three times with different hash seeds and timezones. All 3 runs passed with 0 failures:
- Run 1: `PYTHONHASHSEED=1 TZ=UTC env -u AUDITENV_SECRET uv run python -m unittest discover -s tests -t .` -> exit 0, wall time 76.17s (unittest 75.721s), `Ran 523 tests in 75.721s\n\nOK`.
- Run 2: `PYTHONHASHSEED=4242 TZ=Asia/Almaty env -u AUDITENV_SECRET uv run python -m unittest discover -s tests -t .` -> exit 0, wall time 140.48s (unittest 140.219s), `Ran 523 tests in 140.219s\n\nOK`.
- Run 3: `PYTHONHASHSEED=random TZ=America/New_York env -u AUDITENV_SECRET uv run python -m unittest discover -s tests -t .` -> exit 0, wall time 89.30s (unittest 89.069s), `Ran 523 tests in 89.069s\n\nOK`.
Failing tests: 0 (none). No flakiness or timezone/hashseed sensitivity found across 523 tests.

2026-11-21 22:00 lead (Claude, took over from the previous lead engine) — Merged gemini2a's WIP commit (T7; its LOG.md carried stash conflict markers — removed, kept every entry, dropped one duplicated codex1 T20 line). codex1 was idle: queued T45 (loader red-team via adapter/verify --dir), T46 (JSON-lines server red-team over a pipe), T47 (multi-cue shortcut cheater, evidence only — a generator fix would change default episodes). Started a lead subagent that re-reads the published jury check page line by line against judge_adapter + tests/test_judge_*. Next: merge workers every ~30 min. Assumption: marathon workers all alive (ps shows all 9 night.sh workers).

2026-11-21 22:09 codex1 — T45. Ran 123 independent file/record mutations through the closed adapter reset and `verify --dir` on a copied seed-2003 dev export. Baseline regression run: 47 failures and 25 unexpected errors. Missing files/directories, malformed headers, bad UTF-8, and bad CSV amounts could raise filesystem/parser exceptions or echo file paths → validate regular files, use path-free ValueErrors and check CSV arity, headers and integer cells. Symlinks, raw NUL, empty files and header-only exports could be silently accepted → validate file type/text and compare actual counts with the manifest. Duplicate JSON keys and nonfinite literals could be accepted → reject them in nested JSON/JSONL parsing. Wrong manifest/policy/truth/provenance types, malformed dates, duplicate document IDs, dangling references, and a 10^30 ledger edit could reach closed reset → validate schemas, ids, dates and ledger balance before opening the episode. The regressions check the open episode's remaining budget after each rejected reset and confirm valid BOM, CRLF, trailing blank lines, column reordering and equivalent integer spellings continue to load. The jury's minimal fixture can omit task/provenance and the FX id column. Directory verification still applies exported-episode requirements. All four tests in `tests.test_load_redteam` passed, and `scripts/golden.py --check` matched 80/80. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0, 530 tests, `ALL CHECKS PASSED in 65.8 s`. Next: T46.

2026-11-21 22:12 codex1 — T46. Sent 93 requests across serving subprocess pipes, plus two startup-failure cases and client EOF/cleanup checks (6 tests). Covered invalid UTF-8, a 10 MiB line, truncated and complete final frames at EOF, all three nonstandard constants, overflowing float, duplicate object keys at two nesting levels, 10,000-deep nesting, 5,001 integer digits, blank and whitespace-only lines, CRLF, 64 requests in one write, rejected reset, and post-terminal calls. Duplicate keys were last-wins, overflowing floats reached dispatch, and blank lines silently dropped responses → strict JSON decoding and one error per blank frame. A hidden list configured with train mode exposed terminal score and info with either key setting → hidden queues always use eval mode. Request-supplied config keys and bad hidden-list/grader-log paths were echoed, with a traceback on grader-log failure → bounded validation messages and sanitized startup/I/O errors. Calling a departed server raised BrokenPipeError and close left both stream handles open → defined client RuntimeError on EOF/pipe closure and idempotent stream cleanup. Closed wire checks found no explicit seed, truth, provenance or grading results in either key setting. The server's documented unkeyed public-reproducibility warning remains in effect. Focused regressions and all 24 server tests passed. `env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0, 536 tests, `ALL CHECKS PASSED in 79.2 s`. Next: T47.

2026-11-21 22:16 codex1 — T47. `env -u AUDITENV_SECRET PYTHONPATH=. uv run python -u /tmp/r18-codex1/cheat.py` exited 0 in 53.48 s. Fit up to three single-cue or two-cue rules per document/issue type on seeds 0–499, with minimum training support 20, then evaluated seeds 5000–5499 independently for each difficulty. Inputs came from public train-mode reset/step only. Public-generator truth supplied offline training targets and held-out record labels. The policy selected raw observable amount fields and companion IDs using training frequencies, and cited public documents, early linked ledger rows and available FX metadata without computing rates, journal balances or accounting discrepancies. Per-cue P/R measure record/type classification. Submission F1 is the adapter's exact grading after predicting IDs, amount and evidence. Baseline used the same companies and ordinary reconcile (both difficulties). Text reads preserved one action for submission. No memo fields were available, so memo presence was constant. The last payment row plus four linked ledger rows predicted payment FX errors in both difficulties. Several late ledger-position and invoice-day combinations also exceeded 0.5 precision. Full per-cue results are below and P > 0.5 is flagged. No product code changed.

```text
DEFAULT
invoices/duplicate_invoice metadata rule list: P=0.041 R=0.155 F1=0.065; 62/1520 predicted, 399 actual; rules=[((('text.wording', 'retainer'), ('counts.doc_ref', 0)), 0.05064456721915286), ((('row.ledger_last', 0), ('row.fraction', 2)), 0.059895833333333336), ((('time.day', 26), ('row.ledger_last', 7)), 0.07051282051282051)]
  combined (('text.wording', 'retainer'), ('counts.doc_ref', 0)) P=0.030 R=0.078 (31/1018 predicted; 399 actual)
  combined (('row.ledger_last', 0), ('row.fraction', 2)) P=0.063 R=0.058 (23/363 predicted; 399 actual)
  combined (('time.day', 26), ('row.ledger_last', 7)) P=0.051 R=0.025 (10/197 predicted; 399 actual)
  amount.magnitude=8 P=0.019 R=0.038 (15/797 predicted; 399 actual)
  amount.last_pair=84 P=0.000 R=0.000 (0/23 predicted; 399 actual)
  counts.linked_ledger=2 P=0.025 R=0.769 (307/12443 predicted; 399 actual)
  counts.entity=12 P=0.019 R=0.040 (16/822 predicted; 399 actual)
  id.last_digit=5 P=0.017 R=0.113 (45/2694 predicted; 399 actual)
  id.doc_format=9A9A9A9A P=0.000 R=0.000 (0/27 predicted; 399 actual)
  memo.present=False P=0.015 R=1.000 (399/26394 predicted; 399 actual)
  row.ledger_last=0 P=0.029 R=0.070 (28/953 predicted; 399 actual)
  text.wording=retainer P=0.022 R=0.110 (44/2044 predicted; 399 actual)
  time.day=18 P=0.025 R=0.045 (18/719 predicted; 399 actual)
invoices/period_cutoff metadata rule list: P=0.498 R=0.760 F1=0.602; 441/886 predicted, 580 actual; rules=[((('row.fraction', 9), ('counts.linked_ledger', 2)), 0.4534731323722149), ((('row.ledger_first', 9), ('time.day', 2)), 0.8918918918918919), ((('row.ledger_first', 9), ('time.day', 3)), 0.8767123287671232)]
  combined (('row.fraction', 9), ('counts.linked_ledger', 2)) P=0.500 R=0.728 (422/844 predicted; 580 actual)
  combined (('row.ledger_first', 9), ('time.day', 2)) P=0.881 R=0.128 (74/84 predicted; 580 actual) FINDING
  combined (('row.ledger_first', 9), ('time.day', 3)) P=0.838 R=0.116 (67/80 predicted; 580 actual) FINDING
  amount.magnitude=7 P=0.024 R=0.341 (198/8360 predicted; 580 actual)
  amount.last_pair=5 P=0.091 R=0.003 (2/22 predicted; 580 actual)
  counts.linked_ledger=2 P=0.040 R=0.848 (492/12443 predicted; 580 actual)
  id.format=9-9 P=0.020 R=0.250 (145/7090 predicted; 580 actual)
  id.doc_format=9 P=0.026 R=0.009 (5/189 predicted; 580 actual)
  memo.present=False P=0.022 R=1.000 (580/26394 predicted; 580 actual)
  row.fraction=9 P=0.175 R=0.728 (422/2412 predicted; 580 actual)
  row.from_end=1 P=0.210 R=0.181 (105/500 predicted; 580 actual)
  text.punctuation=8 P=0.024 R=0.336 (195/8223 predicted; 580 actual)
  text.length=7 P=0.024 R=0.176 (102/4171 predicted; 580 actual)
  time.day=3 P=0.078 R=0.153 (89/1139 predicted; 580 actual)
invoices/fx_error metadata rule list: P=0.178 R=0.256 F1=0.210; 138/774 predicted, 540 actual; rules=[((('row.ledger_last', 9), ('row.fraction', 9)), 0.1484149855907781), ((('row.ledger_first', 9), ('time.day', 3)), 0.4931506849315068), ((('row.ledger_first', 9), ('time.day', 2)), 0.5)]
  combined (('row.ledger_last', 9), ('row.fraction', 9)) P=0.173 R=0.235 (127/732 predicted; 540 actual)
  combined (('row.ledger_first', 9), ('time.day', 3)) P=0.512 R=0.076 (41/80 predicted; 540 actual) FINDING
  combined (('row.ledger_first', 9), ('time.day', 2)) P=0.583 R=0.091 (49/84 predicted; 540 actual) FINDING
  amount.roundness=0 P=0.054 R=0.169 (91/1691 predicted; 540 actual)
  amount.last_pair=97 P=0.067 R=0.002 (1/15 predicted; 540 actual)
  counts.linked_ledger=2 P=0.031 R=0.724 (391/12443 predicted; 540 actual)
  id.previous_gap=7 P=0.020 R=0.169 (91/4546 predicted; 540 actual)
  id.doc_format=9A9A9A9A P=0.037 R=0.002 (1/27 predicted; 540 actual)
  memo.present=False P=0.020 R=1.000 (540/26394 predicted; 540 actual)
  row.ledger_first=9 P=0.076 R=0.352 (190/2503 predicted; 540 actual)
  row.fx_local=4 P=0.075 R=0.119 (64/857 predicted; 540 actual)
  text.length=7 P=0.020 R=0.156 (84/4171 predicted; 540 actual)
  time.day=3 P=0.053 R=0.111 (60/1139 predicted; 540 actual)
payments/payment_allocation metadata rule list: P=0.357 R=0.416 F1=0.385; 154/431 predicted, 370 actual; rules=[((('counts.linked_ledger', 4), ('row.fraction', 9)), 0.38028169014084506), ((('counts.linked_ledger', 4), ('amount.last_pair', 0)), 0.31208053691275167), ((('counts.linked_ledger', 5), ('amount.magnitude', 6)), 0.25)]
  combined (('counts.linked_ledger', 4), ('row.fraction', 9)) P=0.476 R=0.292 (108/227 predicted; 370 actual)
  combined (('counts.linked_ledger', 4), ('amount.last_pair', 0)) P=0.404 R=0.343 (127/314 predicted; 370 actual)
  combined (('counts.linked_ledger', 5), ('amount.magnitude', 6)) P=0.167 R=0.014 (5/30 predicted; 370 actual)
  amount.last_pair=0 P=0.033 R=0.554 (205/6163 predicted; 370 actual)
  amount.last_pair=43 P=0.000 R=0.000 (0/69 predicted; 370 actual)
  counts.linked_ledger=4 P=0.171 R=0.516 (191/1117 predicted; 370 actual)
  counts.linked_ledger=5 P=0.094 R=0.024 (9/96 predicted; 370 actual)
  id.format=A9 P=0.036 R=0.419 (155/4280 predicted; 370 actual)
  id.doc_format=9 P=0.050 R=0.014 (5/101 predicted; 370 actual)
  memo.present=False P=0.028 R=1.000 (370/13194 predicted; 370 actual)
  row.from_end=0 P=0.192 R=0.259 (96/500 predicted; 370 actual)
  text.wording=absent P=0.028 R=1.000 (370/13194 predicted; 370 actual)
  time.day=1 P=0.159 R=0.108 (40/251 predicted; 370 actual)
payments/fx_error metadata rule list: P=0.742 R=0.868 F1=0.800; 138/186 predicted, 159 actual; rules=[((('row.from_end', 0), ('counts.linked_ledger', 4)), 0.8686131386861314), ((('counts.linked_ledger', 4), ('time.day', 31)), 0.7333333333333333)]
  combined (('row.from_end', 0), ('counts.linked_ledger', 4)) P=0.788 R=0.818 (130/165 predicted; 159 actual) FINDING
  combined (('counts.linked_ledger', 4), ('time.day', 31)) P=0.753 R=0.403 (64/85 predicted; 159 actual) FINDING
  amount.last_pair=0 P=0.022 R=0.836 (133/6163 predicted; 159 actual)
  amount.last_pair=49 P=0.013 R=0.006 (1/76 predicted; 159 actual)
  counts.linked_ledger=4 P=0.142 R=1.000 (159/1117 predicted; 159 actual)
  id.last_digit=8 P=0.011 R=0.101 (16/1392 predicted; 159 actual)
  id.doc_format=9A9A9A9 P=0.031 R=0.025 (4/127 predicted; 159 actual)
  memo.present=False P=0.012 R=1.000 (159/13194 predicted; 159 actual)
  row.from_end=0 P=0.260 R=0.818 (130/500 predicted; 159 actual)
  text.wording=absent P=0.012 R=1.000 (159/13194 predicted; 159 actual)
  time.day=31 P=0.156 R=0.403 (64/411 predicted; 159 actual)
  time.day=1 P=0.199 R=0.314 (50/251 predicted; 159 actual)
invoice documents unread for budget: 0/26394
default shortcut submissions: P=0.130090 R=0.217892 F1=0.162914 (TP=492 FP=3290 FN=1766)
default reconcile submissions: P=1.000000 R=1.000000 F1=1.000000 (TP=2258 FP=0 FN=0)
collecting hard training observations
grading hard held-out observations

HARD
invoices/duplicate_invoice metadata rule list: P=0.062 R=0.203 F1=0.094; 83/1348 predicted, 409 actual; rules=[((('text.style', 'uppercase'), ('counts.linked_ledger', 2)), 0.07371225577264653), ((('counts.linked_ledger', 2), ('text.style', 'lowercase')), 0.10204081632653061), ((('text.punctuation', 2), ('row.fraction', 6)), 0.058823529411764705)]
  combined (('text.style', 'uppercase'), ('counts.linked_ledger', 2)) P=0.054 R=0.152 (62/1150 predicted; 409 actual)
  combined (('counts.linked_ledger', 2), ('text.style', 'lowercase')) P=0.106 R=0.037 (15/142 predicted; 409 actual)
  combined (('text.punctuation', 2), ('row.fraction', 6)) P=0.106 R=0.027 (11/104 predicted; 409 actual)
  amount.magnitude=5 P=0.020 R=0.088 (36/1777 predicted; 409 actual)
  amount.last_pair=36 P=0.000 R=0.000 (0/22 predicted; 409 actual)
  counts.linked_ledger=2 P=0.024 R=0.736 (301/12449 predicted; 409 actual)
  counts.entity=12 P=0.030 R=0.090 (37/1239 predicted; 409 actual)
  id.last_digit=6 P=0.014 R=0.095 (39/2838 predicted; 409 actual)
  id.doc_format=A9A9A9A9 P=0.056 R=0.005 (2/36 predicted; 409 actual)
  memo.present=False P=0.015 R=1.000 (409/27858 predicted; 409 actual)
  row.ledger_last=1 P=0.028 R=0.086 (35/1260 predicted; 409 actual)
  text.style=uppercase P=0.032 R=0.161 (66/2095 predicted; 409 actual)
  text.style=lowercase P=0.070 R=0.039 (16/229 predicted; 409 actual)
  time.day=17 P=0.011 R=0.024 (10/880 predicted; 409 actual)
  time.minute=0 P=0.020 R=0.024 (10/501 predicted; 409 actual)
invoices/period_cutoff metadata rule list: P=0.449 R=0.746 F1=0.560; 394/878 predicted, 528 actual; rules=[((('row.fraction', 9), ('counts.linked_ledger', 2)), 0.4334862385321101), ((('row.ledger_first', 9), ('time.day', 2)), 0.8977272727272727), ((('row.ledger_first', 9), ('time.day', 3)), 0.8736842105263158)]
  combined (('row.fraction', 9), ('counts.linked_ledger', 2)) P=0.456 R=0.720 (380/834 predicted; 528 actual)
  combined (('row.ledger_first', 9), ('time.day', 2)) P=0.876 R=0.148 (78/89 predicted; 528 actual) FINDING
  combined (('row.ledger_first', 9), ('time.day', 3)) P=0.808 R=0.152 (80/99 predicted; 528 actual) FINDING
  amount.roundness=0 P=0.030 R=0.117 (62/2085 predicted; 528 actual)
  amount.last_pair=98 P=0.036 R=0.002 (1/28 predicted; 528 actual)
  counts.linked_ledger=2 P=0.037 R=0.867 (458/12449 predicted; 528 actual)
  id.last_digit=0 P=0.020 R=0.102 (54/2764 predicted; 528 actual)
  id.previous_gap=5 P=0.024 R=0.002 (1/42 predicted; 528 actual)
  memo.present=False P=0.019 R=1.000 (528/27858 predicted; 528 actual)
  row.fraction=9 P=0.148 R=0.720 (380/2568 predicted; 528 actual)
  row.from_end=0 P=0.178 R=0.169 (89/500 predicted; 528 actual)
  text.wording=absent P=0.117 R=0.064 (34/290 predicted; 528 actual)
  time.day=3 P=0.069 R=0.153 (81/1166 predicted; 528 actual)
  time.day=2 P=0.070 R=0.157 (83/1180 predicted; 528 actual)
invoices/fx_error metadata rule list: P=0.137 R=0.298 F1=0.188; 159/1161 predicted, 533 actual; rules=[((('row.ledger_first', 9), ('row.fraction', 9)), 0.14631197097944376), ((('row.ledger_first', 9), ('time.day', 2)), 0.5568181818181818), ((('row.fx_local', 9), ('row.ledger_first', 9)), 0.1711340206185567)]
  combined (('row.ledger_first', 9), ('row.fraction', 9)) P=0.156 R=0.233 (124/797 predicted; 533 actual)
  combined (('row.ledger_first', 9), ('time.day', 2)) P=0.517 R=0.086 (46/89 predicted; 533 actual) FINDING
  combined (('row.fx_local', 9), ('row.ledger_first', 9)) P=0.168 R=0.165 (88/524 predicted; 533 actual)
  amount.roundness=0 P=0.045 R=0.174 (93/2085 predicted; 533 actual)
  amount.last_pair=29 P=0.000 R=0.000 (0/20 predicted; 533 actual)
  counts.linked_ledger=2 P=0.030 R=0.696 (371/12449 predicted; 533 actual)
  counts.entity=1 P=0.033 R=0.039 (21/630 predicted; 533 actual)
  id.format=A-9 P=0.019 R=0.238 (127/6545 predicted; 533 actual)
  id.doc_format=A-9A9A9A P=0.029 R=0.011 (6/207 predicted; 533 actual)
  memo.present=False P=0.019 R=1.000 (533/27858 predicted; 533 actual)
  row.fx_local=9 P=0.078 R=0.235 (125/1598 predicted; 533 actual)
  text.punctuation=8 P=0.022 R=0.293 (156/7234 predicted; 533 actual)
  text.wording=absent P=0.034 R=0.019 (10/290 predicted; 533 actual)
  time.day=2 P=0.052 R=0.114 (61/1180 predicted; 533 actual)
payments/payment_allocation metadata rule list: P=0.351 R=0.278 F1=0.310; 85/242 predicted, 306 actual; rules=[((('counts.linked_ledger', 4), ('row.fraction', 9)), 0.42016806722689076), ((('counts.linked_ledger', 4), ('row.from_end', 1)), 0.3382352941176471), ((('counts.linked_ledger', 4), ('amount.roundness', 3)), 0.39473684210526316)]
  combined (('counts.linked_ledger', 4), ('row.fraction', 9)) P=0.370 R=0.261 (80/216 predicted; 306 actual)
  combined (('counts.linked_ledger', 4), ('row.from_end', 1)) P=0.176 R=0.039 (12/68 predicted; 306 actual)
  combined (('counts.linked_ledger', 4), ('amount.roundness', 3)) P=0.441 R=0.049 (15/34 predicted; 306 actual)
  amount.magnitude=7 P=0.028 R=0.301 (92/3282 predicted; 306 actual)
  amount.last_pair=22 P=0.000 R=0.000 (0/87 predicted; 306 actual)
  counts.linked_ledger=4 P=0.134 R=0.477 (146/1088 predicted; 306 actual)
  id.format=A9 P=0.030 R=0.503 (154/5100 predicted; 306 actual)
  id.doc_format=9A9A9A9 P=0.008 R=0.003 (1/127 predicted; 306 actual)
  memo.present=False P=0.023 R=1.000 (306/13232 predicted; 306 actual)
  row.from_end=0 P=0.138 R=0.225 (69/500 predicted; 306 actual)
  row.pos=6 P=0.067 R=0.003 (1/15 predicted; 306 actual)
  text.wording=absent P=0.023 R=1.000 (306/13232 predicted; 306 actual)
  time.day=1 P=0.100 R=0.078 (24/239 predicted; 306 actual)
payments/fx_error metadata rule list: P=0.773 R=0.829 F1=0.800; 116/150 predicted, 140 actual; rules=[((('row.from_end', 0), ('counts.linked_ledger', 4)), 0.8280254777070064), ((('time.day', 1), ('counts.linked_ledger', 4)), 0.7428571428571429)]
  combined (('row.from_end', 0), ('counts.linked_ledger', 4)) P=0.764 R=0.764 (107/140 predicted; 140 actual) FINDING
  combined (('time.day', 1), ('counts.linked_ledger', 4)) P=0.854 R=0.293 (41/48 predicted; 140 actual) FINDING
  amount.roundness=3 P=0.021 R=0.107 (15/715 predicted; 140 actual)
  amount.roundness=4 P=0.000 R=0.000 (0/95 predicted; 140 actual)
  counts.linked_ledger=4 P=0.129 R=1.000 (140/1088 predicted; 140 actual)
  id.last_digit=6 P=0.004 R=0.043 (6/1338 predicted; 140 actual)
  id.doc_format=9A9A9A9 P=0.000 R=0.000 (0/127 predicted; 140 actual)
  memo.present=False P=0.011 R=1.000 (140/13232 predicted; 140 actual)
  row.from_end=0 P=0.214 R=0.764 (107/500 predicted; 140 actual)
  text.wording=absent P=0.011 R=1.000 (140/13232 predicted; 140 actual)
  time.day=1 P=0.172 R=0.293 (41/239 predicted; 140 actual)
invoice documents unread for budget: 290/27858
hard shortcut submissions: P=0.120149 R=0.209940 F1=0.152832 (TP=452 FP=3310 FN=1701)
hard reconcile submissions: P=0.780478 R=0.909893 F1=0.840232 (TP=1959 FP=551 FN=194)
```

`env -u AUDITENV_SECRET uv run python -m auditenv.check` exited 0. ALL CHECKS PASSED in 52.1 s.
