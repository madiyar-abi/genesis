# Demo video script (2 min 40 s)

Before recording, open two terminal tabs in the repository root with Python 3.11 and `uv` installed. In tab A run `env -u AUDITENV_SECRET uv run python -m auditenv.check`. Wait for `ALL CHECKS PASSED` and leave the results on screen. In tab B run the public example below and leave it at the first `[enter]` prompt. Both commands use the public companies even when the recording machine has a private grader key.

```bash
env -u AUDITENV_SECRET uv run python -m auditenv.demo --seed 2003 --pause
```

### 1. Introduce the company (0:00–0:25)

Select tab B and press Enter once. Point to the reporting period, record counts and budget in section 1.

> “Can a financial auditor find a real discrepancy among hundreds of plausible transactions and show its evidence? Here the company is fictional, so we can measure that. This episode covers September, with 326 ledger rows, 69 invoices and 100 steps to investigate and submit.”

### 2. Follow one payment (0:25–1:05)

Press Enter for section 2. Scroll up to steps 1–2 to show the two 50-row ledger pages. Scroll back to the submitted findings and point to `PAY-136430` in both `fx_error` and `payment_allocation`.

> “The policy reads the ledger in pages and opens candidate invoices to compare their line items. Look at this payment. One finding cites a dated exchange rate and a cash entry. The other cites the invoice and the entries showing where the payment went. Each claim gives its own amount in minor units and its own evidence. Four findings matched. The policy spent 21 steps inspecting records and one submitting. Only the inspections reduce its return, to 0.958.”

### 3. Check the explanation against the books (1:05–1:30)

Press Enter for section 3. Point to the two I1 findings. Both amounts are labelled in USD minor units. The FX error is 286 cents ($2.86) and the allocation error is 351,331 cents ($3,513.31). Scroll to their two `cause` lines.

> “Now we can see the grader’s records. Part of that payment went to unapplied cash. The cash entry also used the October 1 rate for a September 30 transaction. These are two distinct errors on one payment. The independent verifier reconstructs the clean books and checks which discrepancies the recorded changes introduce.”

### 4. Compare honest and misleading submissions (1:30–1:55)

Press Enter for section 4. Point to the oracle, the repeated oracle answer, and the two silence rows.

> “The oracle has the answer key and scores one. Repeating each finding in one submission drops the score to 0.333 because every repeated finding counts as a false positive. Silence scores minus one on these books. On the clean company below it scores one. The reward depends on what the evidence supports.”

### 5. Show what the policy sees (1:55–2:15)

Press Enter for section 5. Hold on the final `policy side` and `grader log` lines.

> “We run the same policy again with the grader in a separate process. Across 22 actions the policy saw only zero rewards and finished with empty info. The grader recorded four true positives, zero false positives, zero misses and a return of 0.958.”

### 6. Show the jury how to reproduce it (2:15–2:40)

Switch to tab A. Scroll to the dev and hard tables. Point at the `reconcile` F1 column in each, then scroll down to `ALL CHECKS PASSED`. Leave the single check command visible in the video caption.

> “One command runs the tests, independent verifier, baseline comparison and paired checks with renamed IDs and reordered records. Reconciliation reaches F1 of one on dev and about 0.75 on hard episodes. That measures the difficulty for this particular policy. You can run the same check locally with Python 3.11.”
