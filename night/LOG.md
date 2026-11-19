2026-11-20 00:32 lead — Round 6 began with a clean branch and no task list. Four worker assignments pushed. T5 reproduced swapped rate labels on clean seed 0; enforced CONTRACT § FX identifier and unique rate tuples. Both regression tests and official check passed. Existing demo and generator stay compatible. T1–T4 and jury materials follow.
2026-11-20 00:33 lead — T6 rehearsed docs/DEMO.md using its public command and five Enter inputs. PAY-136430 discrepancies were 286 and 351331 minor units; the closed grader recorded TP 4 FP 0 FN 0 and 0.958. The recording script matched throughout.
2026-11-20 00:33 lead — T7 corrected I2 rate selection on slide four after reproducing seed 180. All ten slides checked, official check and docs sync passed. Prior handoff recorded an unresolved DeepSeek worktree; delegated T4 to a fallback on its named branch pending confirmation of branch availability.

2026-11-20 00:33 · deepseek (lead fallback) · T4 passed. Seeds 0–99 generated 26,659 default and 26,242 hard FX rows in 200 heavy episodes. Every date/source/target tuple was unique within its episode and every FX ID matched its tuple. No exceptions. The lead integrates the worker branch. Reproduction command:

```sh
uv run python - <<'PY'
from auditenv.fuzz import HEAVY
from auditenv.generator import generate

for difficulty in ("default", "hard"):
    count = 0
    config = HEAVY if difficulty == "default" else {**HEAVY, "difficulty": difficulty}
    for seed in range(100):
        rows = generate(seed, config)["tables"]["fx"]
        keys = [(r["date"], r["source_currency"], r["target_currency"]) for r in rows]
        assert len(keys) == len(set(keys)), (difficulty, seed, "duplicate FX key")
        assert all(r["fx_id"] == ":".join(k) for r, k in zip(rows, keys)), (difficulty, seed, "FX ID")
        count += len(rows)
    print(difficulty, "100 episodes", count, "FX rows")
PY
```

2026-11-20 00:39 gemini2 — T2 completed: verified that I2 can use an earlier rate than the booking date when abs(conv(booking) - conv(inv._cdate)) < MIN_DIFF (100 minor units). Verified injector fallback in auditenv/inject.py (line 259) across 500 seeds with I2: in 498 episodes (99.6%) the booking-date rate was used, and in 2 episodes (0.4%, seeds 180 and 497) it fell back to 1 day earlier (booking - 1d, 2025-02-27 instead of 2025-02-28). Updated docs/CONTRACT.md and docs/DESIGN.md to describe actual date selection (booking date or earlier fallback day 1, 2, or 4 days before booking). All 311 unit tests pass. Next: IDLE.
2026-11-20 00:40 lead — Reviewed T2 against the generator: the threshold compares converted invoice totals in base minor units. Clarified the threshold and final default in the contract and synchronized the injector docstring.
