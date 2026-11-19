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
`{schema_version, episode_id, base_currency, period_start, period_end, timezone,
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
  payment currency; `sum(amount_minor) <= payment.amount_minor`. Negative
  `amount_minor` on a payment = refund.
- `fx_id` = `"{date}:{source}:{target}"`.
- Accounts: `1000` Cash, `1200` Accounts receivable, `2900` Unapplied cash,
  `4000` Revenue, `6100` Rent, `6200` Payroll, `6300` Software, `6400` Bank fees,
  `7900` FX gain/loss.

### Correct bookkeeping (the "policy"; violations of it are the errors)
- Invoice issued (only if its issue date in company tz is inside the period):
  `Dr 1200 / Cr 4000`, amount = `convert(total_minor, rate(issue date))`,
  rows carry invoice_id + entity_id, payment_id null, timestamp = issued_at.
- Payment received (inside the period): `Dr 1000 convert(amount, rate(payment date))`;
  per ref `Cr 1200 convert(ref.amount, rate(invoice issue date))` with invoice_id;
  remainder (amount − Σrefs, or all of it if refs are null) `Cr 2900` at the payment-date
  rate; any difference `7900`. Every journal (rows sharing payment_id, or an invoice's
  rows with payment_id null) balances: Σdebit == Σcredit.
- Expenses: `Dr 6xxx / Cr 1000`, no invoice/payment ids.
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
| `duplicate_invoice` | [original_invoice_id, duplicate_invoice_id] | ledger AR debit of the later-issued copy | both invoice doc_ids + the later copy's AR (or revenue) row_id |
| `payment_allocation` | [invoice_id, payment_id] | `convert(ref.amount, rate(inv date))` − AR credit actually posted | payment doc_id + invoice doc_id + the 2900 row_id (or the AR credit row_id) + the invoice-date fx_id if foreign |
| `fx_error` | [invoice_id] or [payment_id] | abs(posted − correct) of the AR (resp. cash) row | doc_id + that row_id (invoice: AR or revenue row) + the fx_id of the correct date |
| `period_cutoff` | [invoice_id] | AR debit posted for an invoice dated outside the period | invoice doc_id + AR (or revenue) row_id |

Every evidence set is sufficient on its own: `auditenv/verify.py` recomputes the amount from the
set's records (plus the manifest).

Interacting scenarios: `I1` = foreign-currency payment at the period boundary that is
partially allocated (`payment_allocation`) **and** converted at the wrong date (`fx_error`
on the payment). `I2` = next-period foreign invoice booked in the period (`period_cutoff`)
at the booking-date rate (`fx_error` on the invoice).

## 4. Environment API (`auditenv/env.py`)
```python
env = AuditEnv()
obs, info = env.reset(seed: int, config: dict | None = None)
obs, reward, terminated, truncated, info = env.step(action: dict)
```
All values JSON-compatible. `config` keys (all optional): `mode` ("train" | "eval",
default "train"), `max_steps` (100), `time_limit_s` (60), `errors`
(`{type: count}`), `interacting` (`{"I1": n, "I2": n}`), `n_invoices` (10–100), `distractors`
(bool), `transform_seed` (int | null: benign relabel/permutation).

Grader secret: if the env var `AUDITENV_SECRET` is set (grader process only), it keys both the
generator RNG and the HMAC `episode_id`, so a policy cannot recover the seed or regenerate the
episode. Unset = public, reproducible train/dev episodes.

First observation: `{task, manifest, policy, tools, steps_remaining}`; reset `info` =
`{episode_id, mode, max_steps}`. Step `info` is `{}` except on the terminal step in `mode="train"`:
`{valid, tp, fp, fn, precision, recall, f1, reward, inspection_steps}` (counts only, no truth content);
in `mode="eval"` it is always `{}`.
Step observation: `{step, steps_remaining, result, error}` — `error` is null or
`{code, message}`; `result` holds only what was requested.

Actions (`type` + params):
- `{"type":"list_records","table":T,"cursor":null|str,"limit":int}` → `{rows, next_cursor, total}`, max 50 rows (larger limit is clamped), cursor opaque & stable.
  `invoices` rows in listings omit `line_items`.
- `{"type":"get_record","table":T,"id":str}` → `{record}`
- `{"type":"get_document","doc_id":str}` → `{kind: "invoice"|"payment", document}` (full record)
- `{"type":"calculator","expression":str}` → `{value: str}`
- `{"type":"submit","findings":{episode_id, findings:[...]}}` → terminates.

Errors (unknown action/table/id, bad params) consume a step; codes:
`unknown_action, bad_params, unknown_table, not_found, calc_error, episode_over`, plus
`time_limit` (wall-clock limit hit → truncated) and `invalid_findings` (train mode only; in eval
the policy just sees `{"submitted": true}`).
Step 100 without submit → `truncated=true`, empty findings are graded.
Reward is 0.0 on every non-terminal step. Terminal reward is returned to the policy
only in `mode="train"`; in `"eval"` it is 0.0 and the result goes to the grader log only.

## 5. Findings (`auditenv/schema.py`)
```json
{"episode_id": "ep_...", "findings": [{"type": "fx_error", "affected_ids": ["INV-1"],
  "claimed_amount_minor": 1234, "currency": "USD", "evidence_ids": ["D-1","L-7"],
  "explanation": "short reason"}]}
```
Limits: ≤ 30 findings, ≤ 10 evidence_ids, explanation ≤ 1000 chars, `type` ∈ the 4
types, `affected_ids` non-empty list of non-empty strings (≤ 10), amount int ≥ 0
(not bool), currency 3 uppercase letters, `episode_id` must equal the episode's.
Invalid structure → episode ends, reward −1, error recorded in the grader log.

## 6. Matching & reward (`auditenv/matcher.py`, `auditenv/metrics.py`)
- Normalise: strip ids, dedupe + sort affected_ids and evidence_ids (ids are case-sensitive;
  currency must be exactly `[A-Z]{3}` or the submission is invalid). Top-level keys other than
  `episode_id` and `findings` are invalid.
- TP iff type equal, normalised affected_ids equal, currency equal,
  `abs(claimed − expected) <= max(1, expected // 1000)`, and `set(evidence_ids)`
  ⊇ some evidence set.
- One-to-one, greedy in submission order: each finding takes the first unmatched truth
  issue (truth order) it satisfies; otherwise FP. Unmatched truth = FN.
- `P=TP/(TP+FP)`, `R=TP/(TP+FN)` (0 if denominator 0), `F1=2TP/(2TP+FP+FN)`;
  truth and findings both empty → F1=1; truth empty, findings non-empty → F1=0.
- `reward = clip(2*F1 − 1 − 0.002*inspection_steps, −1, 1)`; inspection_steps =
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
