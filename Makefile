.PHONY: check test verify fuzz stress attack golden mutate miner bench sensitivity chart


check:
	uv run python -m auditenv.check

test:
	uv run python -m unittest discover -s tests -t .

verify:
	uv run python -m auditenv.verify --seeds 0-199

fuzz:
	uv run python -m auditenv.fuzz --seeds 0-999

stress:
	uv run python -m auditenv.fuzz --stress reconcile --seeds 0-299
	uv run python -m auditenv.fuzz --hard --stress reconcile_hard --seeds 0-299

attack:
	uv run python -m auditenv.attack

golden:
	uv run python scripts/golden.py --check

mutate:
	uv run python scripts/mutate_reward.py

miner:
	uv run python scripts/shortcut_miner.py --report-only

bench:
	uv run python scripts/bench.py

sensitivity:
	uv run python scripts/sensitivity.py

chart:
	uv run python -m auditenv.check --json /tmp/auditenv-metrics.json && uv run python scripts/chart.py
