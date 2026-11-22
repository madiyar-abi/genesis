2026-11-22 06:21 lead — Round 23 started (open improvement round, freeze 18:00). Read NIGHT/HANDOFF/CASE_UPDATES/REVIEW r20–r22/r22 archive. No known defect left from r22. Plan: clean-room checkers for what is not independently covered yet — Block 2 condition 1 rebuilt from provenance.json as README documents it (codex2 Y1), Block 1 C01–C20 from the published text with a separate policy process (codex1 X1), matcher differential from the published conventions (codex1 X2), engineering anchors self-score (codex2 Y2); rb re-runs r20–r22 checkers on unseen seeds + fresh-clone README walk; gemini sweeps on unseen seeds. Lead: baseline check, three red-team subagents, merge/fix, DEMO/PITCH. Assumption: unseen seed ranges 62000–72099 for checkers, 19000–20999 fuzz, 87000/90000 configs, 10000–11999 verify, 14000 stress, 34000–36000 jury_run (none used in r18–r22 logs).
2026-11-22 06:22 lead — L1 done: baseline `env -u AUDITENV_SECRET uv run python -m auditenv.check --json /tmp/r23-lead-check.json` exit 0, 565 tests, all gates, 55.7 s; sync_docs --check: no drift. L2 started: three read-only red-team subagents (contract/reward vs CASE_UPDATES, data ambiguity/evidence on seeds 73000+, jury-facing doc claims).
2026-11-22 06:22 lead — L4 done: `yes '' | uv run python -m auditenv.demo` exit 0; PAY-136430 286 and 351331 USD minor units, 21 inspections, terminal 0.958, grader TP 4 FP 0 FN 0, comparison table (oracle 1.000 … clean reconcile 0.958) — every number in docs/DEMO.md matches.

2026-11-22 06:29 codex2 — Y1 complete. `/usr/bin/time -p env PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r23.provenance_rebuild` exited 1 in 106.10 s. Rebuilt books and issue discrepancies held in 4,200/4,200 episodes. Evidence held in 4,002/4,200 under a set-only reading of CASE_UPDATES §Block 2. The 198 failures are in scenarios where the allocation can be missing entirely. The 2900 row alone omits the allocation to the target invoice. A foreign full-unapplied payment also needs the payment-date rate or a cash witness. For a merged payment, the set needs the other allocation rows and enough cash/FX evidence to isolate the target. The missing facts are available through the public ledger and FX tools, so the distinction is between what the listed evidence set proves and what can be reconstructed with wider tool access. No product changes made.

Assumptions: the strict check reconstructs the amount using only cited public records plus the manifest/policy. The documented I2 FX entry may have no changes; with a single I2 cutoff its inserted invoice journal identifies the same invoice without the truth label. With multiple I2 cutoff entries a change-less FX entry lacks a structured pairing key, outside the assigned matrix. The adapter uses the existing local grader key; same-seed fixture IDs require the same key.

Reproduction: `/usr/bin/time -p env PYTHONPATH=. env -u AUDITENV_SECRET uv run python -m night.r23.provenance_rebuild --seeds 72075 --scenario default --difficulty hard` exits 1 in 0.15 s. RCPT0013676's cited rate is 2025-03-02:CHF:EUR, while its cash date is 2025-03-15; its 2900 credit R2435 is 2704670 and its uncited cash row R2436 is 2704670. Base-currency merged example: seed 72077 hard default, PAY-667031 cites only 2900 row L02974 (2579500); cash L02975 (3665400) and the other AR credit L02976 (1085900, invoice 2610-347702) complete the journal.

| Scenario | Difficulty | Rebuilt | Discrepancy | Evidence |
|---|---|---:|---:|---:|
| default | default | 100/100 | 100/100 | 85/100 |
| default | hard | 100/100 | 100/100 | 79/100 |
| D01 | default | 100/100 | 100/100 | 100/100 |
| D01 | hard | 100/100 | 100/100 | 100/100 |
| D02 | default | 100/100 | 100/100 | 100/100 |
| D02 | hard | 100/100 | 100/100 | 100/100 |
| D03 | default | 100/100 | 100/100 | 100/100 |
| D03 | hard | 100/100 | 100/100 | 100/100 |
| D04 | default | 100/100 | 100/100 | 100/100 |
| D04 | hard | 100/100 | 100/100 | 100/100 |
| D05 | default | 100/100 | 100/100 | 100/100 |
| D05 | hard | 100/100 | 100/100 | 100/100 |
| D06 | default | 100/100 | 100/100 | 100/100 |
| D06 | hard | 100/100 | 100/100 | 100/100 |
| D07 | default | 100/100 | 100/100 | 100/100 |
| D07 | hard | 100/100 | 100/100 | 100/100 |
| D08 | default | 100/100 | 100/100 | 100/100 |
| D08 | hard | 100/100 | 100/100 | 100/100 |
| D09 | default | 100/100 | 100/100 | 44/100 |
| D09 | hard | 100/100 | 100/100 | 44/100 |
| D10 | default | 100/100 | 100/100 | 100/100 |
| D10 | hard | 100/100 | 100/100 | 100/100 |
| D11 | default | 100/100 | 100/100 | 79/100 |
| D11 | hard | 100/100 | 100/100 | 71/100 |
| D12 | default | 100/100 | 100/100 | 100/100 |
| D12 | hard | 100/100 | 100/100 | 100/100 |
| D13 | default | 100/100 | 100/100 | 100/100 |
| D13 | hard | 100/100 | 100/100 | 100/100 |
| D14 | default | 100/100 | 100/100 | 100/100 |
| D14 | hard | 100/100 | 100/100 | 100/100 |
| D15 | default | 100/100 | 100/100 | 100/100 |
| D15 | hard | 100/100 | 100/100 | 100/100 |
| D16 | default | 100/100 | 100/100 | 100/100 |
| D16 | hard | 100/100 | 100/100 | 100/100 |
| D17 | default | 100/100 | 100/100 | 100/100 |
| D17 | hard | 100/100 | 100/100 | 100/100 |
| D18 | default | 100/100 | 100/100 | 100/100 |
| D18 | hard | 100/100 | 100/100 | 100/100 |
| D19 | default | 100/100 | 100/100 | 100/100 |
| D19 | hard | 100/100 | 100/100 | 100/100 |
| D20 | default | 100/100 | 100/100 | 100/100 |
| D20 | hard | 100/100 | 100/100 | 100/100 |

First failed issue per episode, verbatim (episode is the scoring unit):

```text
FAIL seed=72007 default default evidence: ISS-3 ['2511-372006', 'PAY-080450']: no sufficient evidence set [['2025-10-20:USD:GBP', '2395cd5f', '4cc457e6', 'GL-004943']]
FAIL seed=72008 default default evidence: ISS-6 ['RCPT0619444', 'SI-2026-980173']: no sufficient evidence set [['2026-02-09:USD:GBP', 'D-01bcd1', 'D-08aba7', 'GL-004088']]
FAIL seed=72010 default default evidence: ISS-6 ['2603-892047', 'BNK-100294']: no sufficient evidence set [['2026-02-15:JPY:EUR', 'D-0990d7', 'D-0d4b00', 'GL-003947']]
FAIL seed=72011 default default evidence: ISS-5 ['2510-666508', 'RCPT0092837']: no sufficient evidence set [['036e2a78', '0b019027', '2025-09-19:GBP:EUR', 'L01025']]
FAIL seed=72012 default default evidence: ISS-8 ['RCPT0272927', 'SI-2025-884475']: no sufficient evidence set [['2025-01-05:GBP:KZT', 'D-06648e', 'D-0694d8', 'L01750']]
FAIL seed=72022 default default evidence: ISS-4 ['INV-429923', 'PAY-653551']: no sufficient evidence set [['2026-06-12:CHF:USD', 'DOC0167832', 'DOC0681907', 'GL-004410']]
FAIL seed=72044 default default evidence: ISS-3 ['BNK-954861', 'INV-396221']: no sufficient evidence set [['2025-04-02:JPY:KZT', 'D-031c73', 'D-04a263', 'R685']]
FAIL seed=72045 default default evidence: ISS-5 ['INV-305078', 'PAY-328051']: no sufficient evidence set [['2026-06-10:JPY:GBP', 'D-00497c', 'D-0baf1c', 'L04534']]
FAIL seed=72056 default default evidence: ISS-5 ['INV-355977', 'PAY-443473']: no sufficient evidence set [['2025-08-09:EUR:KZT', 'D-023ebe', 'D-063b3a', 'GL-001901']]
FAIL seed=72059 default default evidence: ISS-4 ['BNK-286267', 'F0646321']: no sufficient evidence set [['2026-03-15:USD:KZT', 'DOC0071827', 'DOC0391314', 'L03318']]
FAIL seed=72069 default default evidence: ISS-7 ['2511-627150', 'PAY-422376']: no sufficient evidence set [['2025-11-02:CHF:KZT', 'DOC0546689', 'DOC0958644', 'GL-002693']]
FAIL seed=72077 default default evidence: ISS-6 ['2608-192943', 'PAY-076588']: no sufficient evidence set [['2026-08-26:CHF:KZT', 'DOC0009206', 'DOC0789264', 'GL-003047']]
FAIL seed=72080 default default evidence: ISS-3 ['F0673078', 'PAY-044015']: no sufficient evidence set [['2026-12-23:CHF:GBP', 'L02376', 'ad6ad402', 'b36bf29c']]
FAIL seed=72087 default default evidence: ISS-2 ['PAY-334778', 'SI-2026-181336']: no sufficient evidence set [['2026-12-01:CHF:EUR', '89e0e317', 'GL-003101', 'e6224db8']]
FAIL seed=72096 default default evidence: ISS-5 ['2507-602824', 'BNK-569381']: no sufficient evidence set [['2025-07-02:KZT:EUR', 'DOC0155453', 'DOC0558837', 'GL-004445']]
FAIL seed=72008 default hard evidence: ISS-3 ['2611-053080', 'RCPT0712902']: no sufficient evidence set [['DOC0432551', 'DOC0909848', 'L03578']]
FAIL seed=72014 default hard evidence: ISS-5 ['BNK-228343', 'INV-733297']: no sufficient evidence set [['DOC0232972', 'DOC0409079', 'R1395']]
FAIL seed=72016 default hard evidence: ISS-4 ['PAY-339755', 'SI-2026-868262']: no sufficient evidence set [['1e23c780', '8647ba1b', 'L01523']]
FAIL seed=72022 default hard evidence: ISS-6 ['2508-274524', 'RCPT0423385']: no sufficient evidence set [['1e0699ab', '2025-08-10:USD:KZT', '9aa61e76', 'GL-004025']]
FAIL seed=72026 default hard evidence: ISS-9 ['BNK-922726', 'INV-747584']: no sufficient evidence set [['2025-06-10:USD:KZT', 'DOC0330211', 'DOC0943347', 'R3737']]
FAIL seed=72030 default hard evidence: ISS-4 ['BNK-787741', 'SI-2025-849341']: no sufficient evidence set [['2025-05-30:USD:EUR', 'D-016df7', 'D-09b30c', 'GL-004937']]
FAIL seed=72034 default hard evidence: ISS-6 ['INV-353718', 'PAY-280852']: no sufficient evidence set [['2026-07-18:JPY:USD', 'D-055db0', 'D-0e020b', 'R5164']]
FAIL seed=72037 default hard evidence: ISS-4 ['2510-934042', 'PAY-833556']: no sufficient evidence set [['2025-10-02:CHF:EUR', '33a3887a', '8465b132', 'L02481']]
FAIL seed=72042 default hard evidence: ISS-6 ['RCPT0878069', 'SI-2026-493407']: no sufficient evidence set [['2026-12-17:KZT:USD', 'D-056269', 'D-0e4a00', 'L02607']]
FAIL seed=72051 default hard evidence: ISS-5 ['BNK-475997', 'SI-2025-962998']: no sufficient evidence set [['2025-02-16:GBP:USD', '8f56ac8d', 'GL-004787', 'cd0cadd6']]
FAIL seed=72065 default hard evidence: ISS-3 ['F0452029', 'RCPT0073433']: no sufficient evidence set [['D-0052df', 'D-0bca41', 'R2773']]
FAIL seed=72068 default hard evidence: ISS-7 ['2512-855848', 'PAY-348616']: no sufficient evidence set [['DOC0108699', 'DOC0478204', 'R2927']]
FAIL seed=72070 default hard evidence: ISS-5 ['BNK-029852', 'SI-2026-432561']: no sufficient evidence set [['2026-04-15:CHF:KZT', '55804823', 'R1321', 'ed180dd8']]
FAIL seed=72071 default hard evidence: ISS-6 ['2503-169132', 'BNK-958943']: no sufficient evidence set [['2025-03-08:JPY:GBP', 'D-093c28', 'D-09dbbe', 'L03507']]
FAIL seed=72074 default hard evidence: ISS-9 ['BNK-566594', 'F0707785']: no sufficient evidence set [['2026-09-28:KZT:GBP', 'DOC0278730', 'DOC0984527', 'GL-005543']]
FAIL seed=72075 default hard evidence: ISS-3 ['INV-312653', 'RCPT0013676']: no sufficient evidence set [['2025-03-02:CHF:EUR', 'D-062313', 'D-0b1f54', 'R2435']]
FAIL seed=72077 default hard evidence: ISS-4 ['2610-849381', 'PAY-667031']: no sufficient evidence set [['56d48559', 'L02974', 'e4cb8d0f']]
FAIL seed=72082 default hard evidence: ISS-3 ['2605-850544', 'BNK-861402']: no sufficient evidence set [['04982e05', '2026-05-05:JPY:EUR', 'L01289', 'd941bd29']]
FAIL seed=72085 default hard evidence: ISS-6 ['F0702038', 'PAY-300958']: no sufficient evidence set [['2025-09-08:EUR:KZT', '4722b382', '7f46afe2', 'R2748']]
FAIL seed=72088 default hard evidence: ISS-5 ['BNK-542667', 'INV-221315']: no sufficient evidence set [['2025-05-03:CHF:EUR', 'D-0089e7', 'D-070bbc', 'R5349']]
FAIL seed=72089 default hard evidence: ISS-5 ['BNK-791795', 'INV-828684']: no sufficient evidence set [['2026-11-03:GBP:EUR', 'DOC0058867', 'DOC0392769', 'GL-001653']]
FAIL seed=72000 D09 default evidence: ISS-1 ['INV-271145', 'PAY-453849']: no sufficient evidence set [['2026-01-04:JPY:GBP', 'DOC0277072', 'DOC0707890', 'R3412']]
FAIL seed=72002 D09 default evidence: ISS-1 ['BNK-834484', 'SI-2026-115007']: no sufficient evidence set [['2026-10-22:GBP:EUR', 'D-0787f2', 'D-0b03de', 'GL-004783']]
FAIL seed=72003 D09 default evidence: ISS-1 ['2505-654881', 'BNK-750537']: no sufficient evidence set [['0a288f0e', 'R3213', 'fdc26a3d']]
FAIL seed=72004 D09 default evidence: ISS-1 ['2503-219840', 'RCPT0078635']: no sufficient evidence set [['2025-03-08:EUR:KZT', 'D-004326', 'D-011ba8', 'L03474']]
FAIL seed=72010 D09 default evidence: ISS-1 ['INV-415530', 'PAY-981432']: no sufficient evidence set [['2026-11-18:JPY:KZT', 'DOC0523935', 'DOC0890394', 'L03834']]
FAIL seed=72011 D09 default evidence: ISS-1 ['BNK-544002', 'SI-2026-756028']: no sufficient evidence set [['2026-05-02:GBP:KZT', 'D-032b4e', 'D-077ab2', 'GL-001598']]
FAIL seed=72012 D09 default evidence: ISS-1 ['2604-228586', 'PAY-131288']: no sufficient evidence set [['2026-04-15:USD:KZT', 'GL-001521', 'bdbcd2ef', 'f4dd73d1']]
FAIL seed=72013 D09 default evidence: ISS-1 ['F0862601', 'RCPT0156799']: no sufficient evidence set [['2025-10-21:CHF:USD', 'D-04c184', 'D-0a124d', 'L01913']]
FAIL seed=72017 D09 default evidence: ISS-1 ['2610-842467', 'RCPT0368271']: no sufficient evidence set [['2026-10-01:GBP:KZT', 'DOC0224013', 'DOC0431576', 'L04441']]
FAIL seed=72019 D09 default evidence: ISS-1 ['2606-189237', 'RCPT0932674']: no sufficient evidence set [['9d1a7cc9', '9f5780b8', 'GL-000721']]
FAIL seed=72020 D09 default evidence: ISS-1 ['BNK-071450', 'INV-262521']: no sufficient evidence set [['2026-09-13:JPY:KZT', '6e85b0e6', '77dc4c35', 'L00571']]
FAIL seed=72021 D09 default evidence: ISS-1 ['2608-060637', 'RCPT0293114']: no sufficient evidence set [['2026-08-07:CHF:KZT', '5898c72c', '665f191f', 'GL-004402']]
FAIL seed=72022 D09 default evidence: ISS-1 ['BNK-107355', 'INV-040448']: no sufficient evidence set [['2026-09-14:JPY:EUR', 'D-01ef6e', 'D-0d204f', 'GL-001452']]
FAIL seed=72023 D09 default evidence: ISS-1 ['RCPT0361231', 'SI-2026-383643']: no sufficient evidence set [['2026-06-05:USD:KZT', '83fcab5a', 'R287', 'a5ec8332']]
FAIL seed=72025 D09 default evidence: ISS-1 ['2506-068713', 'BNK-590506']: no sufficient evidence set [['2025-06-08:CHF:GBP', '60b272da', 'R805', 'd0dcb721']]
FAIL seed=72029 D09 default evidence: ISS-1 ['BNK-551345', 'SI-2026-811110']: no sufficient evidence set [['2026-07-30:CHF:GBP', 'DOC0019794', 'DOC0083062', 'GL-003992']]
FAIL seed=72030 D09 default evidence: ISS-1 ['RCPT0583820', 'SI-2025-028496']: no sufficient evidence set [['2025-03-01:EUR:USD', 'DOC0096340', 'DOC0701705', 'GL-002179']]
FAIL seed=72031 D09 default evidence: ISS-1 ['PAY-390083', 'SI-2025-802437']: no sufficient evidence set [['2025-01-28:CHF:USD', 'D-073453', 'D-0ef136', 'L04093']]
FAIL seed=72034 D09 default evidence: ISS-1 ['2604-800822', 'RCPT0839546']: no sufficient evidence set [['0a87da73', 'GL-002519', 'e765c06f']]
FAIL seed=72035 D09 default evidence: ISS-1 ['PAY-304369', 'SI-2025-402968']: no sufficient evidence set [['2025-09-01:USD:KZT', 'D-019c95', 'D-0ec397', 'GL-000229']]
FAIL seed=72036 D09 default evidence: ISS-1 ['BNK-732362', 'SI-2026-058245']: no sufficient evidence set [['2026-10-11:GBP:USD', 'DOC0521730', 'DOC0527228', 'GL-003632']]
FAIL seed=72039 D09 default evidence: ISS-1 ['F0428782', 'RCPT0513825']: no sufficient evidence set [['2026-05-13:CHF:EUR', 'R1867', 'ca3631fb', 'f90b6fc3']]
FAIL seed=72040 D09 default evidence: ISS-1 ['2609-980452', 'PAY-941418']: no sufficient evidence set [['2026-09-08:KZT:EUR', 'D-02683e', 'D-035425', 'GL-000372']]
FAIL seed=72041 D09 default evidence: ISS-1 ['INV-903497', 'RCPT0878071']: no sufficient evidence set [['06971700', '2026-05-23:CHF:KZT', '89cdf18c', 'R4145']]
FAIL seed=72042 D09 default evidence: ISS-1 ['2601-269556', 'PAY-970549']: no sufficient evidence set [['2026-01-24:GBP:KZT', 'DOC0023620', 'DOC0513464', 'GL-001558']]
FAIL seed=72044 D09 default evidence: ISS-1 ['INV-843408', 'PAY-393439']: no sufficient evidence set [['2025-07-05:KZT:EUR', '899a64d2', 'R3145', 'b8d4d274']]
FAIL seed=72045 D09 default evidence: ISS-1 ['F0372469', 'RCPT0635825']: no sufficient evidence set [['2026-10-19:KZT:GBP', 'DOC0887711', 'DOC0973371', 'L05175']]
FAIL seed=72048 D09 default evidence: ISS-1 ['F0870081', 'PAY-521689']: no sufficient evidence set [['2025-01-17:JPY:EUR', 'D-07aed3', 'D-08f707', 'GL-003926']]
FAIL seed=72049 D09 default evidence: ISS-1 ['BNK-793259', 'F0477933']: no sufficient evidence set [['2025-10-12:JPY:KZT', 'DOC0473476', 'DOC0821044', 'GL-004089']]
FAIL seed=72054 D09 default evidence: ISS-1 ['BNK-137208', 'SI-2025-015027']: no sufficient evidence set [['2025-05-19:EUR:USD', '9399f12c', 'GL-000953', 'a09c3d2c']]
FAIL seed=72055 D09 default evidence: ISS-1 ['BNK-272738', 'INV-498671']: no sufficient evidence set [['2025-09-27:CHF:USD', 'DOC0562289', 'DOC0924042', 'L02027']]
FAIL seed=72057 D09 default evidence: ISS-1 ['F0039140', 'RCPT0421176']: no sufficient evidence set [['2025-04-07:USD:EUR', 'DOC0050829', 'DOC0733066', 'R796']]
FAIL seed=72058 D09 default evidence: ISS-1 ['F0299987', 'RCPT0952337']: no sufficient evidence set [['2025-07-07:JPY:USD', 'D-0235d1', 'D-0c48da', 'L00291']]
FAIL seed=72061 D09 default evidence: ISS-1 ['2604-100633', 'BNK-324419']: no sufficient evidence set [['2026-04-17:JPY:USD', '689f62e3', '92ab20cf', 'L01153']]
FAIL seed=72062 D09 default evidence: ISS-1 ['2511-277578', 'PAY-360525']: no sufficient evidence set [['2025-10-08:JPY:GBP', 'D-07021a', 'D-0e88ba', 'L00536']]
FAIL seed=72064 D09 default evidence: ISS-1 ['2505-441149', 'BNK-956856']: no sufficient evidence set [['D-0330e0', 'D-0c3bfa', 'L01841']]
FAIL seed=72065 D09 default evidence: ISS-1 ['2506-309948', 'PAY-050237']: no sufficient evidence set [['2025-05-30:EUR:GBP', '53e2da6c', '5b9227c4', 'R5085']]
FAIL seed=72066 D09 default evidence: ISS-1 ['2603-700427', 'BNK-371985']: no sufficient evidence set [['2026-03-21:JPY:KZT', '29cc28e8', '859ee360', 'R3581']]
FAIL seed=72067 D09 default evidence: ISS-1 ['BNK-909036', 'F0252844']: no sufficient evidence set [['7011b531', '87d60b39', 'GL-000941']]
FAIL seed=72068 D09 default evidence: ISS-1 ['BNK-173329', 'INV-573014']: no sufficient evidence set [['2026-02-14:USD:GBP', 'D-095a7c', 'D-0b337e', 'L02287']]
FAIL seed=72069 D09 default evidence: ISS-1 ['2501-589651', 'PAY-411380']: no sufficient evidence set [['2024-12-08:JPY:KZT', 'D-03711c', 'D-086a8f', 'R437']]
FAIL seed=72070 D09 default evidence: ISS-1 ['F0227195', 'RCPT0047846']: no sufficient evidence set [['2026-05-15:GBP:KZT', 'D-0e2a18', 'D-0f08c3', 'R1234']]
FAIL seed=72071 D09 default evidence: ISS-1 ['BNK-759408', 'INV-408555']: no sufficient evidence set [['2025-01-30:KZT:USD', 'DOC0007547', 'DOC0146724', 'GL-003436']]
FAIL seed=72072 D09 default evidence: ISS-1 ['PAY-524958', 'SI-2025-649867']: no sufficient evidence set [['2025-03-08:JPY:EUR', '7ce7da68', '88d66987', 'GL-001565']]
FAIL seed=72075 D09 default evidence: ISS-1 ['BNK-351954', 'SI-2026-409494']: no sufficient evidence set [['16e263ee', '2026-10-11:JPY:GBP', '996160c6', 'GL-001262']]
FAIL seed=72076 D09 default evidence: ISS-1 ['F0325374', 'RCPT0394023']: no sufficient evidence set [['D-0a8b6e', 'D-0f163c', 'R1966']]
FAIL seed=72079 D09 default evidence: ISS-1 ['INV-617658', 'RCPT0273641']: no sufficient evidence set [['2025-11-12:GBP:EUR', 'DOC0423895', 'DOC0842484', 'L00505']]
FAIL seed=72081 D09 default evidence: ISS-1 ['2612-314429', 'BNK-476596']: no sufficient evidence set [['1167d206', 'R4432', 'a14e1fd9']]
FAIL seed=72082 D09 default evidence: ISS-1 ['2609-949878', 'BNK-135586']: no sufficient evidence set [['2026-09-01:USD:EUR', 'D-0ad63d', 'D-0b0922', 'R3137']]
FAIL seed=72085 D09 default evidence: ISS-1 ['RCPT0396527', 'SI-2026-232859']: no sufficient evidence set [['DOC0574570', 'DOC0668775', 'L04365']]
FAIL seed=72089 D09 default evidence: ISS-1 ['2502-165694', 'RCPT0237197']: no sufficient evidence set [['2025-01-11:JPY:EUR', 'D-039776', 'D-03ffce', 'GL-004922']]
FAIL seed=72090 D09 default evidence: ISS-1 ['2504-064199', 'PAY-497783']: no sufficient evidence set [['2025-03-02:CHF:KZT', 'D-0949f2', 'D-0c2c06', 'GL-004800']]
FAIL seed=72091 D09 default evidence: ISS-1 ['2609-359625', 'RCPT0681705']: no sufficient evidence set [['2026-09-10:EUR:GBP', 'DOC0843105', 'DOC0857038', 'GL-003361']]
FAIL seed=72093 D09 default evidence: ISS-1 ['INV-541184', 'RCPT0992397']: no sufficient evidence set [['6dd46336', 'L01143', 'f9c7fea7']]
FAIL seed=72094 D09 default evidence: ISS-1 ['2503-395892', 'BNK-971413']: no sufficient evidence set [['DOC0165104', 'DOC0602524', 'R3382']]
FAIL seed=72099 D09 default evidence: ISS-1 ['INV-601190', 'PAY-821517']: no sufficient evidence set [['15d3f9cf', '2026-08-08:CHF:GBP', 'L01649', 'a4c6480c']]
FAIL seed=72000 D09 hard evidence: ISS-1 ['BNK-972761', 'F0649093']: no sufficient evidence set [['2026-12-12:KZT:GBP', '31fa9e3a', 'R1790', 'b5b9eb06']]
FAIL seed=72001 D09 hard evidence: ISS-1 ['F0198176', 'PAY-678701']: no sufficient evidence set [['2026-07-02:GBP:USD', 'DOC0541816', 'DOC0594946', 'L02291']]
FAIL seed=72002 D09 hard evidence: ISS-1 ['F0098523', 'RCPT0500982']: no sufficient evidence set [['3a000318', 'GL-003864', 'ad663ec0']]
FAIL seed=72004 D09 hard evidence: ISS-1 ['PAY-477614', 'SI-2025-884487']: no sufficient evidence set [['9f29ca57', 'R5300', 'd03d9aec']]
FAIL seed=72008 D09 hard evidence: ISS-1 ['INV-201916', 'PAY-605358']: no sufficient evidence set [['346ff58e', '5c5fb202', 'L04689']]
FAIL seed=72014 D09 hard evidence: ISS-1 ['BNK-541206', 'SI-2025-766580']: no sufficient evidence set [['DOC0220678', 'DOC0331028', 'GL-001684']]
FAIL seed=72016 D09 hard evidence: ISS-1 ['BNK-355208', 'F0911343']: no sufficient evidence set [['2026-10-25:JPY:EUR', '210b5bad', 'GL-004873', 'fd125755']]
FAIL seed=72020 D09 hard evidence: ISS-1 ['2605-088495', 'RCPT0941855']: no sufficient evidence set [['103b1da3', 'GL-004422', 'b8b7e1fe']]
FAIL seed=72023 D09 hard evidence: ISS-1 ['F0379208', 'RCPT0890819']: no sufficient evidence set [['2025-03-20:GBP:USD', 'DOC0148538', 'DOC0564531', 'R2906']]
FAIL seed=72025 D09 hard evidence: ISS-1 ['BNK-539239', 'F0428761']: no sufficient evidence set [['2025-10-10:GBP:USD', 'D-0b49af', 'D-0e2ff5', 'GL-003583']]
FAIL seed=72026 D09 hard evidence: ISS-1 ['F0204950', 'RCPT0055690']: no sufficient evidence set [['2026-01-25:KZT:GBP', 'DOC0017413', 'DOC0309909', 'R1798']]
FAIL seed=72027 D09 hard evidence: ISS-1 ['2603-334920', 'RCPT0722621']: no sufficient evidence set [['2026-03-13:EUR:KZT', 'DOC0531621', 'DOC0659614', 'L02943']]
FAIL seed=72029 D09 hard evidence: ISS-1 ['2606-703098', 'BNK-665640']: no sufficient evidence set [['DOC0764968', 'DOC0963419', 'R2196']]
FAIL seed=72033 D09 hard evidence: ISS-1 ['2511-482053', 'RCPT0350944']: no sufficient evidence set [['2025-11-06:KZT:GBP', 'DOC0750002', 'DOC0825364', 'L01093']]
FAIL seed=72039 D09 hard evidence: ISS-1 ['RCPT0058758', 'SI-2026-985422']: no sufficient evidence set [['2026-02-14:JPY:GBP', 'D-04d797', 'D-07d97a', 'R3969']]
FAIL seed=72040 D09 hard evidence: ISS-1 ['PAY-652624', 'SI-2025-678745']: no sufficient evidence set [['2025-09-07:KZT:GBP', 'DOC0920754', 'DOC0945074', 'L00621']]
FAIL seed=72042 D09 hard evidence: ISS-1 ['2608-997426', 'PAY-543077']: no sufficient evidence set [['2026-08-18:USD:KZT', '2e29b1c9', 'GL-004574', 'e236046b']]
FAIL seed=72045 D09 hard evidence: ISS-1 ['2603-319977', 'PAY-045789']: no sufficient evidence set [['2026-02-21:EUR:USD', '4b82dbc9', 'L00717', 'c625b737']]
FAIL seed=72046 D09 hard evidence: ISS-1 ['BNK-281017', 'INV-841473']: no sufficient evidence set [['2026-02-22:GBP:EUR', '48244dea', 'R4466', 'f584210a']]
FAIL seed=72047 D09 hard evidence: ISS-1 ['2507-919253', 'RCPT0527023']: no sufficient evidence set [['2025-07-16:GBP:EUR', 'DOC0101327', 'DOC0968801', 'L03793']]
FAIL seed=72049 D09 hard evidence: ISS-1 ['F0349238', 'RCPT0437407']: no sufficient evidence set [['2025-01-01:JPY:USD', 'DOC0110560', 'DOC0234163', 'L03525']]
FAIL seed=72050 D09 hard evidence: ISS-1 ['BNK-114202', 'SI-2025-654310']: no sufficient evidence set [['2025-09-08:JPY:GBP', 'DOC0666849', 'DOC0733059', 'L01828']]
FAIL seed=72051 D09 hard evidence: ISS-1 ['2605-587896', 'PAY-332680']: no sufficient evidence set [['2026-05-13:CHF:GBP', 'DOC0265863', 'DOC0738718', 'R4104']]
FAIL seed=72053 D09 hard evidence: ISS-1 ['INV-495780', 'RCPT0134834']: no sufficient evidence set [['2026-05-21:KZT:EUR', 'D-077581', 'D-0dcf50', 'L04353']]
FAIL seed=72055 D09 hard evidence: ISS-1 ['RCPT0409302', 'SI-2026-787866']: no sufficient evidence set [['2026-10-02:USD:GBP', 'D-02a49a', 'D-0e223c', 'R1265']]
FAIL seed=72056 D09 hard evidence: ISS-1 ['2511-853485', 'BNK-578106']: no sufficient evidence set [['DOC0465139', 'DOC0762947', 'R3080']]
FAIL seed=72057 D09 hard evidence: ISS-1 ['BNK-000859', 'INV-364738']: no sufficient evidence set [['2026-03-01:USD:EUR', 'DOC0427925', 'DOC0428711', 'L02490']]
FAIL seed=72060 D09 hard evidence: ISS-1 ['BNK-594996', 'SI-2025-704821']: no sufficient evidence set [['2025-01-04:KZT:GBP', 'D-0aa4e0', 'D-0aa7ab', 'R1829']]
FAIL seed=72061 D09 hard evidence: ISS-1 ['F0176745', 'RCPT0360081']: no sufficient evidence set [['2025-04-01:USD:KZT', '46bed6e4', 'GL-003515', 'db20d8eb']]
FAIL seed=72062 D09 hard evidence: ISS-1 ['PAY-298520', 'SI-2026-122387']: no sufficient evidence set [['2026-08-21:USD:KZT', 'DOC0106521', 'DOC0128881', 'R1873']]
FAIL seed=72065 D09 hard evidence: ISS-1 ['F0978186', 'PAY-289024']: no sufficient evidence set [['1d4fdaa9', '2026-12-15:EUR:GBP', 'L03837', 'b933401e']]
FAIL seed=72066 D09 hard evidence: ISS-1 ['INV-399480', 'PAY-535166']: no sufficient evidence set [['2025-11-06:GBP:KZT', 'D-075e3e', 'D-0c282e', 'GL-002967']]
FAIL seed=72068 D09 hard evidence: ISS-1 ['2601-438850', 'PAY-474996']: no sufficient evidence set [['2025-12-15:KZT:USD', '85735481', 'GL-005006', 'ba46fdc9']]
FAIL seed=72069 D09 hard evidence: ISS-1 ['BNK-766769', 'INV-078677']: no sufficient evidence set [['2026-11-08:CHF:EUR', 'D-030fa9', 'D-0e5982', 'R4978']]
FAIL seed=72070 D09 hard evidence: ISS-1 ['BNK-256812', 'INV-080823']: no sufficient evidence set [['2026-02-23:EUR:KZT', 'DOC0609461', 'DOC0741639', 'R2584']]
FAIL seed=72071 D09 hard evidence: ISS-1 ['BNK-854142', 'INV-719074']: no sufficient evidence set [['2026-01-08:KZT:USD', '3feacad0', '4b25c47b', 'L03238']]
FAIL seed=72072 D09 hard evidence: ISS-1 ['F0750748', 'RCPT0451051']: no sufficient evidence set [['2026-10-24:JPY:EUR', 'D-0be92f', 'D-0d632a', 'R5265']]
FAIL seed=72074 D09 hard evidence: ISS-1 ['INV-406138', 'RCPT0267411']: no sufficient evidence set [['2026-08-11:GBP:KZT', '68fa3e72', '850da23a', 'R3874']]
FAIL seed=72075 D09 hard evidence: ISS-1 ['BNK-133449', 'INV-470694']: no sufficient evidence set [['2026-06-26:CHF:EUR', 'D-08d0a4', 'D-0bf552', 'R4454']]
FAIL seed=72076 D09 hard evidence: ISS-1 ['INV-355481', 'RCPT0404588']: no sufficient evidence set [['D-012b30', 'D-064ea8', 'R3862']]
FAIL seed=72077 D09 hard evidence: ISS-1 ['PAY-152538', 'SI-2025-049464']: no sufficient evidence set [['2025-11-01:JPY:USD', 'D-02eb3c', 'D-05e379', 'R4471']]
FAIL seed=72079 D09 hard evidence: ISS-1 ['PAY-450615', 'SI-2026-134462']: no sufficient evidence set [['2026-08-21:EUR:GBP', 'DOC0348342', 'DOC0622082', 'GL-002719']]
FAIL seed=72080 D09 hard evidence: ISS-1 ['RCPT0062279', 'SI-2025-078116']: no sufficient evidence set [['124b8114', 'GL-001573', 'abf11c8c']]
FAIL seed=72082 D09 hard evidence: ISS-1 ['2502-392142', 'PAY-092282']: no sufficient evidence set [['2025-02-12:EUR:USD', 'DOC0614874', 'DOC0721213', 'R4743']]
FAIL seed=72084 D09 hard evidence: ISS-1 ['F0717602', 'RCPT0095016']: no sufficient evidence set [['2025-08-07:USD:EUR', 'DOC0044928', 'DOC0653375', 'L02645']]
FAIL seed=72085 D09 hard evidence: ISS-1 ['F0234928', 'PAY-957151']: no sufficient evidence set [['2026-01-08:CHF:GBP', 'DOC0077934', 'DOC0735926', 'L04119']]
FAIL seed=72086 D09 hard evidence: ISS-1 ['BNK-858926', 'F0946942']: no sufficient evidence set [['2026-01-10:JPY:USD', 'D-038199', 'D-0c8cca', 'GL-003205']]
FAIL seed=72087 D09 hard evidence: ISS-1 ['F0911463', 'RCPT0113558']: no sufficient evidence set [['2026-01-19:GBP:USD', 'D-08ef6a', 'D-0c4a28', 'R4855']]
FAIL seed=72090 D09 hard evidence: ISS-1 ['PAY-273339', 'SI-2025-328922']: no sufficient evidence set [['2025-12-10:CHF:KZT', 'DOC0099069', 'DOC0977881', 'GL-003526']]
FAIL seed=72091 D09 hard evidence: ISS-1 ['PAY-358846', 'SI-2026-961581']: no sufficient evidence set [['2026-06-03:CHF:GBP', 'D-02a4f8', 'D-0c8839', 'R2621']]
FAIL seed=72092 D09 hard evidence: ISS-1 ['F0796543', 'RCPT0730152']: no sufficient evidence set [['5e891707', '8f2f11bd', 'R2504']]
FAIL seed=72093 D09 hard evidence: ISS-1 ['INV-235773', 'RCPT0699001']: no sufficient evidence set [['15679ba8', '2025-01-13:GBP:EUR', 'L01805', 'a28f76dc']]
FAIL seed=72095 D09 hard evidence: ISS-1 ['2509-016697', 'PAY-798568']: no sufficient evidence set [['2025-09-14:USD:EUR', 'L02477', 'c8d7a13b', 'cbd98c49']]
FAIL seed=72096 D09 hard evidence: ISS-1 ['BNK-401942', 'F0288799']: no sufficient evidence set [['2026-11-03:KZT:GBP', 'DOC0066438', 'DOC0406898', 'L01844']]
FAIL seed=72097 D09 hard evidence: ISS-1 ['F0082155', 'RCPT0200177']: no sufficient evidence set [['2026-10-02:CHF:USD', 'DOC0454679', 'DOC0685365', 'GL-003194']]
FAIL seed=72098 D09 hard evidence: ISS-1 ['2605-733207', 'PAY-844058']: no sufficient evidence set [['2026-05-05:EUR:GBP', '5a8ffe03', 'GL-005243', 'f4f317fe']]
FAIL seed=72000 D11 default evidence: ISS-1 ['RCPT0892767', 'SI-2025-133485']: no sufficient evidence set [['2025-02-26:KZT:EUR', 'DOC0055854', 'DOC0729052', 'GL-003179']]
FAIL seed=72013 D11 default evidence: ISS-1 ['RCPT0702961', 'SI-2026-183016']: no sufficient evidence set [['2026-07-29:GBP:EUR', 'DOC0239728', 'DOC0996228', 'L03996']]
FAIL seed=72017 D11 default evidence: ISS-1 ['2601-844623', 'PAY-419074']: no sufficient evidence set [['2025-12-22:CHF:USD', '2f2dfaff', '506f27f9', 'GL-001476']]
FAIL seed=72019 D11 default evidence: ISS-1 ['BNK-232840', 'SI-2025-964800']: no sufficient evidence set [['DOC0027372', 'DOC0373000', 'L03602']]
FAIL seed=72024 D11 default evidence: ISS-1 ['2611-585433', 'PAY-238617']: no sufficient evidence set [['2026-10-12:CHF:USD', 'D-03113c', 'D-0dcb6f', 'GL-002502']]
FAIL seed=72025 D11 default evidence: ISS-1 ['F0163964', 'PAY-922964']: no sufficient evidence set [['2026-03-12:GBP:EUR', 'DOC0072942', 'DOC0291507', 'GL-001449']]
FAIL seed=72026 D11 default evidence: ISS-1 ['BNK-633890', 'F0826896']: no sufficient evidence set [['2025-01-11:EUR:USD', 'DOC0691477', 'DOC0989907', 'L00433']]
FAIL seed=72028 D11 default evidence: ISS-1 ['F0985944', 'RCPT0156814']: no sufficient evidence set [['2025-11-01:GBP:KZT', 'D-0644df', 'D-0a47bf', 'GL-001511']]
FAIL seed=72039 D11 default evidence: ISS-1 ['F0015797', 'RCPT0000164']: no sufficient evidence set [['GL-001528', 'e0913b87', 'ffe47a7c']]
FAIL seed=72043 D11 default evidence: ISS-1 ['BNK-645196', 'SI-2025-474328']: no sufficient evidence set [['2025-11-10:EUR:KZT', 'DOC0361525', 'DOC0454411', 'GL-005257']]
FAIL seed=72053 D11 default evidence: ISS-1 ['2504-414402', 'PAY-546923']: no sufficient evidence set [['2025-02-28:KZT:EUR', 'D-085e5f', 'D-09dd27', 'GL-004203']]
FAIL seed=72061 D11 default evidence: ISS-1 ['F0237485', 'PAY-524690']: no sufficient evidence set [['D-04b5f1', 'D-0d879d', 'L00873']]
FAIL seed=72066 D11 default evidence: ISS-1 ['2607-103595', 'PAY-131167']: no sufficient evidence set [['2026-07-01:JPY:GBP', 'D-0b903f', 'D-0e85ce', 'R1790']]
FAIL seed=72073 D11 default evidence: ISS-1 ['BNK-024479', 'F0453065']: no sufficient evidence set [['2026-07-07:JPY:USD', 'DOC0387407', 'DOC0625613', 'L04485']]
FAIL seed=72074 D11 default evidence: ISS-1 ['2610-309086', 'PAY-620845']: no sufficient evidence set [['2026-10-13:CHF:USD', '6dd07c4b', 'R2693', 'fd583adc']]
FAIL seed=72083 D11 default evidence: ISS-1 ['BNK-322378', 'F0902716']: no sufficient evidence set [['2025-12-15:EUR:GBP', 'D-008231', 'D-01e54e', 'R1563']]
FAIL seed=72084 D11 default evidence: ISS-1 ['2608-675264', 'PAY-966536']: no sufficient evidence set [['2026-08-06:EUR:USD', '8502fbb6', 'GL-003649', 'bf63fddb']]
FAIL seed=72088 D11 default evidence: ISS-1 ['BNK-142561', 'SI-2026-860890']: no sufficient evidence set [['2026-04-26:GBP:EUR', 'D-049939', 'D-0e7252', 'GL-000320']]
FAIL seed=72089 D11 default evidence: ISS-1 ['BNK-811405', 'INV-285945']: no sufficient evidence set [['33499473', 'R4839', 'ed603c98']]
FAIL seed=72095 D11 default evidence: ISS-1 ['RCPT0502598', 'SI-2026-376664']: no sufficient evidence set [['2026-07-08:CHF:USD', 'D-075a1d', 'D-080fad', 'R263']]
FAIL seed=72096 D11 default evidence: ISS-1 ['INV-495236', 'RCPT0896283']: no sufficient evidence set [['D-01b101', 'D-05aaab', 'R5023']]
FAIL seed=72002 D11 hard evidence: ISS-1 ['INV-226436', 'PAY-751436']: no sufficient evidence set [['2025-03-29:EUR:USD', 'D-057d3f', 'D-0bac3a', 'R3152']]
FAIL seed=72011 D11 hard evidence: ISS-1 ['BNK-100117', 'INV-727862']: no sufficient evidence set [['2025-10-10:CHF:EUR', 'D-03b88c', 'D-0a1313', 'GL-005565']]
FAIL seed=72012 D11 hard evidence: ISS-1 ['F0799022', 'PAY-508591']: no sufficient evidence set [['2025-11-08:USD:GBP', 'DOC0228567', 'DOC0768304', 'L00948']]
FAIL seed=72014 D11 hard evidence: ISS-1 ['2611-177170', 'RCPT0752694']: no sufficient evidence set [['2026-11-06:CHF:USD', 'D-0d2051', 'D-0e8c85', 'L04777']]
FAIL seed=72023 D11 hard evidence: ISS-1 ['INV-696310', 'PAY-036007']: no sufficient evidence set [['2025-04-03:KZT:GBP', 'DOC0000772', 'DOC0799057', 'GL-001042']]
FAIL seed=72024 D11 hard evidence: ISS-1 ['2609-799908', 'RCPT0534682']: no sufficient evidence set [['2026-09-18:CHF:USD', '59339081', 'GL-004880', 'bb975326']]
FAIL seed=72027 D11 hard evidence: ISS-1 ['INV-327997', 'RCPT0475732']: no sufficient evidence set [['0fe636e5', '2026-10-13:EUR:KZT', 'L01339', 'f86a5aa3']]
FAIL seed=72029 D11 hard evidence: ISS-1 ['BNK-428778', 'SI-2025-134630']: no sufficient evidence set [['2025-04-09:EUR:KZT', '3cbad2ee', 'GL-001816', 'e880f7b0']]
FAIL seed=72036 D11 hard evidence: ISS-1 ['2603-561048', 'RCPT0819605']: no sufficient evidence set [['3453174b', 'GL-003960', 'ef12f361']]
FAIL seed=72042 D11 hard evidence: ISS-1 ['2506-699168', 'RCPT0172281']: no sufficient evidence set [['2025-06-16:EUR:KZT', 'DOC0172404', 'DOC0386687', 'GL-002929']]
FAIL seed=72045 D11 hard evidence: ISS-1 ['F0178320', 'PAY-006350']: no sufficient evidence set [['19a6248f', '2026-01-26:GBP:KZT', '67e183ba', 'GL-003843']]
FAIL seed=72046 D11 hard evidence: ISS-1 ['PAY-276740', 'SI-2026-183790']: no sufficient evidence set [['2026-06-16:GBP:KZT', 'DOC0191341', 'DOC0955405', 'GL-005517']]
FAIL seed=72047 D11 hard evidence: ISS-1 ['2609-000534', 'RCPT0745102']: no sufficient evidence set [['2026-09-07:GBP:USD', '46cbec99', 'L03873', 'ca062e7d']]
FAIL seed=72049 D11 hard evidence: ISS-1 ['INV-036015', 'PAY-425134']: no sufficient evidence set [['2026-09-21:GBP:KZT', 'D-051048', 'D-08de9c', 'R2088']]
FAIL seed=72050 D11 hard evidence: ISS-1 ['INV-852004', 'PAY-106831']: no sufficient evidence set [['2026-07-25:CHF:KZT', '22a0a311', '7855b295', 'R3672']]
FAIL seed=72055 D11 hard evidence: ISS-1 ['BNK-852314', 'F0619041']: no sufficient evidence set [['2024-12-31:USD:EUR', 'DOC0183854', 'DOC0929938', 'L03847']]
FAIL seed=72056 D11 hard evidence: ISS-1 ['F0313150', 'PAY-855761']: no sufficient evidence set [['D-0695d6', 'D-08f870', 'L04318']]
FAIL seed=72057 D11 hard evidence: ISS-1 ['PAY-355995', 'SI-2026-932022']: no sufficient evidence set [['1925c727', '2026-01-10:JPY:EUR', '8d99c37d', 'GL-001234']]
FAIL seed=72067 D11 hard evidence: ISS-1 ['2608-353690', 'PAY-801809']: no sufficient evidence set [['D-0081db', 'D-0a82e7', 'GL-001821']]
FAIL seed=72068 D11 hard evidence: ISS-1 ['PAY-246386', 'SI-2025-424863']: no sufficient evidence set [['2025-03-17:GBP:EUR', 'DOC0606029', 'DOC0638262', 'L02149']]
FAIL seed=72071 D11 hard evidence: ISS-1 ['2502-873429', 'BNK-541775']: no sufficient evidence set [['2025-02-12:USD:KZT', 'D-04757d', 'D-093f20', 'R5972']]
FAIL seed=72074 D11 hard evidence: ISS-1 ['BNK-031500', 'F0349974']: no sufficient evidence set [['2026-07-14:CHF:EUR', 'D-01bb3c', 'D-030c75', 'L03802']]
FAIL seed=72079 D11 hard evidence: ISS-1 ['INV-308006', 'PAY-898777']: no sufficient evidence set [['2025-04-06:EUR:USD', 'DOC0134410', 'DOC0210577', 'GL-001495']]
FAIL seed=72080 D11 hard evidence: ISS-1 ['F0240698', 'PAY-561611']: no sufficient evidence set [['2025-07-17:GBP:USD', '6702bf9b', 'R4500', 'acb30684']]
FAIL seed=72082 D11 hard evidence: ISS-1 ['2605-652553', 'BNK-997255']: no sufficient evidence set [['D-0286a5', 'D-06e737', 'L03647']]
FAIL seed=72083 D11 hard evidence: ISS-1 ['INV-332494', 'RCPT0392029']: no sufficient evidence set [['2026-08-31:CHF:KZT', 'D-03d36b', 'D-0455c9', 'R1531']]
FAIL seed=72094 D11 hard evidence: ISS-1 ['PAY-760809', 'SI-2026-349005']: no sufficient evidence set [['2026-08-01:CHF:KZT', 'DOC0330081', 'DOC0987622', 'GL-003512']]
FAIL seed=72095 D11 hard evidence: ISS-1 ['BNK-283793', 'INV-724591']: no sufficient evidence set [['2025-09-12:EUR:GBP', 'D-065373', 'D-0a001f', 'GL-003527']]
FAIL seed=72098 D11 hard evidence: ISS-1 ['2510-841255', 'RCPT0294964']: no sufficient evidence set [['6d744ffc', '96dcf69d', 'GL-005441']]
```

Next for codex2: Y2 engineering anchors.

2026-11-22 06:33 codex2 — Y2 complete. Engineering anchors (CASE_UPDATES lines 168–175), 10/10.

| Criterion | Score | Evidence |
|---|---:|---|
| One command | 2 | README.md:27–36. Fresh local `git clone --branch night/2026-11-22-r23-codex2 "$PWD" /tmp/r23-codex2/clone` at cc6dfae, exit 0, 0.64 s. From that clean checkout `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.check`, exit 0, 160.24 s during concurrent sweeps. It created its own .venv with CPython 3.11.14, reported `[PASS] unit tests — 565 tests, 0 failures, 0 errors` and `ALL CHECKS PASSED in 160.0 s`. |
| Versioned configuration | 2 | configs/*.json:2 pin config_version 1.0, configs/train.json:4–9 shows the seed/config form; episodes/train/ep_f1d31e7a39cc/public/manifest.json:16 records generator_version 1.0.0; .python-version:1 pins 3.11; uv.lock:1–8 records revision 3, 3.11.*, package 1.0.0. On cc6dfae all 40 episode folders and their indexes regenerated and matched recursively byte for byte. |
| Trajectories | 2 | trajectories.jsonl:1–674 and README.md:201–216. `/usr/bin/time -p env -u AUDITENV_SECRET uv run python ../scan_trajectories.py` from the clone, exit 0, 0.79 s. `674 rows, 20 episodes, 20 terminal flags, 0 nonpublic affected IDs, 0 unexpected observations`. Every row has all seven fields and each episode has sequential steps from reset through its one terminal flag. |
| Measured failure analysis | 2 | docs/DESIGN.md:258–274 names errors and causes, including treating legitimate unapplied cash as allocation findings. `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.analyze --policy naive_reconcile --config configs/dev.json`, exit 0, 0.33 s: allocation 2 TP/6 FN, I1 0 TP/2 FN, 101 FP. Same command with `--policy reconcile`, exit 0, 0.21 s: allocation 8 TP/0 FN, I1 2 TP/0 FN, 0 FP and F1 1.0. The named failure, cause and re-check are evidenced. |
| Honest limitations | 2 | README.md:451–468 and docs/DESIGN.md:351 onward explicitly discuss synthetic scope, rule-script solvability, observable shortcuts and no claim of learning gains. `/usr/bin/time -p env -u AUDITENV_SECRET uv run python scripts/shortcut_miner.py --seeds 0-999 --report-only`, exit 0 in 53.03 s, and with `--hard`, exit 0 in 130.39 s: 2,000 episodes per mode, same-entity/currency/total-count-two precision 0.996 (4910/4928) and 0.356 (4874/13680), respectively. The documented duplicate heuristic is reproduced. |

The split reproduction from the clone used `/usr/bin/time -p env -u AUDITENV_SECRET uv run python -m auditenv.export --config configs/<cfg>.json --out ../y2-<split>`, then `/usr/bin/time -p diff -r episodes/<split> ../y2-<split>`. train/train: export 10 episodes, exit 0, 0.29 s, diff exit 0, 0.01 s. dev/dev: export 10, exit 0, 0.17 s, diff exit 0, 0.02 s. hard/eval_hard: export 20, exit 0, 0.62 s, diff exit 0, 0.04 s. Exported 10 hard-train episodes using `configs/train_hard.json` and `../y2-hard_train` for the scan (exit 0, 0.31 s).

Observation scan matches each episode with the two train exports. It searches observation keys and string leaves for `truth`, `seed`, `provenance`, `evidence_sets`, `expected_amount_minor`, `issue_id`, `ISS-`, concrete issue IDs and any affected ID absent from the public records. It compares every expected amount against JSON integer leaves and decimal digit tokens in string leaves. Assumption: identical amounts in public records are legitimate values. The scan finds 240 such integer coincidences and six hits of 210, which equals the manifest's public FX count (one manifest field, five list totals). None occur in a grader field.

Two stale figures for the lead to correct. In docs/DESIGN.md:262 and :265, update naive FP total 102 → 101 and allocation FP 27 → 26 (zip terminal findings with grader labels on the dev config and count unmatched findings by submitted type: allocation 26, duplicate 30, FX 27, cutoff 18, including 22 on clean companies). In docs/DESIGN.md:365, update the default 2900 four-or-more amount-frequency cue from 0.964 (214/222) to 0.949 (240/253), from the current miner's `amount_count_in_table@acct2900 | 4+` row. The scores above use the published qualitative anchors and confirmed scenario behavior. Product and jury-facing files were left to the lead.

Next for codex2: idle until another tagged task is assigned.
2026-11-22 06:37 lead — L2 (a) contract/reward red-team: every C01–C20 row, Block 3 rows 1–20 and M01–M12 reproduce exactly (1e-9) through judge_adapter. Two confirmed text mismatches, fixed test-first in 5700626: (1) closed-mode submit with an invalid structure (31 findings, non-object findings) answered {"accepted": true} while the grader logged -1 — CASE_UPDATES line 58 allows only {"accepted": true} or a bounded structure error; eval now returns error invalid_findings (structure only, never truth; result null, reward 0, info {}, terminated) — regression tests.test_judge_contract...test_invalid_submit_gets_a_bounded_structure_error_not_accepted failed before; (2) reset on a copy without task.txt (the case's file list has none) gave task "" (C02) — the loader falls back to generator.TASK_TEXT (+TASK_HARD when policy.ledger publishes credit_note); verify --dir still rejects an export without task.txt — regression tests.test_load_redteam...test_missing_task_text_falls_back_to_the_published_task failed before. CONTRACT §4 and README adapter table updated. check exit 0, 567 tests; golden 80/80; sync_docs no drift. Not changed (logged as decisions): limit=null is bad_params (absent limit = 50; schema says integer); explanation stays optional (CONTRACT §5; no published row tests its absence and requiring it could make a jury policy's finding a structure error).
2026-11-22 06:37 lead — L2 (c) docs-claims red-team: 9 stale prose numbers after round 22, fixed in f7fae58 — DESIGN §9 naive FPs 102→101 (26 allocation), seed sweep 1 986/1 014 and random>0 on 247, §10 miner 0.458→0.454 and 0.964 (214/222)→0.949 (240/253; hard 0.835), a test path; CHECKS reconcile hard 0.752→0.755, 2,563/2,576 postings, 7,057/7,197 rows, 16 limitations. Doc tests OK.
