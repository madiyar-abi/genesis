# Design note — auditenv

An RL environment for training AI financial auditors: reproducible synthetic companies,
read-only investigation tools, hidden misstatements with recorded causes, and a published
matcher + terminal reward. Interfaces: [`CONTRACT.md`](CONTRACT.md). Numbers below come from
`uv run python -m auditenv.check` and `uv run python -m auditenv.analyze` (see "Results").

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

Same `(seed, config, GENERATOR_VERSION)` → byte-identical episode (the config is normalised first,
so equivalent configs give the same company). `episode_id` is an HMAC of them; with the grader-only
key `AUDITENV_SECRET` set, the key also enters the generator RNG, so the seed can neither be
brute-forced from the id nor the episode regenerated from the open-source code. Episode size: about 236–435 ledger rows and 52–108 documents by default (measured over 300 seeds)
(≤ 2000), 20–200 documents (enforced by `n_invoices` ∈ [10, 100]), 0–12 issues.

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
  rate, remainder to `2900 Unapplied cash`, FX difference to `7900`; refunds `Dr 2900 / Cr 1000`;
  expenses `Dr 6xxx / Cr 1000`. Every journal balances.

## 3. Errors (closed `truth.json`)

| type | causal change | expected amount (base currency) | evidence (any one full set) |
|---|---|---|---|
| `duplicate_invoice` | a second invoice document with identical entity, currency and line items, issued strictly later, booked again | AR debit of the later copy | both invoice docs + the later copy's AR (or revenue) row |
| `payment_allocation` | remittance says the payment covers an invoice, the ledger credits only part (or none) of it to AR; the rest lands in 2900 | expected AR credit − posted AR credit | payment doc + invoice doc + 2900 row (or AR row) + invoice-date FX rate if foreign |
| `fx_error` | invoice or payment converted at the rate of a wrong date (the document's own local/UTC date, or ±1..7 days); difference ≥ 10 minor units | abs(posted − correct) | doc + AR/revenue row (invoice) or cash row (payment) + the correct-date FX rate |
| `period_cutoff` | invoice issued in the next period (backdated to the period end) or in the previous period, booked in this period | AR debit posted | invoice doc + AR (or revenue) row |

**Interacting scenarios** (each yields two truth issues computed after both changes):
- `I1` — foreign-currency payment late on the last day: partially allocated **and** its cash
  converted at the next day's rate (the date shown in the bank's timezone).
- `I2` — next-period foreign invoice backdated into the period **and** converted at the
  booking-date rate (period_cutoff + fx_error on the same invoice). The two amounts overlap on
  purpose: the cutoff amount is the whole posting (it must be reversed), the FX amount is the rate
  component (it would remain wrong if the invoice were simply re-dated into the next period). Both
  are reportable, each is matched by its own type, so an auditor who finds only one gets partial credit.

Every type is independently configurable (`errors: {type: count}`), injectors never touch an
already-affected document, and amounts are the real ledger misstatement — not a "suspicious row".

## 4. Clean cases and distractors

Clean companies (`errors: {}`) have empty truth. Every episode (unless `distractors: false`)
contains legitimate look-alikes:

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
| posting lag | ledger timestamp 1–3 days after the invoice | still inside the period; issue-date rate used |

## 5. Environment contract and isolation

- `reset(seed, config) → (observation, info)`; `step(action) → (observation, reward, terminated,
  truncated, info)`; all JSON-compatible. Five tools; pages ≤ 50 rows with stable cursors;
  invoice listings omit line items (use `get_document`). Every action, including errors
  (`unknown_action`, `bad_params`, `unknown_table`, `not_found`, `calc_error`), costs one step.
- 100 steps including the submit; the 100th non-submit step, or 60 s wall time, ends the episode
  with `truncated=true` and an empty answer is graded. A step after the end returns
  `episode_over` and changes nothing.
- Observations contain only the requested records (deep copies) and bounded error messages that
  never echo long input. Truth, provenance, seed and grading stay in the grader:
  `mode="eval"` returns reward 0.0 and empty info; `auditenv.server` runs the environment and
  grader in a separate process, takes the hidden episode list itself and writes results only
  to its grader log. The calculator is an AST whitelist over `Decimal` (`+ - * / ( )`, decimals).

## 6. Matcher and reward (`auditenv/matcher.py`, published)

- **Validation** (`schema.py`): ≤ 30 findings, ≤ 10 evidence ids, explanation ≤ 1000 chars,
  known type, integer non-negative amount, 3-letter upper-case currency, matching episode_id,
  no unknown keys. Invalid → episode ends, reward −1, error in the grader log.
- **Normalisation**: strip ids, dedupe and sort affected/evidence ids (ids are case-sensitive; the
  currency must already be 3 upper-case ASCII letters, otherwise the submission is invalid).
- **TP** iff type, canonical affected_ids, currency equal, `|claimed − expected| ≤ max(1,
  expected // 1000)` and the evidence ids contain one complete acceptable set.
- **One-to-one, greedy in submission order**: a finding takes the first unmatched truth issue
  it satisfies; repeats and everything else are FP; unmatched truth is FN. Because affected ids
  are canonical and an injector never reuses a document for the same type, a finding can satisfy
  at most one issue, so the order only decides which of two identical findings is the duplicate.
- `P = TP/(TP+FP)`, `R = TP/(TP+FN)` (0 on a zero denominator), `F1 = 2TP/(2TP+FP+FN)`, F1 = 1
  when truth and findings are both empty. Terminal reward
  `clip(2·F1 − 1 − 0.002·inspection_steps, −1, 1)`; steps before the submit count. Exploration
  reward is 0. The reward depends only on fields and evidence, never on the explanation text.
- `tests/test_reward_attacks.py` proves on real episodes: correct answer > silence on dirty books;
  silence > false accusations on clean books; duplicates never help; flag-everything < 0;
  0.002/step only separates equal answers; guessed ids, unsupported evidence, wrong currency,
  out-of-tolerance amounts are FP; resubmission, malformed input and timeouts behave as specified.

## 7. Verification of data and truth (`auditenv/verify.py`)

Independent of the generator, from the public tables and closed files only:
1. structure — unique ids, manifest counts, base-currency one-sided integer ledger rows, size limits;
2. **before the errors** — revert the provenance changes; every journal balances and the books
   have zero discrepancies (each in-period invoice booked once at the right rate, every payment
   cash/AR/2900 line exact, no duplicates, nothing out of period);
3. **after the errors** — journals still balance and the discrepancies recomputed from the records
   are exactly the truth (type, ids, amount): nothing undeclared, nothing unsupported;
4. **evidence** — every id exists in the public tables, each set covers the affected records, and
   the declared amount is recomputed from the records of each set alone (sufficiency).

A jury-style review (separate agent, before submission) found and we fixed: seed recovery from a
plain-hash `episode_id` (now HMAC + grader key in the RNG); a crash/overrun on non-string `table`
(now a bounded error, 100-step cap holds — plus a 3 000-action fuzz test); a telltale timezone on the
I1 payment, a timestamp-mismatch shortcut for cutoff, a telltale hour on duplicate copies (removed,
measured with the shortcut's precision: 1.00 → undefined / 0.09 / 0.02); evidence sets that did not
contain the FX rate or the invoice document; skipping hidden episodes in server mode (now graded as
abandoned); config spelling changing the company; a rare injector crash; < 20 documents in tiny configs.

The verifier found one real generator bug during development (two retainer invoices could get
the same ISO-week label → an undeclared duplicate in clean books); it is fixed and covered by tests.

## 8. Reproducibility and generalisation

- Replay: same seed + config + version + actions → identical records, transitions, rewards
  (hash-compared in the check). `reset` rebuilds all episode state.
- `transform_seed` relabels every id (rows, documents, invoices, payments, entities) and permutes
  row order (incl. the FX table; `fx_id` stays `date:currency:base` because it is derived data); truth and
  provenance are remapped. The check translates the *original* oracle answer through the id map and
  requires it to stay a full answer on the transformed episode. The oracle answer under the new ids keeps the
  same reward and the old answer scores 0 TP. Train (1000–1009) and dev (2000–2009) seeds are
  public; evaluation should use secret large seeds, new parameter mixes and transforms.

## 9. Results

`uv run python -m auditenv.check` (dev split; P/R/F1 micro-averaged; return, steps, time = means):

| policy | P | R | F1 | return | steps | time s | exp. return* |
|---|---|---|---|---|---|---|---|
| random explorer (seeded) | 0.000 | 0.000 | 0.000 | −0.807 | 31.0 | 0.004 | −0.807 |
| naive reconciliation | 0.177 | 0.733 | 0.286 | −0.488 | 17.2 | 0.004 | −0.207 |
| reconciliation (policy-aware) | 1.000 | 1.000 | 1.000 | 0.957 | 22.5 | 0.004 | 0.957 |
| flag-everything attack | 0.000 | 0.000 | 0.000 | −1.000 | 3.8 | 0.003 | −1.000 |
| oracle (grader-side) | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 0.003 | 1.000 |

Dev split = `configs/dev.json` (10 episodes: 2 clean, 2 interacting, 6 mixed; 30 truth issues).
P/R/F1 micro-averaged over episodes; return, steps (incl. submit), time = means per episode.
\*Experimental materiality-weighted reward (`auditenv/experimental.py`): FN/TP weighted by the
expected amount, FP by the claimed amount; reported separately, the shared reward is unchanged.
Other gates in the same run: 187 unit tests pass; verifier 200/200 episodes valid (600/600 with
`auditenv.verify --seeds 0-199`); 20/20 paired checks; out-of-process run leaks nothing.

Reconcile stress test: 1 200 episodes (300 seeds × default / clean / 12-issue / 12-issue with
100 invoices): **0 imperfect episodes**, max 32 steps, no truncation — every truth issue can be
found from the records within the budget.

**Measured failure analysis** (`uv run python -m auditenv.analyze --policy <p> --config configs/dev.json`):

| | duplicate | allocation | fx | cutoff | I1 | I2 | FP |
|---|---|---|---|---|---|---|---|
| naive reconciliation, recall | 7/7 | 2/8 | 6/8 | 7/7 | 0/2 | 2/2 | 102 |
| reconciliation, recall | 7/7 | 8/8 | 8/8 | 7/7 | 2/2 | 2/2 | 0 |

Where the naive rules fail (102 FPs: 27 allocation, 30 duplicate, 27 fx, 18 cutoff; 22 of them
on the 2 clean companies):
- *allocation*: every 2900 credit is flagged → overpayments and refunds become false accusations;
  the truth amount is the AR shortfall, not the 2900 credit, and the evidence needs the invoice
  document → allocation recall 2/8, I1 recall 0/2;
- *duplicate*: same entity + amount ignores line items → weekly retainers are flagged;
- *fx / cutoff*: the date written in the timestamp is used instead of the company-timezone date →
  midnight documents get the wrong rate or the wrong period.
The random explorer finds nothing (0 TP) and is punished on dirty books (−1) while scoring on
clean books only when it happens to submit no findings. Flag-everything scores −1 on every episode.

## 10. Honest limitations

- Synthetic and simplified: receivables only (no payables, tax, accruals), one functional
  currency ledger, foreign → base rates only, fixed UTC offsets (no DST). Not an audit opinion;
  the reward does not prove fitness for real audits.
- The generator is open and deterministic: hidden runs must set `AUDITENV_SECRET` in the grader
  process (otherwise, as for the public splits, anyone can regenerate an episode from its seed).
- Cutoff of a next-period invoice is booked *before* its issue instant; a policy can learn that
  direction-of-lag cue, but it is exactly the audit rule (document date outside the period).
- The I1 payment is always on the last evening of the period (by the definition of the scenario);
  "last-evening payment" alone has precision 0.35.
- Expense journals carry no ids (the schema has no journal id); checks group them by timestamp.
- Duplicates are exact copies; near-duplicates (changed description, rounded amounts) are not modelled.
- Wall-clock truncation (60 s) is the only non-deterministic transition; it never triggers for the
  baselines (≤ 0.01 s per episode).
- Step cost vs F1 granularity: an answer missing one of k issues at 0 steps scores 2·F1 − 1 =
  0.867 / 0.895 / 0.913 for k = 8 / 10 / 12, so the complete answer wins only if it takes fewer than
  66 / 52 / 43 inspection steps. The policy-aware baseline needs ≤ 32 steps, so in practice the
  complete answer wins; the step cost is deliberately small (SPEC: "only slightly separates equal answers").
- A policy-aware rule script solves the default distribution (F1 1.0). The difficulty is for a
  learning agent that must discover these rules from 100 tool calls, not for a hand-written solver;
  the naive-rules baseline measures how much the distractors and timezones hurt shortcuts.
- No model was trained; we make no claim about training improvements.
