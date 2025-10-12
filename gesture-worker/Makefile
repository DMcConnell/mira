PY=python3

.PHONY: setup run run-dev run-mac run-pi run-full fmt clean

setup:
	bash scripts/bootstrap.sh

run:
	bash scripts/run_full.sh

run-dev:
	bash scripts/run.sh

run-mac:
	MIRA_ENV=mac bash scripts/run_full.sh

run-pi:
	MIRA_ENV=pi bash scripts/run_full.sh

run-full:
	bash scripts/run_full.sh

fmt:
	. .venv/bin/activate && ruff check --fix . || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
