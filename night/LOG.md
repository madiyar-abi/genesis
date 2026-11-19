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
2026-11-20 00:39 gemini3 — T3: aligned README.md I2 description with inject.py rate fallback ('converted using the booking-date rate or an earlier fallback rate'); verified auditenv.check description against check.py gates (added naive reconciliation to dev baselines list and clarified paired replay policies reconcile_hard and random); verified split descriptions across configs/ (train, train_hard, dev, eval_example, eval_hard) and episodes/ (train, dev, hard public/grader splits). Ran auditenv.check and sync_docs.py --check: ALL CHECKS PASSED (311 unit tests, 0 failures), docs in sync. Next: IDLE.
2026-11-20 00:40 lead — Reviewed T2 against the generator: the threshold compares converted invoice totals in base minor units. Clarified the threshold and final default in the contract and synchronized the injector docstring.
2026-11-20 00:40 lead — T3 README claims matched split configs and baseline and paired runs. Correction to the T2 worker log: MIN_DIFF is 10 minor units, as documented in the reviewed contract.
2026-11-20 00:41 gemini1 — T1 completed: updated Books.discrepancies in auditenv/verify.py to reject any out-of-period posting across all public and reverted ledger rows using company-local dates (self.in_period). Created tests/test_posting_period.py covering clean seed 0 pass, revenue credit moved to 2099 failure, expense/payment out-of-period failures, pre-injection out-of-period failure, and boundary timestamp checks in company local timezone (5/5 tests pass). All 316 unit tests and all check gates pass. Next: IDLE.
2026-11-20 00:43 lead — Reviewed the final four worker tips and SPEC §§01–13. Final official check passed 316 tests, both sets of 20 pairs and remote isolation. All 40 indexed exports verified. Default and hard sweeps passed 3000 and 600 episodes; all 80 hashes matched, 15/15 mutants were caught, and 11000 reward mutations produced zero violations. Miner reproduced 16 default and 11 hard flags. No new Docker run locally. Recording, slides, credential revocation and access/submission remain with the team; the marathon handles PR and CI.
