# Round 13

- [ ] T1 (lead) Include the public 20-company default evaluation in the official diagnostics — files: auditenv/check.py, tests/test_eval_diagnostics.py, REVIEW.md — accept: all required policies run on eval_example, console and JSON identify that split, dev and hard results remain available.
- [ ] T2 (gemini1) Document the official evaluation split in the jury check map — files: docs/CHECKS.md — accept: distinguish public default evaluation from dev and hidden seeds and identify all six diagnostics.
- [ ] T3 (gemini2) Audit design benchmark claims against measured workload — files: docs/DESIGN.md — accept: correct stale test count at line 221 and reconcile scope with actual verifier/benchmark commands.
- [ ] T4 (gemini3) Independently reproduce the default evaluation policy counts and mean returns — files: night/LOG.md — accept: report four required baselines across all 20 public default eval companies.
- [ ] T5 (deepseek) Verify docs tooling tolerates a third metrics split — files: night/LOG.md — accept: use metrics with eval_example alongside dev/hard and verify sync_docs and chart generation.
- [ ] T8 (lead) Reject malformed JSON seed types and falsey non-object config in episode lists and server resets — files: auditenv/run.py, auditenv/server.py, focused tests — accept: valid selections preserve order and malformed inputs fail explicitly.
- [x] T6 (lead) Rehearse the 2–3 minute recording script — files: docs/DEMO.md — accept: run the prescribed inputs and verify the selected evidence and closed-run totals.
- [ ] T7 (lead) Review slide outline and jury handoff — files: docs/PITCH.md, README.md, HANDOFF.md — accept: public evaluation clearly identified, numeric claims verified, full offline suite and SPEC review passed.
