check:
	uv run python -m auditenv.check

test:
	uv run python -m unittest discover -s tests -t .

verify:
	uv run python -m auditenv.verify --seeds 0-199
