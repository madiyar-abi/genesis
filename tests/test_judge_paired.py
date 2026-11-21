"""Block 4 of the jury's check definitions (P01-P20): the jury copies an exported episode, permutes its records and/or
renames ids consistently in every table, reference, truth and provenance, and serves the copy through
`reset({"episode_dir": ...})`. The transform below is written independently of `auditenv.transform`, as the jury's is.
Each pair passes when (1) replaying the original gives identical transitions and rewards, (2) the oracle's answer on
the copy maps back to the original answer, (3) TP/FP/FN/P/R/F1/return are equal for equal inspection steps, and
(4) a broken evidence set is not rewarded on either side."""

import json
import os
import random
import shutil
import tempfile
import unittest

import judge_adapter as ja
from auditenv import jury
from auditenv.export import export_episode
from auditenv.load import load_episode
from auditenv.verify import verify_episode

SCENARIOS = list(jury.SCENARIOS.values())  # D01-D20 of Block 2 (README "Jury adapter")
ID_FIELDS = {"row_id": "R", "doc_id": "D", "invoice_id": "I", "payment_id": "P", "entity_id": "E"}


def jury_transform(ep: dict, permute: bool, rename: bool, seed: int) -> tuple[dict, dict]:
    """Return (copy, mapping new id -> old id). Each id space gets its own fresh names; fx_id (date:pair) is a key,
    not a surrogate id, so it stays; line_items keep their order."""
    rng = random.Random(seed)
    ep = json.loads(json.dumps(ep))
    t = ep["tables"]
    forward = {}
    if rename:
        for field, prefix in ID_FIELDS.items():
            values = sorted({r[field] for table in t.values() for r in table if r.get(field) is not None})
            fresh = list(range(len(values)))
            rng.shuffle(fresh)
            forward.update({v: f"{prefix}{n:05d}x" for v, n in zip(values, fresh)})

    def ren(value):
        return forward.get(value, value) if isinstance(value, str) else value

    for table in t.values():
        for r in table:
            for field in ID_FIELDS:
                if field in r:
                    r[field] = ren(r[field])
            for ref in r.get("invoice_refs") or []:
                ref["invoice_id"] = ren(ref["invoice_id"])
        if permute:
            rng.shuffle(table)

    def deep(obj):  # closed files: every string that is an old id, and provenance journal keys "inv:<id>", "pay:<id>"
        if isinstance(obj, dict):
            return {k: deep(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [deep(v) for v in obj]
        if isinstance(obj, str) and obj[:4] in ("inv:", "pay:"):
            return obj[:4] + ren(obj[4:])
        return ren(obj)

    ep["truth"], ep["provenance"] = deep(ep["truth"]), deep(ep["provenance"])
    return ep, {new: old for old, new in forward.items()}


def oracle(ep: dict) -> dict:
    return {"episode_id": ep["manifest"]["episode_id"],
            "findings": [{"type": i["type"], "affected_ids": list(i["affected_ids"]),
                          "claimed_amount_minor": i["expected_amount_minor"], "currency": i["currency"],
                          "evidence_ids": list(i["evidence_sets"][0]), "explanation": "oracle"}
                         for i in ep["truth"]["issues"]]}


def back(answer: dict, inverse: dict) -> list:
    """The answer with ids mapped back, as comparable sets per finding."""
    return sorted((f["type"], tuple(sorted(inverse.get(i, i) for i in f["affected_ids"])), f["claimed_amount_minor"],
                   f["currency"], tuple(sorted(inverse.get(i, i) for i in f["evidence_ids"])))
                  for f in answer["findings"])


def run(episode_dir: str, findings: dict, steps: list) -> list:
    """A fixed action script then the submit, in train mode so every reward is visible."""
    env = ja.make_env()
    out = [env.reset(0, {"mode": "train", "episode_dir": episode_dir})]
    for a in steps + [{"name": "submit", "args": {"findings": findings}}]:
        out.append(env.step(a))
    return out


class JudgePairedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.pairs = []
        for n, cfg in enumerate(SCENARIOS, start=1):
            src = os.path.join(cls.tmp, f"D{n:02d}")
            ja.generate_episode(5000 + n, cfg, src)
            permute, rename = (True, False) if n <= 5 else (False, True) if n <= 10 else (True, True)
            copy, inverse = jury_transform(load_episode(src), permute, rename, seed=n)
            dst = os.path.join(cls.tmp, f"P{n:02d}")
            export_episode(copy, dst)
            cls.pairs.append((n, src, dst, inverse))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_scenarios_have_the_declared_errors(self):
        counts = [len(load_episode(src)["truth"]["issues"]) for _, src, _, _ in self.pairs]
        self.assertEqual(counts, [0] * 5 + [1] * 10 + [2] * 5)

    def test_pairs(self):
        steps = [{"name": "list_records", "args": {"table": t, "cursor": None, "limit": 50}}
                 for t in ("ledger", "invoices", "payments", "fx")]
        steps += [{"name": "calculator", "args": {"expression": "0.1+0.2"}},
                  {"name": "get_record", "args": {"table": "ledger", "id": "no-such-row"}}]
        for n, src, dst, inverse in self.pairs:
            with self.subTest(pair=f"P{n:02d}"):
                orig, copy = load_episode(src), load_episode(dst)
                self.assertEqual(verify_episode(copy), [])  # the copy is still consistent, evidence still sufficient
                a, b = oracle(orig), oracle(copy)
                # 1. replay on the original is exact
                self.assertEqual(json.dumps(run(src, a, steps)), json.dumps(run(src, a, steps)))
                # 2. the oracle's answer on the copy is the original answer after mapping ids back
                self.assertEqual(back(b, inverse), back(a, {}))
                # 3. equal metrics and return for equal inspection steps, through the adapter and the env
                for k in (0, 6, 37):
                    self.assertEqual(ja.score_episode(src, a, k), ja.score_episode(dst, b, k))
                ra, rb = run(src, a, steps), run(dst, b, steps)
                self.assertEqual([x[1:] for x in ra[-1:]], [x[1:] for x in rb[-1:]])
                self.assertEqual(ra[-1][4]["inspection_steps"], len(steps))
                # 4. a broken evidence set is not rewarded, on either side
                if a["findings"]:
                    for answer in (a, b):
                        answer["findings"][0]["evidence_ids"] = answer["findings"][0]["evidence_ids"][1:]
                    sa, sb = ja.score_episode(src, a, 6), ja.score_episode(dst, b, 6)
                    self.assertEqual(sa, sb)
                    self.assertEqual(sa["fn"], 1)


if __name__ == "__main__":
    unittest.main()
