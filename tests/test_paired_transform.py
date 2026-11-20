"""Tests for strengthened paired checks and benign transform (T2)."""

from __future__ import annotations

import copy
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from auditenv.check import HEAVY, run_paired
from auditenv.generator import generate
from auditenv.matcher import grade
from auditenv.transform import transform


class TestPairedTransform(unittest.TestCase):
    def test_real_default_pairs_pass(self):
        with redirect_stdout(io.StringIO()):
            self.assertTrue(run_paired(n=4, hard=False))

    def test_real_hard_pairs_pass(self):
        with redirect_stdout(io.StringIO()):
            self.assertTrue(run_paired(n=4, hard=True))

    def test_stub_identity_transform_fails(self):
        def identity_stub(ep, s):
            return copy.deepcopy(ep)

        with patch("auditenv.transform.transform", side_effect=identity_stub):
            with redirect_stdout(io.StringIO()):
                self.assertFalse(run_paired(n=4, hard=False))
                self.assertFalse(run_paired(n=4, hard=True))

    def test_stub_identity_transform_fails_on_clean_episodes(self):
        def identity_stub(ep, s):
            return copy.deepcopy(ep)

        # Report the clean fixture independently of the heavy fixture.
        with patch("auditenv.transform.transform", side_effect=identity_stub):
            with redirect_stdout(io.StringIO()) as output:
                self.assertFalse(run_paired(n=2, hard=False))
            self.assertIn("0/2 pairs pass", output.getvalue())

    def test_untranslated_dirty_findings_earn_zero_tp(self):
        ep1 = generate(5000, HEAVY)
        ep2 = transform(ep1, 100)
        self.assertGreater(len(ep1["truth"]["issues"]), 0)

        untranslated = [
            {
                "type": iss["type"],
                "affected_ids": list(iss["affected_ids"]),
                "claimed_amount_minor": iss["expected_amount_minor"],
                "currency": iss["currency"],
                "evidence_ids": list(iss["evidence_sets"][0]),
            }
            for iss in ep1["truth"]["issues"]
        ]
        # Against transformed truth: old IDs must earn 0 TP
        m_trans = grade(ep2["truth"], {"episode_id": ep2["episode_id"], "findings": untranslated}, ep2["episode_id"], 0)
        self.assertEqual(m_trans["tp"], 0)

        # Against original truth: untranslated findings are the full answer
        m_orig = grade(ep1["truth"], {"episode_id": ep1["episode_id"], "findings": untranslated}, ep1["episode_id"], 0)
        self.assertEqual(m_orig["tp"], len(ep1["truth"]["issues"]))
        self.assertEqual(m_orig["fp"], 0)
        self.assertEqual(m_orig["fn"], 0)

    def test_relabelled_public_ids_and_fx_ids_stable(self):
        for seed, cfg in [(5000, HEAVY), (5001, {"errors": {}})]:
            ep1 = generate(seed, cfg)
            ep2 = transform(ep1, 100)

            id_map = ep2.get("provenance", {}).get("id_map", {})
            self.assertTrue(id_map)
            self.assertFalse(any(k == v for k, v in id_map.items()))

            for tbl, id_key in (("ledger", "row_id"), ("invoices", "doc_id"), ("payments", "doc_id")):
                rows1, rows2 = ep1["tables"][tbl], ep2["tables"][tbl]
                ids1 = [r[id_key] for r in rows1 if r.get(id_key)]
                ids2 = [r[id_key] for r in rows2 if r.get(id_key)]
                self.assertTrue(ids1)
                self.assertTrue(ids2)
                # Disjoint sets: new IDs must be remapped
                self.assertEqual(set(ids1) & set(ids2), set())
                self.assertEqual(set(ids2), {id_map[i] for i in ids1})

            # FX table has no relabelled IDs ("FX ids are stable")
            fx1, fx2 = ep1["tables"]["fx"], ep2["tables"]["fx"]
            fx_tuples1 = [(r["fx_id"], r["date"], r["source_currency"], r["target_currency"], r["rate"]) for r in fx1]
            fx_tuples2 = [(r["fx_id"], r["date"], r["source_currency"], r["target_currency"], r["rate"]) for r in fx2]
            self.assertEqual(set(fx_tuples1), set(fx_tuples2))

            # Row orders must be shuffled across all tables
            for tbl in ("ledger", "invoices", "payments", "fx"):
                self.assertNotEqual(ep1["tables"][tbl], ep2["tables"][tbl])

    def test_alternative_evidence_must_survive_translation(self):
        for change in ("drop", "add", "reorder"):
            def change_alternatives(episode, transform_seed):
                changed = transform(episode, transform_seed)
                issue = next(i for i in changed["truth"]["issues"] if len(i["evidence_sets"]) > 1)
                alternatives = issue["evidence_sets"]
                if change == "drop":
                    alternatives.pop()
                elif change == "add":
                    alternatives.append(alternatives[-1][:1])
                else:
                    alternatives.reverse()
                    for evidence in alternatives:
                        evidence.reverse()
                return changed

            with self.subTest(change=change), patch("auditenv.transform.transform", side_effect=change_alternatives):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(run_paired(n=1), change == "reorder")

    def test_changed_invoice_due_dates_fail(self):
        def change_due_dates(episode, transform_seed):
            changed = transform(episode, transform_seed)
            for invoice in changed["tables"]["invoices"]:
                invoice["due_at"] = invoice["issued_at"]
            return changed

        with patch("auditenv.transform.transform", side_effect=change_due_dates):
            with redirect_stdout(io.StringIO()) as output:
                self.assertFalse(run_paired(n=2))
            self.assertIn("0/2 pairs pass", output.getvalue())
            self.assertIn("invoices", output.getvalue())

    def test_shuffling_only_fx_fails(self):
        def shuffle_only_fx(episode, transform_seed):
            changed = transform(episode, transform_seed)
            mapping = changed["provenance"]["id_map"]
            for table, key in (("ledger", "row_id"), ("invoices", "doc_id"), ("payments", "doc_id")):
                order = {mapping[row[key]]: i for i, row in enumerate(episode["tables"][table])}
                changed["tables"][table].sort(key=lambda row: order[row[key]])
            return changed

        with patch("auditenv.transform.transform", side_effect=shuffle_only_fx):
            with redirect_stdout(io.StringIO()):
                self.assertFalse(run_paired(n=1))

    def test_stub_unrelabelled_ids_fails(self):
        def unrelabelled_stub(ep, s):
            out = transform(ep, s)
            # Reset table IDs back to original unmapped IDs
            id_map_rev = {v: k for k, v in out["provenance"]["id_map"].items()}
            for tbl, id_key in (("ledger", "row_id"), ("invoices", "doc_id"), ("payments", "doc_id")):
                for r in out["tables"][tbl]:
                    if r.get(id_key) in id_map_rev:
                        r[id_key] = id_map_rev[r[id_key]]
            return out

        with patch("auditenv.transform.transform", side_effect=unrelabelled_stub):
            with redirect_stdout(io.StringIO()) as output:
                self.assertFalse(run_paired(n=2, hard=False))
            self.assertIn("0/2 pairs pass", output.getvalue())


if __name__ == "__main__":
    unittest.main()
