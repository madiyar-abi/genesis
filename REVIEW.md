# REVIEW.md — jury-style review (2026-11-19)

Scope: every module in `auditenv/` (env, generator, inject, matcher, metrics, schema, calculator,
experimental, verify, transform, server, client, run, export, load, analyze, check, demo, policies/),
tests/, configs/, Dockerfile, docs. Base: branch `hinabaina/hard-mode` (includes hard mode).
Method: reading the code plus a probe script that plays the jury's checks against the live env
(bad actions, leaks, limits, truncation, time limit, eval mode, determinism, evidence reachability
through the tools) and targeted data checks.

Status legend: **OK** = checked, no problem; **ISSUE n** = see "Findings" below.

## Jury clock and policy isolation (21 November 2026)

On `3180fe4`, 11 seconds loading a closed fixture and 50 seconds before the first action left the episode open. C18 measures from entry to reset. The new regression advances a monotonic test clock during both disk loading and generation, then checks for truncation on the first action at 61 seconds. Run `python -m unittest tests.test_judge_contract.JudgeContractTest.test_c18_reset_work_counts_toward_deadline`.

The original public baseline runner launched the policy from the grader checkout under the same OS user. That process could read files accessible to the grader. The isolated run in README uses a separate public-only image and sends observations over stdin. Use this mode when demonstrating C20.

## Public invoice, CSV and export validation

Before the fix, a repeated debit column with conflicting values was accepted, as were a missing invoice due date and a floating-point total. The split exporter also reported success for duplicate episode IDs or when a smaller requested split left an old episode directory behind. The schema smoke checker accepted duplicate evidence IDs. Targeted regressions live in `tests/test_verify_dir.py`, `tests/test_export.py` and `tests/test_schemas.py`.

## Invoice postings and completeness of the public hard split

- Moving only the revenue line within the accounting period previously left the invoice journal valid. The verifier now compares both booking instants, including the original booking in a reversed journal. Legitimate posting lag and equivalent timezone offsets still pass.
- The disk tests previously passed with one hard episode and skipped three checks when the directory was missing. The roundtrip test now compares the index against the configured 20 episodes before checking their contents. Independent trials with a missing directory, 19 entries and a substituted valid twentieth episode all failed as expected.

## 1.1 Contract and isolation (25)
- `reset(seed, config) -> (observation, info)`; `step -> (obs, reward, terminated, truncated, info)`, JSON-only — OK (`env.py`, probe).
- Exactly 5 actions; anything else → `unknown_action`, step consumed — OK.
- `list_records` ≤ 50 rows (larger limit clamped), stable `table:offset` cursors, cursor at the end → empty page, past the end → `bad_params` — OK.
- Calculator: AST whitelist over `Decimal`, character whitelist, 200-char cap; `__import__`, `open`, `**`, `//`, names, `1e5` rejected; division by zero → `calc_error` — OK.
- Unknown id / doc / table / malformed action (None, str, list, nested dicts) → bounded error, step consumed, never raises — OK (+ 3 000-action fuzz test).
- Observation = `{step, steps_remaining, result, error}` only; no shell/SQL/files/network — OK.
- `submit` → `terminated`; 100th non-submit step or 60 s → `truncated` with an empty answer graded; submit as step 100 is a submit — OK.
- No leak of truth/provenance/seed through observations, errors, info (train: counts and metrics only; eval: reward 0, info `{}`); `episode_id` is an HMAC, seed not recoverable with `AUDITENV_SECRET` — OK.
- `reset` rebuilds all state — OK.

## 1.2 Data and truth (25)
- 4 error types + I1, I2 + clean companies + distractors; history → documents → errors with recorded causal change — OK.
- Journals balance before and after injection; recomputed discrepancies == truth (verifier, 600 default + hard episodes) — OK.
- Formats: ISO-8601 with offset, int minor units + exponents, decimal-string rates, explicit nulls, manifest fields — OK.
- Evidence ids exist and are reachable through `get_document` / `get_record` (probe, 30 seeds) — OK.
- **ISSUE 1** — evidence sufficiency of `payment_allocation` (see below).

## 1.3 Reward reliability (25)
- Formula, P/R/F1, zero denominators, empty/empty = 1, empty truth + findings = 0 (`metrics.py`) — OK.
- TP rule (type, canonical ids, tolerance, currency, one full evidence set), one-to-one greedy matching, repeats = FP, missed = FN — OK.
- Limits 30 / 10 / 1000, unknown keys, bad types → invalid → reward −1 — OK.
- Attack tests (correct > silence, silence > accusations, duplicates, flag-all, step cost, guessed ids, unsupported evidence, wrong currency, resubmit, bad input, timeout, tolerance) exist and pass — OK.

## 1.4 Reproducibility and generalisation (15)
- Same seed + config + version + actions → identical episode and transitions (hash-compared in the check) — OK.
- Relabel + permute keeps the oracle answer/reward under the new ids; old answer scores 0 TP — OK.
- **ISSUE 4** — hard mode is not covered by the replay/transform tests.

## 1.5 Engineering (10)
- One command `uv run python -m auditenv.check`, stdlib only, Python 3.11, JSONL trajectories without truth, versioned configs, failure analysis, honest limitations — OK.
- **ISSUE 2** — the Dockerfile was never built or run (no Docker on the dev machine).
- **ISSUE 3** — `auditenv.verify --seeds` prints only the number of bad episodes, not how many were checked.
- **ISSUE 5** — test gaps from the jury list (see Phase 3).
- **ISSUE 6** — docs: PITCH does not follow the 10-slide structure; DESIGN has no worked example per error type and no seeds column in the baseline table.
- No TODO/FIXME/HACK in code; `print` only in CLI entry points (check, run, verify, analyze, export, demo) — OK.

## Findings

| # | area | severity | finding | status |
|---|---|---|---|---|
| 1 | data & truth | high | For a **partial** `payment_allocation` (incl. I1) truth also accepted the set {payment doc, invoice doc, 2900 row, fx}. That set cannot reproduce the amount (expected AR credit − posted AR credit): the posted AR credit is not in it, and the 2900 row is at the payment-date rate and may hold other remainder. 849 of 1 200 such sets in a 300-seed sample were partial. The verifier only checked `0 < amount ≤ expected` for 2900 sets, so it did not catch it. | fixed: partial → only the AR-credit set, nothing allocated → the 2900 set; verifier requires 2900 sets to equal the full expected credit; policy/CONTRACT text; episodes re-exported, trajectories regenerated; regression tests `tests/test_hardening.py::AllocationEvidenceTest` (fail on the old verifier). Effect: naive_reconcile lost 2 TPs that only matched through the insufficient set (dev F1 0.286 → 0.273). |
| 2 | engineering | medium | Dockerfile never built/run; README promises `docker run`. | fixed: `.github/workflows/check.yml` builds the image and runs `docker run --rm --network none auditenv`, plus plain-Python check + verifier. Run 44503197633: both jobs success; in the container ALL CHECKS PASSED (196 tests then, 32 s) |
| 3 | engineering | low | `verify --seeds` output has no total. | fixed: prints `600/600 episodes valid; …` |
| 4 | reproducibility | low | Replay/transform invariance not tested for `difficulty: "hard"`. | fixed: `tests/test_hard.py::test_replay_and_transform_invariance` |
| 5 | tests | medium | Missing explicit tests: different seeds → different episodes; action after truncation; error messages without paths/truth; reward 0 on every non-terminal tool; train/dev cover all 4 types, I1, I2 and clean books; every truth evidence id reachable via the tools; exported manifests match the schema. | fixed: `tests/test_jury.py` (30 tests, grouped by jury criterion; leak and terminal-state tests checked to fail on an injected leak / removed episode_over guard) |
| 6 | docs | medium | PITCH not in the requested 10-slide order; DESIGN lacks per-type examples and seeds per baseline row. | fixed: PITCH rewritten into the 10-slide order; DESIGN: key decisions, worked example per error type with real ids and amounts, seeds column, edge-case table (with new `EdgeCaseDataTests`), seed sweep and reproducible stress test; README: why/how, errors, reward, results, commands, license; DEMO: numbers and test step |
| 7 | data & truth | high | On seed 7 (default and hard, four inspections), two invoice documents and only the copy booking scored TP=1, reward 0.992. They did not establish that the original was booked. | Fixed. Each evidence alternative binds both documents to a positive AR debit or revenue credit for each invoice. The copy booking determines the claimed amount. The same incomplete submission now scores FP=1, FN=1, reward −1. Tests cover missing, substituted, zero and reversed postings. |

## Round 2 jury-style review (2026-11-19)
Independent read-only review against SPEC §09/§10 (agent). An own checker re-derived truth from public tables on
1 000 episodes (incl. 400 with `AUDITENV_SECRET`): identical to truth.json. Leaks, reward, reproducibility: nothing found.
- **R2-1 (high, fixed):** the agent-facing evidence rule for `duplicate_invoice` (`policy.json`, generator) still
  said "both docs + the later copy's AR row"; since D1 the truth also needs a booking row of the original, so an agent
  following the text literally scored −1 (seed 2003). Text now says "one AR (or revenue) row of each invoice";
  all 40 exported episodes (policy.json only), trajectories and golden hashes regenerated;
  `tests/test_jury.PolicyTextTests` builds the evidence from the text and requires a TP.
- **R2-2 (medium, fixed):** `AUDITENV_SECRET=x auditenv.check` failed 46 fixture tests; the unit-test gate now runs
  with the public key and says so.
- **R2-3 (low-medium, fixed):** unknown action parameters were silently ignored although `schemas/action.schema.json`
  forbids them; now `bad_params`, step consumed; a `submit` with extra parameters still terminates (SPEC §04) as an
invalid submission, −1, logged (CONTRACT updated).
- **R2-4 (low, fixed):** in-process findings with non-string keys crashed grading (episode ended ungraded);
  `schema.validate_findings` now never raises — an invalid submission, −1, logged.
- **R2-5 (low, fixed):** `reset` coerced `seed=1.5/True/"7"` (the server used `int()`), accepted NaN/inf time limits,
  truthy `distractors` and float/bool `transform_seed`; all now `ValueError` / a server error.
  Tests: `tests/test_contract_strict.py`.
- **R2-6 (docs, fixed):** stale test count, `load.py` example path, README server command without `uv run`,
  `hidden.json` format and secret scope, train/hard re-export commands, `trajectories.jsonl` naming.
  Not changed: Docker base image not pinned by digest (no network to resolve a digest here); nightly CI Python
  patch versions unverified locally.

## Round 3 jury review

- On heavy seed 5, changing one truth currency to a different denomination left the verifier green. It now checks the currency against the base currency, as required for ledger misstatements. A separate allocation-evidence test was nested under the module entry point and escaped discovery. Both checks now run in the official suite.
- The jury map described the closed grader transport as a socket. The implementation uses JSON lines over subprocess stdin/stdout.
- The pitch formula abbreviated the chargeable inspections as steps. The seed-2003 demo takes 22 actions including submission and charges 21 inspections.

## Round 4 jury review

- Seed 7 produced an invoice whose quantity could be doubled without triggering a verifier error. Line totals previously checked only their sum against the document total.
- The same seed advertised 68 documents. Substituting 20 passed the verifier because it read the size bound from the manifest.
- An empty directory or an indexed export with an episode folder removed could pass the directory verifier. The reported denominator counted only discovered episodes.
- With a grader key set, the pitch's public demo command could change the company and reported score.

## Round 5 jury review

- In a clean seed-7 company, assigning a missing payment ID to both sides of an expense journal preserved the journal balance and passed verification. Neither posting had a corresponding payment document.
- Replacing the paired transformation with an identity function and an empty ID map passed the default and hard paired gates. The translated answer could reuse all original IDs.
- A clean company's truth file carrying another company's episode ID passed verification. Reusing an issue ID for two distinct findings on dirty books also passed.
- On seed 1 with a single payment allocation error, replacing the unapplied cash posting in the evidence with the original invoice debit passed verification. That debit establishes the invoice booking but provides no evidence of a payment allocation.

## Round 6 jury review

- Swapping the public IDs of two FX rows on clean seed 0 passed verification. Looking up evidence by ID could therefore return a different dated rate from the one used to check the books.
- Moving the revenue credit L02511 on clean seed 0 to 2099 left its receivables debit in the reporting period. The verifier still reported valid books.
- With one I2 scenario, seed 180 books the invoice on 2025-02-28 using the rate for 2025-02-27. The scenario descriptions assumed the booking date always produced a large enough discrepancy.

## Round 7 jury review

- On clean seed 7, moving the unidentified receipt BNK-775392 from unapplied cash to sales revenue preserved journal balance and passed verification. The verifier now checks the signed payment-date amount in account 2900 for payments without invoice references. The regression covers both a foreign-currency receipt and a foreign-currency refund reclassified to FX gain or loss.
- A private grading key on the recording machine changed the hard reconciliation F1 shown in the check tab. Both recording tabs and the slide reproduction command now select the public companies.

## Round 8 jury review

- On clean seed 0 the verifier accepted five ledger tampers that break the published `policy.ledger`. It accepted moving payment L02594's 2900 remainder (a payment with invoice refs) or the 7900 row L02583 to revenue 4000. It also accepted booking an expense to an unknown account 9999 or to 4000, and re-tagging an invoice journal with another customer's entity. The round-7 check of the 2900 amount covered only payments without invoice refs. The verifier now checks account usage in both the reconstructed and the published books: the chart of accounts, the accounts allowed per journal type, the entity on invoice and receivables rows, and the 2900 remainder at the payment-date rate for every payment. `tests/test_ledger_policy.py` covers the five tampers plus three variants.
- An independent red-team pass found more accepted tampers on generated seeds, each now rejected by `tests/test_verify_redteam.py`:
  - On clean seed 0, a remittance listing one invoice twice let a half-credited receivable pass with an invented FX gain on a base-currency payment.
  - On heavy seed 0, the unapplied cash of a payment with an allocation shortfall could be inflated by 50,000.00 against a matching FX loss. The first fix in this round had no upper bound.
  - A full credit note in default mode passed, although only the hard-mode policy publishes that rule.
  - A refund could debit receivables through a negative invoice reference.
  - A payment could settle an invoice issued after it.
  - An inverted invoice journal (Cr 1200 / Dr 4000) passed as an FX error.
  - Period-cutoff evidence accepted a payment's receivable credit in place of the booking row.
  - A policy file contradicting the manifest or the contract chart, exponents or rounding passed.
  - A payment row dated weeks after the payment passed, and so did an invoice booked before its issue date.

  Accepted and not changed: the verifier checks that each truth evidence set is sufficient, not that it is minimal. Malformed rates or currencies still raise an exception in `verify_episode`, which the directory verifier reports as a problem.

## Round 9 jury review

An independent read-only red-team pass covered contract, isolation, reward and reproducibility (not the verifier). It found nothing that leaks truth, beats the oracle or scores above 0 on clean books. It confirmed three defects, now fixed test-first:
- `reset(0, {"time_limit_s": 10**400})` passed the finite check, and then every `step` raised `OverflowError`; over the server the episode could never end. `reset` now rejects any value above the largest float (`tests/test_contract_strict.py`).
- Closing the server session (or EOF) logged only the open hidden episode as abandoned. The hidden episodes never reset were missing from the grader log, so a policy that stopped early shrank the denominator of any average over the log. They are now logged as abandoned with an empty answer (`tests/test_server.py::test_close_grades_every_unplayed_hidden_episode`).
- The experimental materiality-weighted reward weighted a false positive by its claimed amount, so findings claiming 0 were free: the oracle answer plus 25 zero-amount junk findings scored 1.0 on seeds 5 and 2003 (shared reward −0.613 and −0.429). A false positive now weighs at least the mean expected amount, so with every issue found the weighted F1 never exceeds the shared F1 (`tests/test_experimental.py::test_zero_amount_junk_is_not_free`). Naive reconciliation's experimental return on dev moved from −0.210, better than its shared −0.506, to −0.539. The shared reward is unchanged.

Checked and OK: identical episodes, observations and grader logs under `PYTHONHASHSEED` 0, 1, 12345 and 999 (now pinned by `tests/test_hashseed.py`); committed trajectories and exports regenerate byte for byte; transform keeps oracle and reconcile scores on 40 default and 40 hard seeds; type confusion (float, bool, string, negative amounts, lower-case currency) gives −1; id case, whitespace and duplicates follow the contract; eval mode returns 0.0 and `{}` on every terminal path; malformed server lines get bounded errors. The README Python snippets now run in the test suite (`tests/test_readme_snippets.py`), and a fresh clone passes the official check.

## Round 10 jury review

- `reset(1, {"errors": "x"})` or `{"errors": 5}` raised `AttributeError` instead of a bounded `ValueError`. `{"errors": 0}`, `false`, `[]` or `null` silently produced a clean company, and so did the same values for `interacting`. A non-dict `config` such as `[("errors", {})]` was coerced. `errors` and `interacting` must now be objects and `config` an object or null (`tests/test_contract_strict.py::test_reset_rejects_config_of_the_wrong_shape`). Golden hashes, committed episodes and trajectories are unchanged.
- The hard-mode ledger size and credit-note count were documented as fixed ranges. With `{"difficulty":"hard","n_invoices":10,"errors":{"duplicate_invoice":12},"distractors":false}`, seed 3 generates 1,413 ledger rows and seed 4 has one credit note. In `generator._build_expenses` the size target precedes injection, and `_build_reissues` selects from eligible unpaid invoices. README, CONTRACT and DESIGN now describe those bounds.
- README's random mix rule missed the case where only `interacting` is supplied. `generator.gen_config` selects explicit counts when either object is present. CONTRACT now describes the configured step limit and post-terminal counter (`env.AuditEnv.step`), and its four evidence rows render in one table. DESIGN specifies which payment row proves a partial allocation, matching `tests.test_hardening.AllocationEvidenceTest`. The lifecycle row in CHECKS cites the test that actually checks the step decrement.
- The README shell block connected independent Make targets with pipes. A pasted command launched the targets concurrently and hid earlier exit codes. The examples now run the check or preview the available commands with `make -n`.

## Round 11 jury review

The failure-analysis CLI indexed the configured episodes by seed. A two-entry
config using seed 1 for both default and hard mode reported one episode. This
can hide failures in paired experiments using the same company seed with
different configurations. The trajectory runner already retains both entries.

The committed-trajectory test checked row structure and budgets, but did not
compare a saved observation or terminal reward with replaying its recorded action.
Round 11 adds that comparison to the offline check.

A temporary copy of train_reconcile.jsonl with its final reward changed to
0.12345 passed the original structural test. Replay checks the recorded value.

DESIGN §10 overstated the advantage of a complete answer at 60 inspections.
Using auditenv.metrics.prf1 and terminal_reward, eight immediate matches out
of nine earn 0.882353, above the full answer's 0.880000. Seven out of eight
earn 0.866667. The updated worked example gives the crossover explicitly.

Replaying the saved actions exposed an artifact defect. Reconcile enriches invoice
dictionaries when it opens their documents. The runner retained the original
observation objects, so serialization after the episode retroactively added line
items to some earlier invoice-list results. The environment returns those list
results without line items. The comparison must include every observation field.

## Round 12

A reversed seed interval made the verifier print `0/0 episodes valid` and exit
successfully. The shared range parser now rejects reversed intervals, including
an invalid interval mixed into a valid list. The command regression exercises
run, analyze, fuzz, attack and verify.

A failed reset installed the requested configuration before the generator
validated its error counts. On an existing evaluation episode, the next step
then used the rejected budget and mode. The regression takes an inspection,
attempts the reset, continues inspecting and submits in the original episode.

The paired check originally passed both a clean and a dirty episode when the
test transform replaced every invoice due date with its issue date. It now
compares the complete public rows after translating the expected ID fields.

## Round 13

The official comparison covered the ten dev companies and twenty hard companies.
The public default cohort in configs/eval_example.json was missing from both the
console and the metrics JSON. A regression ran the reporting entry point and
failed on the missing split. The check now scores every default baseline on the
same twenty companies and includes all six diagnostics in both outputs.

The episode list loader coerced true, 1.9 and "7" into integer seeds. It also
treated false, zero, an empty list and an empty string as default config, as
did the JSON-lines reset endpoint. Both paths now reject those malformed types.
Omitted and null configs still select defaults.

## Round 14

A deliberately failing unit test produced only the failure count in the official
command. The test name and assertion were discarded. A discovery exception also
left the caller's grader key unset. Both regressions now pass.

The paired check scored an oracle using the first allowed evidence set.
Dropping a second valid evidence set or adding a shorter invalid alternative
still passed. It now compares each issue's complete collection of evidence
sets after translating the record IDs. Reordering equivalent evidence passes.

## Round 15

The JSON-lines server answered a non-object request such as `[]` with
`AttributeError: 'list' object has no attribute 'get'`, which exposed an
internal exception name. It also accepted `NaN` and `Infinity`, which strict
JSON forbids. Non-object requests now get `request must be a JSON object`.
Malformed JSON, non-standard constants and over-deep nesting all get
`invalid json`, and the server keeps serving. A first version of the fix took
parsing out of the generic handler, and a 200,000-deep array then crashed the
server with RecursionError. The regression covers that case too.
In-process probes found no defect. Observations are deep copies. Oversized
ints, NaN, bool and float action values, malformed cursors and a wrong
episode_id all return bounded errors or a valid grade.

## Round 16

A submission with two false positives, one claiming 0 and one claiming
`10**400`, ended the episode with reward 0 and no grader-log line. The
experimental reward's false-positive floor was a float, and adding a 401-digit
claim to it raised `OverflowError` after the step had already set
`terminated`. The step reported a generic "malformed action". In train mode
any answer scoring below 0 could take that 0 instead, and in eval mode it
removed a hidden episode from the log. The floor is now an exact `Fraction`.
The submission is graded (2 FP, reward −1) and logged in both modes.

The JSON-lines server abandoned the open episode before it validated the new
reset config. A typo such as `"mode": "evl"` returned an error, but the open
episode had already been ended and logged with −1. In process, a rejected
reset leaves the episode untouched. The server now abandons the open episode
only after the new one has been generated.

The exported `public/` files for agents had no task text. The duplicate
definition and the hard-mode re-typing rule are stated only in the task text,
which the environment sends in the first observation. In 5 of the 20 public hard
episodes the duplicate copy is re-typed (`IMPLEMENTATION SERVICES - PO/6638`
against `Implementation services (PO-6638)`), so an agent working from the files
alone could not apply the rule. Each export now includes `public/task.txt`, and
`load_episode` reads it back, so the round trip equals `generate()` in full.

Three checks verified less than they claimed. Only the hard export had a
byte-for-byte re-export test. Dev and train were compared through the loader,
which reads a fixed set of files and columns, so a copy of `truth.json` placed in
`public/` or an extra ledger column marking the injected rows still passed
every test and `verify --dir`. All three splits are now byte-compared with a
fresh export. The trajectory replay checks the environment's answers, not which
policy produced the actions, so swapping two trajectory files passed. The
README's byte-for-byte claim is now a test. The unit-test gate printed PASS
for zero discovered tests and now fails.

## Round 17

- SPEC §04. Replacing an exported public/task.txt with an empty string or whitespace left verify --dir reporting 1/1 valid. The verifier now requires nonblank instructions. The directory regression exercises both cases.
- SPEC §03. Removing the JPY exponent from the public seed-0 manifest or replacing 0 with JSON false previously passed verify_episode. The verifier now checks coverage of ledger, invoice, payment and FX currencies and requires integer exponents. The regression pins the public generation key so the same company runs inside the keyed official check.

## Export verifier follow-up

On the dev export (seed 2003), removing the scenario, blanking the issue ID or repeating an evidence ID still allowed verification to pass. Changing the seed or generation config in the split index also passed. The verifier now reports the affected field for each of these five independent corruptions. A valid control episode still passes. Run `uv run python -m unittest tests.test_verify_dir`.

The hard export previously constructed 133 book indexes across 20 episodes because evidence alternatives rebuilt the same post-injection index. Verification now uses two per episode, one for each ledger state. The regression checks the constructor count during on-disk verification.


## Independent audit (Chingiz, 20 November)

Reproduced on origin/main b799231 before each fix; every regression failed first and passes after.

- Verifier, truth labels. A base-currency invoice booked 500 too high, declared as `fx_error`, verified; so did
  a foreign invoice booked at an amount no published rate produces. An `fx_error` is now accepted only for a
  foreign amount that some published rate of the pair produces. Scenario labels were never checked: swapping
  I1/I2, labelling both interacting pairs `single` or a single error `I1` all verified. Labels now have to
  match the books (`tests/test_verify_semantics.py`).
- Verifier, unapplied cash. With a one-minor-unit allocation shortfall, the whole reference could sit in 2900,
  balanced by an invented 7900 loss, while truth declared a misstatement of 1. The 2900 rule accepted anything
  up to the whole short reference; it now requires exactly the unallocated part of the reference at the
  payment-date rate.
- Verifier, hard mode. A full credit note on an invoice with no replacement wrote off revenue and verified with
  unchanged truth. A cancelled invoice now needs its own replacement with the same entity, currency and line items, booked in the period after the credit note (an unbooked copy dated outside the period no longer counts).
- Verifier, public records. `amount_minor` 783500.75 on a payment and its ref, and payment timestamps without an
  offset (read in the host time zone), verified. Payment and ref amounts must be integers and every ledger,
  payment and invoice timestamp needs an offset.
- Server. A policy that closed its pipes with a request in flight crashed the server with `BrokenPipeError`
  before it graded the rest: 1 of 5 hidden episodes reached the grader log, so killing the pipe skipped hard
  episodes. The server now grades every open and unplayed episode as abandoned on a broken pipe too
  (`tests/test_server_robust.py`). One invalid config in the hidden list crashed the server at close with an
  empty grader log; the list is now validated at start (exit 2, the episode named). A reset without a seed
  returned `KeyError: 'seed'` and now gets the contract error `seed must be an int`.
- Server, missing grader key. `auditenv.server --episodes` without `AUDITENV_SECRET` served silently and a
  policy recovered seed 734211 from `episode_id` in 3.8 s. The server now warns on stderr; `--public` marks the
  deliberately public smoke run and demo (`tests/test_server_secret.py`).
- Verifier and server, reporting. A naive invoice or payment timestamp, or a string amount, made `verify_episode`
  raise `TypeError` instead of naming the problem; it now returns the structure problem. A missing, malformed or
  mistyped hidden list ended the server in a traceback; it now exits 2 with one line.
- Measured, not fixed (generator change; listed in DESIGN §10): one page of `payments` flags the I1 payment with
  precision 0.68 and recall 1.0; in hard mode a lookalike pair whose earlier invoice is paid is a duplicate with
  precision 0.995.

## Audit defects from PR #39 and their review (21 November)

Reproduced on `main` at `f270e4d` with `night/archive/audit-f270e4d.py`; every regression below failed on the
code before its fix (checked by running the new tests on the previous commit) and passes after it.

- Export. A failed `export_split` (13 FX issues on seed 3) wrote seeds 1–2 next to the old `index.json`, so a
  valid split failed `verify --dir`. Episodes are now generated in memory, written to a working directory and
  swapped in by renames that are undone on failure; non-episode files stay (`tests/test_export.py`). The review
  of that change found that a working directory beside the split needed a writable parent (main did not) and
  failed with `EXDEV` on a mounted destination (reproduced on a disk image); it now lives inside an existing
  destination, and an interrupted rollback names where the previous files are.
- Verifier, unused FX rate. `not-a-rate` on an unused rate verified. Every published rate must be a plain
  ASCII decimal above 0 and below 10^9: the review found that `1.2_9169`, ` 1.29169`, `129169e-5`, `+1.29169`
  and full-width digits passed on used and unused rates, and `1e30` on a used rate crashed the conversion.
- Verifier, out-of-period payment. An unbooked future payment skipped every reference check, so an unknown
  invoice and refs above the amount verified. `Books.ref_problems` now checks every payment document
  (`tests/test_payment_refs.py`); booking, cash, AR and 2900 checks stay in-period.
- Verifier, manifest. Without `schema_version` the episode verified. The manifest is now checked against
  `schemas/manifest.schema.json`; the review found that extra fields (a `seed` field would leak the grader's
  seed), float or extra counts, bad dates, time zones and currency codes passed or crashed `Books`.
  `generator_version`, listed in CONTRACT §2, is now required by the schema too.
- Verifier, diagnostics. `not-a-date` in a ledger timestamp raised `ValueError`; it is reported with the row
  id (fixed in `3a2f013`, regression in `tests/test_verify_records.py`). A ref without a string `invoice_id`
  raised `KeyError` and blank `row_id` / payment `doc_id` values verified; both are now reported.
- Measured, not fixed: the total settled on one invoice across payments is not bounded (DESIGN §10).

## Jury check definitions (genesis-exe.com/fintech-checks.html, 21 November)

The organisers published how the jury checks every team (adapter, blocks 1–4, exact matcher conventions). Each item
below failed on `main` at `87b1b4c` against a test that replays the definitions, and passes now.

- Matcher. 13 of the 36 Block 3 / M01–M12 cases failed: the tolerance `max(1, expected // 1000)` matched 10001 for
  10000 (row 8, M07); greedy first fit lost a TP that a maximum matching keeps (M10, M11 in reverse truth order);
  ids were stripped and the currency upper-cased (M06); an evidence id absent from the data still matched (M04); the
  reward was rounded to 6 places, 0.313333 for 47/150 (rows 5, 12, 13); an unknown type string, a negative amount or
  a lowercase currency made the whole submission invalid instead of one false positive (rule 8).
- Verifier. After the jury's consistent id renaming the truth's `affected_ids` are no longer sorted, and a correct
  transformed copy failed with "truth mismatch"; they are now compared as a set (`tests/test_judge_paired.py`).
- Data. A clean episode held an invoice paid in two parts in 93 % and a refund in 74 % of seeds 0–199, so D02/D03 could
  miss on a hidden seed; `ensure_distractors` guarantees both (300/300). A missing vs partial allocation (D09/D10)
  could not be requested; `allocation` selects it (40/40 each).
- Env. A loaded episode with an invalid published tolerance was rejected only after the env had switched to it.
- Adapter review (a jury-style harness written independently): with `AUDITENV_SECRET` unset in the generating
  process, a policy recovered the seed from `episode_id` in 3.2 s and scored 1.0; `generate_episode` now warns and the
  README requires the key. A fixture with only the listed files (no task.txt, provenance.json or fx_id column) could
  not be graded; it can now.

## Round 18 (21 November, evening)

Base `night/2026-11-21-r18` at `266a495` (main after PRs #44–#45). `auditenv.check` passed (523 tests, all gates).
Three read-only jury-style passes (docs claims, data ambiguity, §09/§10 engineering) plus the workers' red-team and
evidence tasks (night/TASKS.md, night/LOG.md).

- Engineering (§10, 5 × 0/1/2): scored 2 on every criterion; nothing in the §10 blocking clause (no leak through the
  adapter in closed mode, no grader write path, synthetic data, core runs; Docker job green in CI run 44925790975).
  Gap fixed: 10 of the 20 episode ids in `trajectories.jsonl` (hard train, seeds 1100–1109) were not under
  `episodes/`; README now gives the export command that reproduces them (checked: all 20 ids covered).
- Docs, ~150 claims checked against code and fresh runs; 10 wrong, all fixed. Behaviour: README and CONTRACT said
  `episode_over` costs a step — `AuditEnv.step` returns before counting it (submit, then three actions: remaining
  steps stay at 97). README said jury_run used `judge_adapter.generate_episode`; it uses the public generator. README's
  list of invalid submissions omitted an unknown key and another episode's `episode_id`. Numbers: reward mutants 15 →
  22 (README, CHECKS, PITCH), jury block tests 69 → 70, verify_semantics 10 → 12, verify_redteam 10 → 11, README
  snippets 2 → 3, DESIGN limitations 11 → 14, fuzz actions 20 312 → 20 319, hard random > 0 on 50 → 47 clean episodes;
  DESIGN §10 omitted the strongest remaining payment_allocation cue (2900 amount repeated in ≥ 4 ledger rows, 0.964).
- Closed reset stderr (codex1, T21): a closed `reset` without `episode_dir` and without `AUDITENV_SECRET` printed the
  grader key file path to stderr, which a policy sharing the process can read. Now only `generate_episode` warns;
  regression `JudgeContractTest.test_closed_reset_keeps_key_path_off_stderr` failed before the fix.
- Paired (codex1, T20): an independent transform (all surrogate ids renamed, dates shifted one 400-year cycle so every
  fx_id changes, four tables shuffled) on seeds 0–49 default and hard: 100/100 pairs same closed and oracle reward,
  `verify --dir` 50/50 each. No defect.
- Data ambiguity (case §10: "contradictory or unsolvable data do not count as difficulty"): an independent checker
  that reads only task.txt, policy.json and the public tables and applies the written definitions literally (no
  verifier, policy or truth code) reproduced the truth exactly — type, affected ids, amount — in all 44 000 episodes
  (seeds 20000–20999 × 44 configs: default, hard, heavy, D01–D20 in both difficulties). The 0.4 % of the default
  duplicate cue that misses (18 of 4 920) are same-customer invoices with equal totals but different line items:
  not duplicates under the written definition. One unstated rule found in a baseline, not in the data: `reconcile`
  pairs duplicates only within 3 days; it never changes a result. DESIGN §10 now says so.
- Published check page, re-read line by line (lead subagent): 92 numbered checks (C01–C20, Block 3 rows 1–20,
  M01–M12, D01–D20, P01–P20) plus the interface clauses (function names and keywords, observation/list/error key
  sets, `score_episode` keys, step accounting, closed reward 0 and `info` `{}`) — the code meets all 92. Independent
  harnesses: limits as full closed episodes, the tie rule vs brute force on 3000 random graphs (0 mismatches), the
  jury transform done directly on the CSV/JSONL files with colliding renames (40/40 pairs equal). One test gap: D05
  (currency/period boundary in a clean episode) was not asserted; `test_clean_scenarios_hold_the_legitimate_lookalikes`
  now requires a foreign-currency document and a record whose own-offset and company-timezone dates straddle the
  period edge (holds on 40/40 seeds 900–939). Two readings left as designed, no published check exercises them: a
  closed-mode invalid submit answers `{"accepted": true}` (graded −1 grader-side, as documented), and an unknown key
  in a finding is a structural error although the page lists only wrong type, missing field and limit.
- Loader and server hardening (codex1, T45/T46): 123 corrupted-export cases and 93 hostile wire requests; fixed path
  echoes, silent acceptance of symlinks/NUL/empty/header-only files, duplicate JSON keys, nonfinite numbers, blank
  lines without a response and a train-mode hidden list exposing scores (`tests/test_load_redteam.py`,
  `tests/test_server_redteam.py`). Lead review of that change: the stricter loader rejected a row_id equal to a
  doc_id, which the published paired definitions allow ("different id spaces are handled separately") — a jury copy
  renamed per space would have failed closed reset; loaded episodes now need uniqueness per id space only. The
  server again answers any unexpected exception with a bounded `internal error` instead of exiting.
- Multi-cue cheater (codex1, T47): rules over position, id patterns, timestamps, amount digits and wording, fit on
  seeds 0–499 and scored on 5000–5499 through the adapter: F1 0.163 (default) / 0.153 (hard) vs reconcile 1.000 /
  0.840. Its strongest cues (I1 payment is the last-evening payment; cutoff bookings at the period start) are the
  ones DESIGN §10 already lists.
- Matcher differential (lead subagent, T23): a reference grader written from the published page (before reading
  `matcher.py`) agreed with `matcher.grade` on 60 000 random submissions from 400 episodes (default, hard, D01–D20;
  tie-rule clones in 5 234 cases; tolerance 0/1/5; all 12 invalid classes) and with `score_episode` on 6 000 more,
  0 disagreements; five deliberately broken reference variants were each caught (91–2 779 disagreements), so the
  harness can see a difference. Documented choices the page leaves open: `10000.0` is not an integer amount; an
  unknown key and a wrong `episode_id` invalidate the submission; `explanation` is optional but must be a string.
- D03 generated a refund before its overpayment in 10 of 8,000 scenario episodes. Preserving the original receipt date in the opt-in distractor generator resolved all ten. The repeated sweep passed all 8,000 episodes across both difficulties.
- The on-disk verifier rejected all 4,173 accounting and truth mutations on 60 episodes and accepted all 120 controls. The sweep only treated an FX edit as an error when it changed a rounded conversion used in the books.

## Round 19

- At the starting revision `098d923`, all 560 tests and all jury gates passed. The default fuzz sweep passed 3,000 episodes, and the reward search found zero violations in 11,000 mutations. These checks missed two defects in ordinary use.
- On clean default seed 0, the generator combined two receipts and moved the first receipt to August 14. A refund against its credit had already been posted on August 10. Round 18 had protected only the opt-in distractor scenario. Testing the running credit available to each customer in the payment currency also exposed the problem on hard seed 16.
- Hidden stdio episode queues still selected public episode generation when `AUDITENV_SECRET` was absent. The standalone jury adapter already selected a private key in that case. The server regression on the starting revision explicitly asserted the obsolete public behavior.
- Task F: Fixed ordinary refund chronology in `_build_payments` by preventing merged receipts from moving past subsequent customer refunds. Regression test `test_customer_credit_covers_each_refund` in `tests/test_generator.py` checks both default seed 0 and hard seed 16. Sweeps across 1,000 default and 1,000 hard seeds confirmed zero negative customer credits. Updated exact counts across 100 seeds in `tests/test_ledger_accounts.py`, `tests/test_ledger_timestamps.py`, and `tests/test_payment_entities.py`. Re-exported episodes and matched 80/80 golden records and 7 published trajectories.
- Task K1 & K2: Extracted `grader_key()` and `_key_file()` into `auditenv/grader_key.py`. Updated `auditenv/server.py` to key hidden episode queues by default using `grader_key()` for startup validation, serving, and abandonment when `AUDITENV_SECRET` is unset. Explicit public runs (`--public`) retain the public generator. Updated `tests/test_server_secret.py` to assert unrecoverable default and recoverable `--public` behavior. Fixed `auditenv/jury_run.py` subprocess pipe cleanup to close `proc.stdout`. Verified all 25 server tests and 27 judge contract tests.
- Acceptance checks: `auditenv.check` passed all 561 unit tests and all gates in 50.8 s. Fuzz sweep over 3,000 episodes passed with 0 problems. Automated attack search evaluated 11,000 mutations across 20 seeds with 0 violations. Shortcut miner confirmed documented baseline cues. Documentation tables verified in sync.

## Round 20

- Start `a85fc66`: `auditenv.check` passed 561 tests and all gates in 50.8 s. Workers re-ran every sweep on unseen
  seeds (fuzz 10000–12999 default and hard, config sweeps 60000–68999, verify 2000–2999, stress 8000–9299, jury_run
  seed bases 20000–23000, D01–D20 through `judge_adapter` on 400 closed runs, the suite under three hash seeds,
  three timezones, two locales, `-O`, `-X dev -W error::ResourceWarning` and module by module): 0 problems.
- Defect (data, ordinary use): the in-period posting lag (30 % of invoices booked 1–3 days after issue) was drawn
  independently of the payment date, so a receipt could credit 1200 for an invoice before the invoice was booked —
  a negative receivable in time order on clean books (575 rows in 520 of 3,000 clean D01–D05 episodes; e.g. D01
  default seed 30010, `RCPT0548981` settles `2608-742998` 21 h before its booking). Found by
  `night/r20/chronology.py`, an independent checker that reads only the public tables, task and policy (12,600
  episodes: seeds 30000–30299 × default, hard and D01–D20 in both difficulties). Fix: such an invoice is posted at its
  issue instant (`generator._post_before_payment`, rows moved in place without new random draws: 65 of 80 golden
  hashes and the demo company unchanged). Regression `test_cash_is_applied_after_the_invoice_is_posted` failed in 29
  subtests before. After the fix the checker finds nothing unexplained; the 32 remaining hits are the injected
  prior-period `period_cutoff` invoice itself, paid in the period before its late booking (that late booking is the
  error).
- Jury-machine adapter run (`night/r20/adapter_reality.py`, 20/20): fresh, read-only and missing `HOME`, 8 processes
  racing to create `grader.key` (20 rounds, one key, no partial file), relative / non-ASCII / symlinked /
  trailing-slash `episode_dir`, a leak scan of every observation, two `JudgeEnv` interleaved. No defect.
- Docs: slide 7 and DESIGN §9 still quoted the hard-split failure analysis of 20 November (22 false positives,
  duplicate recall 3/8, 43.2 actions); `auditenv.analyze --config configs/eval_hard.json` gives 20, 2/8 and 43.
  `sync_docs` covers tables, not numbers in prose.
- Slide-7 chart: `docs/baselines.svg` still showed returns from before rounds 18–19 (reconcile hard 0.288 vs 0.293,
  naive dev −0.506 vs −0.480). Regenerated; `scripts/sync_docs.py --check` (run in CI) now renders the chart from the
  same metrics and reports a stale one (`test_stale_chart_is_drift`).
- Docs claims audit (codex2, Y1–Y3): all 36 eligible README commands exit 0 on a fresh clone; ~20 wrong or stale
  statements fixed after re-verification — hard F1 0.752 → 0.755, jury mean actions 21.4 → 21.3, the seed-2003
  worked example (ledger ids from an older generator), sensitivity rows, seed-sweep and naive-analysis counts, miner
  precisions, refund remittance and posting (Dr 2900 / Cr 1000) in CONTRACT, `ensure_distractors` described as a
  guarantee (seed 25 with 10 invoices gets no refund), the per-process key fallback, the time-limit wording, and
  "cannot be gamed" / "still learnable" replaced by what was measured.
- Policy text vs data (codex1, X2, `night/r20/policy_text.py`): every rule sentence of task.txt and policy.json
  checked on 8,400 episodes (seeds 31000–31199 × 42 configs), 33,079,641 checks, 0 unexpected failures. One reading
  note, left as is: the payment rule describes correct postings ("remainder … Cr 2900"); in a misallocated journal
  the shortfall sits on 2900, which is exactly the documented `payment_allocation` definition.
- CHECKS.md semantics (rb, Z3): 23 of 25 sampled rows fully asserted by the cited test, 2 enforced by the cited
  command. Hand-driven server session (rb, Z4) matched CONTRACT key for key; the framing errors and `close` (no
  response line) are now documented in CONTRACT §4.
- End: `env -u AUDITENV_SECRET uv run python -m auditenv.check` 563 tests, all gates, 50.7 s; sync_docs no drift;
  golden 80/80.

## Round 21

- Start `2f7b31e`: `auditenv.check` passed 563 tests and all gates in 50.9 s (peak RSS 203 MB). Workers re-ran every
  sweep on unseen seeds (fuzz 13000–15999 default and hard, config sweeps 69000–77999, verify 3000–5999, stress
  10000–11299, chronology 37000–39299 and 42000–42299, policy text 38000–38199 and 42000–42199, jury_run seed bases
  24000–27000, D01–D20 through `judge_adapter` on seeds 43000–43004, the suite under two more hash seed/timezone
  pairs, golden, mutants, miner, exports, demo): 0 problems.
- Independent text-only auditor (codex1, `night/r21/text_auditor.py`, written from task.txt + policy.json only, no
  look at policies/inject/verify/matcher): F1 1.000 with 0 missed or extra findings on 8,400 episodes (seeds
  40000–40099 and 45000–45099 × default, hard and D01–D20 in both difficulties, scored by `score_episode`). Every
  truth issue is derivable from the stated rules, and nothing the rules flag is missing from truth.
- Independent balance re-derivation (codex1, `night/r21/ledger_identity.py`, 12,600 episodes): every journal and
  the trial balance sum to 0, every 7900 row equals the documented FX difference. Running balances found two
  artefacts of the published per-document rules in clean books, and nothing else (`--classify`: 1,335 clean
  violations = 920 refund FX + 415 rounding, 0 other): a full foreign refund debits 2900 at the refund-date rate
  after the receipt credited it at the receipt-date rate (e.g. D01 seed 41006, E0342, −500,336 KZT minor; up to
  7.3 % of the refund in hard mode), and separately rounded cash applications can leave an invoice's AR a few minor
  units off. Decision: documented (DESIGN §10, README limitations), not changed 13 h before the freeze — a 7900
  realised-FX row would change the posting rule, policy text, every export and the golden hashes; no truth record
  depends on these balances, and the document-currency credit is exactly 0.
- Extreme configs (codex1, `night/r21/extreme_configs.py`): 300 accepted configs (n_invoices 10 with 12 issues of one
  type, interacting only, the full allocation × ensure_distractors × distractors × difficulty × transform_seed
  product, n_invoices 100) verify with exactly the requested count, reconcile F1 1.0; more than 12 issues →
  `ValueError: at most 12 issues per episode`. rb reproduced it.
- Jury copy robustness (codex2, `night/r21/jury_copy.py`): shuffled CSV columns, CRLF, UTF-8 BOM, no final newline,
  pretty/compact JSON, reordered JSONL keys and all combined, on 10 exported episodes — all accepted by closed reset,
  scores equal to the original.
- Timing under load (codex2): low QoS + six parallel hard fuzz sweeps, one random_explorer episode took 54.05 s (of
  60 s); three repeats at two seed bases peaked at 0.165 s, the outlier did not recur.
- Docs defect (codex2 README first read, Y3): the closed-server quick start
  `AUDITENV_SECRET="${GRADER_KEY:?...}"` aborted in bash without `GRADER_KEY`, although the server keys hidden
  episodes by default since round 19; replaced by the plain command. Ten further README clarifications (network
  needs, `AUDITENV_SECRET` unset for published numbers, shortest review path, `JuryPolicy` location, tuple shapes,
  period_cutoff wording, opt-in jury keys, per-difficulty foreign-document count, timing, chart input); codex2
  re-ran every touched command on a fresh clone (Y4): all exit 0 except Docker (not installed).

## Round 22

- Start `774570d`: `auditenv.check` passed 563 tests and all gates in 50.6 s.
- Data defects fixed (clean books, jury Block 2 D01–D05 — every such episode has a split payment and a refund):
  1. *Refund FX.* A foreign refund debited 2900 at the refund-date rate after its receipt credited it at the
     receipt-date rate, so the customer's unapplied cash ended below zero in base currency (round 21's balance
     re-derivation: 920 rows on 300 clean seeds, up to 7.3 % of the refund). Now the refund debits 2900 at the rate of
     the receipt it returns (the latest earlier booked payment with the same ledger `entity_id`, currency and
     remainder equal to the refund) and the cash difference goes to 7900 (realised FX).
  2. *Settlement rounding.* Each cash application was converted and rounded on its own, so a foreign invoice paid in
     parts kept ±1 minor unit in 1200 (54/300 default and 60/300 hard D02 episodes). The ref that completes an invoice
     now credits `convert(total) − Σ convert(earlier refs)`; the difference goes to 7900. The allocation injector never
     picks such a last part, so truth amounts and evidence rules are as published.
  3. *Merged overpayments.* codex2's public-data audit of rule 1 (20,007 refunds, seeds 0–999 × 12 configs, 0
     ambiguous) found 28 refunds in default/hard (none in D01–D05) whose receipt carried two merged overpayments, so
     the rule fell back to the refund-date rate. The merge now keeps one overpayment per receipt: 0 fallbacks.
  Rules in CONTRACT §2 and `policy.json` `ledger.payment`; `verify.py` and `policies/reconcile.py` re-derive them
  independently (the old generator fails the new verifier on 142–266 of 600 episodes). The changes add no random
  draw, so every other record is unchanged: compared with the round-21 generator on 660 episodes, invoices,
  payments, FX rates and non-payment ledger rows are identical; 23 episodes differ in truth (the injector skipping a
  split's last part, the un-merged overpayments). Regressions:
  `tests.test_generator.GeneratorTest.test_refund_clears_the_unapplied_cash_it_returns` and
  `...test_fully_paid_invoice_closes_its_receivable`, each failing before its fix. Measured numbers: only naive
  reconcile moved (dev F1 0.286 → 0.288, hard 0.186 → 0.185); demo, worked examples, reconcile, oracle unchanged.
- Independent checkers (written from the published texts only): clean-room D01–D20 matrix (codex1,
  `night/r22/d_matrix.py`, 8,000 episodes, every "what must differ" requirement holds, 0 failures); clean-room paired
  transform (codex2, `night/r22/paired_cleanroom.py`, D01–D20 × 20 episodes, combined shuffle + rename, 0 score
  differences, no ids inside free text); `ledger_identity --classify` after the fixes: refund (a) 0, rounding (b) 0.
- Evidence sweeps on unseen seeds (workers): verify 6000–7999, fuzz 16000–17999 default and hard, config sweeps
  78000–83999, stress 12000–12299, policy text 56000–56199, chronology 56000–56299, text auditor 54000–54099, jury_run
  28000–31000, re-export diff, golden, mutants, miner, attack, jury modules ×3: 0 problems.
- Re-checks on the final generator (FIX1–3, wording `f713586`): `ledger_identity --classify` 41000–41299 and
  57000–57299 → 0 clean violations of any class; text auditor (updated: a per-ref expected credit gives a 1-minor-unit
  FP on a completing part, D01 hard seed 58001) 58000–58099 → F1 1.000, 0 discrepancies on 4,200 episodes; policy
  text 59000–59199 → 0 unexpected failures (24,500 completing remittances); chronology 59000–59299 → 0 unexplained in
  clean configs; codex2's FIX2 review → 124,905 completing refs, 0 posting mismatches (wording made explicit: strictly
  earlier timestamps; same-instant final parts keep the per-ref rule, 3 base-currency cases); clean-room paired
  60000–60009 → 400/400 pairs equal; D-matrix (updated to the final rules) 50000–50199 and 61000–61199 → 0 failures on
  16,000 episodes; verify 8000–9999 6000/6000; fuzz 18000–18999 default and hard, configs 84000–86999, stress
  13000–13299, `fuzz --configs 20000` (8,037 hard, max 59 steps, as PITCH says); scenarios through `judge_adapter`,
  extreme configs, jury copies, jury_run 32000/33000; re-export diff 0, golden 80/80, mutants 22/22, attack 0,
  sensitivity table equal to DESIGN; demo equal to DEMO.md. All green.

## Round 23

- Start `8699d51`: `auditenv.check` passed 565 tests and all gates in 55.7 s; no doc drift.
- New independent checkers, each written only from the published texts (CASE_UPDATES, README, CONTRACT, policy.json):
  clean-room C01–C20 with the policy in a separate sandboxed process (codex1, `night/r23/c_matrix.py`: 20/20 rows
  pass on 10 fixtures), clean-room matcher differential (codex1, `night/r23/matcher_diff.py`: 110,000 submissions,
  disagreements only on a finding without `explanation`, see decisions) and a Block 2 rebuild of the books before the
  error from `grader/provenance.json` (codex2, `night/r23/provenance_rebuild.py`).
- Data defect (evidence sufficiency, jury Block 2 condition "по нему можно проверить вывод"): with nothing allocated,
  the `payment_allocation` set held the payment and invoice documents, the 2900 row and the rate. A reader of the set
  alone could not see that no AR credit went to the invoice: a merged receipt also credits other invoices and the
  cash row was not in the set (provenance rebuild: evidence 4,002/4,200; D09 44/100, D11 71–79/100, default mix
  79–85/100). Fix `e23958c`: the set holds every row of the payment's journal (cash, 2900, other AR credits, 7900;
  at most 7 ids measured, journals have at most 5 rows); `verify._sufficient` requires the closed journal (the old
  exports fail it: 4/10 dev, 4/10 train, 5/20 hard); `reconcile` cites it; policy.json, CONTRACT §3 and DESIGN §7
  state it. Regression `tests.test_generator.GeneratorTest.test_nothing_allocated_evidence_closes_the_payment_journal`
  (67 failing subtests before). Only naive reconcile moved (it cites the 2900 row alone: dev F1 0.288 → 0.261).
- Contract text mismatches (red-team, both low severity, fixed `5700626`): a closed-mode submit with an invalid
  structure (31 findings, non-object) was answered `{"accepted": true}` while the grader logged −1; CASE_UPDATES allows
  only `{"accepted": true}` or a bounded structure error, so eval now returns `invalid_findings` (structure only, never
  truth). A copy without `task.txt` (the case's file list has none) gave `task: ""` (C02); the loader now falls back
  to the published task text (hard suffix when the policy publishes credit notes) and `verify --dir` still requires
  the file. Regressions in `tests/test_judge_contract.py` and `tests/test_load_redteam.py`.
- Data red-team (10,000 episodes, seeds 73000–73249 × D01–D20 × both difficulties, own text-only auditor: 10,000/10,000
  equal to truth): two wording ambiguities fixed in the published texts — the duplicate amount is the AR debit of the
  later-issued copy "by issued_at, whatever the posting order" (the copy is booked before the original's lagged
  posting in 17 % of duplicate episodes; bookings were not moved, a fixed offset would be a new shortcut cue), and the
  hard task text names spacing (re-typing turns `REF-1` into `REF 1`).
- Docs claims audit: nine stale prose numbers after round 22 fixed (`f7fae58`: naive FPs, seed-sweep counts, miner
  precisions, CHECKS counts, a test path).
- After the fixes: `c_matrix.py` extended with both boundary cases of `5700626` (C02 on a copy without `task.txt`;
  closed submit with 31 findings / non-object findings → bounded `invalid_findings`, grader return −1), seeds
  76000–76004: 20/20 rows pass 10/10. Final `auditenv.check` exit 0 (568 tests, 56.3 s), `sync_docs --check` no drift.
- Decisions: `explanation` stays optional (CONTRACT §5; no published row tests its absence, and requiring it could
  turn an organiser policy's correct finding into a structural −1); `limit: null` stays `bad_params`; the I2 cutoff
  amount includes the wrong-rate part that fx_error also measures (documented scenario).

## Round 24

- Start `3e27abc` (code identical to `main` 1e30a64): `auditenv.check` exit 0, 568 tests and all gates, 56.0 s;
  `sync_docs --check` no drift.
- No valuable improvement found. Every jury block already has an independent clean-room checker with 0 problems on
  unseen seeds (r20–r23); the only open ideas (H1, E5) stay deferred — freeze day, generator risk. No change.

## Round 25

- Start `da8b250` (code identical to round 24 and `main` 83bdd68): `auditenv.check` exit 0, all gates, 56.6 s;
  `sync_docs --check` no drift.
- No valuable improvement found (same inputs and reasoning as round 24). No change.
