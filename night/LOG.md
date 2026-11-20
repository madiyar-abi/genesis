# Round 17 log

2026-11-20 09:02 lead — Started round 17 (open improvement round, Claude Code lead). Wrote night/TASKS.md: T1–T4 worker evidence tasks on angles no earlier round covered (clone path with spaces/non-ASCII, timezone independence of exports, C-locale/ascii output encoding, config sweep on a new range). Next: three read-only red-team subagents (SPEC §04–§06 conformance of reward/contract; data ambiguity/solvability; observation-side leakage), findings → REVIEW.md Round 17 and tasks T5+. Assumption: deepseek still lacks an API key (r13–r16); lead takes T4 over after 1 h.
2026-11-20 09:08 lead — T98 rehearsed seed 2003. Four matches, 21 inspections, 0.958 return, closed policy saw [0.0]. Fresh reconcile micro-F1 1.000 dev and 0.752 hard. Script matches. Next: verify standalone exported task validation (T5).

2026-11-20 09:09 lead — T5. The verifier now rejects blank public/task.txt. Both empty and whitespace-only instructions previously passed standalone directory verification. The directory regressions pass, and all ten dev exports verify.

2026-11-20 09:10 lead — T6. The verifier checks integer exponents for every currency used in public records. Two mutations previously passed: a missing JPY exponent and JSON false in place of zero. Both now fail, and valid dev exports pass.
