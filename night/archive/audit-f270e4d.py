"""Run from the Genesis repository root. All exported data stays in a temporary directory."""
import json
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from auditenv.export import export_episode, export_split
from auditenv.generator import generate
from auditenv.verify import main as verify_dir, verify_episode

ep = generate(2000, {"errors": {}})
with TemporaryDirectory() as tmp:
    root = Path(tmp)
    folder = root / ep["episode_id"]
    for case in ("control", "invalid FX", "out-of-period remittance", "missing version", "malformed timestamp"):
        sample = deepcopy(ep)
        tables, manifest = sample["tables"], sample["manifest"]
        if case == "invalid FX":
            row = next(row for row in tables["fx"] if row["fx_id"] == "2025-03-02:GBP:USD")
            row["rate"] = "not-a-rate"
        if case == "out-of-period remittance":
            pay = dict(next(p for p in tables["payments"] if p["amount_minor"] > 0), payment_id="P-future",
                       doc_id="D-future", timestamp="2027-01-01T12:00:00+00:00", invoice_refs=None)
            tables["payments"].append(pay)
            manifest["counts"]["payments"] += 1
            manifest["counts"]["documents"] += 1
            assert verify_episode(sample) == []
            pay["invoice_refs"] = [{"invoice_id": "nonexistent", "amount_minor": abs(pay["amount_minor"])+1}]
            print("payment", pay["payment_id"], pay["timestamp"], manifest["period_start"],manifest["period_end"])
        if case == "missing version":
            del manifest["schema_version"]
        if case == "malformed timestamp":
            tables["ledger"][0]["timestamp"] = "not-a-date"
            try:
                print("API diagnostics", verify_episode(sample))
            except ValueError as error:
                print("API raised", type(error).__name__, str(error))
        export_episode(sample, folder)
        print(case, "CLI exit", verify_dir(["--dir", str(root)]))

with TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg, out = root/"config.json", root/"split"
    cfg.write_text(json.dumps({"seeds": [1]}))
    export_split(cfg, out)
    cfg.write_text(json.dumps({"episodes": [{"seed":1}, {"seed":2}, {"seed":3,"config":{"errors":{"fx_error":13}}}]}))
    try:
        export_split(cfg, out)
    except ValueError as error:
        print("export rejected:", error)
    print("previously valid split after failure, CLI exit", verify_dir(["--dir",str(out)]))
