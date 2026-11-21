"""R20 X3: judge_adapter.py on a jury machine that is not ours (no AUDITENV_SECRET, unknown HOME).

Every case runs in fresh subprocesses with a controlled environment: AUDITENV_SECRET / AUDITENV_KEY_FILE /
AUDITENV_GRADER_LOG removed, HOME (and AUDITENV_KEY_FILE where noted) pointed at scratch paths under SCRATCH,
so the real ~/.auditenv is never touched. Children run with cwd = repo root (as the jury does) unless a case
needs another cwd (relative episode_dir), and import judge_adapter from the repo root.

Cases:
  a  fresh HOME: generate + reset + steps + submit + score; key file 0600; same seed+config -> same episode_id
  b  read-only HOME (555) and missing HOMEs: works?, which key, what is printed, cross-process scoring agrees
  c  race: 8 simultaneous generate_episode on an empty key dir, x20
  d  episode_dir relative / spaces + non-ASCII / symlink / trailing slash
  e  observations never contain key, key path, episode_dir, seed or truth content (checked in every play)
  f  two JudgeEnv instances in one process alternating steps on different episodes

Run from the repo root:  env -u AUDITENV_SECRET uv run python night/r20/adapter_reality.py
Exit 0 = every case passed.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRATCH = "/tmp/r20-lead-x3"
SEED = 862415973  # distinctive, so a substring hit in an observation means a leak
SEED_B = 731904268
CONFIG: dict = {}
MARK = "@@RESULT@@"
FORBIDDEN_TRUTH_KEYS = ("issue_id", "evidence_sets", "expected_amount_minor", "scenario", "injections",
                        "provenance", "truth", "ISS-")


# ----------------------------------------------------------------------------------------------- child side

def _perfect_findings(episode_dir: str, episode_id: str) -> dict:
    with open(os.path.join(episode_dir, "grader", "truth.json"), encoding="utf-8") as fh:
        truth = json.load(fh)
    return {"episode_id": episode_id, "findings": [
        {"type": i["type"], "affected_ids": i["affected_ids"], "claimed_amount_minor": i["expected_amount_minor"],
         "currency": i["currency"], "evidence_ids": i["evidence_sets"][0]} for i in truth["issues"]]}


def _actions(first_ledger_id=None, first_doc=None):
    return [{"name": "list_records", "args": {"table": "ledger", "cursor": None, "limit": 5}},
            {"name": "list_records", "args": {"table": "invoices", "cursor": None, "limit": 2}},
            {"name": "get_record", "args": {"table": "ledger", "id": first_ledger_id or "R0"}},
            {"name": "get_document", "args": {"doc_id": first_doc or "nope"}},
            {"name": "calculator", "args": {"expression": "2*3"}},
            {"name": "nope", "args": {}},
            {"bad": "envelope"}]


def _play(ja, env, episode_dir: str, truth_dir: str) -> dict:
    """reset + a few steps + perfect submit; returns every value handed to the policy."""
    returned = []
    first, info = env.reset(0, {"mode": "closed", "episode_dir": episode_dir})
    returned.append(["reset", first, info])
    out = env.step(_actions()[0])
    returned.append(["step", *out])
    ledger_id = out[0]["result"]["records"][0]["row_id"]
    out = env.step(_actions()[1])
    returned.append(["step", *out])
    doc = out[0]["result"]["records"][0]["doc_id"]
    for action in _actions(ledger_id, doc)[2:]:
        returned.append(["step", *env.step(action)])
    findings = _perfect_findings(truth_dir, info["episode_id"])
    returned.append(["step", *env.step({"name": "submit", "args": {"findings": findings}})])
    return {"episode_id": info["episode_id"], "returned": returned, "findings": findings,
            "n_issues": len(findings["findings"])}


def child(spec: dict) -> dict:
    sys.path.insert(0, REPO)
    import judge_adapter as ja
    res: dict = {}
    if spec.get("wait_for"):
        real_link = os.link

        def link(src, dst, **kw):  # instrumentation only: did this process contend for the key file?
            try:
                real_link(src, dst, **kw)
                res["link"] = "won"
            except FileExistsError:
                res["link"] = "lost"
                raise
        os.link = link
        while not os.path.exists(spec["wait_for"]):
            time.sleep(0.0005)
    if spec.get("generate"):
        try:
            ja.generate_episode(spec["seed"], CONFIG, spec["generate"])
            with open(os.path.join(spec["generate"], "public", "manifest.json"), encoding="utf-8") as fh:
                res["episode_id"] = json.load(fh)["episode_id"]
        except Exception as exc:  # report, do not hide
            res["generate_error"] = f"{type(exc).__name__}: {exc}"
    if spec.get("read_key_file"):
        try:
            with open(spec["read_key_file"], encoding="ascii") as fh:
                res["key_file_text"] = fh.read()
        except OSError as exc:
            res["key_file_text"] = f"<{type(exc).__name__}>"
    if spec.get("play"):
        env = ja.make_env()
        res["play"] = _play(ja, env, spec["play"], spec.get("truth_dir") or spec["play"])
        res["grader_log"] = env.grader_log
    if spec.get("score"):
        findings = spec.get("findings") or _perfect_findings(spec.get("truth_dir") or spec["score"],
                                                             spec["score_episode_id"])
        res["score"] = ja.score_episode(spec["score"], findings, 7)
    if spec.get("alternate"):
        a, b = spec["alternate"]
        envs = [ja.make_env(), ja.make_env()]
        res["alt"] = _alternate(envs, a, b)
        res["solo"] = [_play(ja, ja.make_env(), a, a)["returned"], _play(ja, ja.make_env(), b, b)["returned"]]
        res["alt_logs"] = [e.grader_log for e in envs]
    res["key"] = ja.grader_key(warn=False)  # what this process would use (fallback is cached per process)
    import auditenv.grader_key as gk
    res["process_key"] = gk._PROCESS_KEY
    return res


def _alternate(envs, a, b):
    """The same action sequence as _play, interleaved step by step across two envs."""
    returned = [[], []]
    infos = []
    for i, (env, d) in enumerate(zip(envs, (a, b))):
        first, info = env.reset(0, {"mode": "closed", "episode_dir": d})
        returned[i].append(["reset", first, info])
        infos.append(info)
    outs = [env.step(_actions()[0]) for env in envs]
    for i in range(2):
        returned[i].append(["step", *outs[i]])
    ledger_ids = [o[0]["result"]["records"][0]["row_id"] for o in outs]
    outs = [env.step(_actions()[1]) for env in envs]
    for i in range(2):
        returned[i].append(["step", *outs[i]])
    docs = [o[0]["result"]["records"][0]["doc_id"] for o in outs]
    seqs = [_actions(ledger_ids[i], docs[i])[2:] for i in range(2)]
    for k in range(len(seqs[0])):
        for i in range(2):
            returned[i].append(["step", *envs[i].step(seqs[i][k])])
    for i, d in enumerate((a, b)):
        findings = _perfect_findings(d, infos[i]["episode_id"])
        returned[i].append(["step", *envs[i].step({"name": "submit", "args": {"findings": findings}})])
    return returned


# ---------------------------------------------------------------------------------------------- parent side

def run_child(spec: dict, home: str | None, key_file: str | None = None, cwd: str = REPO, wait: bool = True):
    env = {k: v for k, v in os.environ.items()
           if k not in ("AUDITENV_SECRET", "AUDITENV_KEY_FILE", "AUDITENV_GRADER_LOG", "HOME")}
    if home is not None:
        env["HOME"] = home
    if key_file is not None:
        env["AUDITENV_KEY_FILE"] = key_file
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child", json.dumps(spec)], cwd=cwd,
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc if not wait else collect(proc)


def collect(proc) -> dict:
    out, err = proc.communicate(timeout=300)
    lines = out.splitlines()
    result_lines = [ln for ln in lines if ln.startswith(MARK)]
    res = json.loads(result_lines[-1][len(MARK):]) if result_lines else {}
    res["_rc"] = proc.returncode
    res["_stdout_other"] = "\n".join(ln for ln in lines if not ln.startswith(MARK))
    res["_stderr"] = err
    return res


RESULTS: list[tuple[str, bool, str]] = []


def report(case: str, ok: bool, evidence: str) -> None:
    RESULTS.append((case, ok, evidence))
    print(f"[{'PASS' if ok else 'FAIL'}] {case}: {evidence}", flush=True)


def fresh(path: str) -> str:
    if os.path.lexists(path):
        _chmod_tree(path)
        if os.path.islink(path) or os.path.isfile(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)
    return path


def _chmod_tree(path):
    if os.path.isdir(path) and not os.path.islink(path):
        os.chmod(path, 0o755)
        for root, dirs, _ in os.walk(path):
            for d in dirs:
                p = os.path.join(root, d)
                if not os.path.islink(p):
                    os.chmod(p, 0o755)


def scan(play: dict, forbidden: dict) -> list[str]:
    """Leaks: forbidden strings or truth-only keys anywhere in what reset/step returned; closed-mode reward/info."""
    blob = json.dumps(play["returned"], ensure_ascii=False)
    blob_ascii = json.dumps(play["returned"])
    hits = [f"{name}={value!r}" for name, value in forbidden.items()
            if value and (value in blob or value in blob_ascii)]
    hits += [f"truth-key {k!r}" for k in FORBIDDEN_TRUTH_KEYS if k in blob]
    for entry in play["returned"]:
        if entry[0] == "reset":
            if set(entry[2]) != {"episode_id", "mode", "max_steps"}:
                hits.append(f"reset info keys {sorted(entry[2])}")
        else:
            _, _obs, reward, _term, _trunc, info = entry
            if reward != 0.0 or info != {}:
                hits.append(f"closed step reward={reward} info={info}")
    return hits


def ok_run(res: dict) -> bool:
    return res.get("_rc") == 0 and "generate_error" not in res


def case_a():
    home = fresh(f"{SCRATCH}/a_home")
    os.makedirs(home)
    ep1, ep2 = fresh(f"{SCRATCH}/a_ep1"), fresh(f"{SCRATCH}/a_ep2")
    r1 = run_child({"seed": SEED, "generate": ep1, "play": ep1}, home)
    keyfile = f"{home}/.auditenv/grader.key"
    if r1.get("play"):
        r1["score"] = run_child({"score": ep1, "score_episode_id": r1["episode_id"]}, home).get("score")
    mode = stat.S_IMODE(os.stat(keyfile).st_mode) if os.path.exists(keyfile) else None
    dmode = stat.S_IMODE(os.stat(os.path.dirname(keyfile)).st_mode) if os.path.exists(keyfile) else None
    r2 = run_child({"seed": SEED, "generate": ep2}, home)
    with open(keyfile) as fh:
        file_key = fh.read().strip()
    score = r1.get("score") or {}
    n = (r1.get("play") or {}).get("n_issues")
    ok = (ok_run(r1) and ok_run(r2) and mode == 0o600 and r1["key"] == file_key == r2["key"]
          and r1["episode_id"] == r2["episode_id"] and score.get("tp") == n and score.get("fn") == 0
          and r1["process_key"] == "" and len(file_key) == 64)
    report("a fresh HOME", ok,
           f"rc={r1['_rc']},{r2['_rc']} key file mode={oct(mode or 0)} dir mode={oct(dmode or 0)} "
           f"key==file key in both procs={r1['key'] == file_key == r2['key']} episode_id {r1.get('episode_id')} "
           f"== {r2.get('episode_id')}; score tp={score.get('tp')}/{n} fn={score.get('fn')} "
           f"return={score.get('return')}; stderr: {r1['_stderr'].strip()!r}")
    leaks = scan(r1["play"], {"key": file_key, "key_path": keyfile, "episode_dir": ep1, "seed": str(SEED),
                              "home": home})
    report("e leak scan (a)", not leaks, f"{len(r1['play']['returned'])} returns scanned; hits={leaks}")
    return file_key


def case_b():
    ro = fresh(f"{SCRATCH}/b_ro_home")
    os.makedirs(ro)
    os.chmod(ro, 0o555)
    missing_parent_writable = fresh(f"{SCRATCH}/b_missing/home")  # parent dir does not exist either
    fresh(f"{SCRATCH}/b_missing")
    missing_unwritable = "/nonexistent-r20-lead-x3/home"  # '/' is read-only on macOS (and for non-root users)
    assert not os.path.exists("/nonexistent-r20-lead-x3")
    other_home = fresh(f"{SCRATCH}/b_other_home")
    os.makedirs(other_home)
    for label, home in (("read-only HOME 555", ro), ("missing HOME, parent creatable", missing_parent_writable),
                        ("missing HOME, unwritable parent", missing_unwritable)):
        ep, ep2 = fresh(f"{SCRATCH}/b_ep_{len(label)}"), fresh(f"{SCRATCH}/b_ep2_{len(label)}")
        r1 = run_child({"seed": SEED, "generate": ep, "play": ep}, home)
        if not ok_run(r1):
            report(f"b {label}", False, f"rc={r1['_rc']} err={r1.get('generate_error')} stderr={r1['_stderr'][-600:]!r}")
            continue
        eid = r1["episode_id"]
        same = run_child({"score": ep, "score_episode_id": eid}, home)
        cross = run_child({"score": ep, "score_episode_id": eid}, other_home)  # another process, other key
        r2 = run_child({"seed": SEED, "generate": ep2}, home)
        keyfile = os.path.join(home, ".auditenv", "grader.key")
        created = os.path.exists(keyfile)
        fallback = r1["process_key"] != ""
        out_all = r1["_stdout_other"] + r1["_stderr"]
        key_printed = r1["key"] in out_all
        ok = (same.get("score") == cross.get("score") and (same.get("score") or {}).get("fn") == 0
              and not key_printed and r1["_stdout_other"] == "")
        report(f"b {label}", ok,
               f"rc=0 key source={'per-process fallback' if fallback else 'key file'} key file created={created} "
               f"2nd-process same seed episode_id {eid} vs {r2.get('episode_id')} "
               f"({'reproduces' if eid == r2.get('episode_id') else 'does NOT reproduce'}); "
               f"score same-HOME proc == other-HOME proc: {same.get('score') == cross.get('score')} "
               f"(tp={(same.get('score') or {}).get('tp')} fn={(same.get('score') or {}).get('fn')}); "
               f"stdout={r1['_stdout_other']!r}; key in output={key_printed}; stderr={r1['_stderr'].strip()!r}")
        leaks = scan(r1["play"], {"key": r1["key"], "key_path": keyfile, "episode_dir": ep, "seed": str(SEED),
                                  "home": home})
        report(f"e leak scan (b {label})", not leaks, f"hits={leaks}")
    os.chmod(ro, 0o755)
    if os.path.exists("/nonexistent-r20-lead-x3"):
        print("WARNING: /nonexistent-r20-lead-x3 was created", flush=True)


def case_c(rounds: int = 20, n: int = 8):
    problems, contended = [], []
    for r in range(rounds):
        keydir = fresh(f"{SCRATCH}/c_keys/r{r}")
        home = fresh(f"{SCRATCH}/c_home")
        os.makedirs(home)
        keyfile = f"{keydir}/sub/grader.key"  # neither keydir nor sub exist: makedirs races too
        start = f"{SCRATCH}/c_start"
        fresh(start)
        procs = [run_child({"seed": SEED, "generate": fresh(f"{SCRATCH}/c_ep/{r}_{i}"), "wait_for": start,
                            "read_key_file": keyfile}, home, key_file=keyfile, wait=False) for i in range(n)]
        time.sleep(0.4)  # let all interpreters reach the barrier
        open(start, "w").close()
        res = [collect(p) for p in procs]
        keys = {x.get("key") for x in res}
        eids = {x.get("episode_id") for x in res}
        texts = {x.get("key_file_text") for x in res}
        leftovers = [f for f in os.listdir(os.path.dirname(keyfile)) if f != "grader.key"]
        with open(keyfile) as fh:
            final = fh.read()
        mode = stat.S_IMODE(os.stat(keyfile).st_mode)
        bad = [x for x in res if not ok_run(x) or x.get("process_key")]
        links = [x.get("link") for x in res]
        contended.append(links.count("won") + links.count("lost"))
        if (bad or len(keys) != 1 or len(eids) != 1 or texts != {final} or len(final.strip()) != 64
                or leftovers or mode != 0o600 or keys != {final.strip()}):
            problems.append(f"round {r}: keys={len(keys)} eids={eids} texts={len(texts)} leftovers={leftovers} "
                            f"mode={oct(mode)} bad={[(x['_rc'], x.get('generate_error'), x['_stderr'][-300:]) for x in bad]}")
    report(f"c race {n} procs x {rounds}", not problems,
           f"{rounds} rounds: one key, one episode_id, full 64-hex key file 0600, no tmp leftovers, no fallback; "
           f"processes that tried to create the key per round (contention, 1 = no race): {contended}"
           if not problems else "; ".join(problems[:3]))


def case_d(file_key: str):
    home = f"{SCRATCH}/a_home"  # reuse the key from (a)
    base = fresh(f"{SCRATCH}/ep ü 7")
    link = fresh(f"{SCRATCH}/link to ep")
    r0 = run_child({"seed": SEED, "generate": base + "/"}, home)  # trailing slash on output_dir too
    if not ok_run(r0):
        report("d generate into 'ep ü 7/'", False, f"{r0.get('generate_error')} {r0['_stderr'][-400:]!r}")
        return
    os.symlink(base, link)
    eid = r0["episode_id"]
    variants = [("spaces+non-ASCII abs", base, REPO), ("trailing slash", base + "/", REPO),
                ("symlinked dir", link, REPO), ("symlink + trailing slash", link + "/", REPO),
                ("relative (cwd=scratch)", "ep ü 7", SCRATCH), ("relative ./x/../", "./c_ep/../ep ü 7/", SCRATCH),
                ("NFD spelling of ü", f"{SCRATCH}/ep ü 7", REPO)]
    for label, path, cwd in variants:
        r = run_child({"play": path, "truth_dir": base, "score": path, "truth_dir_score": base,
                       "score_episode_id": eid}, home, cwd=cwd)
        score = r.get("score") or {}
        ok = r["_rc"] == 0 and r.get("play", {}).get("episode_id") == eid and score.get("fn") == 0
        leaks = scan(r["play"], {"key": file_key, "episode_dir": path.rstrip("/"), "base": base, "link": link,
                                 "seed": str(SEED)}) if r.get("play") else ["no play"]
        report(f"d {label}", ok and not leaks,
               f"rc={r['_rc']} episode_id={r.get('play', {}).get('episode_id')} tp={score.get('tp')} "
               f"fn={score.get('fn')} leaks={leaks}" + ("" if r["_rc"] == 0 else f" stderr={r['_stderr'][-500:]!r}"))
    # generate directly into a relative output_dir
    fresh(f"{SCRATCH}/rel_out")
    r = run_child({"seed": SEED, "generate": "rel_out", "play": "rel_out"}, home, cwd=SCRATCH)
    report("d generate into relative output_dir", ok_run(r) and r.get("episode_id") == eid
           and os.path.exists(f"{SCRATCH}/rel_out/grader/truth.json"),
           f"rc={r['_rc']} episode_id={r.get('episode_id')} (same as abs: {r.get('episode_id') == eid})")


def case_f(file_key: str):
    home = f"{SCRATCH}/a_home"
    a, b = fresh(f"{SCRATCH}/f_a"), fresh(f"{SCRATCH}/f_b")
    run_child({"seed": SEED, "generate": a}, home)
    run_child({"seed": SEED_B, "generate": b}, home)
    r = run_child({"alternate": [a, b]}, home)
    if r["_rc"] != 0:
        report("f two JudgeEnv alternating", False, r["_stderr"][-600:])
        return
    same = [r["alt"][i] == r["solo"][i] for i in range(2)]
    eids = [r["alt"][i][0][2]["episode_id"] for i in range(2)]
    logs = [[e["episode_id"] for e in log] for log in r["alt_logs"]]
    remaining = [[e[1]["remaining_steps"] for e in r["alt"][i]] for i in range(2)]
    ok = all(same) and eids[0] != eids[1] and logs == [[eids[0]], [eids[1]]]
    report("f two JudgeEnv alternating", ok,
           f"interleaved == solo transcripts: {same}; episode_ids {eids}; grader_log per env {logs}; "
           f"remaining_steps A {remaining[0]} B {remaining[1]}; "
           f"true rewards {[e.get('reward') for log in r['alt_logs'] for e in log]}")
    for i, d in enumerate((a, b)):
        leaks = scan({"returned": r["alt"][i]}, {"key": file_key, "episode_dir": d, "seed": str((SEED, SEED_B)[i])})
        report(f"e leak scan (f env {'AB'[i]})", not leaks, f"hits={leaks}")


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    file_key = case_a()
    case_b()
    case_c()
    case_d(file_key)
    case_f(file_key)
    failed = [c for c, ok, _ in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed" + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        spec = json.loads(sys.argv[2])
        if spec.get("score") and spec.get("truth_dir_score"):
            spec["truth_dir"] = spec["truth_dir_score"]
        out = child(spec)
        print(MARK + json.dumps(out, ensure_ascii=False), flush=True)
    else:
        sys.exit(main())
