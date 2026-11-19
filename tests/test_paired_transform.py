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

        # n=2 tests seed 5000 (heavy) and seed 5001 (clean: {"errors": {}})
        with patch("auditenv.transform.transform", side_effect=identity_stub):
            with redirect_stdout(io.StringIO()):
                self.assertFalse(run_paired(n=2, hard=False))

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

    def test_stub_unshuffled_order_fails(self):
        def unshuffled_stub(ep, s):
            out = transform(ep, s)
            # Revert table orders to original unshuffled order
            for tbl in ("ledger", "invoices", "payments", "fx"):
                id_key = "row_id" if tbl == "ledger" else ("doc_id" if tbl in ("invoices", "payments") else None)
                if id_key:
                    id_map = out["provenance"]["id_map"]
                    lookup = {r[id_key]: r for r in out["tables"][tbl]}
                    out["tables"][tbl] = [lookup[id_map[r[id_key]]] for r in ep["tables"][tbl]]
                else:
                    out["tables"][tbl] = copy.deepcopy(ep["tables"][tbl])
            return out

        with patch("auditenv.transform.transform", side_effect=unshuffled_stub):
            with redirect_stdout(io.StringIO()):
                self.assertFalse(run_paired(n=2, hard=False))

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
            with redirect_stdout(io.StringIO()):
                self.assertFalse(run_paired(n=2, hard=False))


if __name__ == "__main__":
    unittest.main()
