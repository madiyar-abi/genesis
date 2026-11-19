"""Narrated demo of the environment (for the demo video):

    uv run python -m auditenv.demo [--seed 2003] [--pause]

1. a generated company and the first observation
2. the scripted reconciliation policy investigating through tools, then submitting
3. the grader's view: matched findings, the recorded cause of each error
4. attacks: silence, flag-everything, guessed ids; a clean company
5. a closed (eval) run in a separate process: the policy never sees reward or truth
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile

from .env import AuditEnv
from .run import make_policy, run_episode

CFG = {"errors": {"duplicate_invoice": 1, "period_cutoff": 1}, "interacting": {"I1": 1}}


def h(title: str, pause: bool) -> None:
    if pause:
        input("\n[enter] ")
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def short_action(a: dict) -> str:
    t = a["type"]
    if t == "list_records":
        return f"list_records(table={a['table']}, cursor={a.get('cursor')})"
    if t == "get_document":
        return f"get_document({a['doc_id']})"
    if t == "get_record":
        return f"get_record({a['table']}, {a['id']})"
    if t == "calculator":
        return f"calculator({a['expression']!r})"
    return f"submit({len(a['findings']['findings'])} findings)"


def short_result(obs: dict) -> str:
    if obs["error"]:
        return f"error {obs['error']['code']}"
    r = obs["result"] or {}
    if "rows" in r:
        return f"{len(r['rows'])} rows of {r['total']}, next_cursor={r['next_cursor']}"
    if "document" in r:
        d = r["document"]
        return f"{r['kind']} {d.get('invoice_id') or d.get('payment_id')}, {len(d.get('line_items') or [])} line items"
    return json.dumps(r)[:70]


def play(env, name, seed, cfg, findings=None):
    if findings is None:
        return run_episode(env, None, seed, cfg, policy_factory=lambda e: make_policy(name, e))
    obs, _ = env.reset(seed, cfg)
    sub = {"episode_id": obs["manifest"]["episode_id"], "findings": findings(env, obs)}
    return [None, {"step": 1, "reward": env.step({"type": "submit", "findings": sub})[1]}]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=2003)
    ap.add_argument("--pause", action="store_true", help="wait for Enter between sections")
    args = ap.parse_args(argv)
    seed, pause = args.seed, args.pause
    env = AuditEnv()

    h("1. A synthetic company: reset(seed, config) -> first observation", pause)
    obs, info = env.reset(seed, CFG)
    m = obs["manifest"]
    print(f"episode_id   {m['episode_id']}   (HMAC of seed+config+version; with the grader key set, the seed cannot be recovered)")
    print(f"company      base {m['base_currency']}, timezone {m['timezone']}, "
          f"period {m['period_start']} .. {m['period_end']}")
    print(f"records      {m['counts']['ledger']} ledger rows, {m['counts']['invoices']} invoices, "
          f"{m['counts']['payments']} payments, {m['counts']['fx']} FX rates")
    print(f"budget       {obs['steps_remaining']} steps; tools: {', '.join(t['type'] for t in obs['tools'])}")
    print(f"task         {obs['task'][:150]}...")

    h("2. The scripted reconciliation policy investigates (read-only tools, 50 rows/page)", pause)
    traj = play(env, "reconcile", seed, CFG)
    for rec in traj[1:]:
        print(f"step {rec['step']:>3}  {short_action(rec['action']):<55} -> {short_result(rec['observation'])}")
    last = traj[-1]
    print("\nsubmitted findings:")
    for f in last["action"]["findings"]["findings"]:
        print(f"  {f['type']:<19} ids={f['affected_ids']} amount={f['claimed_amount_minor']} {f['currency']} "
              f"evidence={f['evidence_ids']}")
    res = env.result
    print(f"\nterminal reward {last['reward']:.3f} = clip(2*F1 - 1 - 0.002*{res['inspection_steps']} steps)   "
          f"P={res['precision']:.2f} R={res['recall']:.2f} F1={res['f1']:.2f}")

    h("3. Grader's view (closed files, never shown to the agent): truth and recorded causes", pause)
    ep = env._ep
    for iss in ep["truth"]["issues"]:
        label = next((lb for lb in res["labels"] if lb.get("issue_id") == iss["issue_id"]), None)
        print(f"  {iss['issue_id']:<6} {iss['type']:<19} scenario={iss['scenario']:<6} amount={iss['expected_amount_minor']:>10} "
              f"{'TP' if label else 'FN'}")
    for inj in ep["provenance"]["injections"]:
        print(f"         cause: {inj['description']}")

    h("4. Reward robustness: the same books, other answers", pause)
    def oracle(e, o):
        return [{"type": i["type"], "affected_ids": i["affected_ids"], "claimed_amount_minor":
                 i["expected_amount_minor"], "currency": i["currency"], "evidence_ids": i["evidence_sets"][0]}
                for i in e._ep["truth"]["issues"]]
    def guessed(e, o):
        inv = e._ep["tables"]["invoices"][:4]
        return [{"type": "duplicate_invoice", "affected_ids": [inv[0]["invoice_id"], inv[1]["invoice_id"]],
                 "claimed_amount_minor": inv[1]["total_minor"], "currency": o["manifest"]["base_currency"],
                 "evidence_ids": [inv[0]["doc_id"], inv[1]["doc_id"]]}]
    rows = [
        ("oracle (truth, 0 steps)", play(env, None, seed, CFG, oracle)[-1]["reward"]),
        ("reconcile policy", last["reward"]),
        ("silence (empty answer)", play(env, None, seed, CFG, lambda e, o: [])[-1]["reward"]),
        ("guessed ids", play(env, None, seed, CFG, guessed)[-1]["reward"]),
        ("oracle answer repeated twice", play(env, None, seed, CFG, lambda e, o: oracle(e, o) * 2)[-1]["reward"]),
        ("flag-everything attack", play(env, "flag_all", seed, CFG)[-1]["reward"]),
        ("random explorer", play(env, "random", seed, CFG)[-1]["reward"]),
    ]
    for name, r in rows:
        print(f"  {name:<32} reward {r:7.3f}")
    clean = {"errors": {}}
    print(f"\n  clean company, silence           reward {play(env, None, seed, clean, lambda e, o: [])[-1]['reward']:7.3f}")
    print(f"  clean company, guessed ids       reward {play(env, None, seed, clean, guessed)[-1]['reward']:7.3f}")
    print(f"  clean company, reconcile policy  reward {play(env, 'reconcile', seed, clean)[-1]['reward']:7.3f}")

    h("5. Closed run: environment + grader in another process, hidden episode list", pause)
    from .client import RemoteEnv
    with tempfile.TemporaryDirectory() as d:
        log, hidden = os.path.join(d, "grader.jsonl"), os.path.join(d, "hidden.json")
        with open(hidden, "w") as fh:
            json.dump({"seeds": [seed], "config": CFG}, fh)
        with RemoteEnv(grader_log=log, episodes=hidden) as remote:
            obs, _ = remote.reset()
            pol = make_policy("reconcile", None)
            pol.reset(obs)
            rewards = []
            while True:
                obs, r, term, trunc, info = remote.step(pol.act(obs))
                rewards.append(r)
                if term or trunc:
                    break
        print(f"  policy side: {len(rewards)} steps, rewards seen = {sorted(set(rewards))}, final info = {info}")
        with open(log) as fh:
            g = json.loads(fh.readline())
        print(f"  grader log : reward {g['reward']:.3f}, F1 {g['f1']:.2f}, TP {g['tp']} FP {g['fp']} FN {g['fn']}")
    print("\nDone. Full check: uv run python -m auditenv.check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
