# auditenv — RL environment for AI financial auditors

[![check](https://github.com/madiyar-abi/genesis/actions/workflows/check.yml/badge.svg?branch=main)](https://github.com/madiyar-abi/genesis/actions/workflows/check.yml)

> **Кратко (RU).** Воспроизводимая RL-среда для дообучения ИИ-аудитора (кейс FinTech, Genesis
> Hackathon 2026). Генератор строит согласованную скрытую историю вымышленной компании,
> правильную двойную запись, затем вносит ошибки четырёх типов (дубли счетов, неполное
> распределение платежа, неверная дата курса, ошибка периода) и два сценария
> взаимодействующих ошибок, записывая причинное изменение. Агент читает записи только через
> узкие инструменты (`reset/step`, JSON, лимит 100 шагов) и отправляет выводы с доказательствами;
> общий matcher и терминальная награда `clip(2*F1 − 1 − 0.002*inspection_steps, −1, 1)` оценивают результат.
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

Needs only [`uv`](https://docs.astral.sh/uv/getting-started/installation/): it fetches Python 3.11 (pinned in
`.python-version`); there are no other dependencies. For an offline checkout with Python 3.11 already installed, run
`python3.11 -m auditenv.check` from the repository root, or use the container below.
The check itself needs no network; a first `uv` run may download Python 3.11 and `docker build` may pull the pinned
base image (the built image then runs with `--network none`). For the published numbers and byte-identical public
exports, run commands with `AUDITENV_SECRET` unset (`env -u AUDITENV_SECRET uv run python -m ...`); set a key only in
the grader process.

Shortest review: `uv run python -m auditenv.demo` (under a second), then the full check above (about a minute on an idle machine).
To connect the official harness, go straight to [For the jury](#for-the-jury); Docker is optional.

### Container

```bash
docker build -t auditenv .
docker run --rm --network none auditenv            # runs python -m auditenv.check offline
```

The container path is exercised on pushes to `main` and on pull requests by `.github/workflows/check.yml` (build, run without
network, plus the verifier and the seed sweep on plain Python 3.11). To run just the unit tests in the same image, use
`docker run --rm --network none auditenv python -m unittest discover -s tests -t .`.

## Isolated baseline run (C20)

From the repo root, build the public policy image and run the grader on the host:

```sh
docker build --target policy -t genesis-policy .
uv run python -m auditenv.jury_run --policy-image genesis-policy
```

Each non-oracle baseline runs as UID 65534 with a read-only filesystem, no network and no host mounts. Only the public policy modules are copied into its image. Observations and actions travel over standard input and output. The episode directory, oracle, matcher and grading key stay with the host grader. The default subprocess command is for trusted public baselines. For organizer-supplied policies, apply the same restriction to their worker and monitor the 60-second deadline from the grader process.

## For the jury

1. **No key to set.** `generate_episode` keys hidden episodes so that neither `episode_id` nor the records reveal
   the seed: by `AUDITENV_SECRET` if you set it, otherwise by a random grader key created once in
   `~/.auditenv/grader.key` (or `$AUDITENV_KEY_FILE`). Keep both out of the policy's process.
2. Connect through **`judge_adapter.py`** in the repository root (working directory `/app` in the container):
   `generate_episode`, `make_env()` → `reset` / `step({"name", "args"})`, `score_episode` — see
   [Jury adapter](#jury-adapter-judge_adapterpy). The `{"type": ...}` actions further down are the environment's
   native form; the adapter translates the jury's envelope to them.
3. Replay the four blocks of the published checks: `uv run python -m unittest tests.test_judge_contract
   tests.test_judge_reward tests.test_judge_scenarios tests.test_judge_paired` (in the container:
   `docker run --rm --network none auditenv python -m unittest tests.test_judge_contract tests.test_judge_reward
   tests.test_judge_scenarios tests.test_judge_paired`); each check → test in [`docs/CHECKS.md`](docs/CHECKS.md).
   The whole flow with our four baselines: `uv run python -m auditenv.jury_run`.

| §09 material | where |
|---|---|
| source, licence, pinned dependencies | `auditenv/`, `judge_adapter.py`, `LICENSE` (MIT); stdlib only, `pyproject.toml`, `uv.lock`, base image pinned by digest |
| README: container and one check command | this file: Quick start, Container |
| matcher and reward, schemas, policies | `auditenv/matcher.py`, `metrics.py`, `schema.py`; `schemas/*.json`; `public/policy.json` in every episode |
| 10 train + 10 dev episodes | `episodes/train`, `episodes/dev` (plus 20 public hard episodes in `episodes/hard`) |
| tests | `tests/` (environment, matching, reward, verifier, jury checks) |
| four baseline-policy adapters | `auditenv/policies/` (random explorer, reconcile, flag-all, oracle; plus naive reconcile and reconcile_hard); `auditenv.policy_worker.JuryPolicy` runs them behind the jury protocol (`auditenv.jury_run` starts random explorer, reconcile and flag-all as separate policy processes; the oracle runs in the grader) |
| `trajectories.jsonl` | [`trajectories.jsonl`](trajectories.jsonl) in the repository root: 20 train episodes (10 default, 10 hard) played by `reconcile_hard`, 674 lines, each exactly `{episode_id, step, action, observation, reward, terminated, truncated}`; no truth in observations; the tests regenerate it byte for byte ([how](#run-a-policy-write-trajectories)); per-policy logs of the other baselines in `trajectories/` |
| design note | [`docs/DESIGN.md`](docs/DESIGN.md) (interfaces: [`docs/CONTRACT.md`](docs/CONTRACT.md)) |
| demo | `uv run python -m auditenv.demo` (narrated, seed 2003 of the demo config), [`docs/demo.cast`](docs/demo.cast), script [`docs/DEMO.md`](docs/DEMO.md) |

## Errors the agent must find

| type | what happened | amount in truth (base currency, minor units) |
|---|---|---|
| `duplicate_invoice` | the same invoice (entity, currency, line items) entered and booked twice | AR debit of the later copy |
| `payment_allocation` | the remittance says a payment covers an invoice, the ledger credits less (or nothing) to its receivable; the rest sits in 2900 | expected AR credit − posted AR credit |
| `fx_error` | an invoice or payment converted with the rate of a wrong date | abs(posted − correct) |
| `period_cutoff` | an invoice issued outside the period booked inside it | AR debit posted |
| `I1` (interacting) | foreign payment late on the last day: partially allocated **and** converted at another day's rate (usually the next day) | two issues |
| `I2` (interacting) | next-period foreign invoice backdated into the period **and** converted using the booking-date rate or an earlier fallback rate | two issues |

Clean companies (no errors) and legitimate look-alikes (split/partial payments, refunds,
unidentified receipts, weekly retainers with equal amounts, documents near midnight in other
timezones) are part of every split. Worked examples with real ids: [`docs/DESIGN.md`](docs/DESIGN.md) §3.

## Reward

A finding is a true positive iff type, the exact set of canonical `affected_ids`, currency (exact string),
amount within the published `policy.findings.tolerance_minor` (0: exact) and at least one complete acceptable
evidence set all match, with every evidence id present in the episode's public data; matching is a one-to-one
maximum matching with a published tie rule (repeats are false positives). Only a wrong JSON type, a missing
field, an unknown key, an exceeded limit or another episode's `episode_id` makes a submission invalid; a wrong value
inside a finding is a false positive. `P = TP/(TP+FP)`, `R = TP/(TP+FN)`, `F1 = 2TP/(2TP+FP+FN)`
(F1 = 1 when truth and answer are both empty), terminal reward
`clip(2·F1 − 1 − 0.002·inspection_steps, −1, 1)`, 0 on every other step. An invalid submission ends
the episode with −1. Code: `auditenv/matcher.py`, `metrics.py`.

## Results (from the check, dev split = `configs/dev.json`, 10 episodes)

| policy | P | R | F1 | mean return | mean steps |
|---|---|---|---|---|---|
| oracle (grader-side) | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 |
| reconcile (policy-aware rules) | 1.000 | 1.000 | 1.000 | 0.956 | 22.8 |
| naive reconcile | 0.177 | 0.733 | 0.286 | −0.480 | 17.5 |
| random explorer | 0.000 | 0.000 | 0.000 | −0.807 | 31.0 |
| flag-everything | 0.000 | 0.000 | 0.000 | −1.000 | 3.8 |

Hard mode (`configs/eval_hard.json`): the same reconcile script drops to F1 0.755, oracle stays 1.0.
Separately from the check, `uv run python -m auditenv.fuzz --seeds 0-999` (3 000 episodes): 0 problems. Details and failure analysis: [`docs/DESIGN.md`](docs/DESIGN.md) §9.
## What the check does

`auditenv.check` exits 0 only if every gate passes:

1. **Unit tests** — `tests/` (env contract, matcher, reward attacks, generator, verifier, transform, server).
2. **Data & truth verifier** — for generated episodes: every journal balances; with the recorded
   injections reverted the books contain zero discrepancies; after injection the discrepancies
   recomputed independently from the public records equal `truth.json` (type, ids, amount); both
   books follow the published posting policy (accounts per journal, entities, unapplied cash, dates);
   every evidence set exists and covers the affected records. The verifier also requires nonblank task
   instructions and integer minor-unit exponents for every currency used in the public tables.
3. **Baselines on dev and the public default evaluation split** — random explorer, naive reconciliation, rule-based reconciliation, flag-everything
   attack, oracle → P / R / F1 / return / steps / time. The check reports 10 dev companies and
   20 companies from `configs/eval_example.json` separately. The latter mirrors the hidden cohort’s composition.
4. **20 paired checks** replay the same seed and actions, then relabel IDs and shuffle rows.
   Each translated public row must match in full, and the translated oracle answer must earn the same reward.
5. **Out-of-process eval run (public smoke)** — a two-episode public smoke test (seeds 7001–7002, `flag_all` policy)
   with environment and grader isolated in a subprocess; the policy sees no reward and no truth; results go only
   to the grader log. This tests the subprocess harness locally, distinct from the withheld evaluation cohort.
6. **Hard mode** — verifier on hard episodes, baselines on `configs/eval_hard.json`; gates: oracle 1.0,
   `reconcile_hard` (the policy's hard rules) solves it from the records, plain `reconcile` does not;
   20 more paired checks on hard episodes (replay with `reconcile_hard` and `random`, relabel + permute incl. FX rows).
7. **The jury's flow** — the 20 jury scenarios D01–D20 generated with the public generator (seeds 3001–3020), served in
   closed mode from their directories, each baseline policy in its own process behind the baseline-policy adapter
   (`auditenv/jury_run.py`); gates: oracle 1.0, reconcile solves them, flag-all and random are penalised, every
   episode within 60 s. The four jury blocks themselves are replayed by the unit tests `tests/test_judge_*.py`.

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

(Run from the repo root, e.g. in `uv run python` or `python3.11`; elsewhere set `PYTHONPATH` to the repo root.)

Actions: `list_records(table, cursor, limit≤50)`, `get_record(table, id)`, `get_document(doc_id)`,
`calculator(expression)`, `submit(findings)`. Full interface: [`docs/CONTRACT.md`](docs/CONTRACT.md).

Config keys: `mode` (`train` returns the terminal reward, `eval` hides it), `max_steps` (≤ 100),
`time_limit_s` (60), `errors` (`{type: count}`), `interacting`
(`{"I1": n, "I2": n}`), `n_invoices` (10–100), `distractors`, `transform_seed` (benign relabel/permute),
`difficulty` (`"default"` | `"hard"`: credit-note reissues, re-typed duplicates, a ledger padded to a target of 900–1 400 rows before injection —
see [`docs/DESIGN.md`](docs/DESIGN.md) “Hard mode”; `configs/eval_hard.json` is a 20-episode hard split).
Two opt-in keys used by the jury scenarios: `allocation` (`"partial"` | `"missing"` | null) picks the
`payment_allocation` variant, and `ensure_distractors` (bool) adds a split payment and a refunded overpayment when
suitable receipts exist (CONTRACT §4).

Omit both `errors` and `interacting` for a random mix. Supplying either object sets every unspecified count to zero.

### Run a policy, write trajectories

```bash
uv run python -m auditenv.run --policy reconcile --config configs/dev.json --out /tmp/dev_reconcile.jsonl
uv run python -m auditenv.run --policy random --seeds 2000-2009 --mode eval
```

Policies: `random`, `naive_reconcile`, `reconcile`, `reconcile_hard`, `flag_all`, `oracle` (grader-side, reads truth — reward ceiling only).
Each trajectory line has exactly the case's fields `episode_id, step, action, observation, reward, terminated, truncated`.

**`trajectories.jsonl`** (repository root, the case's deliverable) holds the policy-aware script `reconcile_hard` on the
10 train and 10 hard train episodes (seeds 1000–1009 and 1100–1109, train mode), 674 lines. One policy per file keeps
`(episode_id, step)` a unique key, so no extra `policy` field is needed; `reconcile_hard` plays default books exactly
like `reconcile`, so the file equals `trajectories/train_reconcile.jsonl` followed by
`trajectories/train_hard_reconcile_hard.jsonl`. The 10 train episodes are shipped in `episodes/train`; the 10 hard train
episodes are not exported (`episodes/hard` holds the hard evaluation seeds 9100–9119) — write them with
`uv run python -m auditenv.export --config configs/train_hard.json --out /tmp/train_hard`. The file is reproduced byte for byte by:

```bash
uv run python -m auditenv.run --policy reconcile_hard --config configs/train.json --config configs/train_hard.json --out trajectories.jsonl
```

`tests/test_trajectory_files.py` (part of the check) fails if any committed log differs from a fresh run, has another
field, misses a step, or carries a grader marker (`truth`, `evidence_sets`, `expected_amount_minor`, `provenance`,
`issue_id`) in an observation, and replays the saved actions against the environment.

The other baselines are logged per policy in `trajectories/`, reproduced byte for byte by (train mode, no truth in observations):

```bash
for p in random naive_reconcile reconcile; do
  uv run python -m auditenv.run --policy $p --config configs/train.json --out trajectories/train_$p.jsonl
done
for p in random naive_reconcile reconcile reconcile_hard; do  # hard train split, seeds 1100–1109
  uv run python -m auditenv.run --policy $p --config configs/train_hard.json --out trajectories/train_hard_$p.jsonl
done
```

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

### Jury adapter (`judge_adapter.py`)

The jury's single connection point ([check definitions](https://genesis-exe.com/fintech-checks.html), "Единый способ
подключения") is `judge_adapter.py` in the repository root. Working directory: the repository root (`/app` in the
container); it imports `auditenv` and needs nothing else. The adapter only translates names and shapes; the
environment, matcher and reward are the ones described above.

**Hidden episodes are keyed by default.** The generator is open source, so a public key would let a policy recover
the seed of a hidden episode by enumeration and regenerate its truth. `generate_episode` (and a closed `reset` without
`episode_dir`) therefore use `AUDITENV_SECRET` if it is set, and otherwise a random grader key that is created once in
`~/.auditenv/grader.key` (`$AUDITENV_KEY_FILE` overrides the path; mode 0600 on creation) and named on stderr by
`generate_episode` (a closed `reset` is quiet). The same seed and
config give the same episode again on that machine. If the file cannot be written (read-only home), a random key of
the process is used and stderr says so. Keep the key out of the policy's process. Loading, `reset` with
`episode_dir` and `score_episode` read the files and need no key. Open mode (`train` without `episode_dir`) and the
published splits use the public generator on purpose (open mode uses `AUDITENV_SECRET` if it is set).

```python
import os, tempfile
import judge_adapter as ja
out = os.path.join(tempfile.mkdtemp(), "ep")
ja.generate_episode(7, {"errors": {"fx_error": 1}, "interacting": {"I1": 0, "I2": 0}}, out)  # public/ + grader/
env = ja.make_env()
first, info = env.reset(0, {"mode": "closed", "episode_dir": out, "team_config": {}})
obs, reward, terminated, truncated, _ = env.step({"name": "list_records",
                                                  "args": {"table": "ledger", "cursor": None, "limit": 50}})
print(first["remaining_steps"], obs["remaining_steps"], len(obs["result"]["records"]), reward)  # 100 99 50 0.0
print(ja.score_episode(out, {"episode_id": info["episode_id"], "findings": []}, 1))  # tp 0, fn 1, return -1
```

| call | behaviour |
|---|---|
| `generate_episode(seed, config, output_dir)` | our generator with the config of `docs/CONTRACT.md` §4; writes `public/` (task.txt, manifest.json, ledger.csv, invoices.jsonl, payments.jsonl, fx.csv, policy.json) and `grader/` (truth.json, provenance.json) |
| `reset(seed, {"mode": "closed", "episode_dir": d, "team_config": {...}})` | serves the episode in `d` as it is (no generation, ids unchanged); a second reset restarts it. The files are validated first (CONTRACT shapes, balanced journals, known references; ids unique within each id space, so a copy renamed per space may reuse a string across tables); a malformed directory raises `ValueError` with a path-free message and leaves the open episode untouched. `team_config` may set `max_steps` and `time_limit_s` only. Reward to the policy is 0 on every step and `info` holds only `episode_id`, `mode`, `max_steps` (reset) or `{}` (steps) |
| `reset(seed, {"mode": "train", "team_config": cfg})` | generates `generate(seed, cfg)`; with `episode_dir` it serves that episode. The terminal step returns the reward and `info` = `{valid, tp, fp, fn, precision, recall, f1, reward, inspection_steps}` |
| `step({"name": ..., "args": {...}})` | returns `(observation, reward, terminated, truncated, info)` with observation `{result, error, remaining_steps}`; `reset` returns `(first_observation, info)` with `{task, manifest, policy, remaining_steps}` (100 by default) |
| `score_episode(d, findings, inspection_steps)` | the shared matcher and reward on `d`'s truth; an invalid structure returns `return = -1` and nulls, and the reason goes to `judge_adapter.GRADER_LOG` (and to the JSON-lines file `$AUDITENV_GRADER_LOG`, if set) |

| `name` | `args` | `result` |
|---|---|---|
| `list_records` | `table` (`ledger`, `invoices`, `payments`, `fx`), `cursor` (null first), `limit` (≤ 50) | `{"records": [...], "next_cursor": str or null}`; invoice rows in listings omit `line_items` |
| `get_record` | `table`, `id` (row_id, invoice_id, payment_id or fx_id) | the record |
| `get_document` | `doc_id` | the invoice or payment document |
| `calculator` | `expression` (`+ - * / ( )` and decimals) | a decimal string, e.g. `"0.3"` for `0.1+0.2` |
| `submit` | `findings` (the findings.json object, §5 of the case) | `{"accepted": true}` with no correctness signal; it ends the episode |

Errors are `{"code", "message"}` with no paths, seeds or truth, and every one costs a step: `unknown_action` (also a
malformed envelope), `bad_params`, `unknown_table`, `not_found`, `calc_error`, `time_limit`, and in train mode
`invalid_findings`. Only `episode_over` (any action after the episode ended) is free and changes nothing. The submit is one of the 100 actions but not an inspection step; every earlier step,
including failed ones, is. 100 actions without a submit, or any action that arrives more than 60 s after reset (policy time included; that
action, even a submit, is not executed), end the episode as truncated with empty findings (defaults; the team
config may set both).

The four error types (`type` in truth and findings; amounts in base-currency minor units):

| case | `type` | `affected_ids` (a set) | expected amount |
|---|---|---|---|
| duplicate invoice | `duplicate_invoice` | original and duplicate invoice_id | AR debit of the later copy |
| missing or partial payment allocation | `payment_allocation` | invoice_id and payment_id | expected AR credit − credit posted |
| wrong conversion date or rate | `fx_error` | the invoice_id or payment_id | abs(posted − correct) |
| period error | `period_cutoff` | the invoice_id | AR debit posted inside the period for an invoice issued outside it |

Matching follows the jury's exact conventions: ids, type and currency are compared as exact strings, `affected_ids`
and `evidence_ids` as sets, an evidence id that is not a public record or document makes the finding a false
positive, the amount tolerance is `policy.findings.tolerance_minor` (0 in every episode), and the one-to-one
assignment is a maximum matching with the deterministic tie rule of the definitions (`auditenv/matcher.py`,
`docs/CONTRACT.md` §6).

Block 2 scenarios through the generator's config (`auditenv/jury.py`; the jury chooses the seeds):

| scenarios | config |
|---|---|
| D01–D05 clean | `{"errors": {}, "interacting": {"I1": 0, "I2": 0}, "ensure_distractors": true}` — adds an invoice paid in two parts (D02) and a refunded overpayment (D03) when the company has suitable full payments (with this config both appeared on all 200 seeds 0–199, default and hard); equal invoice totals (D04), unidentified receipts and records on the period's first and last day in company time (D05) are present anyway (200/200 on seeds 0–199, default and hard); foreign-currency documents in 199/200 default and 200/200 hard companies (a company whose entities all bill in the base currency has none) |
| D06–D08 duplicate invoice | `{"errors": {"duplicate_invoice": 1}, "interacting": {"I1": 0, "I2": 0}}` |
| D09 missing allocation | `{"errors": {"payment_allocation": 1}, "interacting": {"I1": 0, "I2": 0}, "allocation": "missing"}` |
| D10 partial allocation | the same with `"allocation": "partial"` |
| D11 either | the same without `"allocation"`: the variant is drawn, 60 % partial |
| D12–D13 conversion date or rate | `{"errors": {"fx_error": 1}, "interacting": {"I1": 0, "I2": 0}}` |
| D14–D15 period | `{"errors": {"period_cutoff": 1}, "interacting": {"I1": 0, "I2": 0}}` |
| D16–D18 interaction I1 | `{"errors": {}, "interacting": {"I1": 1, "I2": 0}}` — period-end foreign payment, partially allocated and converted at the wrong date |
| D19–D20 interaction I2 | `{"errors": {}, "interacting": {"I1": 0, "I2": 1}}` — next-period foreign invoice booked in the period at the wrong rate |

Any count up to 12 issues in total, `"difficulty": "hard"`, `n_invoices` and `distractors` combine with these.
`grader/provenance.json` records `generator_version`, `seed`, the normalised `config`, the `company` (currencies,
timezone, entities) and one entry per injection: `issue_id`, `type`, `scenario`, `description`, `documents_added`
and `changes`, each `{journal, before, after}` with the full ledger rows before and after (journal keys:
`inv:<invoice_id>`, `pay:<payment_id>`), so the books before the error can be rebuilt and checked independently
(`auditenv/verify.py` does exactly that). For the paired checks rename `row_id`, `doc_id`, `invoice_id`,
`payment_id`, `entity_id` consistently, including `invoice_refs`, truth and these journal keys; `fx_id` is the
key `date:source:target` and stays. Evidence ids share one namespace (`row_id`, `doc_id`, `fx_id`), so keep the new
`row_id` and `doc_id` values distinct from each other. For grading only, `task.txt` and `provenance.json` may be
absent and `fx.csv` may omit the `fx_id` column (it is then derived as `date:source:target`).

The jury's whole flow with our four baselines, each policy in its own process speaking only the jury protocol
(`auditenv.jury_run.JuryPolicy` is the baseline-policy adapter; the oracle is grader-side by definition):

```bash
uv run python -m auditenv.jury_run        # D01–D20, seeds 3001–3020
```

| policy | P | R | F1 | return | steps |
|---|---|---|---|---|---|
| random explorer | 0.000 | 0.000 | 0.000 | −1.000 | 33.0 |
| reconcile | 1.000 | 1.000 | 1.000 | 0.959 | 21.3 |
| flag-everything | 0.000 | 0.000 | 0.000 | −1.000 | 3.6 |
| oracle (grader-side) | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 |

`jury_run` prints the mean and maximum wall time per policy, including starting the policy's process; on the
development Mac every episode took under 0.06 s of the 60 s limit when the machine was otherwise idle.

Run the jury's four blocks locally: `uv run python -m unittest tests.test_judge_contract tests.test_judge_reward
tests.test_judge_scenarios tests.test_judge_paired` (C01–C20; Block 3 rows 1–20 and M01–M12; D01–D20; P01–P20).
They are part of `auditenv.check`.

### Out-of-process evaluation (closed run)

```bash
# organiser side: hidden episode list never reaches the agent
uv run python -m auditenv.server --episodes hidden.json --grader-log grader.jsonl   # keyed by the grader key file by default
```

`hidden.json` uses the `configs/*.json` format (`{"episodes": [{"seed": int, "config": {...}}, ...]}`) or
`{"seeds": [...], "config": {...}}`. Set the secret in the server process if a custom key is desired.
When `AUDITENV_SECRET` is unset, the server keys hidden episodes by default using a random grader key file
(`~/.auditenv/grader.key`, identical to `judge_adapter`), preventing seed recovery by enumeration, and prints
a reminder on stderr. `--public` uses the public generator without warning for lists that are public on purpose,
as in the check's smoke test and the demo.

`auditenv.server` communicates via JSON lines over stdin/stdout (`{"cmd": "reset"}`, `{"cmd": "step", "action": {...}}`, `{"cmd": "close"}`, which ends the session without a response line; framing errors: CONTRACT §4).
`auditenv.client.RemoteEnv` manages the subprocess and speaks the same `reset/step` API; with `--episodes`
the client cannot choose seeds, rewards are 0.0 and results are written only to `grader.jsonl`.

To verify the out-of-process harness locally without withheld data, `auditenv.check` runs a public two-episode smoke test (seeds 7001–7002, `flag_all` policy), which can also be run independently:
```bash
uv run python -c "from auditenv.check import run_remote; assert run_remote()"
```

### Other commands

With Python 3.11 installed, the checks below run offline. You can substitute `python3.11` for `uv run python` throughout.

```bash
uv run python -m unittest discover -s tests -t .     # tests only
uv run python -m unittest tests.test_env             # one module
uv run python -c "from auditenv.check import run_remote; assert run_remote()"  # public 2-episode out-of-process smoke
uv run python -m auditenv.verify --seeds 0-199       # verifier on 600 generated episodes
uv run python -m auditenv.verify --dir episodes/train  # verifier on the exported splits: 10 train,
uv run python -m auditenv.verify --dir episodes/dev    # 10 dev
uv run python -m auditenv.verify --dir episodes/hard   # and 20 hard episodes
uv run python -m auditenv.attack                     # 11,000 mutations on 20 fixed public seeds
uv run python -m tests.test_fuzz                     # action count and runtime
uv run python -m auditenv.check --json /tmp/auditenv-metrics.json
uv run python scripts/sync_docs.py --check --json /tmp/auditenv-metrics.json  # omit --check to update
uv run python -m auditenv.fuzz --seeds 0-999         # seed sweep: 3 000 episodes end to end
uv run python -m auditenv.fuzz --configs 3000        # sample valid parameter combinations (add --start N to replay from case N)
uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299   # every error findable in budget?
uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json  # failure analysis
uv run python -m auditenv.demo                       # narrated demo (see docs/DEMO.md)
uv run python -m auditenv.export --config configs/dev.json --out episodes/dev       # re-export files
uv run python -m auditenv.export --config configs/train.json --out episodes/train   #   (all three after
uv run python -m auditenv.export --config configs/eval_hard.json --out episodes/hard  #  a generator change)
uv run python scripts/mutate_reward.py               # 22 one-line mutants of matcher/reward, all must be caught
uv run python scripts/sensitivity.py                 # baseline ranking under other step costs / tolerances
uv run python scripts/shortcut_miner.py --report-only  # single-feature data-leak search (add --hard)
uv run python scripts/golden.py --check              # 80 golden hashes: generator drift detector
uv run python scripts/bench.py                       # timing benchmark
uv run python scripts/chart.py --json /tmp/auditenv-metrics.json  # docs/baselines.svg from the check --json output above
make check                                           # run one target, or combine targets: make test verify
make -n check test verify fuzz stress attack golden mutate miner bench sensitivity chart  # preview commands
```

To compare variants of the same seed, list each configuration as a separate episode in your config file. With `uv run python -m auditenv.analyze --config FILE --seeds N`, the failure report includes every entry for seed N.

## Repository layout

| path | what |
|---|---|
| `auditenv/generator.py`, `inject.py` | company history → correct ledger → errors, truth, provenance |
| `auditenv/env.py` | `AuditEnv` reset/step, tools, limits, modes |
| `auditenv/matcher.py`, `metrics.py`, `schema.py` | findings validation, normalisation, one-to-one matching, P/R/F1, reward |
| `auditenv/calculator.py` | arithmetic-only calculator (AST whitelist, Decimal) |
| `auditenv/verify.py` | independent data/truth verifier |
| `auditenv/transform.py` | benign transformation (new ids, permuted rows) |
| `judge_adapter.py` | the jury's connection point (generate_episode, make_env, score_episode) |
| `auditenv/jury.py`, `jury_run.py` | configs of the jury scenarios D01–D20; their flow end to end with our baselines |
| `auditenv/server.py`, `client.py` | out-of-process environment/grader |
| `auditenv/policies/` | baselines: random explorer, naive reconcile, reconcile, reconcile_hard, flag-all, oracle |
| `scripts/` | round-2 tools: mutation testing, sensitivity, shortcut miner, golden hashes, benchmark, chart, doc sync |
| `auditenv/run.py`, `check.py` | runner/trajectories, single check command |
| `auditenv/fuzz.py`, `analyze.py` | seed and configuration sweeps, policy stress tests, measured failure analysis |
| `auditenv/export.py`, `load.py`, `demo.py` | episode files on disk and back, narrated demo |
| `auditenv/experimental.py` | materiality-weighted reward, reported next to the shared one |
| `schemas/` | JSON Schemas: action, observation, findings, manifest, truth, trajectory step |
| `configs/` | versioned episode lists: train (1000–1009), dev (2000–2009), eval_example (9000–9019), eval_hard (9100–9119), train_hard (1100–1109) |
| `episodes/` | exported 10 train + 10 dev + 20 public hard episodes (`public/` for agents: task text, manifest, policy, four tables; `grader/` closed) |
| `trajectories.jsonl` | the case's training trajectories: `reconcile_hard` on the train and hard train splits (20 episodes) |
| `trajectories/` | training trajectories (JSONL) of reconcile, naive reconcile and random on the train split, and the same three plus reconcile_hard on the hard train split (`train_hard_*`) |
| `tests/` | Unit tests; `tests/test_jury.py` maps the jury checklist to tests |
| `docs/` | contract, design note, demo script, pitch outline, `CHECKS.md` (jury criteria → test → command → result) |
| `REVIEW.md` | jury-style review log: every defect found, its reproduction and fix |
| `HANDOFF.md`, `NIGHT.md`, `night/`, `scripts/night.sh`, `scripts/marathon.sh`, `scripts/deepseek_worker.py` | the team's development tooling (handoff notes, autonomous agent runs); not used by the check, which needs no network or paid API |

## Honest limitations

- Synthetic data only: all companies, people and money are fictional; the reward does not prove
  fitness for real audits.
- The generator is deterministic and public. Hidden episodes from `judge_adapter.generate_episode` and the
  closed server (`auditenv.server`) are keyed by `AUDITENV_SECRET` or, without it, by a random grader key file
  (`tests/test_grader_key.py`, `tests/test_server_secret.py`), so seeds can't be recovered and episodes can't be
  regenerated by the agent. `--public` marks an episode list as deliberately public.
- Simplified books: receivables only (no payables, tax or accruals), one base-currency ledger,
  fixed UTC offsets (no DST).
- Scriptable: a policy-aware rule script solves the default distribution (F1 1.0) and, with two extra
  rules, hard mode; the baselines measure how much distractors hurt shortcuts, not agent difficulty.
- Measured shortcut cues remain in default mode (`scripts/shortcut_miner.py`): "same entity, currency and
  total exactly twice" finds duplicates with precision 0.996, because default mode has no near-miss decoys
  (hard mode has them: 0.356). Each cue names a record, not the amount — scoring still needs reconciliation.
- Refunds book no realised FX difference and receivables no rounding plug: by the published rules a full
  foreign-currency refund can leave a customer's unapplied cash (2900) below zero in base currency (largest
  measured 7.3 % of the refund), although the credit is exactly 0 in the document currency (DESIGN §10).
- No model was trained; we make no claim about training improvements.
- Full list with measurements: [`docs/DESIGN.md`](docs/DESIGN.md) §10.

## License

MIT — see [`LICENSE`](LICENSE). All companies, people and amounts are synthetic.

## Contributing

Read [`HANDOFF.md`](HANDOFF.md) first. Branch, small commits, PR into `main`.
AI agent rules: [`CLAUDE.md`](CLAUDE.md).
