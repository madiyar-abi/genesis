# REVIEW.md — jury-style review (2026-11-19)

Scope: every module in `auditenv/` (env, generator, inject, matcher, metrics, schema, calculator,
experimental, verify, transform, server, client, run, export, load, analyze, check, demo, policies/),
tests/, configs/, Dockerfile, docs. Base: branch `hinabaina/hard-mode` (includes hard mode).
Method: reading the code plus a probe script that plays the jury's checks against the live env
(bad actions, leaks, limits, truncation, time limit, eval mode, determinism, evidence reachability
through the tools) and targeted data checks.

Status legend: **OK** = checked, no problem; **ISSUE n** = see "Findings" below.

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
