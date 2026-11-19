.PHONY: check test verify fuzz stress attack golden mutate


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
