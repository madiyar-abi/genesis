"""Public baseline process speaking the jury observation/action protocol over stdio."""
import json
import sys

from .tool_spec import TOOLS
from .policies.flag_all import FlagAll
from .policies.random_explorer import RandomExplorer
from .policies.reconcile import Reconcile

POLICIES = {"random_explorer": RandomExplorer, "reconcile": Reconcile, "flag_all": FlagAll}
RESULT_KEY = {"get_record": "record", "get_document": "document", "calculator": "value"}


class JuryPolicy:
    """Baseline-policy adapter: jury observations in, jury actions `{"name", "args"}` out."""

    def __init__(self, policy):
        self.policy, self.last = policy, None

    def act(self, observation: dict) -> dict:
        if "task" in observation:  # first observation
            ours = {"task": observation["task"], "manifest": observation["manifest"], "policy": observation["policy"],
                    "tools": TOOLS, "steps_remaining": observation["remaining_steps"]}
            self.policy.reset(ours)
        else:
            result = observation["result"]
            if result is not None:
                if self.last == "list_records":
                    result = {"rows": result["records"], "next_cursor": result["next_cursor"]}
                elif self.last in RESULT_KEY:
                    result = {RESULT_KEY[self.last]: result}
            ours = {"steps_remaining": observation["remaining_steps"], "result": result, "error": observation["error"]}
        action = self.policy.act(ours)
        self.last = action.get("type")
        return {"name": action.get("type"), "args": {k: v for k, v in action.items() if k != "type"}}


def worker(name: str) -> int:
    """Policy process: one jury observation per stdin line, one action per stdout line."""
    policy = JuryPolicy(POLICIES[name](seed=0))
    for line in sys.stdin:
        print(json.dumps(policy.act(json.loads(line))), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(worker(sys.argv[1]))
