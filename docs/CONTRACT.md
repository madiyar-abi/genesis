# CONTRACT — auditenv interfaces (source of truth for all code)

Package: `auditenv/` (Python 3.11, **stdlib only**, tests with `unittest`).
Run tests: `uv run python -m unittest discover -s tests -t .`
Single test module: `uv run python -m unittest tests.test_calculator`

Every module below is owned by the task in `night/TASKS.md` that lists it.
If you need something not described here, choose the simplest option and log it.

## 1. Money, currencies, FX
- Money = **int minor units**. Currency exponents (`auditenv/money.py: EXPONENT`):
  `USD 2, EUR 2, GBP 2, CHF 2, KZT 2, JPY 0`.
- FX rate = **decimal string**, `rate` = units of `target_currency` per 1 unit of
  `source_currency` (major units). Never float.
- Conversion: `to_minor = round_half_up(amount_minor * 10**-exp_src * rate * 10**exp_tgt)`
  using `decimal.Decimal`, `ROUND_HALF_UP`.
- Rate date = the transaction date **in the company timezone** (`manifest.timezone`).
- Ledger is kept in `base_currency` only: every ledger row has `currency == base_currency`.

## 2. Public tables (what the agent may read)
`manifest` (in the first observation):
`{schema_version, generator_version, episode_id, base_currency, period_start, period_end, timezone,
  counts: {ledger, invoices, payments, fx, documents}, rounding: "ROUND_HALF_UP",
  amount_exponents: {CUR: exp}}` — `period_start/end` are dates `YYYY-MM-DD`
(inclusive), `timezone` is a fixed offset like `+05:00`.

| table | id field | fields |
|---|---|---|
| `ledger` | `row_id` | row_id, timestamp, account, debit_minor, credit_minor, currency, entity_id, invoice_id, payment_id |
| `invoices` | `invoice_id` | doc_id, invoice_id, entity_id, issued_at, due_at, currency, total_minor, line_items |
| `payments` | `payment_id` | doc_id, payment_id, timestamp, currency, amount_minor, invoice_refs |
| `fx` | `fx_id` | fx_id, date, source_currency, target_currency, rate |

- Timestamps: ISO-8601 with offset, e.g. `2026-10-31T23:40:00-03:00`.
- Missing links are JSON `null` (CSV: empty cell), never guessed.
- `line_items`: `[{description, quantity:int, unit_price_minor:int, amount_minor:int}]`,
  `total_minor == sum(amount_minor)`.
- `invoice_refs`: `null` (no remittance info) or `[{invoice_id, amount_minor}]` in the
  payment currency, each ref positive; `sum(amount_minor) <= max(payment.amount_minor, 0)`. Negative
  `amount_minor` on a payment = refund, with `invoice_refs: null`.
- `fx_id` = `"{date}:{source}:{target}"`.
- Accounts: `1000` Cash, `1200` Accounts receivable, `2900` Unapplied cash,
  `4000` Revenue, `6100` Rent, `6200` Payroll, `6300` Software, `6400` Bank fees,
  `7900` FX gain/loss.

### Correct bookkeeping (the "policy"; violations of it are the errors)
- Invoice issued (only if its issue date in company tz is inside the period):
  `Dr 1200 / Cr 4000`, amount = `convert(total_minor, rate(issue date))`,
  rows carry invoice_id + entity_id and payment_id null. Both rows share one booking instant.
  An in-period invoice may be posted later in the period than its issue instant.
- Payment received (inside the period): `Dr 1000 convert(amount, rate(payment date))`;
  per ref `Cr 1200 convert(ref.amount, rate(invoice issue date))` with invoice_id — except the ref that completes
  the invoice (with the refs of payments with a strictly earlier timestamp, booked or not, it adds up to
  `total_minor`): it credits the rest, `convert(total_minor) − Σ convert(earlier refs)`, each at the invoice-date
  rate, so a fully paid invoice's receivable closes exactly (two final parts at the same instant keep the per-ref rule);
  remainder (amount − Σrefs, or all of it if refs are null) `Cr 2900` at the payment-date
  rate; any difference `7900`. A refund (negative amount) is `Dr 2900 / Cr 1000`: the 2900 debit is
  converted at the payment-date rate of the receipt it returns (the latest earlier booked payment in that currency
  whose ledger rows carry the refund's `entity_id` and whose `amount_minor − Σ invoice_refs` equals the refunded
  amount; the refund-date rate if there is none — the generator always books that receipt), the cash credit at the refund-date rate, any difference `7900` (realised FX).
  Every journal (rows sharing payment_id, or an invoice's rows with payment_id null) balances: Σdebit == Σcredit.
- Expenses: `Dr 6xxx / Cr 1000`, no invoice/payment ids.
- Hard mode only (`difficulty: "hard"`): a cancelled invoice is reversed in full by a credit note,
  `Dr 4000 / Cr 1200` with the same invoice_id, payment_id null, inside the period and after the
  booking; its replacement is a new invoice (new id, identical line items) booked normally. The
  invoice journal then has 4 rows and still balances. A credit-noted invoice is never a duplicate.
- A record belongs to the period iff its timestamp converted to company tz has a
  date in `[period_start, period_end]`.

## 3. Error types (closed files: `truth.json`)
Truth issue: `{issue_id, type, scenario, affected_ids, expected_amount_minor, currency, evidence_sets}`
(`scenario` = "single" | "I1" | "I2").
`expected_amount_minor` = the misstatement in the ledger, **base currency**, positive int.
`currency` = base currency. `affected_ids` canonical = sorted list of strings.
`evidence_sets` = list of acceptable sets (lists) of `doc_id` / `row_id` / `fx_id`.

| type | affected_ids | amount | evidence (any one full set) |
|---|---|---|---|
| `duplicate_invoice` | [original_invoice_id, duplicate_invoice_id] | ledger AR debit of the later-issued copy | both invoice doc_ids + the original's and later copy's AR (or revenue) row_ids |
| `payment_allocation` | [invoice_id, payment_id] | `convert(ref.amount, rate(inv date))` − AR credit actually posted | payment doc_id + invoice doc_id + the AR credit row_id of that invoice in the payment (if nothing was allocated to it: the 2900 row_id) + the invoice-date fx_id if foreign |
| `fx_error` | [invoice_id] or [payment_id] | abs(posted − correct) of the AR (resp. cash) row | doc_id + that row_id (invoice: AR or revenue row) + the fx_id of the correct date |
| `period_cutoff` | [invoice_id] | AR debit posted for an invoice dated outside the period | invoice doc_id + AR (or revenue) row_id |

"Same line items" = equal as a multiset of `(description, quantity, unit_price_minor, amount_minor)`
with descriptions compared lower-case, letters and digits only (order, case and punctuation ignored).
Default-mode copies are exact. Each hard-mode copy has a 50% chance of being re-typed.

Every evidence set is sufficient on its own: `auditenv/verify.py` recomputes the amount from the
set's records (plus the manifest).

Interacting scenarios: `I1` = foreign-currency payment at the period boundary that is
partially allocated (`payment_allocation`) **and** converted at the wrong date (`fx_error`
on the payment). `I2` = next-period foreign invoice booked in the period (`period_cutoff`)
and converted at the wrong rate (`fx_error` on the invoice). The injector tries the booking
date, then 1, 2 and 4 days before booking. It selects the first date whose converted invoice
total differs from the issue-date valuation by at least 10 base-currency minor units.
If none qualifies, it uses the booking date.

## 4. Environment API (`auditenv/env.py`)
```python
env = AuditEnv()
obs, info = env.reset(seed: int, config: dict | None = None)
obs, reward, terminated, truncated, info = env.step(action: dict)
```
All values JSON-compatible. `config` keys (all optional): `mode` ("train" | "eval",
default "train"), `max_steps` (100), `time_limit_s` (60), `errors`
(`{type: count}`), `interacting` (`{"I1": n, "I2": n}`; both must be objects — both omitted → random mix,
either given → exactly the listed counts, the rest 0), `n_invoices` (10–100), `distractors`
(bool), `transform_seed` (int | null: benign relabel/permutation), `difficulty` ("default" |
"hard"; default "default" — absent from the normalised config, so default episodes are unchanged), `allocation`
("partial" | "missing" | null: which variant an injected `payment_allocation` takes; null = drawn, 60 % partial),
`ensure_distractors` (bool, default false: if missing, turns a full single payment into an invoice paid in two
legitimate parts and another into a refunded overpayment; it needs suitable full payments, so a tiny company may
lack one, e.g. seed 25 with `n_invoices: 10, distractors: false` gets no refund). The last two are also absent from the normalised config unless set (jury scenarios, `auditenv/jury.py`).
Hard mode pads the ledger to a target of 900–1 400 rows before injection and selects up to three eligible invoices for credit-note reissues. Duplicates may be re-typed. The task text and `policy.ledger.credit_note` give the extra rules.

A rejected seed or config raises `ValueError` (over `auditenv.server`: a bounded `{"error": ...}`) and leaves
the current episode unchanged. A successful server reset grades an open episode as abandoned (empty answer).
Server framing: one JSON object per line and one response line per `reset`/`step`; `{"cmd": "close"}` ends the
session without a response. A line the server cannot handle gets `{"error": ...}` without consuming a step:
`request too large`, `invalid utf-8`, `invalid input type`, `invalid json`, `request must be a JSON object`,
`unknown cmd`, `no more episodes` (hidden queue exhausted), `RuntimeError: call reset() first`, `internal error`.

Grader secret: if the env var `AUDITENV_SECRET` is set (grader process only), it keys both the
generator RNG and the HMAC `episode_id`, so a policy cannot recover the seed or regenerate the
episode. Unset = public, reproducible train/dev episodes. `judge_adapter.generate_episode` and
closed server queues (`auditenv.server --episodes`, unless `--public`) never use the public key:
without `AUDITENV_SECRET` they use a random grader key file, or a per-process random key if that file is
unusable (README "Jury adapter").

First observation: `{task, manifest, policy, tools, steps_remaining}`; reset `info` =
`{episode_id, mode, max_steps}`. Step `info` is `{}` except on the terminal step in `mode="train"`:
`{valid, tp, fp, fn, precision, recall, f1, reward, inspection_steps}` (counts only, no truth content);
in `mode="eval"` it is always `{}`.
Step observation: `{step, steps_remaining, result, error}` — `error` is null or
`{code, message}`; `result` holds only what was requested.

Actions (`type` + params):
- `{"type":"list_records","table":T,"cursor":null|str,"limit":int}` → `{rows, next_cursor, total}`, max 50 rows (larger limit is clamped), cursor stable (`table:offset`; a hand-written offset only pages the same public table).
  `invoices` rows in listings omit `line_items`.
- `{"type":"get_record","table":T,"id":str}` → `{record}`
- `{"type":"get_document","doc_id":str}` → `{kind: "invoice"|"payment", document}` (full record)
- `{"type":"calculator","expression":str}` → `{value: str}`
- `{"type":"submit","findings":{episode_id, findings:[...]}}` → terminates.

Errors (unknown action/table/id, bad params — including parameters not listed for the action, as in
`schemas/action.schema.json`; a `submit` with such parameters still ends the episode, as an invalid
submission) consume a step; codes:
`unknown_action, bad_params, unknown_table, not_found, calc_error`, plus
`time_limit` (the action arrived after `time_limit_s` → it is not executed, even a submit; truncated) and `invalid_findings` (a submit
whose structure breaks §5 — a structure check only, it never depends on the truth; the episode still ends with reward −1 in the
grader log; in eval a valid submit just sees `{"submitted": true}`, with no correctness signal).
A non-submit action at the configured `max_steps` (default 100) truncates the episode and grades empty findings. After termination or truncation, every action returns the error `episode_over` without consuming a step: the final step counter and the outcome are preserved.
Reward is 0.0 on every non-terminal step. Terminal reward is returned to the policy
only in `mode="train"`; in `"eval"` it is 0.0 and the result goes to the grader log only.

## 5. Findings (`auditenv/schema.py`)
```json
{"episode_id": "ep_...", "findings": [{"type": "fx_error", "affected_ids": ["INV-1"],
  "claimed_amount_minor": 1234, "currency": "USD", "evidence_ids": ["D-1","L-7"],
  "explanation": "short reason"}]}
```
Structure (anything else here makes the submission invalid): top-level keys exactly `episode_id` (must equal
the episode's) and `findings`; ≤ 30 findings; each finding a dict with the keys above, all required except
`explanation`, and no others; `type` and `currency` strings, `affected_ids` and `evidence_ids` lists of
strings, `claimed_amount_minor` an int (not bool; a JSON integer literal — `1234.0` is a float here, although
JSON Schema calls it an integer), `explanation` a string. Limits are checked on the raw values: ≤ 10
`evidence_ids` counted before repeats are dropped, explanation ≤ 1000 code points.
Invalid structure → episode ends, reward −1, error recorded in the grader log.
Wrong values of the right type are *not* structural errors: an unknown `type` string, a negative or wrong
amount, a currency that is not the issue's (`"usd"`, `" USD"`), empty or unknown ids are a valid finding that
does not match (a false positive).

## 6. Matching & reward (`auditenv/matcher.py`, `auditenv/metrics.py`)
- Normalise: nothing is stripped, case-folded or converted — ids and currency compare as exact strings.
  `affected_ids` and `evidence_ids` are sets (order and repeats do not matter).
- Edge finding → issue iff type equal, `set(affected_ids) == set(issue.affected_ids)`, currency equal,
  `abs(claimed − expected) <= tolerance`, every evidence id is a public id of the episode
  (`matcher.public_ids`: ledger `row_id`, invoice/payment `doc_id`, `invoice_id`, `payment_id`, `fx_id`), and
  `set(evidence_ids)` ⊇ some evidence set. An unknown evidence id makes the finding unmatched.
- Tolerance: `policy.findings.tolerance_minor` (a fixed non-negative int, `matcher.tolerance_of`; default 0).
  Generated episodes publish 0, so the amount must be exact.
- One-to-one: a maximum-cardinality matching of findings (repeats included) to truth issues. Among maximum
  matchings, issue ids are sorted by code point and the lexicographically smallest sorted sequence of
  (issue_id, finding index) pairs wins, so submission order never changes TP/FP/FN. TP = matched pairs,
  FP = findings − TP (repeats included), FN = issues − TP.
- `P=TP/(TP+FP)`, `R=TP/(TP+FN)` (0 if denominator 0), `F1=2TP/(2TP+FP+FN)`;
  truth and findings both empty → F1=1; truth empty, findings non-empty → F1=0.
- `reward = clip(2*F1 − 1 − 0.002*inspection_steps, −1, 1)`, not rounded; inspection_steps =
  steps taken before the submit (the submit itself is not counted).

## 7. Policies (`auditenv/policies/`)
```python
class Policy:
    name: str
    def __init__(self, seed: int = 0): ...
    def reset(self, first_observation: dict) -> None: ...
    def act(self, observation: dict) -> dict: ...   # returns an action
```
Policies see only observations. The oracle is built grader-side from truth.
Runner: `auditenv.run.run_episode(env, policy, seed, config) -> list[dict]`
(trajectory steps: episode_id, step, action, observation, reward, terminated, truncated).
