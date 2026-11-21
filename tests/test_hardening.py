"""Regression tests for the jury-style review findings."""
import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from auditenv.client import RemoteEnv
from auditenv.env import AuditEnv
from auditenv.generator import generate
from auditenv.matcher import grade_episode
from auditenv.verify import verify_episode


def dumps(ep):
    return json.dumps(ep, sort_keys=True)


class HardeningTest(unittest.TestCase):
    def test_secret_keys_episode_id_and_content(self):
        public = generate(7345123, {"errors": {"fx_error": 1}})
        with mock.patch.dict(os.environ, {"AUDITENV_SECRET": "grader-only-key"}):
            hidden = generate(7345123, {"errors": {"fx_error": 1}})
            again = generate(7345123, {"errors": {"fx_error": 1}})
        self.assertNotEqual(public["episode_id"], hidden["episode_id"])
        self.assertNotEqual(public["tables"]["ledger"], hidden["tables"]["ledger"])
        self.assertEqual(dumps(hidden), dumps(again))  # still reproducible for the key holder
        self.assertEqual(verify_episode(hidden), [])

    def test_equivalent_configs_same_company(self):
        a = generate(3, {"errors": {"fx_error": 1}})
        b = generate(3, {"errors": {"fx_error": 1, "duplicate_invoice": 0}, "interacting": {}})
        self.assertEqual(dumps(a), dumps(b))
        self.assertEqual(dumps(generate(3, {})), dumps(generate(3, {"distractors": True})))

    def test_crash_config_and_min_documents(self):
        cfg = {"errors": {"duplicate_invoice": 9, "fx_error": 2}, "n_invoices": 10, "distractors": False}
        self.assertEqual(verify_episode(generate(61, cfg)), [])
        for seed in range(30):
            ep = generate(seed, {"errors": {}, "n_invoices": 10, "distractors": False})
            self.assertGreaterEqual(ep["manifest"]["counts"]["documents"], 20)

    def test_malformed_table_never_crashes_or_overruns(self):
        env = AuditEnv()
        env.reset(1, {"errors": {}})
        for i in range(100):
            obs, r, term, trunc, info = env.step({"type": "list_records", "table": ["ledger"]})
            self.assertEqual(obs["error"]["code"], "unknown_table")
        self.assertTrue(trunc)
        obs, r, term, trunc, info = env.step({"type": "submit", "findings": {}})
        self.assertEqual(obs["error"]["code"], "episode_over")

    def test_server_grades_abandoned_episodes(self):
        with tempfile.TemporaryDirectory() as d:
            log, hidden = os.path.join(d, "g.jsonl"), os.path.join(d, "h.json")
            with open(hidden, "w") as fh:
                json.dump({"seeds": [1, 2, 3], "config": {"errors": {"fx_error": 1}}}, fh)
            with RemoteEnv(grader_log=log, episodes=hidden, public=True) as env:
                env.reset()
                env.step({"type": "list_records", "table": "ledger"})
                env.reset()  # skip episode 1 mid-way
                env.reset()  # skip episode 2 without a step; episode 3 left open at close
            with open(log) as fh:
                recs = [json.loads(line) for line in fh]
            self.assertEqual([r["end"] for r in recs], ["abandoned"] * 3)
            self.assertTrue(all(r["reward"] < 0 for r in recs))

    def test_validator_matches_published_schema(self):
        from auditenv.schema import validate_findings
        from tests.test_schemas import _matches, load_schemas
        schemas = load_schemas()
        f = {"type": "fx_error", "affected_ids": ["X"], "claimed_amount_minor": 1, "currency": "USD",
             "evidence_ids": []}
        cases = [({"episode_id": "e", "findings": [f]}, True),
                 ({"episode_id": "e", "findings": [f], "extra": 1}, False)]
        # any currency string is structurally valid (it just never matches another currency); a non-string is not
        cases += [({"episode_id": "e", "findings": [{**f, "currency": cur}]}, True)
                  for cur in ("ÄÖÜ", "ＵＳＤ", "usd", "US1")]
        cases += [({"episode_id": "e", "findings": [{**f, "currency": cur}]}, False) for cur in (None, 840)]
        for sub, valid in cases:
            with self.subTest(sub=sub):
                self.assertEqual(validate_findings(sub, "e") is None, valid)
                self.assertEqual(_matches(sub, schemas["findings.schema.json"], "findings.schema.json", schemas), valid)

    def test_server_accepts_config_episode_lists(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "g.jsonl")
            with RemoteEnv(grader_log=log, episodes=os.path.join(root, "configs", "eval_example.json"),
                           public=True) as env:
                obs, info = env.reset()
                self.assertEqual(info["mode"], "eval")


if __name__ == "__main__":
    unittest.main()


class AllocationEvidenceTest(unittest.TestCase):
    """REVIEW.md #1: every payment_allocation evidence set must reproduce the amount on its own."""

    CFG = {"errors": {"payment_allocation": 3}, "interacting": {"I1": 1}}

    def test_partial_allocation_needs_the_posted_ar_credit(self):
        seen_partial = seen_full = 0
        for seed in range(40):
            ep = generate(seed, self.CFG)
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            for iss in ep["truth"]["issues"]:
                if iss["type"] != "payment_allocation":
                    continue
                accounts = {rows[i]["account"] for s in iss["evidence_sets"] for i in s if i in rows}
                inv_id, pay_id = sorted(iss["affected_ids"], key=lambda i: i not in {r["invoice_id"] for r in
                                                                                      ep["tables"]["invoices"]})
                posted = any(r["account"] == "1200" and r["payment_id"] == pay_id and r["invoice_id"] == inv_id
                             for r in ep["tables"]["ledger"])
                if posted:  # partial: only the AR-row set reproduces expected - posted
                    seen_partial += 1
                    self.assertEqual(accounts, {"1200"}, (seed, iss["issue_id"]))
                else:
                    seen_full += 1
                    self.assertEqual(accounts, {"2900"}, (seed, iss["issue_id"]))
            self.assertEqual(verify_episode(ep), [], seed)
        self.assertGreater(seen_partial, 10)
        self.assertGreater(seen_full, 10)

    def test_verifier_rejects_an_insufficient_2900_set(self):
        for seed in range(40):
            ep = generate(seed, self.CFG)
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            for iss in ep["truth"]["issues"]:
                s = iss["evidence_sets"][0]
                if iss["type"] != "payment_allocation" or not any(rows.get(i, {}).get("account") == "1200" for i in s):
                    continue
                pay_id = next(i for i in iss["affected_ids"] if i in {p["payment_id"] for p in ep["tables"]["payments"]})
                unapplied = next((r["row_id"] for r in ep["tables"]["ledger"]
                                  if r["account"] == "2900" and r["payment_id"] == pay_id), None)
                if unapplied is None:
                    continue
                iss["evidence_sets"] = [[unapplied if rows.get(i, {}).get("account") == "1200" else i for i in s]]
                self.assertTrue(any("does not reproduce" in p for p in verify_episode(ep)))
                return
        self.fail("no partial allocation with a 2900 row found")


class DuplicateEvidenceTest(unittest.TestCase):
    """D1: duplicate_invoice evidence requires booking rows for both invoices plus both docs."""

    def test_duplicate_evidence_sets_contain_all_four_alternatives(self):
        """Positive test: default and hard episodes provide all 4 booking row combinations."""
        for difficulty in ("default", "hard"):
            cfg = {"errors": {"duplicate_invoice": 2}}
            if difficulty == "hard":
                cfg["difficulty"] = "hard"
            for seed in range(20):
                ep = generate(seed, cfg)
                self.assertEqual(verify_episode(ep), [], (difficulty, seed))
                rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
                docs = {d["doc_id"]: d for d in ep["tables"]["invoices"]}
                for iss in ep["truth"]["issues"]:
                    if iss["type"] != "duplicate_invoice":
                        continue
                    self.assertEqual(len(iss["evidence_sets"]), 4, (difficulty, seed, iss["issue_id"]))
                    inv_ids = sorted(iss["affected_ids"])
                    for s in iss["evidence_sets"]:
                        ev_docs = [docs[i] for i in s if i in docs]
                        ev_rows = [rows[i] for i in s if i in rows]
                        self.assertEqual(len(ev_docs), 2)
                        self.assertEqual(len(ev_rows), 2)
                        # Docs match affected_ids
                        self.assertEqual(sorted(d["invoice_id"] for d in ev_docs), inv_ids)
                        # Rows match affected_ids, are booking rows (payment_id is None, account 1200 or 4000)
                        self.assertEqual(sorted(r["invoice_id"] for r in ev_rows), inv_ids)
                        for r in ev_rows:
                            self.assertIsNone(r.get("payment_id"))
                            self.assertIn(r["account"], ("1200", "4000"))
                        # Test each alternative independently matches with grade()
                        sub = {"episode_id": ep["manifest"]["episode_id"],
                               "findings": [{"type": "duplicate_invoice",
                                             "affected_ids": inv_ids,
                                             "claimed_amount_minor": iss["expected_amount_minor"],
                                             "currency": iss["currency"],
                                             "evidence_ids": list(s),
                                             "explanation": "positive test"}]}
                        res = grade_episode(ep, sub, 0)
                        self.assertEqual(res["tp"], 1)
                        self.assertEqual(res["fp"], 0)

    def test_reproduce_incomplete_two_doc_copy_row_before_after(self):
        """Reproduce the seed 7 gap: 2 docs + copy row only matched before D1, rejected after."""
        for difficulty in ("default", "hard"):
            cfg = {"errors": {"duplicate_invoice": 1}}
            if difficulty == "hard":
                cfg["difficulty"] = "hard"
            ep = generate(7, cfg)
            iss = ep["truth"]["issues"][0]
            orig_inv, dup_inv = sorted(
                [i for i in ep["tables"]["invoices"] if i["invoice_id"] in iss["affected_ids"]],
                key=lambda x: x["issued_at"]
            )
            orig_doc, dup_doc = orig_inv["doc_id"], dup_inv["doc_id"]
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            ev_rows = [rows[i] for i in iss["evidence_sets"][0] if i in rows]
            orig_row = next(r["row_id"] for r in ev_rows if r["invoice_id"] == orig_inv["invoice_id"])
            copy_row = next(r["row_id"] for r in ev_rows if r["invoice_id"] == dup_inv["invoice_id"])
            if difficulty == "default":  # the original seed-7 gap from REVIEW.md
                self.assertEqual((orig_row, copy_row), ("R390", "R445"))

            # Incomplete submission (the "before" pattern: 2 docs + copy row only)
            incomplete_sub = {
                "episode_id": ep["manifest"]["episode_id"],
                "findings": [{
                    "type": "duplicate_invoice",
                    "affected_ids": sorted(iss["affected_ids"]),
                    "claimed_amount_minor": iss["expected_amount_minor"],
                    "currency": iss["currency"],
                    "evidence_ids": [orig_doc, dup_doc, copy_row],
                    "explanation": "incomplete before pattern",
                }]
            }
            res_before = grade_episode(ep, incomplete_sub, 4)
            self.assertEqual(res_before["tp"], 0, f"{difficulty} incomplete must not match")
            self.assertEqual(res_before["fp"], 1)
            self.assertEqual(res_before["fn"], 1)

            # Complete submission (augmented with original invoice's booking row)
            complete_sub = copy.deepcopy(incomplete_sub)
            complete_sub["findings"][0]["evidence_ids"].append(orig_row)
            res_after = grade_episode(ep, complete_sub, 4)
            self.assertEqual(res_after["tp"], 1, f"{difficulty} complete must match")
            self.assertEqual(res_after["fp"], 0)
            self.assertEqual(res_after["fn"], 0)
            self.assertEqual(res_after["reward"], 0.992)

    def test_zero_and_reversed_postings_do_not_prove_a_duplicate(self):
        from auditenv.verify import Books, _sufficient

        for mode in ("default", "hard"):
            ep = generate(7, {"difficulty": mode, "errors": {"duplicate_invoice": 1}})
            tables = ep["tables"]
            issue = ep["truth"]["issues"][0]
            evidence = issue["evidence_sets"][0]
            books = Books(ep["manifest"], tables)
            docs = {d["doc_id"]: d for d in tables["invoices"]}
            rows = {r["row_id"]: r for r in tables["ledger"]}
            for row_id in (key for key in evidence if key in rows):
                row = rows[row_id]
                for debit, credit in ((0, 0), (row["credit_minor"], row["debit_minor"])):
                    changed = dict(rows, **{row_id: dict(row, debit_minor=debit, credit_minor=credit)})
                    self.assertTrue(_sufficient(books, issue, evidence, changed, docs))

    def test_missing_evidence_rejected_default_and_hard(self):
        """Missing original row, copy row, or document fails matching and verifier."""
        for difficulty in ("default", "hard"):
            cfg = {"errors": {"duplicate_invoice": 1}}
            if difficulty == "hard":
                cfg["difficulty"] = "hard"
            ep = generate(7, cfg)
            iss = ep["truth"]["issues"][0]
            full_set = list(iss["evidence_sets"][0])  # 2 docs + 2 rows
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            docs = {d["doc_id"]: d for d in ep["tables"]["invoices"]}

            doc_ids = [i for i in full_set if i in docs]
            row_ids = [i for i in full_set if i in rows]
            self.assertEqual(len(doc_ids), 2)
            self.assertEqual(len(row_ids), 2)

            # Test 1: missing original row in submission
            bad_sub = {
                "episode_id": ep["manifest"]["episode_id"],
                "findings": [{"type": "duplicate_invoice", "affected_ids": sorted(iss["affected_ids"]),
                              "claimed_amount_minor": iss["expected_amount_minor"], "currency": iss["currency"],
                              "evidence_ids": [doc_ids[0], doc_ids[1], row_ids[1]], "explanation": "missing orig"}]
            }
            self.assertEqual(grade_episode(ep, bad_sub, 0)["tp"], 0)

            # Test 2: missing copy row in submission
            bad_sub["findings"][0]["evidence_ids"] = [doc_ids[0], doc_ids[1], row_ids[0]]
            self.assertEqual(grade_episode(ep, bad_sub, 0)["tp"], 0)

            # Test 3: missing one doc in submission
            bad_sub["findings"][0]["evidence_ids"] = [doc_ids[0], row_ids[0], row_ids[1]]
            self.assertEqual(grade_episode(ep, bad_sub, 0)["tp"], 0)

            # Test 4: verifier rejects episode truth if missing original row
            bad_ep = copy.deepcopy(ep)
            bad_ep["truth"]["issues"][0]["evidence_sets"] = [[doc_ids[0], doc_ids[1], row_ids[1]]]
            problems = verify_episode(bad_ep)
            self.assertTrue(any("booking rows for both invoices" in p or "missing a record" in p for p in problems))

            # Test 5: verifier rejects episode truth if missing one doc
            bad_ep2 = copy.deepcopy(ep)
            bad_ep2["truth"]["issues"][0]["evidence_sets"] = [[doc_ids[0], row_ids[0], row_ids[1]]]
            problems2 = verify_episode(bad_ep2)
            self.assertTrue(any("both documents" in p or "missing a record" in p for p in problems2))

    def test_substituted_evidence_rejected_default_and_hard(self):
        """Substituted rows (unrelated invoice, duplicate copy row, cash row, payment row) fail."""
        for difficulty in ("default", "hard"):
            cfg = {"errors": {"duplicate_invoice": 1}}
            if difficulty == "hard":
                cfg["difficulty"] = "hard"
            ep = generate(7, cfg)
            iss = ep["truth"]["issues"][0]
            full_set = list(iss["evidence_sets"][0])
            rows = {r["row_id"]: r for r in ep["tables"]["ledger"]}
            docs = {d["doc_id"]: d for d in ep["tables"]["invoices"]}

            doc_ids = [i for i in full_set if i in docs]
            row_ids = [i for i in full_set if i in rows]

            # Find unrelated invoice row
            unrelated_row = next(r["row_id"] for r in ep["tables"]["ledger"]
                                 if r["invoice_id"] and r["invoice_id"] not in iss["affected_ids"]
                                 and r["account"] == "1200")
            # Find cash row
            cash_row = next(r["row_id"] for r in ep["tables"]["ledger"] if r["account"] == "1000")

            def check_bad_set(bad_set, desc):
                sub = {
                    "episode_id": ep["manifest"]["episode_id"],
                    "findings": [{"type": "duplicate_invoice", "affected_ids": sorted(iss["affected_ids"]),
                                  "claimed_amount_minor": iss["expected_amount_minor"], "currency": iss["currency"],
                                  "evidence_ids": bad_set, "explanation": desc}]
                }
                res = grade_episode(ep, sub, 0)
                self.assertEqual(res["tp"], 0, f"Matcher should reject {desc}")
                bad_ep = copy.deepcopy(ep)
                bad_ep["truth"]["issues"][0]["evidence_sets"] = [bad_set]
                probs = verify_episode(bad_ep)
                self.assertTrue(len(probs) > 0, f"Verifier should reject {desc}")

            # Sub 1: unrelated invoice row instead of orig row
            check_bad_set([doc_ids[0], doc_ids[1], unrelated_row, row_ids[1]], "unrelated invoice row")

            # Sub 2: duplicated copy row instead of orig row
            check_bad_set([doc_ids[0], doc_ids[1], row_ids[1], row_ids[1]], "duplicated copy row")

            # Sub 3: cash row (account 1000) instead of orig row
            check_bad_set([doc_ids[0], doc_ids[1], cash_row, row_ids[1]], "cash row (wrong account)")
