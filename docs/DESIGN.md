# Design note — auditenv

An RL environment for training AI financial auditors: reproducible synthetic companies,
read-only investigation tools, hidden misstatements with recorded causes, and a published
matcher + terminal reward. Interfaces: [`CONTRACT.md`](CONTRACT.md). Numbers below come from
`uv run python -m auditenv.check` and `uv run python -m auditenv.analyze` (see "Results").

## 0. Key decisions and why

| decision | why |
|---|---|
| Generate a consistent hidden history first, book it correctly, then inject errors as recorded changes | the truth is a real, causal ledger misstatement that an independent verifier can recompute; nothing is a "suspicious row" |
| Integer minor units, decimal-string rates, `Decimal` + ROUND_HALF_UP | no float drift; every amount is exactly reproducible from the records |
| Five narrow read-only tools, 50-row pages, 100 steps, 60 s | the agent must investigate; no shell/SQL/files means no way around the tools; step cost rewards efficiency |
| Truth and provenance live only in the grader (eval mode, out-of-process server, HMAC ids + grader secret) | the jury can run closed evaluations; a policy cannot read or regenerate the answer |
| One published matcher with explicit tolerance and tie rule, evidence required | the matcher checks fields and evidence and ignores the explanation; guessed ids, flag-everything and 11 000 tested reward mutations (`auditenv.attack`) did not beat the honest answer |
| Standard library only, one check command, Docker | the jury runs everything offline with one command |
| Opt-in hard level instead of changing the default | default numbers stay comparable; hard mode shows the environment can be made harder than a rule script |

## 1. Episode lifecycle

```
generate(seed, config)
  1. company      base currency, 2-3 foreign currencies, fixed UTC offset, one calendar month
  2. history      customers, invoices (prior 35 days .. next 7 days), payments, expenses, daily FX
  3. ledger       correct double-entry postings for the period (base currency)
  4. inject       errors change documents/journals; before/after journals recorded (provenance)
  5. render       ids drawn from an episode-specific style, rows sorted by time, internal keys -> ids
  6. truth        issue_id, type, affected_ids, expected amount, acceptable evidence sets
  7. transform    optional: relabel every id + permute rows (paired generalisation checks)
AuditEnv.reset -> first observation (task, manifest, policy, tools, budget)
AuditEnv.step  -> read-only tools ... submit -> matcher -> terminal reward (train) / grader log (eval)
```

Same `(seed, config, GENERATOR_VERSION)` and key → byte-identical episode (the config is normalised first,
so equivalent configs give the same company). `episode_id` is an HMAC of them; with the grader-only
key `AUDITENV_SECRET` set, the key also enters the generator RNG, so the seed can neither be
brute-forced from the id nor the episode regenerated from the open-source code. Episode size: the default history is padded to 230–420 ledger rows
before injection (236–434 after it on seeds 0–199; hard target 900–1 400); strict exports allow 200–2 000 rows and
20–200 documents (enforced by `n_invoices` ∈ [10, 100]); 0–12 issues.

## 2. Company model and correct bookkeeping

- **Money** is integer minor units with the currency exponent (`JPY` 0, others 2); FX rates are
  decimal strings (6 significant digits, foreign → base, daily random walk). Conversion:
  `round_half_up(amount / 10^exp_src × rate × 10^exp_base)`.
- **Time**: every timestamp is ISO-8601 with an offset. Invoices carry the customer's offset,
  payments the bank's offset, the ledger the company offset. The period and the FX rate date are
  decided by the date **in the company timezone** — so documents near midnight have a "written"
  date that differs from their accounting date.
- **Postings** (also in `policy.json`): invoice `Dr 1200 / Cr 4000` at the issue-date rate;
  payment `Dr 1000` at the payment-date rate, `Cr 1200` per remittance line at that invoice's
  rate (the line that completes a split credits the rest of the booked amount, so the receivable closes), remainder to `2900 Unapplied cash`, FX difference to `7900`; refunds `Dr 2900` at the rate of the
  receipt they return `/ Cr 1000` at the refund-date rate, the difference to `7900` (realised FX);
  expenses `Dr 6xxx / Cr 1000`. Every journal balances.

## 3. Errors (closed `truth.json`)

| type | causal change | expected amount (base currency) | evidence (any one full set) |
|---|---|---|---|
| `duplicate_invoice` | a second invoice document with identical entity, currency and line items, issued strictly later, booked again | AR debit of the later copy | both invoice docs + one positive booking row for each invoice (AR debit or revenue credit) |
| `payment_allocation` | remittance says the payment covers an invoice, the ledger credits only part (or none) of it to AR; the rest lands in 2900 | expected AR credit − posted AR credit | payment doc + invoice doc + payment’s AR credit for that invoice (when the credit is missing: every row of the payment’s journal) + invoice-date FX rate if foreign |
| `fx_error` | invoice or payment converted at the rate of a wrong date (the document's own local/UTC date, or 1, 2, 3, 5, 7 days later or 1, 2, 3, 5 days earlier); difference ≥ 10 minor units | abs(posted − correct) | doc + AR/revenue row (invoice) or cash row (payment) + the correct-date FX rate |
| `period_cutoff` | invoice issued in the next period (backdated to the period end) or in the previous period, booked in this period | AR debit posted | invoice doc + AR (or revenue) row |

**Interacting scenarios** (each yields two truth issues computed after both changes):
- `I1` — foreign-currency payment late on the last day: partially allocated **and** its cash
  converted at another day's rate: the date shown in the bank's timezone, usually the next day
  (two or three days later, or the day before, when the next day's rate would not change the amount).
- `I2` — next-period foreign invoice backdated into the period **and** converted using the rate
  of the booking date or an earlier fallback day (1, 2, or 4 days earlier when the booking-date conversion
  differs from the correct invoice value by less than 10 base-currency minor units; period_cutoff + fx_error on the same invoice).

In `I2` the two amounts measure two different rule breaks on one booking, so they are not a split of one total:
`period_cutoff` is the whole AR debit posted for an invoice that belongs to the next period (it should not be in
these books at all), and `fx_error` is how far that posted amount is from the policy's rate for the invoice date
(the misvaluation an auditor must also report). A policy that finds only one of them gets partial credit.

Every type is independently configurable (`errors: {type: count}`), single-error injectors never touch an
already-affected document (I1/I2 put two issues on one document on purpose), and amounts are the real ledger misstatement — not a "suspicious row".

### Worked examples (real dev episodes; reproduce with `generate(seed, config)` from `configs/dev.json`)

| type | episode (seed) | what the records show | truth amount |
|---|---|---|---|
| `duplicate_invoice` | `ep_14eca11ac929` (2003), base USD, tz +05:00 | `INV-441644` (issued 09-26 08:49) and `INV-588950` (09-26 16:00, company time): same customer `CUST52061`, GBP 6 787.00, identical line items; original AR debit `R4132`, later copy AR debit `R4153` = 6 787.00 × 1.22534 | 831 638 (the later copy's AR debit) |
| `payment_allocation` | `ep_14eca11ac929` (2003) | `PAY-779598` remits USD 8 371.00 for `INV-336399`; the ledger credits nothing to its AR: its whole journal is `R4164` (Dr 1000) and `R4163` (Cr 2900), both in the evidence set. Base-currency payment, so expected AR credit = the remitted amount | 837 100 |
| `fx_error` | `ep_7f8a101fa36a` (2005), base KZT | `F0926539` is USD 14 007.00 issued 09-12; AR row `R944` = 698 834 443, correct = 14 007.00 × 494.388 (rate `2026-09-12:USD:KZT`) = 692 489 272 | 6 345 171 |
| `period_cutoff` | `ep_d671645ebdd1` (2002), period 2026-03 | `INV-142472` is issued 2026-04-04 (next period) but its AR row `GL-000311` is dated 03-29 | 638 435 000 (the AR debit posted) |
| `I1` | `ep_d671645ebdd1` (2002), base KZT | `PAY-827484` (EUR 9 610.00, 03-31 23:38 bank time) pays `INV-589644` in full; AR credit `GL-000333` = 218 992 539 instead of 9 610.00 × 509.208 = 489 348 888 → allocation 270 356 349; the cash row `GL-000332` = 486 321 738 instead of 9 610.00 × 504.218 (03-31) = 484 553 498 → fx 1 768 240 | two issues |
| `I2` | `ep_14eca11ac929` (2003) | `INV-959754` (GBP 8 974.00) is issued 2026-10-01, booked 09-30 (`R4224`) → cutoff 1 110 820; and converted at the 09-30 rate 1.23782: correct 8 974.00 × 1.24037 = 1 113 108 → fx 2 288 | two issues |

## 4. Clean cases and distractors

Clean companies (`errors: {}` with no interacting pairs) have empty truth. With distractors on (default) the
generator draws these legitimate look-alikes; which ones appear varies by company (clean default, seeds 0–199:
a split payment in 186/200, a refund in 148/200; `ensure_distractors` adds the two when it can):

| distractor | why it looks wrong | why it is correct |
|---|---|---|
| split payments | one invoice, two payments | each remittance line fully credited |
| partial payments | invoice stays open | remittance amount fully credited |
| overpayment + refund | money in 2900 | excess over the invoice, later refunded |
| unidentified receipts | whole payment in 2900 | `invoice_refs: null` — nothing to allocate |
| multi-invoice payments | one payment, several AR credits | one remittance line per invoice |
| weekly retainers | same entity, same amount, 4×/month | line items name different service weeks |
| midnight documents | written date ≠ accounting date | period/rate use the company timezone |
| next-period invoices in the document set | issued after the period end | correctly *not* booked |
| posting lag | ledger timestamp 1–3 days after the invoice | still inside the period and never after a payment applied to it; issue-date rate used |

## 5. Environment contract and isolation

- `reset(seed, config) → (observation, info)`; `step(action) → (observation, reward, terminated,
  truncated, info)`; all JSON-compatible. Five tools; pages ≤ 50 rows with stable cursors;
  invoice listings omit line items (use `get_document`). Every action, including errors
  (`unknown_action`, `bad_params`, `unknown_table`, `not_found`, `calc_error`), costs one step.
- 100 steps including the submit (`max_steps`); the 100th non-submit step, or any action that arrives after
  60 s wall time (`time_limit_s`; checked on arrival, so a late submit is not executed), ends the episode
  with `truncated=true` and an empty answer is graded. A step after the end returns
  `episode_over` and changes nothing.
- Observations contain only the requested records (deep copies) and bounded error messages that
  never echo long input. Truth, provenance, seed and grading stay in the grader:
  `mode="eval"` returns reward 0.0 and empty info; `auditenv.server` runs the environment and
  grader in a separate process, takes the hidden episode list itself and writes results only
  to its grader log. The calculator is an AST whitelist over `Decimal` (`+ - * / ( )`, decimals).

## 6. Matcher and reward (`auditenv/matcher.py`, published)

- **Validation** (`schema.py`), structure only: ≤ 30 findings, ≤ 10 evidence ids counted before repeats are
  dropped, explanation ≤ 1000 code points, the five required keys with the right JSON types (amount a JSON
  integer, not bool), matching episode_id, no unknown keys. Invalid → episode ends, reward −1, error in the
  grader log. A wrong value of the right type (unknown type string, negative amount, `"usd"`) is a valid
  finding that does not match.
- **Normalisation**: none on strings — ids and currency compare exactly (case and whitespace count);
  affected/evidence ids are sets.
- **TP edge** iff type, canonical affected_ids, currency equal, `|claimed − expected| ≤ tolerance_minor`
  (published in the policy, 0 in every generated episode) and the evidence ids are all public ids of the
  episode and contain one complete acceptable set.
- **One-to-one, maximum matching**: the matcher takes a maximum-cardinality matching of findings (repeats
  included) to issues, so a finding that fits two issues cannot steal the only issue another finding fits.
  Ties: issue ids sorted by code point, lexicographically smallest (issue_id, finding index) pairs. Repeats
  and everything else are FP; unmatched truth is FN. Submission order never changes the counts.
- `P = TP/(TP+FP)`, `R = TP/(TP+FN)` (0 on a zero denominator), `F1 = 2TP/(2TP+FP+FN)`, F1 = 1
  when truth and findings are both empty. Terminal reward
  `clip(2·F1 − 1 − 0.002·inspection_steps, −1, 1)`; steps before the submit count. Exploration
  reward is 0. The reward depends only on fields and evidence, never on the explanation text.
- `tests/test_reward_attacks.py` proves on real episodes: correct answer > silence on dirty books;
  silence > false accusations on clean books; duplicates never help; flag-everything < 0;
  0.002/step breaks ties between equal-F1 answers (it can also reverse a small F1 gap, §10); guessed ids, unsupported evidence, wrong currency,
  amounts off by one minor unit are FP; resubmission, malformed input and timeouts behave as specified.
  `tests/test_judge_reward.py` reproduces the organisers' matcher checks (Block 3 rows 1–20, M01–M12).

**Sensitivity of the design choices** (`uv run python scripts/sensitivity.py`, 2 s): every baseline episode is
played once, then re-graded offline with the real matcher and the step cost / amount tolerance overridden
(the default re-grade reproduces every env reward exactly). Mean return:

| policy · split | cost 0.001 | **0.002** | 0.005 | **τ 0** | τ 1 | τ 100 |
|---|---|---|---|---|---|---|
| oracle · dev | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| reconcile · dev | 0.978 | 0.956 | 0.891 | 0.956 | 0.956 | 0.956 |
| naive_reconcile · dev | −0.516 | −0.529 | −0.569 | −0.529 | −0.529 | −0.529 |
| random · dev | −0.803 | −0.807 | −0.817 | −0.807 | −0.807 | −0.807 |
| flag_all · dev | −1.000 | −1.000 | −1.000 | −1.000 | −1.000 | −1.000 |
| reconcile_hard · hard | 0.958 | 0.916 | 0.790 | 0.916 | 0.916 | 0.916 |
| reconcile · hard | 0.329 | 0.293 | 0.186 | 0.293 | 0.293 | 0.293 |
| naive_reconcile · hard | −0.704 | −0.725 | −0.786 | −0.725 | −0.725 | −0.725 |

The ranking (oracle > reconcile(_hard) > … > random > flag_all) is identical under all five settings on both
splits: the step cost only spreads the middle, and tolerance never changes a mean (the rule policies compute
exact amounts; naive's false positives stay false positives at τ = 100 minor units). The defaults are not tuned to a ranking.

## 7. Verification of data and truth (`auditenv/verify.py`)

Independent of the generator, from the public tables and closed files only:
1. structure — the manifest matches `schemas/manifest.schema.json` (required fields, types, patterns, dates, no
   extra fields), unique non-blank ids, manifest counts, base-currency one-sided integer ledger rows, integer
   payment and ref amounts with string invoice ids, timestamps with a UTC offset, every published FX rate (used
   or not) a plain positive decimal below 10^9, size limits; the policy agrees with the manifest and with the
   contract's chart of accounts, exponents and rounding. Remittance references are checked on every payment
   document, whatever its period: known, same-currency, not cancelled invoices issued before the payment,
   positive, unique and within the payment amount;
2. **before the errors** — revert the provenance changes; every journal balances and the books
   have zero discrepancies (each in-period invoice booked once at the right rate, every payment
   cash/AR/2900 line exact, no duplicates, nothing out of period). In both books every account is
   allowed for its journal type (invoice 1200/4000, payment 1000/1200/2900/7900, expense Dr 6xxx /
   Cr 1000), entities match the invoices, payment rows carry the payment's instant, no invoice is
   booked before its issue. Credit notes are accepted only where the hard-mode policy publishes the rule, and
   each cancelled invoice needs its own replacement with the same entity, currency and line items, issued at
   or after the credit note and booked in the period;
3. **after the errors** — journals still balance and the discrepancies recomputed from the records
   are exactly the truth (type, ids, amount): nothing undeclared, nothing unsupported. A wrong booked
   amount counts as an `fx_error` only if it is foreign and some published rate of the pair produces it;
   scenario labels must match the books (I1 = allocation + FX error on one payment, I2 = cutoff + FX
   error on one invoice, everything else `single`);
4. **evidence** — every id exists in the public tables, each set covers the affected records, and
   the declared amount is recomputed from the records of each set alone (sufficiency).

Decision for `payment_allocation` with **nothing allocated** (the AR credit row was removed): the set is the
payment document, the invoice document, **every ledger row of the payment** (cash, 2900 unapplied cash, any AR
credits to other invoices of a merged receipt, 7900) and the invoice-date FX rate for foreign currency. The amount
is the referenced amount × the invoice-date rate, reproduced from the two documents and the rate; the rows show
that the payment's journal balances without an AR credit for the invoice, so the absence is read from the set
itself (at most 8 ids: payment journals have at most 5 rows). Until round 23 the set held only the 2900 row and
the absence had to be proven from the full ledger; a clean-room rebuild from provenance
(a development checker) showed that a reader of the set alone cannot tell a merged receipt's other
allocations or the cash amount from it (198 of 4,200 episodes, D09/D11 and the default mix).

A jury-style review (separate agent, before submission) found and we fixed: seed recovery from a
plain-hash `episode_id` (now HMAC + grader key in the RNG); a crash/overrun on non-string `table`
(now a bounded error, 100-step cap holds — plus a 20 319-action fuzz test); a telltale timezone on the
I1 payment, a timestamp-mismatch shortcut for cutoff, a telltale hour on duplicate copies (removed,
measured with the shortcut's precision: 1.00 → undefined / 0.09 / 0.02); evidence sets that did not
contain the FX rate or the invoice document; skipping hidden episodes in server mode (now graded as
abandoned, including the ones never reset before close or EOF); config spelling changing the company;
a rare injector crash; < 20 documents in tiny configs.

The verifier found one real generator bug during development (two retainer invoices could get
the same ISO-week label → an undeclared duplicate in clean books); it is fixed and covered by tests.

## 8. Reproducibility and generalisation

- Replay: same seed + config + version + key + actions → identical records, transitions, rewards
  (hash-compared in the check). `reset` rebuilds all episode state.
- `transform_seed` relabels every id (rows, documents, invoices, payments, entities) and permutes
  row order; truth and provenance are remapped. The oracle answer under the new ids keeps the
  same reward and, on dirty episodes, the old answer scores 0 TP. Train (1000–1009) and dev (2000–2009) seeds are
  public; evaluation should use secret large seeds, new parameter mixes and transforms.

## 9. Results

`uv run python -m auditenv.check` (dev split; P/R/F1 micro-averaged; return, steps, time = means):

| policy | seeds | P | R | F1 | return | steps | time s | exp. return* |
|---|---|---|---|---|---|---|---|---|
| random explorer (seeded) | 2000–2009 | 0.000 | 0.000 | 0.000 | −0.807 | 31.0 | 0.006 | −0.807 |
| naive reconciliation | 2000–2009 | 0.163 | 0.667 | 0.261 | −0.529 | 17.5 | 0.007 | −0.560 |
| reconciliation (policy-aware) | 2000–2009 | 1.000 | 1.000 | 1.000 | 0.956 | 22.8 | 0.007 | 0.956 |
| flag-everything attack | 2000–2009 | 0.000 | 0.000 | 0.000 | −1.000 | 3.8 | 0.004 | −1.000 |
| oracle (grader-side) | 2000–2009 | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 0.004 | 1.000 |

Dev split = `configs/dev.json` (10 episodes: 2 clean, 2 interacting, 6 mixed; 30 truth issues).
P/R/F1 micro-averaged over episodes; return, steps (incl. submit), time = means per episode. Timing is a snapshot of the measurement host. CI compares deterministic cells and checks that times are finite and nonnegative.
\*Experimental materiality-weighted reward (`auditenv/experimental.py`): FN/TP weighted by the
expected amount, FP by the claimed amount but at least the mean expected amount (a zero claim is no free
accusation); reported separately, the shared reward is unchanged.
Other gates in the same run: all unit tests pass (the check prints the count); verifier 200/200 episodes valid (50 seeds × 4 configs in check; 600/600 with
`auditenv.verify --seeds 0-199` over 200 seeds × 3 configs); 20/20 paired checks on default and 20/20 on hard episodes; the two-episode out-of-process run shows the policy no reward or truth.

Reconcile stress test (`uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299`): 1 200
episodes (300 seeds × random mix / clean / 12 issues / 12 issues with 100 invoices): **0 imperfect
episodes**, max 33 steps, no truncation — every truth issue can be found from the records within the budget.

**Seed sweep** (`uv run python -m auditenv.fuzz --seeds 0-999`; generate → verifier → oracle, random
explorer and flag-everything through the env, 3 configs per seed): 3 000 episodes (1 986 dirty, 1 014
clean) — 0 exceptions, 0 verifier problems, oracle > 0.9 on every dirty and 1.0 on every clean episode (the
sweep's gate); the random explorer scores > 0 on 247 episodes, all clean books where it submitted nothing (the correct answer), never on
dirty books; flag-everything is negative on 3 000/3 000. Hard mode, seeds 0–199: 600 episodes, 0 problems,
random > 0 only on 47 clean episodes, flag-everything negative on 600/600. CI runs both sweeps.

**Measured failure analysis** (`uv run python -m auditenv.analyze --policy <p> --config configs/dev.json`):

| | duplicate | allocation | fx | cutoff | I1 | I2 | FP |
|---|---|---|---|---|---|---|---|
| naive reconciliation, recall | 7/7 | 0/8 | 6/8 | 7/7 | 0/2 | 2/2 | 103 |
| reconciliation, recall | 7/7 | 8/8 | 8/8 | 7/7 | 2/2 | 2/2 | 0 |

Where the naive rules fail (103 FPs: 28 allocation, 30 duplicate, 27 fx, 18 cutoff; 22 of them
on the 2 clean companies):
- *allocation*: every 2900 credit is flagged → overpayments and refunds become false accusations;
  the truth amount is the AR shortfall, not the 2900 credit, and the evidence needs the invoice
  document (and, with nothing allocated, every row of the payment's journal) → allocation recall 0/8, I1 recall 0/2;
- *duplicate*: same entity + amount ignores line items → weekly retainers are flagged;
- *fx / cutoff*: the date written in the timestamp is used instead of the company-timezone date →
  midnight documents get the wrong rate or the wrong period.
The random explorer finds nothing (0 TP) and is punished on dirty books (−1) while scoring on
clean books only when it happens to submit no findings. Flag-everything scores −1 on every episode.

### Hard mode (`{"difficulty": "hard"}`, `configs/eval_hard.json`)

The default distribution is solved by a hand-written rule script, so we add an opt-in hard level.
It is additive: without the key the normalised config, the RNG stream and every default episode are
byte-identical (the committed `episodes/` still match the generator).

| change | effect on a shortcut | why it stays solvable |
|---|---|---|
| Up to three eligible invoices form legitimate **cancel-and-reissue** pairs: the unpaid original is reversed by a full credit note (`Dr 4000 / Cr 1200`, same invoice_id), the replacement carries equivalent line items that may be re-typed | looks exactly like a duplicate | the reversal rows are in the ledger; the rule is in `policy.ledger.credit_note` and the task text |
| each injected **duplicate has a 50% chance of being re-typed**: other line order, case and ref punctuation | exact line-item comparison misses them | same products, quantities and prices; duplicates are defined order/case/punctuation-insensitively (CONTRACT §3) |
| **larger ledger**: expense journals pad the pre-injection ledger to a target of 900–1 400 rows (default target 230–420) | more pages to read, higher step cost | full reading still fits in 100 steps |

The verifier treats credit-noted invoices as non-duplicates, compares lines with the same normalised key
and checks that every credit note is in the period and after its booking.

`uv run python -m auditenv.check`, hard section (`configs/eval_hard.json`: 20 episodes, seeds 9100–9119,
5 clean, 5 interacting, 10 mixed — the `eval_example` mix):

| policy | P | R | F1 | return | steps | exp. return* |
|---|---|---|---|---|---|---|
| random explorer (seeded) | 0.000 | 0.000 | 0.000 | −0.806 | 33.1 | −0.806 |
| naive reconciliation | 0.101 | 0.609 | 0.173 | −0.725 | 33.1 | −0.789 |
| reconciliation (default rules) | 0.667 | 0.870 | 0.755 | 0.293 | 43.0 | 0.081 |
| reconciliation + hard rules (`reconcile_hard`) | 1.000 | 1.000 | 1.000 | 0.916 | 43.0 | 0.916 |
| flag-everything attack | 0.000 | 0.000 | 0.000 | −1.000 | 3.8 | −1.000 |
| oracle (grader-side) | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 1.000 |

Gates in the check: hard verifier 50/50 episodes valid; oracle 1.0; `reconcile_hard` F1 ≥ 0.95;
default `reconcile` F1 ≤ 0.8; flag-everything < 0. Failure analysis of the default rules
(`auditenv.analyze --policy reconcile --config configs/eval_hard.json`): duplicate recall 2/8 (re-typed
copies missed), all other types 100 %; 20 false positives, all `no_matching_issue` — the credit-note
reissues flagged as duplicates. `reconcile_hard` is the same script plus the two policy rules: it shows
the level is solvable from the records, not that a learning agent finds those rules.
Stress test of `reconcile_hard` (`auditenv.fuzz --stress reconcile_hard --seeds 0-299 --hard`, 1 200 hard
episodes): 0 imperfect, max 57 steps, no truncation.

**Timing** (historical snapshot, Round 11; not re-measured since). On an Apple-silicon Mac running Python 3.11.14, `uv run python scripts/bench.py` reported the median of three runs for each workload. Policy timings use the first company in each split.

| operation | workload | time |
|---|---|---|
| `generate()` default | 100 seeds | 0.266 s (2.66 ms / episode) |
| `generate()` hard | 100 seeds | 0.953 s (9.53 ms / episode) |
| `auditenv.verify` | 100 seeds × 3 configs (300 eps) | 1.783 s (5.94 ms / episode) |
| one full episode, any baseline | dev / hard | 2.88–4.64 ms / 7.50–10.56 ms |

The measured scripted policies finished both sampled companies within the 60 s episode limit.

**Step-budget margin** (same stress runs, 300 seeds per row, steps used of the 100-step budget):

| policy · mode | config | median | p95 | max |
|---|---|---|---|---|
| reconcile · default | random mix | 22 | 26 | 28 |
| reconcile · default | 12 issues, 100 invoices | 29 | 31 | 33 |
| reconcile_hard · hard | random mix | 44 | 50 | 53 |
| reconcile_hard · hard | 12 issues, 100 invoices | 50 | 56 | 57 |

The heaviest hard episode leaves 43 % of the budget: a script needs ≤ 57 steps, a learning agent has room
to explore.

### Edge cases (all tested)

| case | behaviour | test |
|---|---|---|
| clean books, empty answer | F1 = 1, reward = 1 − 0.002·steps | `test_jury.RewardTests`, `test_metrics` |
| clean books, any finding | F1 = 0, reward < 0 | `test_reward_attacks` |
| invalid submission (structure, limits, wrong episode_id) | episode ends, reward −1, bounded error message | `test_env`, `test_jury.ContractTests` |
| the 100th action is not a submit / an action (even a submit) arrives after 60 s | `truncated`, empty answer graded | `test_env`, `test_jury` |
| the 100th action is the submit | it is a submit (`terminated`) | `test_env.TerminationTests.test_submit_on_last_step_is_submit` |
| action after the end, resubmission | `episode_over`, nothing changes, the first grade stays | `test_jury` |
| malformed actions (None, lists, nested dicts, huge strings, unicode digits in cursors) | bounded error, step consumed, never an exception | `test_fuzz` (20 319 episode actions) |
| cursor exactly at the end / past the end | empty page / `bad_params` | `test_jury` |
| JPY (exponent 0), refunds (negative payment), multi-invoice and split payments, overpayments, unidentified receipts | correct postings, verifier finds 0 discrepancies | `test_jury.EdgeCaseDataTests`, seed sweep |
| documents near midnight in other timezones | period and rate date decided in the company timezone | `test_jury.EdgeCaseDataTests`, naive baseline FPs |
| same finding twice | one TP + one FP | `test_matcher`, `test_jury` |

## 10. Honest limitations

- Synthetic and simplified: receivables only (no payables, tax, accruals), one functional
  currency ledger, foreign → base rates only, fixed UTC offsets (no DST). Not an audit opinion;
  the reward does not prove fitness for real audits.
- The generator is open and deterministic. The jury adapter and our server's hidden queue (`auditenv.server
  --episodes`) key hidden episodes by default: `AUDITENV_SECRET`, else a persistent random grader key file, else a
  per-process key if the file is unusable (`auditenv/grader_key.py`, `tests/test_grader_key.py`). Reproducing a
  hidden episode needs the same key (on another machine: the same secret or key file). `--public` opts the server
  queue into public generation; the public splits are regenerable from their seeds.
- Shortcut miner (`uv run python scripts/shortcut_miner.py [--hard]`, 1 000 seeds): single observable
  features that predict truth records with precision > 0.5 (16 flagged in default mode, 11 in hard mode).
  Fixed: re-typed descriptions marked hard-mode duplicate copies (1.000 → 0.454 on 1 000 seeds: invoices and
  re-issues are now keyed in by hand too). Left, measured: in default mode "same entity,
  currency and total exactly twice" finds duplicates (0.996) — it is the duplicate definition, but default mode
  has no near-miss decoys (hard mode has: 0.356); I1 payments are always on the last day, so a 2900/7900 row on
  the last day hints at fx_error (0.70) and a large 2900 amount at payment_allocation (0.75–0.77);
  a 2900 row whose amount occurs in four or more ledger rows points at payment_allocation too (0.949, 240 of
  253 rows; hard mode 0.835). Each hint names
  a record, not the claimed amount — scoring still needs the reconciliation.
- Cutoff of a next-period invoice is booked *before* its issue instant; a policy can learn that
  direction-of-lag cue, but it is exactly the audit rule (document date outside the period).
- The I1 payment is always on the last evening of the period (by the definition of the scenario);
  "last-evening payment" alone has precision 0.35. Narrowed to a foreign payment on the last company day after
  18:00 with one invoice ref equal to its amount, one page of `payments` flags it with precision 0.68 (random mix,
  1 000 seeds, default and hard; Round 17 probe) and recall 1.0. It names the payment, not the two amounts, which still need the
  reconciliation; changing it would change the default episodes, so it stays and is reported here.
- Hard mode re-issues (credit note + new invoice) are drawn only from unpaid invoices, while duplicates may copy a
  paid one. A lookalike pair whose earlier invoice is already paid is a duplicate with precision 0.995 (recall
  432/830, 1 000 hard seeds; Round 17 probe) without reading the ledger; the credit-note rows in the ledger separate all pairs.
- Expense journals carry no ids (the schema has no journal id); checks group them by timestamp.
- Settlement residues (fixed in Round 22). Converting and rounding every document on its own left two artefacts in
  clean books, found by an independent balance re-derivation (a development checker, clean
  D01–D05 config, seeds 41000–41299): a foreign refund debited 2900 at the refund-date rate, so the customer's
  unapplied cash ended below zero in base currency (920 rows, up to 7.3 % of the refund), and a foreign invoice paid
  in parts kept a minor unit in 1200 (415 rows; 18 % of D02 episodes). Now a refund debits 2900 at the rate of the
  receipt it returns and the part that completes an invoice credits the rest of its booked amount; the cash
  difference is realised FX (7900) — CONTRACT §2, `policy.json` `ledger.payment`; a merged receipt never carries two
  overpayments, so every refund finds its receipt (0 refund-date fallbacks on seeds 0–999, default and hard; codex2's
  public-data audit found 0 ambiguous receipts on 12 000 episodes). Two final parts of one invoice paid at the same
  instant keep the per-ref rule, so a foreign pair could still leave a minor unit (3 same-instant pairs, all in base
  currency, on 42 000 episodes; codex2's review found 0 posting mismatches on 124 905 completing refs). The allocation injector never
  picks such a last part, so "expected AR credit for the ref" stays the ref converted on its own. Regressions:
  `tests.test_generator.GeneratorTest.test_refund_clears_the_unapplied_cash_it_returns` and
  `...test_fully_paid_invoice_closes_its_receivable`.
- A wrong conversion is always the published rate of another date (the document's local or UTC date, nearby days,
  the bank's date); a rate value that appears on no date, or a wrong currency pair, is not modelled.
- The verifier does not bound the total settled on one invoice across payments: an extra future payment of 5×
  an invoice's total verifies (the generator did not over-settle in our sample: 0 of 9 385 invoices with remittance refs on seeds
  0–199, default and hard). The free-text rules in `policy.json` and `task.txt` are checked only where the books depend
  on them (base currency, timezone, period, chart of accounts, credit-note rule, non-blank task).
- Default duplicates are exact copies; hard mode re-types the text, but changed amounts or quantities
  (a "near-duplicate" that is really a different sale) are not modelled.
- The 60 s wall-clock limit can make a replay truncate under load. The scripted baselines completed
  the published dev and hard runs within the limit.
- With eight issues and no false positives, submitting seven matches immediately earns 0.867.
  A complete answer after 60 inspections earns 0.880. At nine issues the order reverses: eight
  immediate matches earn 0.882. With twelve issues, eleven immediate matches earn 0.913.
- A policy-aware rule script solves the default distribution (F1 1.0); the same script gets F1 0.755 in
  hard mode, and only after adding the two hard rules (`reconcile_hard`) is it perfect again. Whether an agent
  that must discover the rules within 100 tool calls can learn them was not measured;
  the baselines measure how much the distractors hurt shortcuts, not agent difficulty.
- The baseline `reconcile` pairs duplicate candidates only when they were issued within 3 days of each other, a
  window the task text does not state (the generator issues copies 0–3 days later). It never changes a result: an
  independent checker that applies only the written definitions, with no window, reproduced the truth exactly on
  44 000 episodes in Round 18 (seeds 20000–20999 × default, hard, heavy and the 20 jury scenarios in both difficulties).
- No model was trained; we make no claim about training improvements.
