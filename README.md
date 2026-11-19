# auditenv — RL environment for AI financial auditors

> **Кратко (RU).** Воспроизводимая RL-среда для дообучения ИИ-аудитора (кейс FinTech, Genesis
> Hackathon 2026). Генератор строит согласованную скрытую историю вымышленной компании,
> правильную двойную запись, затем вносит ошибки четырёх типов (дубли счетов, неполное
> распределение платежа, неверная дата курса, ошибка периода) и два сценария
> взаимодействующих ошибок, записывая причинное изменение. Агент читает записи только через
> узкие инструменты (`reset/step`, JSON, лимит 100 шагов) и отправляет выводы с доказательствами;
> общий matcher и терминальная награда `clip(2*F1 − 1 − 0.002*steps, −1, 1)` оценивают результат.
> Одна команда проверки: `uv run python -m auditenv.check`. Без сети, без GPU, без зависимостей.

Python 3.11, **standard library only** (zero runtime dependencies), MIT licence.

**Why.** An AI auditor needs practice on books with known, verifiable errors. Real ledgers cannot be
shared and have no answer key; an LLM judge can be argued with. `auditenv` generates unlimited
reproducible companies whose misstatements are known exactly, lets a policy investigate them only
through narrow tools, and scores the answer with a published matcher that requires evidence.

**How.** `generate(seed, config)` builds a hidden company history (customers, invoices, payments,
expenses, daily FX), books it correctly in a base-currency double-entry ledger, then injects errors
as recorded changes (before/after journals) and writes the truth with acceptable evidence sets.
`AuditEnv` exposes the public records through `reset/step`; `submit` is graded by the matcher.

## Quick start

```bash
git clone https://github.com/madiyar-abi/genesis.git && cd genesis
uv run python -m auditenv.check        # the single official check (exit code 0 = pass)
```

No `uv`? Any Python 3.11 works the same: `python3.11 -m auditenv.check` from the repo root.

### Container

```bash
docker build -t auditenv .
docker run --rm --network none auditenv            # runs python -m auditenv.check
```

The container path is exercised on every push by `.github/workflows/check.yml` (build, run without
network, plus the verifier and the seed sweep on plain Python 3.11).

## Errors the agent must find

| type | what happened | amount in truth (base currency, minor units) |
|---|---|---|
| `duplicate_invoice` | the same invoice (entity, currency, line items) entered and booked twice | AR debit of the later copy |
| `payment_allocation` | the remittance says a payment covers an invoice, the ledger credits less (or nothing) to its receivable; the rest sits in 2900 | expected AR credit − posted AR credit |
| `fx_error` | an invoice or payment converted with the rate of a wrong date | abs(posted − correct) |
| `period_cutoff` | an invoice issued outside the period booked inside it | AR debit posted |
| `I1` (interacting) | foreign payment late on the last day: partially allocated **and** converted at the next day's rate | two issues |
| `I2` (interacting) | next-period foreign invoice backdated **and** converted at the booking-date rate | two issues |

Clean companies (no errors) and legitimate look-alikes (split/partial payments, refunds,
unidentified receipts, weekly retainers with equal amounts, documents near midnight in other
timezones) are part of every split. Worked examples with real ids: [`docs/DESIGN.md`](docs/DESIGN.md) §3.

## Reward

A finding is a true positive iff type, canonical `affected_ids`, currency, amount within
`max(1, expected // 1000)` and at least one complete acceptable evidence set all match; matching is
one-to-one (repeats are false positives). `P = TP/(TP+FP)`, `R = TP/(TP+FN)`, `F1 = 2TP/(2TP+FP+FN)`
(F1 = 1 when truth and answer are both empty), terminal reward
`clip(2·F1 − 1 − 0.002·inspection_steps, −1, 1)`, 0 on every other step. An invalid submission ends
the episode with −1. Code: `auditenv/matcher.py`, `metrics.py`.

## Results (from the check, dev split = `configs/dev.json`, 10 episodes)

| policy | P | R | F1 | mean return | mean steps |
|---|---|---|---|---|---|
| oracle (grader-side) | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 |
| reconcile (policy-aware rules) | 1.000 | 1.000 | 1.000 | 0.957 | 22.5 |
| naive reconcile | 0.169 | 0.700 | 0.273 | −0.506 | 17.2 |
| random explorer | 0.000 | 0.000 | 0.000 | −0.807 | 31.0 |
| flag-everything | 0.000 | 0.000 | 0.000 | −1.000 | 3.8 |

Hard mode (`configs/eval_hard.json`): the same reconcile script drops to F1 0.611, oracle stays 1.0.
Seed sweep over 3 000 episodes: 0 problems. Details and failure analysis: [`docs/DESIGN.md`](docs/DESIGN.md) §9.
## What the check does

`auditenv.check` exits 0 only if every gate passes:

1. **Unit tests** — `tests/` (env contract, matcher, reward attacks, generator, verifier, transform, server).
2. **Data & truth verifier** — for generated episodes: every journal balances; with the recorded
   injections reverted the books contain zero discrepancies; after injection the discrepancies
   recomputed independently from the public records equal `truth.json` (type, ids, amount);
   every evidence set exists and covers the affected records.
3. **Baselines on the dev split** — random explorer, rule-based reconciliation, flag-everything
   attack, oracle → P / R / F1 / return / steps / time.
4. **20 paired checks** — exact replay of seed + actions; relabelled ids + permuted rows keep the
   oracle answer and reward (under the new ids).
5. **Out-of-process eval run** — environment and grader in a subprocess; the policy sees no
   reward and no truth; results go only to the grader log.
6. **Hard mode** — verifier on hard episodes, baselines on `configs/eval_hard.json`; gates: oracle 1.0,
   `reconcile_hard` (the policy's hard rules) solves it from the records, plain `reconcile` does not;
   20 more paired checks on hard episodes (replay with `reconcile_hard`, relabel + permute incl. FX rows).

## Using the environment

```python
from auditenv.env import AuditEnv

env = AuditEnv()
obs, info = env.reset(seed=2001, config={"errors": {"fx_error": 1}, "interacting": {"I1": 1}})
episode_id = obs["manifest"]["episode_id"]
obs, reward, terminated, truncated, info = env.step(
    {"type": "list_records", "table": "ledger", "cursor": None, "limit": 50})
obs, reward, terminated, truncated, info = env.step({"type": "calculator", "expression": "1250.00*1.0842"})
obs, reward, terminated, truncated, info = env.step(
    {"type": "submit", "findings": {"episode_id": episode_id, "findings": []}})
print(reward, info)   # train mode: terminal reward + P/R/F1 counts (no truth content)
```

(Run from the repo root, e.g. in `uv run python`; elsewhere set `PYTHONPATH` to the repo.)

Actions: `list_records(table, cursor, limit≤50)`, `get_record(table, id)`, `get_document(doc_id)`,
`calculator(expression)`, `submit(findings)`. Full interface: [`docs/CONTRACT.md`](docs/CONTRACT.md).

Config keys: `mode` (`train` returns the terminal reward, `eval` hides it), `max_steps` (≤ 100),
`time_limit_s` (60), `errors` (`{type: count}`; omitted → random mix), `interacting`
(`{"I1": n, "I2": n}`), `n_invoices` (10–100), `distractors`, `transform_seed` (benign relabel/permute),
`difficulty` (`"default"` | `"hard"`: credit-note reissues, re-typed duplicates, 900–1 400 ledger rows —
see [`docs/DESIGN.md`](docs/DESIGN.md) “Hard mode”; `configs/eval_hard.json` is a 20-episode hard split).

### Run a policy, write trajectories

```bash
uv run python -m auditenv.run --policy reconcile --config configs/dev.json --out trajectories.jsonl
uv run python -m auditenv.run --policy random --seeds 2000-2009 --mode eval
```

Policies: `random`, `naive_reconcile`, `reconcile`, `reconcile_hard`, `flag_all`, `oracle` (grader-side, reads truth — reward ceiling only).
Each trajectory line: `episode_id, step, action, observation, reward, terminated, truncated`.

### Plugging in your own policy (organisers' baselines)

Any object with `reset(first_observation)` and `act(observation) -> action` works:

```python
from auditenv.env import AuditEnv
from auditenv.run import run_episode

class MyPolicy:
    def reset(self, first_observation): self.ep = first_observation["manifest"]["episode_id"]
    def act(self, observation):
        return {"type": "submit", "findings": {"episode_id": self.ep, "findings": []}}

traj = run_episode(AuditEnv(), MyPolicy(), seed=2001, config={"mode": "train"})
print(traj[-1]["reward"])
```

A policy in another language talks to `python -m auditenv.server` over JSON lines (below).
The four baseline adapters live in `auditenv/policies/` (`random_explorer.py`, `reconcile.py`,
`flag_all.py`, `oracle.py`; plus `naive_reconcile.py`).

### Out-of-process evaluation (closed run)

```bash
# organiser side: hidden episode list never reaches the agent
AUDITENV_SECRET=<grader-only key> python -m auditenv.server --episodes hidden.json --grader-log grader.jsonl
```

`auditenv.client.RemoteEnv` speaks the same `reset/step` API over JSON lines; with `--episodes`
the client cannot choose seeds, rewards are 0.0 and results are written only to `grader.jsonl`.

### Other commands

```bash
uv run python -m unittest discover -s tests -t .     # tests only
uv run python -m unittest tests.test_env             # one module
uv run python -m auditenv.verify --seeds 0-199       # verifier on 600 episodes
uv run python -m auditenv.verify --dir episodes/dev  # verifier on the exported files
uv run python -m auditenv.attack                     # 11,000 mutations on 20 fixed public seeds
uv run python -m tests.test_fuzz                     # action count and runtime
uv run python -m auditenv.verify --dir episodes/hard
uv run python -m auditenv.check --json /tmp/auditenv-metrics.json
uv run python scripts/sync_docs.py --check --json /tmp/auditenv-metrics.json  # omit --check to update
uv run python -m auditenv.fuzz --seeds 0-999         # seed sweep: 3 000 episodes end to end
uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299   # every error findable in budget?
uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json  # failure analysis
uv run python -m auditenv.demo                       # narrated demo (see docs/DEMO.md)
uv run python -m auditenv.export --config configs/dev.json --out episodes/dev       # re-export files
make check | make test | make verify
```

## Repository layout

| path | what |
|---|---|
| `auditenv/generator.py`, `inject.py` | company history → correct ledger → errors, truth, provenance |
| `auditenv/env.py` | `AuditEnv` reset/step, tools, limits, modes |
| `auditenv/matcher.py`, `metrics.py`, `schema.py` | findings validation, normalisation, one-to-one matching, P/R/F1, reward |
| `auditenv/calculator.py` | arithmetic-only calculator (AST whitelist, Decimal) |
| `auditenv/verify.py` | independent data/truth verifier |
| `auditenv/transform.py` | benign transformation (new ids, permuted rows) |
| `auditenv/server.py`, `client.py` | out-of-process environment/grader |
| `auditenv/policies/` | baselines: random explorer, naive reconcile, reconcile, reconcile_hard, flag-all, oracle |
| `auditenv/run.py`, `check.py` | runner/trajectories, single check command |
| `auditenv/fuzz.py`, `analyze.py` | seed sweep + stress test, measured failure analysis |
| `auditenv/export.py`, `load.py`, `demo.py` | episode files on disk and back, narrated demo |
| `auditenv/experimental.py` | materiality-weighted reward, reported next to the shared one |
| `schemas/` | JSON Schemas: action, observation, findings, manifest, truth, trajectory step |
| `configs/` | versioned episode lists: train (1000–1009), dev (2000–2009), eval_example (9000–9019), eval_hard (9100–9119) |
| `episodes/` | exported 10 train + 10 dev + 20 public hard episodes (`public/` for agents, `grader/` closed) |
| `trajectories/` | training trajectories (JSONL) of reconcile, naive reconcile and random on the train split |
| `tests/` | 256 unittest tests; `tests/test_jury.py` maps the jury checklist to tests |
| `docs/` | contract, design note, demo script, pitch outline; `REVIEW.md` — jury-style review log |

## Honest limitations

- Synthetic data only: all companies, people and money are fictional; the reward does not prove
  fitness for real audits.
- The generator is deterministic and public: for hidden evaluation set `AUDITENV_SECRET` in the
  grader process — it keys the generator and the HMAC `episode_id`, so seeds can't be recovered
  and episodes can't be regenerated by the agent.
- More in [`docs/DESIGN.md`](docs/DESIGN.md).

## License

MIT — see [`LICENSE`](LICENSE). All companies, people and amounts are synthetic.

## Contributing

Read [`HANDOFF.md`](HANDOFF.md) first. Branch, small commits, PR into `main`.
AI agent rules: [`CLAUDE.md`](CLAUDE.md).
