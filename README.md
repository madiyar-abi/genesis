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

## Quick start

```bash
git clone https://github.com/madiyar-abi/genesis.git && cd genesis
uv run python -m auditenv.check        # the single official check (≈ 6 s, exit code 0 = pass)
```

No `uv`? Any Python 3.11 works the same: `python3.11 -m auditenv.check` from the repo root.

### Container

```bash
docker build -t auditenv .
docker run --rm --network none auditenv            # runs python -m auditenv.check
```

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
(`{"I1": n, "I2": n}`), `n_invoices` (10–100), `distractors`, `transform_seed` (benign relabel/permute).

### Run a policy, write trajectories

```bash
uv run python -m auditenv.run --policy reconcile --config configs/dev.json --out trajectories.jsonl
uv run python -m auditenv.run --policy random --seeds 2000-2009 --mode eval
```

Policies: `random`, `reconcile`, `flag_all`, `oracle` (grader-side, reads truth — reward ceiling only).
Each trajectory line: `episode_id, step, action, observation, reward, terminated, truncated`.

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
| `auditenv/policies/` | baselines: random explorer, reconcile, flag-all, oracle |
| `auditenv/run.py`, `check.py` | runner/trajectories, single check command |
| `configs/` | versioned train/dev/eval-example episode lists |
| `episodes/` | exported 10 train + 10 dev episodes (`public/` for agents, `grader/` closed) |
| `docs/` | contract, design note, demo script, pitch outline |

## Honest limitations

- Synthetic data only: all companies, people and money are fictional; the reward does not prove
  fitness for real audits.
- The generator is deterministic and public: for hidden evaluation set `AUDITENV_SECRET` in the
  grader process — it keys the generator and the HMAC `episode_id`, so seeds can't be recovered
  and episodes can't be regenerated by the agent.
- More in [`docs/DESIGN.md`](docs/DESIGN.md).

## Contributing

Read [`HANDOFF.md`](HANDOFF.md) first. Branch, small commits, PR into `main`.
AI agent rules: [`CLAUDE.md`](CLAUDE.md).
