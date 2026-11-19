# Demo video script (2–3 min)

Setup before recording: terminal ~110 columns wide, large font, repo cloned, `uv` installed.
Run everything from the repo root. Every command below was run while writing this script; the outputs
quoted are what the default seed prints.

---

**1. Title (0:00–0:15)** — show `README.md` top in the browser/editor.

> "auditenv is a reproducible RL environment for training AI financial auditors. It generates a
> fictional company with hidden accounting errors, gives the agent read-only investigation tools, and
> grades its findings with a published matcher and reward. No network, no GPU, zero dependencies."

**2. One-command check (0:15–0:40)**

```bash
uv run python -m auditenv.check
```

Show the `[PASS]` lines, the dev baseline table and the hard-mode table.

> "This is the official check, one command. It runs 283 unit tests, an
> independent verifier that recomputes every hidden error from the records, the baseline
> policies, twenty paired reproducibility checks on default and twenty on hard episodes, a closed run
> in a separate process and the hard mode. The oracle reaches reward 1, the flag-everything attack
> gets −1, a rule script that is perfect on the default books drops to F1 0.75 in hard mode."

Optional, if time allows (tests only, ~10 s):

```bash
uv run python -m unittest tests.test_jury -v 2>&1 | tail -5
```

> "The jury's checklist is a test file: contract, leaks, reward, reproducibility, data."

Optional (~40 s): the reward tests really bite —

```bash
uv run python scripts/mutate_reward.py | tail -3
```

> "We break the matcher and the reward one line at a time — fifteen mutants, a wider tolerance, a dropped
> evidence check, swapped precision and recall. Every one is caught by the tests."

**3. A company and the first observation (0:40–1:00)**

```bash
uv run python -m auditenv.demo --pause
```

Section 1 on screen (press Enter to advance through the sections).

> "reset with a seed and a config gives the first observation: the task, the manifest — base
> currency, company timezone, period, record counts — the bookkeeping policy and a 100-step budget.
> The episode id is an HMAC; in a closed run the grader sets a secret key, so the seed can't be
> recovered and the episode can't be regenerated from our open-source code."

**4. The agent investigates (1:00–1:30)** — section 2.

> "A scripted reconciliation policy pages through the ledger, invoices, payments and FX rates —
> at most 50 rows per call — and opens only the invoices that might be duplicates. Every call costs a step.
> It submits four findings with the type, the affected ids, the amount in base currency and the
> evidence ids. Reward: 2·F1 − 1 minus 0.002 per step — here 0.958."

Point at the `payment_allocation` + `fx_error` pair on the same payment.

> "These two are an interacting error: a foreign-currency payment on the last evening of the month,
> partially allocated and converted at the next day's rate — the date in the bank's timezone."

**5. The grader's side (1:30–1:50)** — section 3.

> "The truth and the provenance are closed files. Each error was injected into an otherwise correct
> set of books, and the cause is recorded. Our verifier reverts these changes and confirms the books
> balance with zero discrepancies before the errors, and exactly the declared ones after."

**6. Reward cannot be gamed (1:50–2:20)** — section 4.

> "Same books, different answers. Silence: −1. Guessed ids: −1. Repeating the right answer
> lowers the score to 0.33 — duplicates are false positives. Flag-everything: −1. On a clean company,
> silence scores 1 and any accusation is punished. Wrong currency, partial evidence, amounts outside
> the tolerance — all false positives, all covered by tests."

**7. Closed evaluation (2:20–2:40)** — section 5.

> "For the closed run the environment and the grader live in another process that reads the hidden
> episode list itself. The policy only ever sees reward 0 and an empty info; the real score goes to
> the grader log."

**8. Wrap-up (2:40–3:00)** — show `docs/DESIGN.md` headings and the `configs/` + `episodes/` folders.

> "Four error types, two interacting scenarios, clean companies and look-alike distractors; ten train,
> ten dev and twenty hard episodes, trajectories, a seed sweep over three thousand episodes with zero
> problems, a shortcut miner that hunts for data leaks, and a design note with measured results —
> including a sensitivity table showing the baseline ranking doesn't depend on our reward constants —
> and honest limitations. Run it yourself with one command."

---

Fallbacks: if `uv` is missing, `python3.11 -m auditenv.demo` works the same. Another company:
`uv run python -m auditenv.demo --seed 2005`.
